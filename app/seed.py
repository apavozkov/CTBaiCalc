from .database import SessionLocal, engine, Base
from .models import Study, BudgetVersion, BudgetItem


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(Study).count() > 0:
        db.close()
        return

    categories = ["Sites", "Monitoring", "Laboratory", "Logistics"]
    for i in range(1, 6):
        study = Study(name=f"CT-{1000+i}", indication="Oncology", phase="III", status="Draft")
        db.add(study)
        db.flush()
        for v in range(1, 3):
            version = BudgetVersion(study_id=study.id, name=f"Baseline v{v}", currency="USD")
            db.add(version)
            db.flush()
            for j in range(1, 31):
                cat = categories[j % len(categories)]
                qtype = ["per-patient", "per-visit", "per-site", "fixed"][j % 4]
                db.add(BudgetItem(
                    budget_version_id=version.id,
                    category=cat,
                    subcategory="Default",
                    item_name=f"{cat} item {j}",
                    unit="service",
                    unit_cost=50 + j * 3,
                    qty_formula_type=qtype,
                    manual_qty=10,
                    notes="Demo"
                ))
    db.commit()
    db.close()


if __name__ == "__main__":
    run_seed()
