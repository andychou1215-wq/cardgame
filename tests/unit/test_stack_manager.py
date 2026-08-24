from types import SimpleNamespace
from src.core.stack_manager import StackManager

def test_cancel_pending_item():
    item = SimpleNamespace(stack_item_id="x", status="pending")
    item.mark_cancelled = lambda reason: setattr(item, "status", "cancelled")
    manager = StackManager(SimpleNamespace(stack=[item]))
    assert manager.cancel("x")
    assert item.status == "cancelled"

def test_missing_item_not_cancelled():
    assert not StackManager(SimpleNamespace(stack=[])).cancel("missing")
