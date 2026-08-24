from types import SimpleNamespace
from src.playtest.simulation import decision_player_index

def test_priority_actor():
    game = SimpleNamespace(
        pending_choice=None,
        priority_window=SimpleNamespace(is_open=True,current_player_index=1),
        active_player_index=0,
    )
    assert decision_player_index(game) == 1
