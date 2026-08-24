from src.playtest.mirrored_baseline import (
    MirroredGameResult,
    summarize_mirrored_baseline,
)


def test_mirrored_summary_separates_deck_and_seat():
    rows = [
        MirroredGameResult(
            pairing="random_vs_random",
            mirror_group=1,
            mirror_side="A",
            game_seed=1,
            bot_p1="random",
            bot_p2="random",
            deck_p1="D001",
            deck_p2="D002",
            winner_index=0,
            winning_bot="random",
            winning_deck="D001",
            turn_number=10,
            actions=100,
            status="finished",
        ),
        MirroredGameResult(
            pairing="random_vs_random",
            mirror_group=1,
            mirror_side="B",
            game_seed=1,
            bot_p1="random",
            bot_p2="random",
            deck_p1="D002",
            deck_p2="D001",
            winner_index=1,
            winning_bot="random",
            winning_deck="D001",
            turn_number=10,
            actions=100,
            status="finished",
        ),
    ]

    summary = summarize_mirrored_baseline(rows)

    assert summary["overall"]["p1_win_rate"] == 0.5

    decks = {row["deck"]: row for row in summary["decks"]}
    assert decks["D001"]["win_rate"] == 1.0
    assert decks["D002"]["win_rate"] == 0.0


def test_pairing_summary_tracks_engine_health():
    rows = [
        MirroredGameResult(
            pairing="heuristic_vs_random",
            mirror_group=1,
            mirror_side="A",
            game_seed=2,
            bot_p1="heuristic",
            bot_p2="random",
            deck_p1="D001",
            deck_p2="D002",
            winner_index=None,
            winning_bot="",
            winning_deck="",
            turn_number=4,
            actions=25,
            status="invalid_legal_action",
            reason="x",
        )
    ]

    summary = summarize_mirrored_baseline(rows)
    row = summary["pairings"][0]

    assert row["invalid_legal_action"] == 1
    assert row["finished"] == 0
