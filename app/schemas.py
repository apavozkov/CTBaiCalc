from pydantic import BaseModel


class StudyCreate(BaseModel):
    name: str
    indication: str = "General"
    phase: str = "II"
    status: str = "Draft"

class StudyUpdate(BaseModel):
    name: str
    indication: str


class VersionCreate(BaseModel):
    name: str
    currency: str = "USD"


class ItemCreate(BaseModel):
    category: str
    subcategory: str = "General"
    item_name: str
    unit: str = "unit"
    unit_cost: float
    qty_formula_type: str = "fixed"
    manual_qty: float = 1
    notes: str = ""


class ScenarioCreate(BaseModel):
    label: str
    patients: int
    sites: int
    visits: int
    monitoring_visits_per_site: int = 4


class ComparePayload(BaseModel):
    scenario_a_id: int
    scenario_b_id: int
