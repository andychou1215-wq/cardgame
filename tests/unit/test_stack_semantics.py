from types import SimpleNamespace
from src.core.stack import StackItem, validate_target_ref

class FakeGame:
    def __init__(self):
        self.units={"u1":object()}; self.owners={"u1":1}
    def find_unit(self,i): return self.units.get(i)
    def owner_of_card(self,i): return self.owners.get(i)

def test_stack_item_fizzle_status():
    i=StackItem("s","R1",1,[],"response_to_response")
    i.mark_fizzled("gone")
    assert i.status=="fizzled"

def test_target_revalidation():
    g=FakeGame(); r=SimpleNamespace(kind="unit",player_index=1,instance_id="u1")
    assert validate_target_ref(g,r).valid
    del g.units["u1"]
    assert not validate_target_ref(g,r).valid
