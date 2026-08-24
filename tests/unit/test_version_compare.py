import pandas as pd
from src.playtest.version_compare import version_summary

def test_version_summary():
    summaries = pd.DataFrame([
        {"rules_version": "v1", "winner_index": 0, "turn_number": 6, "first_player_index": 0},
        {"rules_version": "v1", "winner_index": 1, "turn_number": 8, "first_player_index": 0},
        {"rules_version": "v2", "winner_index": 0, "turn_number": 5, "first_player_index": 1},
    ])
    result = version_summary(summaries).set_index("version")
    assert result.loc["v1", "games"] == 2
    assert result.loc["v1", "avg_turns"] == 7
    assert result.loc["v1", "first_player_win_rate"] == 0.5
