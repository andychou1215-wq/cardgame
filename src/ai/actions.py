from dataclasses import dataclass
from typing import Any

PLAY_CARD = "play_card"
ACTIVATE_ABILITY = "activate_ability"
DECLARE_ATTACK = "declare_attack"
PLAY_RESPONSE = "play_response"
PASS_PRIORITY = "pass_priority"
RESOLVE_COMBAT = "resolve_combat"
END_TURN = "end_turn"
CHOOSE_TARGET = "choose_target"

@dataclass(frozen=True)
class GameAction:
    kind: str
    player_index: int
    hand_index: int | None = None
    source_id: str = ""
    effect_id: str = ""
    target: Any | None = None
    metadata: dict[str, Any] | None = None

    @property
    def key(self) -> str:
        target_key = getattr(self.target, "key", "") if self.target is not None else ""
        return "|".join([
            self.kind,
            str(self.player_index),
            str(self.hand_index if self.hand_index is not None else ""),
            self.source_id,
            self.effect_id,
            target_key,
        ])
