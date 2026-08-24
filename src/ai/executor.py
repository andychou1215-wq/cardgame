from dataclasses import dataclass

from src.ai.actions import (
    ACTIVATE_ABILITY,
    CHOOSE_TARGET,
    DECLARE_ATTACK,
    END_TURN,
    PASS_PRIORITY,
    PLAY_CARD,
    PLAY_RESPONSE,
    RESOLVE_COMBAT,
)


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    message: str = ""


def execute_action(game, action):
    if action.kind == PLAY_CARD:
        return _norm(game.play_card(action.hand_index, action.target))

    if action.kind == ACTIVATE_ABILITY:
        return _norm(
            game.activate(
                action.source_id,
                action.effect_id,
                action.target,
            )
        )

    if action.kind == DECLARE_ATTACK:
        return _norm(game.declare_attack(action.source_id, action.target))

    if action.kind == PLAY_RESPONSE:
        # Current M1.2+ API accepts optional player_index.
        try:
            return _norm(game.play_response(action.hand_index, action.player_index))
        except TypeError:
            return _norm(game.play_response(action.hand_index))

    if action.kind == PASS_PRIORITY:
        return _norm(game.pass_priority())

    if action.kind == RESOLVE_COMBAT:
        return _norm(game.resolve_combat())

    if action.kind == END_TURN:
        return _norm(game.end_turn())

    if action.kind == CHOOSE_TARGET:
        return _norm(game.resolve_pending_choice(action.target))

    return ActionResult(False, f"unknown action kind: {action.kind}")


def _norm(result):
    if isinstance(result, ActionResult):
        return result
    if isinstance(result, tuple):
        return ActionResult(
            bool(result[0]),
            str(result[1]) if len(result) > 1 else "",
        )
    return ActionResult(bool(result), "")
