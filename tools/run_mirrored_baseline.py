from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.game import Game
from src.deck.loader import GameData
from src.playtest.mirrored_baseline import (
    run_standard_mirrored_baseline,
    save_rows,
    summarize_mirrored_baseline,
)
from src.playtest.persistence import PlaytestStore


def main():
    parser = argparse.ArgumentParser(
        description="M3.5.1 mirrored seat/deck baseline"
    )
    parser.add_argument("--mirror-groups-per-pairing", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--deck-a", default="D001")
    parser.add_argument("--deck-b", default="D002")
    parser.add_argument("--max-actions", type=int, default=1000)
    parser.add_argument("--rules-version", default="M3.5.1-mirrored")
    parser.add_argument("--commit-hash", default="")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args()

    data = GameData(ROOT)

    def game_factory(deck_p1, deck_p2, seed):
        return Game(data, deck_p1, deck_p2, seed=seed)

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

    results = run_standard_mirrored_baseline(
        game_factory,
        deck_a=args.deck_a,
        deck_b=args.deck_b,
        mirror_groups_per_pairing=args.mirror_groups_per_pairing,
        seed=args.seed,
        max_actions=args.max_actions,
        persist_callback=callback,
    )

    summary = summarize_mirrored_baseline(results)

    detail_path = (
        ROOT
        / "playtest_data"
        / "summaries"
        / "m3_5_1_mirrored_games.csv"
    )
    pairing_path = (
        ROOT
        / "playtest_data"
        / "summaries"
        / "m3_5_1_pairing_summary.csv"
    )
    deck_path = (
        ROOT
        / "playtest_data"
        / "summaries"
        / "m3_5_1_deck_summary.csv"
    )
    policy_path = (
        ROOT
        / "playtest_data"
        / "summaries"
        / "m3_5_1_policy_summary.csv"
    )
    overall_path = (
        ROOT
        / "playtest_data"
        / "summaries"
        / "m3_5_1_overall.json"
    )

    save_rows(detail_path, results)
    save_rows(pairing_path, summary["pairings"])
    save_rows(deck_path, summary["decks"])
    save_rows(policy_path, summary["policies"])

    overall_path.parent.mkdir(parents=True, exist_ok=True)
    overall_path.write_text(
        json.dumps(summary["overall"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    overall = summary["overall"]

    print("")
    print("=== M3.5.1 Mirrored Baseline ===")
    print(
        f"games={overall['games']} "
        f"finished={overall['finished']} "
        f"P1={overall['p1_win_rate']:.1%} "
        f"avg_turns={overall['avg_turns']:.2f} "
        f"avg_actions={overall['avg_actions']:.2f} "
        f"invalid={overall['invalid_legal_action']} "
        f"stalled={overall['stalled']} "
        f"limit={overall['action_limit']}"
    )

    print("")
    print("Deck results:")
    for row in summary["decks"]:
        print(
            f"  {row['deck']}: "
            f"wins={row['wins']} "
            f"opportunities={row['opportunities']} "
            f"WR={row['win_rate']:.1%}"
        )

    print("")
    print("Policy results:")
    for row in summary["policies"]:
        print(
            f"  {row['policy']}: "
            f"wins={row['wins']} "
            f"opportunities={row['opportunities']} "
            f"WR={row['win_rate']:.1%}"
        )

    print("")
    print("Pairings:")
    for row in summary["pairings"]:
        print(
            f"  {row['pairing']}: "
            f"games={row['games']} "
            f"P1={row['p1_win_rate']:.1%} "
            f"avg_turns={row['avg_turns']:.2f} "
            f"avg_actions={row['avg_actions']:.2f}"
        )

    print("")
    print("detail:", detail_path)
    print("pairings:", pairing_path)
    print("decks:", deck_path)
    print("policies:", policy_path)
    print("overall:", overall_path)


if __name__ == "__main__":
    main()
