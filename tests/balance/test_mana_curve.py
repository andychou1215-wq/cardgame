import json
import math
import pytest

import pandas as pd

from src.playtest.mana_curve import (
    analyze_mana_curve,
    build_deck_curve,
    probability_at_least_one,
)

from src.playtest.mana_curve import build_deck_curve

def _cards():
    return pd.DataFrame(
        [
            {"card_id": "A", "cost": 1},
            {"card_id": "B", "cost": 2},
            {"card_id": "C", "cost": 4},
        ]
    )


def _decks():
    return pd.DataFrame([
        {"deck_id": "D001", "card_id": "A", "quantity": 2},
        {"deck_id": "D001", "card_id": "B", "quantity": 2},
        {"deck_id": "D001", "card_id": "C", "quantity": 1},
        {"deck_id": "D002", "card_id": "A", "quantity": 1},
        {"deck_id": "D002", "card_id": "B", "quantity": 1},
        {"deck_id": "D002", "card_id": "C", "quantity": 3},
    ])


def test_curve_counts_and_shares():
    curve = build_deck_curve(_cards(), _decks())
    d1 = curve[curve.deck_id == "D001"].set_index("cost")
    assert d1.loc[1, "copies"] == 2
    assert d1.loc[2, "copies"] == 2
    assert math.isclose(d1.loc[1, "share"], 0.4)


def test_opening_probability_is_hypergeometric():
    expected = 1 - math.comb(22, 5) / math.comb(25, 5)
    assert math.isclose(probability_at_least_one(25, 3, 5), expected)


def test_static_summary_weighted_costs():
    result = analyze_mana_curve(_cards(), _decks())
    d1 = result.deck_summary.set_index("deck_id").loc["D001"]
    assert math.isclose(d1.average_cost, 2.0)
    assert d1.median_cost == 2.0
    assert "runtime telemetry: unavailable" in result.report


def test_runtime_telemetry_metrics():
    summaries = pd.DataFrame([
        {"game_id": "G1", "deck_id_p1": "D001", "deck_id_p2": "D002"},
    ])
    events = pd.DataFrame([
        {"game_id": "G1", "event_type": "card_played", "turn": 1, "player_index": 0, "metadata": "{}"},
        {"game_id": "G1", "event_type": "turn_resource_snapshot", "turn": 1, "player_index": 0,
         "metadata": json.dumps({"max_mana": 1, "mana_remaining": 0, "mana_spent": 1, "dead_hand": False, "spend_actions_available": 0})},
        {"game_id": "G1", "event_type": "turn_resource_snapshot", "turn": 2, "player_index": 1,
         "metadata": json.dumps({"max_mana": 1, "mana_remaining": 1, "mana_spent": 0, "dead_hand": True, "spend_actions_available": 0})},
        {"game_id": "G1", "event_type": "card_played", "turn": 3, "player_index": 0, "metadata": "{}"},
        {"game_id": "G1", "event_type": "turn_resource_snapshot", "turn": 3, "player_index": 0,
         "metadata": json.dumps({"max_mana": 2, "mana_remaining": 1, "mana_spent": 1, "dead_hand": False, "spend_actions_available": 0})},
        {"game_id": "G1", "event_type": "turn_resource_snapshot", "turn": 4, "player_index": 1,
         "metadata": json.dumps({"max_mana": 2, "mana_remaining": 0, "mana_spent": 2, "dead_hand": False, "spend_actions_available": 0})},
    ])
    result = analyze_mana_curve(_cards(), _decks(), summaries, events)
    idx = result.deck_summary.set_index("deck_id")
    # D001: spent 2 of 3 total available mana, avg remaining 0.5.
    assert math.isclose(idx.loc["D001", "mana_efficiency"], 2 / 3)
    assert math.isclose(idx.loc["D001", "avg_unused_mana"], 0.5)
    assert math.isclose(idx.loc["D001", "dead_hand_rate"], 0.0)
    assert idx.loc["D001", "avg_first_card_player_turn"] == 1
    assert idx.loc["D001", "avg_cards_played_by_player_turn_3"] == 2
    # D002: one of two turns is a dead-hand turn.
    assert math.isclose(idx.loc["D002", "dead_hand_rate"], 0.5)

def test_build_deck_curve_accepts_project_cards_schema():
    cards = pd.DataFrame(
        [
            {"id": "U001", "cost": 1},
            {"id": "U002", "cost": 2},
        ]
    )

    deck_cards = pd.DataFrame(
        [
            {"deck_id": "D001", "card_id": "U001", "quantity": 3},
            {"deck_id": "D001", "card_id": "U002", "quantity": 2},
        ]
    )

    result = build_deck_curve(cards, deck_cards)

    assert list(result.columns) == [
        "deck_id",
        "cost",
        "copies",
        "share",
    ]

    assert len(result) == 2

    d1 = result.set_index("cost")

    assert d1.loc[1, "copies"] == 3
    assert d1.loc[2, "copies"] == 2

    assert d1.loc[1, "share"] == pytest.approx(3 / 5)
    assert d1.loc[2, "share"] == pytest.approx(2 / 5)
