import json
import pandas as pd
import pytest

from src.playtest.transform_efficiency import analyze_transform_efficiency


pytestmark = pytest.mark.balance


def _data():
    summaries = pd.DataFrame([
        {"game_id": "G1", "deck_id_p1": "D001", "deck_id_p2": "D002", "winner_index": 0},
        {"game_id": "G2", "deck_id_p1": "D002", "deck_id_p2": "D001", "winner_index": 0},
    ])

    rows = [
        # G1: D001 plays U1 and transforms, wins.
        {"game_id":"G1","event_type":"card_played","turn":1,"player_index":0,"card_id":"U1","source_id":"I1","metadata":"{}"},
        {"game_id":"G1","event_type":"transform","turn":3,"player_index":0,"card_id":"U1","source_id":"I1","metadata":"{}"},
        {"game_id":"G1","event_type":"trigger","turn":3,"player_index":0,"card_id":"U1","source_id":"I1",
         "metadata":json.dumps({"trigger":"on_flip","side":"back"})},

        # G1: D002 plays U2 but does not transform.
        {"game_id":"G1","event_type":"card_played","turn":1,"player_index":1,"card_id":"U2","source_id":"I2","metadata":"{}"},

        # G2: D001 is P2, plays U1 but does not transform and loses.
        {"game_id":"G2","event_type":"card_played","turn":2,"player_index":1,"card_id":"U1","source_id":"I3","metadata":"{}"},

        # G2: D002 transforms and wins.
        {"game_id":"G2","event_type":"card_played","turn":1,"player_index":0,"card_id":"U2","source_id":"I4","metadata":"{}"},
        {"game_id":"G2","event_type":"transform","turn":2,"player_index":0,"card_id":"U2","source_id":"I4","metadata":"{}"},
        {"game_id":"G2","event_type":"trigger","turn":2,"player_index":0,"card_id":"U2","source_id":"I4",
         "metadata":json.dumps({"trigger":"on_flip","side":"back"})},
    ]
    return summaries, pd.DataFrame(rows)


def test_transform_rate_and_deck_attribution():
    summaries, events = _data()
    result = analyze_transform_efficiency(summaries, events)
    cards = result["card_summary"].set_index(["deck_id", "card_id"])

    assert cards.loc[("D001", "U1"), "played_instances"] == 2
    assert cards.loc[("D001", "U1"), "transformed_instances"] == 1
    assert cards.loc[("D001", "U1"), "transform_rate_per_play"] == pytest.approx(0.5)
    assert cards.loc[("D002", "U2"), "transform_rate_per_play"] == pytest.approx(0.5)


def test_transform_outcome_and_flip_trigger():
    summaries, events = _data()
    result = analyze_transform_efficiency(summaries, events)
    cards = result["card_summary"].set_index(["deck_id", "card_id"])
    outcomes = result["outcome_summary"]

    assert cards.loc[("D001", "U1"), "on_flip_trigger_count"] == 1
    assert cards.loc[("D001", "U1"), "avg_transform_turn"] == pytest.approx(3.0)

    d1_transformed = outcomes[
        (outcomes.deck_id == "D001") & (outcomes.transformed_any == True)
    ].iloc[0]
    d1_not = outcomes[
        (outcomes.deck_id == "D001") & (outcomes.transformed_any == False)
    ].iloc[0]

    assert d1_transformed.win_rate == pytest.approx(1.0)
    assert d1_not.win_rate == pytest.approx(0.0)
