from types import SimpleNamespace

from src.playtest.simulation import decision_player_index, describe_decision_state


def test_pending_choice_actor_comes_from_queued_source():
    queued = SimpleNamespace(source_player_index=1, effect=SimpleNamespace(effect_id="E1"))
    pending = SimpleNamespace(queued=queued, candidates=[1, 2])

    game = SimpleNamespace(
        pending_choice=pending,
        priority_window=None,
        active_player_index=0,
    )

    assert decision_player_index(game) == 1


def test_stall_diagnostic_describes_pending_choice():
    queued = SimpleNamespace(source_player_index=1, effect=SimpleNamespace(effect_id="E1"))
    pending = SimpleNamespace(queued=queued, candidates=[1, 2])

    game = SimpleNamespace(
        pending_choice=pending,
        pending_combat=None,
        priority_window=None,
        active_player_index=0,
    )

    text = describe_decision_state(game, 1)
    assert "pending_choice" in text
    assert "source_player=1" in text
    assert "candidates=2" in text
