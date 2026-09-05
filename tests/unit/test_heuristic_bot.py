from types import SimpleNamespace

from src.ai.actions import DECLARE_ATTACK, END_TURN, GameAction
from src.ai.heuristic_bot import HeuristicBot


def test_lethal_attack_scores_above_end_turn():
    attacker = SimpleNamespace(instance_id="u1", attack=5)
    target = SimpleNamespace(kind="leader", player_index=1, key="leader:1")

    game = SimpleNamespace(
        winner_index=None,
        players=[
            SimpleNamespace(mana=0, hand=[], battlefield=[attacker]),
            SimpleNamespace(leader_health=5),
        ],
        find_unit=lambda instance_id: attacker if instance_id == "u1" else None,
    )

    bot = HeuristicBot(0, seed=1)
    attack = GameAction(DECLARE_ATTACK, 0, source_id="u1", target=target)
    end = GameAction(END_TURN, 0)

    assert bot.score_action(game, attack) > bot.score_action(game, end)


def test_combined_attacks_recognized_as_lethal():
    """No single attacker can finish the leader alone, but two together can."""
    attacker_a = SimpleNamespace(instance_id="u1", attack=3)
    attacker_b = SimpleNamespace(instance_id="u2", attack=3)
    leader_target = SimpleNamespace(kind="leader", player_index=1, key="leader:1")

    game = SimpleNamespace(
        winner_index=None,
        players=[
            SimpleNamespace(mana=0, hand=[], battlefield=[attacker_a, attacker_b]),
            SimpleNamespace(leader_health=5),
        ],
        find_unit=lambda instance_id: {"u1": attacker_a, "u2": attacker_b}.get(
            instance_id
        ),
    )

    bot = HeuristicBot(0, seed=1)
    attack_a = GameAction(DECLARE_ATTACK, 0, source_id="u1", target=leader_target)
    attack_b = GameAction(DECLARE_ATTACK, 0, source_id="u2", target=leader_target)

    lethal_targets = bot._lethal_targets(game, [attack_a, attack_b])
    assert lethal_targets == {1}

    score_with_context = bot.score_action(game, attack_a, lethal_targets=lethal_targets)
    score_without_context = bot.score_action(game, attack_a)

    assert score_with_context >= bot.weights.lethal_bonus
    assert score_with_context > score_without_context


def test_combined_lethal_outscores_favorable_trade():
    """Regression test: before the fix, a favorable board trade could
    outscore committing to a combined-attacker lethal on the leader,
    causing the bot to clear the board instead of winning the game."""
    attacker_a = SimpleNamespace(instance_id="u1", attack=3, current_health=4)
    attacker_b = SimpleNamespace(instance_id="u2", attack=3, current_health=4)
    enemy_unit = SimpleNamespace(instance_id="e1", attack=1, current_health=2)
    leader_target = SimpleNamespace(kind="leader", player_index=1, key="leader:1")
    unit_target = SimpleNamespace(kind="unit", instance_id="e1", key="unit:e1")

    game = SimpleNamespace(
        winner_index=None,
        players=[
            SimpleNamespace(mana=0, hand=[], battlefield=[attacker_a, attacker_b]),
            SimpleNamespace(leader_health=5),
        ],
        find_unit=lambda instance_id: {
            "u1": attacker_a,
            "u2": attacker_b,
            "e1": enemy_unit,
        }.get(instance_id),
    )

    bot = HeuristicBot(0, seed=1)
    attack_leader_a = GameAction(DECLARE_ATTACK, 0, source_id="u1", target=leader_target)
    attack_leader_b = GameAction(DECLARE_ATTACK, 0, source_id="u2", target=leader_target)
    attack_unit = GameAction(DECLARE_ATTACK, 0, source_id="u1", target=unit_target)

    lethal_targets = bot._lethal_targets(
        game, [attack_leader_a, attack_leader_b, attack_unit]
    )

    leader_score = bot.score_action(game, attack_leader_a, lethal_targets=lethal_targets)
    trade_score = bot.score_action(game, attack_unit, lethal_targets=lethal_targets)

    assert leader_score > trade_score
