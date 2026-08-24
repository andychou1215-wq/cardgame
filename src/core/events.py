from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TriggerEvent:
    """A rules trigger waiting to be converted into one or more card effects.

    The event stores a snapshot of the source card identity/side so that
    on_leave and on_flip still resolve correctly even after the source moves
    zones or changes state.
    """

    trigger: str
    source_id: str
    card_id: str
    side: str
    owner_index: int
    trigger_target: Any | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class TriggerQueue:
    """FIFO trigger queue.

    AP/NAP ordering is produced by enqueue order.  The Game engine remains
    responsible for collecting simultaneous events in AP/NAP order before
    pushing them here.
    """

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
