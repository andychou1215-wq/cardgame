from __future__ import annotations

from dataclasses import dataclass

from src.ai.executor import execute_action
from src.ai.legal_actions import legal_actions
from src.playtest.simulation import choose_bot_action, decision_player_index


@dataclass(frozen=True)
class AIAdvanceResult:
    actions_taken: int
    status: str
    message: str = ""
    last_action_kind: str = ""


def advance_ai_until_human(
    game,
    bot,
    ai_player_index: int,
    *,
    max_actions: int = 200,
) -> AIAdvanceResult:
    """Advance only decisions owned by the AI, then yield to the human.

    This includes the AI Mulligan, main-phase actions, target choices, response
    priority, and combat resolution. It deliberately stops as soon as the
    authoritative decision boundary belongs to the human player.
    """
    if ai_player_index not in (0, 1):
        raise ValueError("ai_player_index must be 0 or 1")

    actions_taken = 0
    last_action_kind = ""

    while getattr(game, "winner_index", None) is None:
        if not getattr(game, "game_started", False):
            if getattr(game, "mulligan_player_index", None) != ai_player_index:
                return AIAdvanceResult(
                    actions_taken,
                    "waiting_for_human",
                    last_action_kind=last_action_kind,
                )
            ok, message = game.mulligan_hand([])
            if not ok:
                return AIAdvanceResult(
                    actions_taken,
                    "error",
                    message,
                    last_action_kind,
                )
            actions_taken += 1
            last_action_kind = "mulligan"
            if actions_taken >= max_actions:
                break
            continue

        actor = decision_player_index(game)
        if actor != ai_player_index:
            return AIAdvanceResult(
                actions_taken,
                "waiting_for_human",
                last_action_kind=last_action_kind,
            )

        actions = legal_actions(game, actor)
        if not actions:
            return AIAdvanceResult(
                actions_taken,
                "stalled",
                "AI 沒有合法動作。",
                last_action_kind,
            )

        action = choose_bot_action(bot, game, actions)
        if action is None:
            return AIAdvanceResult(
                actions_taken,
                "stalled",
                "AI 未能選擇動作。",
                last_action_kind,
            )

        result = execute_action(game, action)
        actions_taken += 1
        last_action_kind = action.kind
        if not result.ok:
            return AIAdvanceResult(
                actions_taken,
                "error",
                f"{action.kind}: {result.message}",
                last_action_kind,
            )
        if actions_taken >= max_actions:
            break

    if getattr(game, "winner_index", None) is not None:
        return AIAdvanceResult(
            actions_taken,
            "finished",
            last_action_kind=last_action_kind,
        )
    return AIAdvanceResult(
        actions_taken,
        "action_limit",
        f"AI 單次推進超過 {max_actions} 個動作。",
        last_action_kind,
    )

