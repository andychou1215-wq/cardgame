from dataclasses import dataclass

@dataclass(frozen=True)
class StackTargetRef:
    stack_item_id: str

    @property
    def key(self) -> str:
        return f"stack:{self.stack_item_id}"
