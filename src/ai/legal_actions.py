from src.ai.actions import (
    ACTIVATE_ABILITY,
    CHOOSE_TARGET,
    DECLARE_ATTACK,
    END_TURN,
    PASS_PRIORITY,
    PLAY_CARD,
    PLAY_RESPONSE,
    RESOLVE_COMBAT,
    GameAction,
)


def legal_actions(game, player_index=None):
    """Enumerate legal decisions using Game's authoritative helpers."""

    if getattr(game, "winner_index", None) is not None:
        return []

    # Pending effect target choice.
    pending = getattr(game, "pending_choice", None)
    if pending is not None:
        queued = getattr(pending, "queued", None)
        actor = getattr(
            queued,
            "source_player_index",
            getattr(game, "active_player_index", 0),
        )
        if player_index is not None and player_index != actor:
            return []
        return [
            GameAction(CHOOSE_TARGET, actor, target=target)
            for target in list(getattr(pending, "candidates", []) or [])
        ]

    # Priority / Response.
    window = getattr(game, "priority_window", None)
    combat = getattr(game, "pending_combat", None)
    if combat is not None and window is not None:
        if getattr(window, "is_open", False):
            actor = window.current_player_index
            if player_index is not None and player_index != actor:
                return []

            actions = []
            seen = set()
            for hand_index, card, effect in game.available_responses(actor):
                if hand_index in seen:
                    continue
                seen.add(hand_index)
                actions.append(
                    GameAction(
                        PLAY_RESPONSE,
                        actor,
                        hand_index=hand_index,
                        source_id=card.instance_id,
                        effect_id=getattr(effect, "effect_id", ""),
                        target=combat.defender,
                    )
                )
            actions.append(GameAction(PASS_PRIORITY, actor))
            return actions

        actor = game.active_player_index
        if player_index is not None and player_index != actor:
            return []
        return [GameAction(RESOLVE_COMBAT, actor)]

    actor = game.active_player_index
    if player_index is not None and player_index != actor:
        return []

    player = game.players[actor]
    actions = []

    # Card play.
    for hand_index, card in enumerate(player.hand):
        if card.cost > player.mana:
            continue

        # Response is never a Main Phase play.
        if getattr(card, "card_type", "") == "response":
            continue

        # Ask the Game wrapper when available. This keeps AI from duplicating
        # BATTLEFIELD_LIMIT and future card-play restrictions.
        can_play = getattr(game, "can_play_card", None)
        if callable(can_play):
            ok, _ = can_play(hand_index)
            if not ok:
                continue
        else:
            # Compatibility fallback for current engine.
            if getattr(card, "card_type", "") == "unit":
                limit = _battlefield_limit(game)
                if len(player.battlefield) >= limit:
                    continue

        on_play = game.data.effects_for(card.card_id, "on_play", "none")
        targeted = next(
            (e for e in on_play if getattr(e, "target_required", False)),
            None,
        )

        if targeted is not None:
            targets = list(game.legal_play_targets(hand_index))
            if not targets:
                continue
            for target in targets:
                actions.append(
                    GameAction(
                        PLAY_CARD,
                        actor,
                        hand_index=hand_index,
                        source_id=card.instance_id,
                        target=target,
                    )
                )
        else:
            actions.append(
                GameAction(
                    PLAY_CARD,
                    actor,
                    hand_index=hand_index,
                    source_id=card.instance_id,
                )
            )

    # Activated abilities.
    for source, effect in game.activated_options():
        if getattr(effect, "target_required", False):
            for target in game.legal_activation_targets(source, effect):
                actions.append(
                    GameAction(
                        ACTIVATE_ABILITY,
                        actor,
                        source_id=source.instance_id,
                        effect_id=effect.effect_id,
                        target=target,
                    )
                )
        else:
            actions.append(
                GameAction(
                    ACTIVATE_ABILITY,
                    actor,
                    source_id=source.instance_id,
                    effect_id=effect.effect_id,
                )
            )

    # Combat: engine is authoritative.
    attackers = list(game.legal_attackers())
    targets = list(game.legal_attack_targets())
    for unit in attackers:
        for target in targets:
            actions.append(
                GameAction(
                    DECLARE_ATTACK,
                    actor,
                    source_id=unit.instance_id,
                    target=target,
                )
            )

    actions.append(GameAction(END_TURN, actor))
    return _dedupe(actions)


def _battlefield_limit(game):
    """Read the engine module constant without hard-coding 5 in AI rules."""
    module = __import__(game.__class__.__module__, fromlist=["BATTLEFIELD_LIMIT"])
    return int(getattr(module, "BATTLEFIELD_LIMIT", 5))


def _dedupe(actions):
    seen = set()
    out = []
    for action in actions:
        if action.key in seen:
            continue
        seen.add(action.key)
        out.append(action)
    return out
