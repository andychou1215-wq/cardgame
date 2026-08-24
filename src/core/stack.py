from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class StackItem:
    """One response/priority object waiting to resolve.

    Field order intentionally preserves the M1.3 positional constructor:

        StackItem(source_id, card_id, controller_index, effects, trigger)

    M1.4's stack_item_id is optional and comes after the original required
    fields so older tests/callers remain compatible.
    """

    source_id: str
    card_id: str
    controller_index: int
    effects: list[Any]
    trigger: str

    stack_item_id: str = ""
    trigger_target: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    status: str = "pending"
    result_reason: str = ""

    def __post_init__(self) -> None:
        if not self.stack_item_id:
            self.stack_item_id = f"stk-{uuid4().hex}"

    def mark_resolved(self) -> None:
        self.status = "resolved"
        self.result_reason = ""

    def mark_fizzled(self, reason: str) -> None:
        self.status = "fizzled"
        self.result_reason = reason

    def mark_cancelled(self, reason: str = "") -> None:
        self.status = "cancelled"
        self.result_reason = reason


@dataclass(frozen=True)
class TargetValidation:
    valid: bool
    reason: str = ""


def validate_target_ref(game: Any, target: Any | None) -> TargetValidation:
    if target is None:
        return TargetValidation(True)

    kind = getattr(target, "kind", None)
    player_index = getattr(target, "player_index", None)
    instance_id = getattr(target, "instance_id", None)

    if kind == "leader":
        if player_index not in (0, 1):
            return TargetValidation(False, "invalid leader target")
        return TargetValidation(True)

    if kind == "unit":
        if player_index not in (0, 1) or not instance_id:
            return TargetValidation(False, "incomplete unit target")

        unit = game.find_unit(instance_id)
        if unit is None:
            return TargetValidation(False, "target unit is no longer on battlefield")

        if game.owner_of_card(instance_id) != player_index:
            return TargetValidation(False, "target controller changed")

        return TargetValidation(True)

    return TargetValidation(False, f"unsupported target kind: {kind}")
