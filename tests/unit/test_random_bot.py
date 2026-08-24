from types import SimpleNamespace
from src.ai.random_bot import RandomBot

def test_game_over_has_no_action():
    game = SimpleNamespace(winner_index=0)
    assert RandomBot(0,1).choose_action(game) is None
