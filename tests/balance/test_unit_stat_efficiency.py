import pandas as pd
import pytest

from src.playtest.unit_stat_efficiency import (
    analyze_unit_stat_efficiency,
    build_unit_efficiency_table,
)


pytestmark = pytest.mark.balance


def _inputs():
    cards = pd.DataFrame(
        [
            {"id": "U001", "name": "A", "type": "unit", "cost": 2},
            {"id": "U002", "name": "B", "type": "unit", "cost": 4},
            {"id": "S001", "name": "Spell", "type": "spell", "cost": 1},
        ]
    )
    unit_sides = pd.DataFrame(
        [
            {"card_id": "U001", "side": "front", "attack": 2, "health": 2},
            {"card_id": "U001", "side": "back", "attack": 3, "health": 2},
            {"card_id": "U002", "side": "front", "attack": 3, "health": 5},
            {"card_id": "U002", "side": "back", "attack": 3, "health": 6},
        ]
    )
    deck_cards = pd.DataFrame(
        [
            {"deck_id": "D001", "card_id": "U001", "quantity": 2},
            {"deck_id": "D001", "card_id": "S001", "quantity": 1},
            {"deck_id": "D002", "card_id": "U002", "quantity": 3},
        ]
    )
    effects = pd.DataFrame(
        [
            {"effect_id": "E1", "card_id": "U001"},
            {"effect_id": "E2", "card_id": "U001"},
            {"effect_id": "E3", "card_id": "U002"},
        ]
    )
    return cards, unit_sides, deck_cards, effects


def test_unit_table_uses_repo_schema_and_excludes_non_units():
    cards, unit_sides, deck_cards, effects = _inputs()
    result = build_unit_efficiency_table(
        cards, unit_sides, deck_cards, effects
    )

    assert set(result["card_id"]) == {"U001", "U002"}
    assert "S001" not in set(result["card_id"])
    assert result.loc[result.card_id == "U001", "quantity"].iloc[0] == 2


def test_base_and_transform_efficiency_math():
    cards, unit_sides, deck_cards, effects = _inputs()
    result = build_unit_efficiency_table(
        cards, unit_sides, deck_cards, effects
    ).set_index("card_id")

    u1 = result.loc["U001"]
    assert u1["front_total_stats"] == 4
    assert u1["front_stats_per_mana"] == pytest.approx(2.0)
    assert u1["back_total_stats"] == 5
    assert u1["back_stats_per_mana"] == pytest.approx(2.5)
    assert u1["transform_attack_delta"] == 1
    assert u1["transform_health_delta"] == 0
    assert u1["transform_total_stat_delta"] == 1
    assert u1["transform_stat_gain_pct"] == pytest.approx(0.25)
    assert u1["effect_count"] == 2


def test_deck_summary_is_quantity_weighted():
    cards, unit_sides, deck_cards, effects = _inputs()
    result = analyze_unit_stat_efficiency(
        cards, unit_sides, deck_cards, effects
    )
    summary = result["deck_summary"].set_index("deck_id")

    assert summary.loc["D001", "unit_copies"] == 2
    assert summary.loc["D002", "unit_copies"] == 3
    assert summary.loc["D001", "avg_front_stats_per_mana"] == pytest.approx(2.0)
    assert summary.loc["D002", "avg_front_stats_per_mana"] == pytest.approx(2.0)
