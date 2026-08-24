import math

import pytest

from src.playtest.mana_curve import (
    analyze_mana_curve,
    build_deck_curve,
    probability_at_least_one,
)


pytestmark = pytest.mark.balance


def test_curve_contract_and_math(sample_cards, sample_deck_cards):
    """One test covers project schema acceptance + curve aggregation contract."""
    curve = build_deck_curve(sample_cards, sample_deck_cards)

    assert list(curve.columns) == ["deck_id", "cost", "copies", "share"]

    d1 = curve[curve.deck_id == "D001"].set_index("cost")
    assert d1.loc[1, "copies"] == 2
    assert d1.loc[2, "copies"] == 2
    assert math.isclose(d1.loc[1, "share"], 0.4)


def test_opening_probability_is_hypergeometric():
    expected = 1 - math.comb(22, 5) / math.comb(25, 5)
    assert math.isclose(probability_at_least_one(25, 3, 5), expected)


def test_static_summary_weighted_costs(sample_cards, sample_deck_cards):
    result = analyze_mana_curve(sample_cards, sample_deck_cards)
    d1 = result.deck_summary.set_index("deck_id").loc["D001"]

    assert math.isclose(d1.average_cost, 2.0)
    assert d1.median_cost == 2.0
    assert "runtime telemetry: unavailable" in result.report


def test_runtime_telemetry_metrics(
    sample_cards,
    sample_deck_cards,
    mana_curve_runtime_data,
):
    summaries, events = mana_curve_runtime_data
    result = analyze_mana_curve(
        sample_cards,
        sample_deck_cards,
        summaries,
        events,
    )
    idx = result.deck_summary.set_index("deck_id")

    # D001: spent 2 of 3 total available mana, avg remaining 0.5.
    assert math.isclose(idx.loc["D001", "mana_efficiency"], 2 / 3)
    assert math.isclose(idx.loc["D001", "avg_unused_mana"], 0.5)
    assert math.isclose(idx.loc["D001", "dead_hand_rate"], 0.0)
    assert idx.loc["D001", "avg_first_card_player_turn"] == 1
    assert idx.loc["D001", "avg_cards_played_by_player_turn_3"] == 2

    # D002: one of two turns is a dead-hand turn.
    assert math.isclose(idx.loc["D002", "dead_hand_rate"], 0.5)
