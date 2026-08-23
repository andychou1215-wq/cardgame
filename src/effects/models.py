from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EffectDefinition:
    effect_id: str
    card_id: str
    side: str
    sequence: int
    activation_type: str
    trigger: str
    condition: str
    target: str
    target_count: str
    target_filter: str
    target_required: bool
    operation: str
    value: int
    parameter: str
    duration: str
    mana_cost: int
    usage_limit_type: str
    usage_limit_count: int
    optional: bool
    failure_behavior: str
    effect_text: str


@dataclass(frozen=True)
class TargetRef:
    kind: str  # unit / leader / player
    player_index: int
    instance_id: str = ""

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.player_index}:{self.instance_id}"
