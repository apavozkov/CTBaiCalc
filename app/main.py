import json
import os
from fastapi import FastAPI, Depends, HTTPException, Request
from pathlib import Path
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import httpx
from openpyxl import Workbook
from io import BytesIO

from .database import Base, engine, get_db
from .models import Study, BudgetVersion, BudgetItem, ScenarioRun, AIReport
from .schemas import StudyCreate, StudyUpdate, VersionCreate, VersionUpdate, ItemCreate, ScenarioCreate, ComparePayload
from .services import calculate_budget, compare_scenarios
from datetime import datetime

app = FastAPI(title="CTBaiCalc")
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

Base.metadata.create_all(bind=engine)


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    studies = db.query(Study).order_by(Study.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "studies": studies})


@app.post("/api/studies")
def create_study(payload: StudyCreate, db: Session = Depends(get_db)):
    study = Study(**payload.model_dump())
    db.add(study)
    db.commit()
    db.refresh(study)
    return {"id": study.id}


@app.put("/api/studies/{study_id}")
def update_study(study_id: int, payload: StudyUpdate, db: Session = Depends(get_db)):
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(404)
    study.name = payload.name
    study.indication = payload.indication
    db.commit()
    return {"ok": True}


@app.delete("/api/studies/{study_id}")
def delete_study(study_id: int, db: Session = Depends(get_db)):
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(404)
    db.delete(study)
    db.commit()
    return {"ok": True}


@app.get("/study/{study_id}", response_class=HTMLResponse)
def study_page(study_id: int, request: Request, db: Session = Depends(get_db)):
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(404)
    return templates.TemplateResponse("study.html", {"request": request, "study": study})


@app.post("/api/studies/{study_id}/versions")
def create_version(study_id: int, payload: VersionCreate, db: Session = Depends(get_db)):
    version = BudgetVersion(study_id=study_id, **payload.model_dump())
    db.add(version)
    db.commit()
    db.refresh(version)
    return {"id": version.id}


@app.put("/api/versions/{version_id}")
def rename_version(version_id: int, payload: VersionUpdate, db: Session = Depends(get_db)):
    version = db.get(BudgetVersion, version_id)
    if not version:
        raise HTTPException(404)
    version.name = payload.name
    db.commit()
    return {"ok": True}


@app.delete("/api/versions/{version_id}")
def delete_version(version_id: int, db: Session = Depends(get_db)):
    version = db.get(BudgetVersion, version_id)
    if not version:
        raise HTTPException(404)
    db.delete(version)
    db.commit()
    return {"ok": True}


@app.post("/api/versions/{version_id}/copy")
def copy_version(version_id: int, db: Session = Depends(get_db)):
    version = db.get(BudgetVersion, version_id)
    if not version:
        raise HTTPException(404)

    copied_name = f"{version.name} Copy {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    version_copy = BudgetVersion(study_id=version.study_id, name=copied_name, currency=version.currency)
    db.add(version_copy)
    db.flush()

    for item in version.items:
        item_copy = BudgetItem(
            budget_version_id=version_copy.id,
            category=item.category,
            subcategory=item.subcategory,
            item_name=item.item_name,
            unit=item.unit,
            unit_cost=item.unit_cost,
            qty_formula_type=item.qty_formula_type,
            manual_qty=item.manual_qty,
            notes=item.notes,
        )
        db.add(item_copy)

    db.commit()
    db.refresh(version_copy)
    return {"id": version_copy.id}


@app.get("/version/{version_id}", response_class=HTMLResponse)
def version_page(version_id: int, request: Request, db: Session = Depends(get_db)):
    version = db.get(BudgetVersion, version_id)
    if not version:
        raise HTTPException(404)
    return templates.TemplateResponse("version.html", {"request": request, "version": version})


@app.post("/api/versions/{version_id}/items")
def create_item(version_id: int, payload: ItemCreate, db: Session = Depends(get_db)):
    item = BudgetItem(budget_version_id=version_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}


@app.post("/api/versions/{version_id}/scenarios/recalculate")
def recalc(version_id: int, payload: ScenarioCreate, db: Session = Depends(get_db)):
    items = db.query(BudgetItem).filter(BudgetItem.budget_version_id == version_id).all()
    result = calculate_budget(items, payload.patients, payload.sites, payload.visits, payload.monitoring_visits_per_site)
    scen = ScenarioRun(budget_version_id=version_id, grand_total=result["grand_total"], **payload.model_dump())
    db.add(scen)
    db.commit()
    db.refresh(scen)
    return {"scenario_id": scen.id, **result}


@app.post("/api/ai/structure-analysis/{scenario_id}")
async def ai_structure(scenario_id: int, db: Session = Depends(get_db)):
    scenario = db.get(ScenarioRun, scenario_id)
    if not scenario:
        raise HTTPException(404)
    items = db.query(BudgetItem).filter(BudgetItem.budget_version_id == scenario.budget_version_id).all()
    calc = calculate_budget(items, scenario.patients, scenario.sites, scenario.visits, scenario.monitoring_visits_per_site)

    prompt = {
        "task": "Analyze structure, top cost drivers, optimization ideas without harming data quality.",
        "scenario": {"label": scenario.label, "patients": scenario.patients, "sites": scenario.sites, "visits": scenario.visits},
        "categories": calc["categories"],
        "top_rows": calc["rows"][:10],
    }

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        text = "AI disabled: set OPENROUTER_API_KEY"
    else:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": os.getenv("OPENROUTER_MODEL", "openrouter/auto"),
            "messages": [
                {"role": "system", "content": "You are a clinical trial finance analyst. Use only given JSON."},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
            ]
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]

    report = AIReport(scenario_run_id=scenario.id, report_type="structure", input_snapshot=json.dumps(prompt, ensure_ascii=False), output_text=text)
    db.add(report)
    db.commit()
    return {"report": text}


@app.post("/api/ai/compare")
def ai_compare(payload: ComparePayload, db: Session = Depends(get_db)):
    a = db.get(ScenarioRun, payload.scenario_a_id)
    b = db.get(ScenarioRun, payload.scenario_b_id)
    if not a or not b:
        raise HTTPException(404)
    return compare_scenarios(a, b)


@app.get("/api/scenarios/{scenario_id}/export.xlsx")
def export_xlsx(scenario_id: int, db: Session = Depends(get_db)):
    scenario = db.get(ScenarioRun, scenario_id)
    if not scenario:
        raise HTTPException(404)
    items = db.query(BudgetItem).filter(BudgetItem.budget_version_id == scenario.budget_version_id).all()
    calc = calculate_budget(items, scenario.patients, scenario.sites, scenario.visits, scenario.monitoring_visits_per_site)

    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["Scenario", scenario.label])
    ws.append(["Grand Total", calc["grand_total"]])
    ws.append([])
    ws.append(["Category", "Total", "Share %"])
    for c in calc["categories"]:
        ws.append([c["category"], c["total"], c["share_pct"]])

    ws2 = wb.create_sheet("Line Items")
    ws2.append(["Category", "Item", "Unit Cost", "Qty", "Line Total"])
    for r in calc["rows"]:
        ws2.append([r["category"], r["item_name"], r["unit_cost"], r["qty"], r["line_total"]])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=scenario_{scenario_id}.xlsx"})
