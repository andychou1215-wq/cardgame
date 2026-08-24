from src.playtest.card_deck_diagnostics import build_static_diagnostics


def test_static_diagnostics_compare_decks():
    tables = {
        "cards": [
            {
                "id": "U1",
                "name": "A",
                "type": "unit",
                "cost": "1",
                "faction_id": "F1",
                "rarity": "R",
                "transform_condition_type": "attack_count",
            },
            {
                "id": "U2",
                "name": "B",
                "type": "unit",
                "cost": "2",
                "faction_id": "F2",
                "rarity": "R",
                "transform_condition_type": "",
            },
        ],
        "unit_sides": [
            {
                "card_id": "U1",
                "side": "front",
                "attack": "2",
                "max_health": "2",
                "keywords": "庇護",
            },
            {
                "card_id": "U1",
                "side": "back",
                "attack": "3",
                "max_health": "3",
                "keywords": "庇護|格檔",
            },
            {
                "card_id": "U2",
                "side": "front",
                "attack": "2",
                "max_health": "2",
                "keywords": "",
            },
        ],
        "effects": [
            {
                "card_id": "U1",
                "operation": "damage",
                "trigger": "on_play",
            }
        ],
        "deck_cards": [
            {"deck_id": "D1", "card_id": "U1", "quantity": "2"},
            {"deck_id": "D2", "card_id": "U2", "quantity": "2"},
        ],
        "decks": [
            {"deck_id": "D1", "name": "Deck A", "faction_id": "F1"},
            {"deck_id": "D2", "name": "Deck B", "faction_id": "F2"},
        ],
    }

    result = build_static_diagnostics(tables)
    decks = {row["deck_id"]: row for row in result["deck_summary"]}

    assert decks["D1"]["avg_cost"] == 1.0
    assert decks["D2"]["avg_cost"] == 2.0
    assert decks["D1"]["avg_unit_front_stats_per_mana"] == 4.0
    assert decks["D2"]["avg_unit_front_stats_per_mana"] == 2.0

    cards = {
        (row["deck_id"], row["card_id"]): row
        for row in result["card_efficiency"]
    }
    assert cards[("D1", "U1")]["transform_total_stat_gain"] == 2
    assert cards[("D1", "U1")]["effect_count"] == 1


def test_zero_win_or_missing_telemetry_does_not_break_static_layer():
    tables = {
        "cards": [],
        "unit_sides": [],
        "effects": [],
        "deck_cards": [],
        "decks": [],
    }
    result = build_static_diagnostics(tables)
    assert result["deck_summary"] == []
    assert result["card_efficiency"] == []
