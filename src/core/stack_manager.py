class StackManager:
    def __init__(self, priority_window):
        self.window = priority_window

    def pending_items(self):
        return [
            item for item in self.window.stack
            if getattr(item, "status", "pending") == "pending"
        ]

    def find(self, stack_item_id: str):
        for item in self.window.stack:
            if getattr(item, "stack_item_id", None) == stack_item_id:
                return item
        return None

    def cancel(self, stack_item_id: str, reason: str = "countered") -> bool:
        item = self.find(stack_item_id)
        if item is None or getattr(item, "status", None) != "pending":
            return False
        item.mark_cancelled(reason)
        return True
