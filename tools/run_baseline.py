from __future__ import annotations

from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.game import Game
from src.deck.loader import GameData
from src.playtest.baseline import (
    run_standard_baseline,
    save_rows,
    summarize_baseline,
)
from src.playtest.persistence import PlaytestStore


def main():
    p = argparse.ArgumentParser(description="M3.5 balance baseline")
    p.add_argument("--games-per-pairing", type=int, default=100)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--deck1", default="D001")
    p.add_argument("--deck2", default="D002")
    p.add_argument("--max-actions", type=int, default=1000)
    p.add_argument("--rules-version", default="M3.5-baseline")
    p.add_argument("--commit-hash", default="")
    p.add_argument("--persist", action="store_true")
    args = p.parse_args()

    data = GameData(ROOT)

    def factory(seed):
        return Game(data, args.deck1, args.deck2, seed=seed)

    callback = None
    if args.persist:
        store = PlaytestStore(ROOT / "playtest_data")

        def callback(game):
            store.save_game(
                game.telemetry,
                game,
                rules_version=args.rules_version,
                commit_hash=args.commit_hash,
            )

    results = run_standard_baseline(
        factory,
        games_per_pairing=args.games_per_pairing,
        seed=args.seed,
        max_actions=args.max_actions,
        persist_callback=callback,
    )
    summary = summarize_baseline(results)

    detail_path = ROOT / "playtest_data" / "summaries" / "m3_baseline_games.csv"
    summary_path = ROOT / "playtest_data" / "summaries" / "m3_baseline_summary.csv"

    save_rows(detail_path, results)
    save_rows(summary_path, summary)

    print("")
    print("=== M3.5 Baseline ===")
    for row in summary:
        print(
            f"{row['pairing']}: "
            f"games={row['games']} "
            f"finished={row['finished']} "
            f"P1={row['p1_win_rate']:.1%} "
            f"P2={row['p2_win_rate']:.1%} "
            f"avg_turns={row['avg_turns']:.2f} "
            f"avg_actions={row['avg_actions']:.2f} "
            f"invalid={row['invalid_legal_action']} "
            f"stalled={row['stalled']} "
            f"limit={row['action_limit']}"
        )

    print("")
    print("detail:", detail_path)
    print("summary:", summary_path)


if __name__ == "__main__":
    main()
