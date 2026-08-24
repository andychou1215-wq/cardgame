from __future__ import annotations

import random
from dataclasses import dataclass

from src.ai.actions import (
    ACTIVATE_ABILITY,
    DECLARE_ATTACK,
    END_TURN,
    PASS_PRIORITY,
    PLAY_CARD,
    PLAY_RESPONSE,
    RESOLVE_COMBAT,
)
from src.ai.executor import execute_action
from src.ai.legal_actions import legal_actions


@dataclass(frozen=True)
class HeuristicWeights:
    play_card: float = 30.0
    play_unit_bonus: float = 18.0
    use_mana_per_point: float = 2.5
    declare_attack: float = 20.0
    attack_leader_bonus: float = 12.0
    favorable_trade_bonus: float = 30.0
    lethal_bonus: float = 10000.0
    activate_ability: float = 22.0
    play_response: float = 28.0
    pass_priority: float = -2.0
    resolve_combat: float = 5.0
    end_turn: float = -25.0
    empty_mana_end_turn_bonus: float = 18.0


class HeuristicBot:
    def __init__(
        self,
        player_index: int,
        seed: int | None = None,
        weights: HeuristicWeights | None = None,
    ) -> None:
        self.player_index = player_index
        self.rng = random.Random(seed)
        self.weights = weights or HeuristicWeights()

    def choose_action(self, game):
        actions = legal_actions(game, self.player_index)
        if not actions:
            return None

        action_count = len(actions)
        scored = [
            (self.score_action(game, action, action_count=action_count), action)
            for action in actions
        ]
        best_score = max(score for score, _ in scored)
        best = [action for score, action in scored if score == best_score]
        return self.rng.choice(best)

    def act(self, game):
        action = self.choose_action(game)
        if action is None:
            return None, None
        return action, execute_action(game, action)

    def score_action(
        self,
        game,
        action,
        *,
        action_count: int | None = None,
    ) -> float:
        w = self.weights
        player = game.players[action.player_index]

        if action.kind == PLAY_CARD:
            score = w.play_card
            card = _hand_card(player, action.hand_index)
            if card is not None:
                score += float(getattr(card, "cost", 0)) * w.use_mana_per_point
                if getattr(card, "card_type", "") == "unit":
                    score += w.play_unit_bonus
            return score

        if action.kind == DECLARE_ATTACK:
            score = w.declare_attack
            attacker = _find_unit(game, action.source_id)

            if getattr(action.target, "kind", "") == "leader":
                score += w.attack_leader_bonus
                target_player = getattr(
                    action.target,
                    "player_index",
                    1 - action.player_index,
                )
                leader_hp = game.players[target_player].leader_health
                if (
                    attacker is not None
                    and getattr(attacker, "attack", 0) >= leader_hp
                ):
                    score += w.lethal_bonus
                return score

            defender = _target_unit(game, action.target)
            if attacker is not None and defender is not None:
                atk = getattr(attacker, "attack", 0)
                hp = getattr(
                    attacker,
                    "current_health",
                    getattr(attacker, "health", 0),
                )
                enemy_atk = getattr(defender, "attack", 0)
                enemy_hp = getattr(
                    defender,
                    "current_health",
                    getattr(defender, "health", 0),
                )

                kills_enemy = atk >= enemy_hp
                survives = hp > enemy_atk

                if kills_enemy and survives:
                    score += w.favorable_trade_bonus
                elif kills_enemy:
                    score += w.favorable_trade_bonus * 0.5
                elif not survives:
                    score -= w.favorable_trade_bonus * 0.5

            return score

        if action.kind == ACTIVATE_ABILITY:
            return w.activate_ability

        if action.kind == PLAY_RESPONSE:
            return w.play_response

        if action.kind == PASS_PRIORITY:
            return w.pass_priority

        if action.kind == RESOLVE_COMBAT:
            return w.resolve_combat

        if action.kind == END_TURN:
            score = w.end_turn

            if getattr(player, "mana", 0) <= 0:
                score += w.empty_mana_end_turn_bonus

            # Important: do NOT call legal_actions() recursively here.
            # choose_action() already enumerated them and passes action_count.
            if action_count == 1:
                score += 100.0

            return score

        return 0.0


def _hand_card(player, hand_index):
    if hand_index is None:
        return None
    if hand_index < 0 or hand_index >= len(player.hand):
        return None
    return player.hand[hand_index]


def _find_unit(game, instance_id):
    fn = getattr(game, "find_unit", None)
    return fn(instance_id) if callable(fn) else None


def _target_unit(game, target):
    if getattr(target, "kind", "") != "unit":
        return None
    return _find_unit(game, getattr(target, "instance_id", ""))
