from types import SimpleNamespace
from src.playtest.simulation import choose_bot_action, decision_player_index

def test_priority_actor():
    game = SimpleNamespace(
        pending_choice=None,
        priority_window=SimpleNamespace(is_open=True,current_player_index=1),
        active_player_index=0,
    )
    assert decision_player_index(game) == 1


def test_configured_bot_policy_selects_the_action():
    expected = object()

    class PolicyBot:
        def __init__(self):
            self.calls = 0

        def choose_action(self, game):
            self.calls += 1
            return expected

    bot = PolicyBot()
    game = object()

    assert choose_bot_action(bot, game, [object(), expected]) is expected
    assert bot.calls == 1
