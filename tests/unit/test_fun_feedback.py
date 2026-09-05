import csv

import pytest

from src.playtest.fun_feedback import FunFeedback, append_fun_feedback, validate_feedback


def _base_feedback(**overrides) -> FunFeedback:
    fields = dict(
        game_id="g1",
        human_player_index=0,
        human_deck="D002",
        ai_deck="D001",
        winner_index=0,
        first_player_index=0,
        turn_number=10,
        human_won=True,
        decision_depth=4,
        u011_playability=None,
        u011_payoff=None,
        shelter_clarity=None,
        fairness=4,
        replay_desire=5,
        overall_fun=4,
        u011_drawn=0,
        u011_played=0,
        u011_transformed=0,
    )
    fields.update(overrides)
    return FunFeedback(**fields)


def test_optional_u011_ratings_accept_none_when_not_exposed():
    feedback = _base_feedback()
    validate_feedback(feedback)  # should not raise


def test_optional_u011_ratings_still_range_checked_when_present():
    feedback = _base_feedback(u011_playability=9)
    with pytest.raises(ValueError):
        validate_feedback(feedback)


def test_mandatory_ratings_reject_none():
    feedback = _base_feedback(fairness=None)
    with pytest.raises(ValueError):
        validate_feedback(feedback)


def test_not_applicable_ratings_are_written_as_empty_cells(tmp_path):
    path = tmp_path / "fun_ratings.csv"
    feedback = _base_feedback()

    append_fun_feedback(path, feedback)

    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    row = rows[0]
    assert row["u011_playability"] == ""
    assert row["u011_payoff"] == ""
    assert row["shelter_clarity"] == ""
    # Unaffected ratings should still round-trip normally.
    assert row["fairness"] == "4"
