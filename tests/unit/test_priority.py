import pytest

from src.core.priority import PriorityWindow


def test_priority_starts_with_requested_player():
    window = PriorityWindow(first_player_index=1)
    assert window.current_player_index == 1
    assert window.is_open


def test_response_resets_passes_and_switches_priority():
    window = PriorityWindow(first_player_index=1)
    window.pass_priority(1)
    assert window.consecutive_passes == 1
    window.add_response(0, "R1")
    assert window.consecutive_passes == 0
    assert window.current_player_index == 1


def test_two_passes_close_window():
    window = PriorityWindow(first_player_index=1)
    assert not window.pass_priority(1)
    assert window.pass_priority(0)
    assert not window.is_open


def test_stack_is_lifo():
    window = PriorityWindow(first_player_index=1)
    window.add_response(1, "first")
    window.add_response(0, "second")
    assert window.drain_lifo() == ["second", "first"]


def test_wrong_player_cannot_act():
    window = PriorityWindow(first_player_index=1)
    with pytest.raises(ValueError):
        window.pass_priority(0)
