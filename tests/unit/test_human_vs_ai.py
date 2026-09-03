import csv
from pathlib import Path
from types import SimpleNamespace

from src.ai.heuristic_bot import HeuristicBot
from src.core.game import Game
from src.deck.loader import GameData
from src.playtest.fun_feedback import (
    FunFeedback,
    append_fun_feedback,
    card_exposure,
)
from src.playtest.simulation import decision_player_index
from src.playtest.telemetry import PlaytestEvent
from src.ui.human_vs_ai import advance_ai_until_human


ROOT = Path(__file__).resolve().parents[2]


def test_ai_completes_its_mulligan_and_yields_to_human():
    game = Game(GameData(ROOT), "D001", "D002", seed=21)
    assert game.mulligan_hand([])[0]
    assert game.mulligan_player_index == 1

    result = advance_ai_until_human(
        game,
        HeuristicBot(1, seed=22),
        1,
    )

    assert game.game_started
    assert game.mulligan_done == [True, True]
    assert result.status in {"waiting_for_human", "finished"}
    if game.winner_index is None:
        assert decision_player_index(game) == 0


def test_ai_never_executes_a_human_owned_decision():
    game = Game(GameData(ROOT), "D001", "D002", seed=23)
    assert game.mulligan_hand([])[0]
    assert game.mulligan_hand([])[0]
    game.active_player_index = 0
    before = len(game.telemetry.events)

    result = advance_ai_until_human(
        game,
        HeuristicBot(1, seed=24),
        1,
    )

    assert result.status == "waiting_for_human"
    assert result.actions_taken == 0
    assert len(game.telemetry.events) == before


def test_ai_executes_its_turn_then_yields_to_human():
    game = Game(GameData(ROOT), "D001", "D002", seed=26)
    assert game.mulligan_hand([])[0]
    assert game.mulligan_hand([])[0]
    game.active_player_index = 1

    result = advance_ai_until_human(
        game,
        HeuristicBot(1, seed=27),
        1,
    )

    assert result.actions_taken > 0
    assert result.status in {"waiting_for_human", "finished"}
    if game.winner_index is None:
        assert decision_player_index(game) == 0


def test_fun_feedback_appends_one_csv_row(tmp_path: Path):
    path = tmp_path / "feedback.csv"
    feedback = FunFeedback(
        game_id="G1",
        human_player_index=0,
        human_deck="D001",
        ai_deck="D002",
        winner_index=0,
        first_player_index=1,
        turn_number=10,
        human_won=True,
        decision_depth=4,
        u011_playability=3,
        u011_payoff=5,
        shelter_clarity=4,
        fairness=4,
        replay_desire=5,
        overall_fun=4,
        u011_drawn=1,
        u011_played=1,
        u011_transformed=1,
        notes="再來一局",
    )

    append_fun_feedback(path, feedback)

    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["game_id"] == "G1"
    assert rows[0]["human_won"] == "true"
    assert rows[0]["overall_fun"] == "4"
    assert rows[0]["notes"] == "再來一局"


def test_card_exposure_counts_only_selected_player():
    game = SimpleNamespace(
        telemetry=SimpleNamespace(
            events=[
                PlaytestEvent(1, "card_drawn", 1, 0, 0, "U011"),
                PlaytestEvent(2, "card_played", 2, 0, 0, "U011"),
                PlaytestEvent(3, "card_played", 2, 1, 1, "U011"),
            ]
        )
    )

    assert card_exposure(game, 0, "U011") == {
        "drawn": 1,
        "played": 1,
        "transformed": 0,
    }
