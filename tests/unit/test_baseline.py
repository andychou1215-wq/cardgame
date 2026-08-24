from src.playtest.baseline import BaselineGameResult, summarize_baseline


def test_baseline_summary():
    rows = [
        BaselineGameResult("random_vs_random",1,1,"random","random",0,10,100,"finished"),
        BaselineGameResult("random_vs_random",2,2,"random","random",1,12,120,"finished"),
    ]

    summary = summarize_baseline(rows)[0]
    assert summary["games"] == 2
    assert summary["finished"] == 2
    assert summary["p1_win_rate"] == 0.5
    assert summary["avg_turns"] == 11
    assert summary["avg_actions"] == 110
