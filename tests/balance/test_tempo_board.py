import json
import pandas as pd
import pytest

from src.playtest.tempo_board import analyze_tempo_board


pytestmark = pytest.mark.balance


def test_tempo_board_metrics():
    summaries = pd.DataFrame(
        [
            {
                "game_id": "G1",
                "deck_id_p1": "D001",
                "deck_id_p2": "D002",
            }
        ]
    )

    rows = []
    def snap(turn, player, units, atk, hp, played):
        rows.append(
            {
                "game_id": "G1",
                "event_type": "board_state_snapshot",
                "turn": turn,
                "player_index": player,
                "metadata": json.dumps(
                    {
                        "unit_count": units,
                        "board_attack": atk,
                        "board_health": hp,
                        "cards_played_total": played,
                    }
                ),
            }
        )

    snap(1, 0, 1, 2, 3, 1)
    snap(1, 1, 1, 1, 2, 1)
    snap(2, 0, 2, 5, 7, 2)
    snap(2, 1, 1, 2, 3, 2)

    result = analyze_tempo_board(
        summaries,
        pd.DataFrame(rows),
    )

    summary = result["deck_summary"].set_index("deck_id")
    assert summary.loc["D001", "avg_unit_count"] == pytest.approx(1.5)
    assert summary.loc["D002", "avg_unit_count"] == pytest.approx(1.0)
    assert summary.loc["D001", "avg_board_attack"] == pytest.approx(3.5)

    comp = result["comparison"].set_index("metric")
    assert comp.loc["avg_unit_count", "D001_minus_D002"] == pytest.approx(0.5)


def test_first_advantage_is_attributed_to_deck():
    summaries = pd.DataFrame(
        [
            {
                "game_id": "G1",
                "deck_id_p1": "D002",
                "deck_id_p2": "D001",
            }
        ]
    )
    events = pd.DataFrame(
        [
            {
                "game_id": "G1",
                "event_type": "board_state_snapshot",
                "turn": 1,
                "player_index": 0,
                "metadata": json.dumps(
                    {
                        "unit_count": 0,
                        "board_attack": 0,
                        "board_health": 0,
                        "cards_played_total": 0,
                    }
                ),
            },
            {
                "game_id": "G1",
                "event_type": "board_state_snapshot",
                "turn": 1,
                "player_index": 1,
                "metadata": json.dumps(
                    {
                        "unit_count": 1,
                        "board_attack": 2,
                        "board_health": 3,
                        "cards_played_total": 1,
                    }
                ),
            },
        ]
    )

    result = analyze_tempo_board(summaries, events)
    first = result["first_advantage"]
    assert set(first["advantage_deck_id"]) == {"D001"}
