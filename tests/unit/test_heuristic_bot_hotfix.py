from types import SimpleNamespace

from src.ai.actions import DECLARE_ATTACK, END_TURN, GameAction
from src.ai.heuristic_bot import HeuristicBot


def test_score_action_does_not_require_full_game_for_end_turn():
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

    attack = GameAction(
        DECLARE_ATTACK,
        0,
        source_id="u1",
        target=target,
    )
    end_turn = GameAction(END_TURN, 0)

    assert bot.score_action(game, attack) > bot.score_action(game, end_turn)


def test_end_turn_only_action_bonus_uses_context():
    game = SimpleNamespace(
        players=[
            SimpleNamespace(mana=0, hand=[], battlefield=[]),
            SimpleNamespace(),
        ]
    )
    bot = HeuristicBot(0, seed=1)
    end_turn = GameAction(END_TURN, 0)

    normal = bot.score_action(game, end_turn, action_count=2)
    only_action = bot.score_action(game, end_turn, action_count=1)

    assert only_action > normal
