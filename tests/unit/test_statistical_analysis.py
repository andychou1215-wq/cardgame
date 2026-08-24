from src.playtest.statistical_analysis import (
    analyze_mirrored_games,
    wilson_interval,
)


def test_wilson_interval_contains_observed_rate():
    e = wilson_interval(50, 100)
    assert e.win_rate == 0.5
    assert e.ci_low < 0.5 < e.ci_high


def test_deck_by_seat_separates_seat_effect():
    rows = [
        {
            "pairing": "random_vs_random",
            "bot_p1": "random",
            "bot_p2": "random",
            "deck_p1": "D001",
            "deck_p2": "D002",
            "winner_index": 0,
            "winning_bot": "random",
            "winning_deck": "D001",
            "turn_number": 10,
            "actions": 100,
            "status": "finished",
        },
        {
            "pairing": "random_vs_random",
            "bot_p1": "random",
            "bot_p2": "random",
            "deck_p1": "D002",
            "deck_p2": "D001",
            "winner_index": 1,
            "winning_bot": "random",
            "winning_deck": "D001",
            "turn_number": 10,
            "actions": 100,
            "status": "finished",
        },
    ]

    analysis = analyze_mirrored_games(rows)
    by_key = {
        (r["deck"], r["seat"]): r
        for r in analysis["deck_by_seat"]
    }

    assert by_key[("D001", "P1")]["win_rate"] == 1.0
    assert by_key[("D001", "P2")]["win_rate"] == 1.0
    assert by_key[("D002", "P1")]["win_rate"] == 0.0
    assert by_key[("D002", "P2")]["win_rate"] == 0.0


def test_policy_h2h_excludes_same_policy_games():
    rows = [
        {
            "pairing": "heuristic_vs_random",
            "bot_p1": "heuristic",
            "bot_p2": "random",
            "deck_p1": "D001",
            "deck_p2": "D002",
            "winner_index": 0,
            "winning_bot": "heuristic",
            "winning_deck": "D001",
            "turn_number": 10,
            "actions": 100,
            "status": "finished",
        },
        {
            "pairing": "random_vs_heuristic",
            "bot_p1": "random",
            "bot_p2": "heuristic",
            "deck_p1": "D001",
            "deck_p2": "D002",
            "winner_index": 1,
            "winning_bot": "heuristic",
            "winning_deck": "D002",
            "turn_number": 10,
            "actions": 100,
            "status": "finished",
        },
        {
            "pairing": "random_vs_random",
            "bot_p1": "random",
            "bot_p2": "random",
            "deck_p1": "D001",
            "deck_p2": "D002",
            "winner_index": 0,
            "winning_bot": "random",
            "winning_deck": "D001",
            "turn_number": 10,
            "actions": 100,
            "status": "finished",
        },
    ]

    analysis = analyze_mirrored_games(rows)
    h2h = analysis["policy_head_to_head"]["overall"]

    assert h2h["games"] == 2
    assert h2h["heuristic_wins"] == 2
    assert h2h["heuristic_win_rate"] == 1.0
