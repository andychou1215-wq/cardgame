from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class StackItem:
    source_id: str
    card_id: str
    controller_index: int
    effects: list[Any]
    trigger: str
    trigger_target: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result_reason: str = ""

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
        return TargetValidation(player_index in (0, 1), "invalid leader target" if player_index not in (0, 1) else "")
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
