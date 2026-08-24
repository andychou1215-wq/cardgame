from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TriggerEvent:
    trigger: str
    source_id: str
    card_id: str
    side: str
    owner_index: int
    trigger_target: Any | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class TriggerQueue:
    def __init__(self) -> None:
        self._items: list[TriggerEvent] = []

    def __bool__(self) -> bool:
        return bool(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def push(self, event: TriggerEvent) -> None:
        self._items.append(event)

    def pop(self) -> TriggerEvent:
        if not self._items:
            raise IndexError("trigger queue is empty")
        return self._items.pop(0)

    def clear(self) -> None:
        self._items.clear()

    def snapshot(self) -> tuple[TriggerEvent, ...]:
        return tuple(self._items)
