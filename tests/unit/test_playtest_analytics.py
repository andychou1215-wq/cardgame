import pandas as pd

from src.playtest.analytics import PlaytestAnalytics


def test_overview():
    summaries = pd.DataFrame([
        {"game_id": "g1", "winner_index": 0, "turn_number": 7, "first_player_index": 0, "deck_id_p1": "D1", "deck_id_p2": "D2"},
        {"game_id": "g2", "winner_index": 1, "turn_number": 9, "first_player_index": 0, "deck_id_p1": "D1", "deck_id_p2": "D2"},
    ])
    result = PlaytestAnalytics(summaries, pd.DataFrame()).overview()
    assert result["games"] == 2
    assert result["avg_turns"] == 8
    assert result["first_player_win_rate"] == 0.5


def test_deck_results():
    summaries = pd.DataFrame([
        {"game_id": "g1", "winner_index": 0, "turn_number": 7, "deck_id_p1": "D1", "deck_id_p2": "D2"},
        {"game_id": "g2", "winner_index": 1, "turn_number": 9, "deck_id_p1": "D1", "deck_id_p2": "D2"},
    ])
    result = PlaytestAnalytics(summaries, pd.DataFrame()).deck_results().set_index("deck_id")
    assert result.loc["D1", "wins"] == 1
    assert result.loc["D2", "wins"] == 1


def test_card_usage():
    events = pd.DataFrame([
        {"game_id": "g1", "event_type": "card_played", "card_id": "U001", "player_index": 0},
        {"game_id": "g1", "event_type": "transform", "card_id": "U001", "player_index": 0},
        {"game_id": "g1", "event_type": "response_played", "card_id": "R001", "player_index": 1},
    ])
    result = PlaytestAnalytics(pd.DataFrame(), events).card_usage().set_index("card_id")
    assert result.loc["U001", "plays"] == 1
    assert result.loc["U001", "transforms"] == 1
    assert result.loc["R001", "responses"] == 1
