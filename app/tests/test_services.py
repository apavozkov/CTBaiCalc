from app.services import calculate_budget


class I:
    def __init__(self, id, category, item_name, unit_cost, qty_formula_type, manual_qty):
        self.id=id; self.category=category; self.item_name=item_name; self.unit_cost=unit_cost; self.qty_formula_type=qty_formula_type; self.manual_qty=manual_qty


def test_calculate_budget():
    items=[I(1,'Sites','A',100,'per-patient',0), I(2,'Logistics','B',10,'fixed',5)]
    res=calculate_budget(items, patients=10, sites=2, visits=3, monitoring_visits_per_site=1)
    assert res['grand_total']==1050
    assert len(res['categories'])==2
