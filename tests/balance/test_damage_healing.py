import json
import pandas as pd
import pytest

from src.playtest.damage_healing import analyze_damage_healing


pytestmark = pytest.mark.balance


def _data():
    summaries = pd.DataFrame([
        {
            "game_id": "G1",
            "deck_id_p1": "D001",
            "deck_id_p2": "D002",
            "winner_index": 0,
        }
    ])

    events = pd.DataFrame([
        {
            "game_id":"G1","event_type":"combat_damage_leader","turn":2,
            "player_index":0,"card_id":"U001","source_id":"I1",
            "target_kind":"leader","target_player_index":1,
            "amount":3,"metadata":"{}",
        },
        {
            "game_id":"G1","event_type":"combat_damage_unit","turn":2,
            "player_index":1,"card_id":"U007","source_id":"I2",
            "target_kind":"unit","target_player_index":0,
            "amount":2,"metadata":json.dumps({"blocked":1}),
        },
        {
            "game_id":"G1","event_type":"effect_damage","turn":3,
            "player_index":0,"card_id":"U012","source_id":"I3",
            "target_kind":"leader","target_player_index":1,
            "amount":2,"metadata":json.dumps({"source_type":"effect"}),
        },
        {
            "game_id":"G1","event_type":"heal","turn":3,
            "player_index":0,"card_id":"U001","source_id":"I1",
            "target_kind":"unit","target_player_index":0,
            "amount":2,
            "metadata":json.dumps({
                "source_type":"lifesteal",
                "requested_amount":3,
                "overheal":1,
            }),
        },
        {
            "game_id":"G1","event_type":"heal","turn":4,
            "player_index":1,"card_id":"U010","source_id":"I4",
            "target_kind":"leader","target_player_index":1,
            "amount":2,
            "metadata":json.dumps({
                "source_type":"effect",
                "requested_amount":2,
                "overheal":0,
            }),
        },
    ])
    return summaries, events


def test_damage_channels_and_deck_attribution():
    summaries, events = _data()
    result = analyze_damage_healing(summaries, events)
    deck = result["deck_summary"].set_index("deck_id")

    assert deck.loc["D001", "avg_combat_damage_leader"] == pytest.approx(3)
    assert deck.loc["D001", "avg_effect_damage_leader"] == pytest.approx(2)
    assert deck.loc["D001", "avg_total_leader_damage"] == pytest.approx(5)
    assert deck.loc["D002", "avg_combat_damage_unit"] == pytest.approx(2)


def test_healing_actual_requested_and_overheal():
    summaries, events = _data()
    result = analyze_damage_healing(summaries, events)
    deck = result["deck_summary"].set_index("deck_id")

    assert deck.loc["D001", "avg_lifesteal_healing"] == pytest.approx(2)
    assert deck.loc["D001", "avg_overheal"] == pytest.approx(1)
    assert deck.loc["D001", "healing_efficiency"] == pytest.approx(2 / 3)
    assert deck.loc["D002", "avg_leader_healing"] == pytest.approx(2)
