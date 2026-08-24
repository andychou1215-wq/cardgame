from src.playtest.mirrored_baseline import (
    MirroredGameResult,
    summarize_mirrored_baseline,
)


def test_zero_win_deck_is_kept_in_summary():
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
    decks = {row["deck"]: row for row in summary["decks"]}

    assert "D001" in decks
    assert "D002" in decks
    assert decks["D001"]["wins"] == 2
    assert decks["D002"]["wins"] == 0
    assert decks["D001"]["win_rate"] == 1.0
    assert decks["D002"]["win_rate"] == 0.0
