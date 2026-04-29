from collections import defaultdict
from .models import BudgetItem


def calc_effective_qty(item: BudgetItem, patients: int, sites: int, visits: int, monitoring_visits_per_site: int) -> float:
    qt = item.qty_formula_type
    if qt == "per-patient":
        return float(patients)
    if qt == "per-visit":
        return float(patients * visits)
    if qt == "per-site":
        return float(sites)
    if qt == "per-site-visit":
        return float(sites * monitoring_visits_per_site)
    return float(item.manual_qty)


def calculate_budget(items, patients: int, sites: int, visits: int, monitoring_visits_per_site: int):
    rows = []
    category_totals = defaultdict(float)
    grand_total = 0.0
    for item in items:
        qty = calc_effective_qty(item, patients, sites, visits, monitoring_visits_per_site)
        total = round(item.unit_cost * qty, 2)
        grand_total += total
        category_totals[item.category] += total
        rows.append({
            "id": item.id,
            "category": item.category,
            "item_name": item.item_name,
            "unit_cost": item.unit_cost,
            "qty": qty,
            "line_total": total,
        })

    category_summary = []
    for category, total in sorted(category_totals.items()):
        share = (total / grand_total * 100) if grand_total else 0
        category_summary.append({"category": category, "total": round(total, 2), "share_pct": round(share, 2)})

    rows = sorted(rows, key=lambda x: x["line_total"], reverse=True)
    return {"rows": rows, "categories": category_summary, "grand_total": round(grand_total, 2)}


def compare_scenarios(a, b):
    delta = round(b.grand_total - a.grand_total, 2)
    delta_pct = round((delta / a.grand_total * 100), 2) if a.grand_total else 0
    return {"scenario_a": a.label, "scenario_b": b.label, "delta": delta, "delta_pct": delta_pct}
