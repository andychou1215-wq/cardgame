from __future__ import annotations

from pathlib import Path
import argparse
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.playtest.card_outliers import load_csv, load_deck_baselines
from src.playtest.card_outliers_attributed import build_attributed_outliers


def save_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return path

    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def main():
    p = argparse.ArgumentParser(
        description="M3.5.4b deck-attributed card outliers"
    )
    p.add_argument(
        "--telemetry",
        default=str(
            ROOT
            / "playtest_data"
            / "analysis"
            / "m3_5_4b"
            / "deck_card_telemetry.csv"
        ),
    )
    p.add_argument(
        "--card-efficiency",
        default=str(
            ROOT
            / "playtest_data"
            / "analysis"
            / "m3_5_3"
            / "card_efficiency.csv"
        ),
    )
    p.add_argument(
        "--deck-overall",
        default=str(
            ROOT
            / "playtest_data"
            / "analysis"
            / "m3_5_2"
            / "deck_overall.csv"
        ),
    )
    p.add_argument(
        "--output-dir",
        default=str(
            ROOT
            / "playtest_data"
            / "analysis"
            / "m3_5_4b"
        ),
    )
    p.add_argument("--min-draws", type=int, default=10)
    p.add_argument("--min-uses", type=int, default=5)
    args = p.parse_args()

    telemetry = load_csv(args.telemetry)
    efficiency = load_csv(args.card_efficiency)
    baselines = load_deck_baselines(args.deck_overall)

    if not telemetry:
        raise SystemExit(
            "deck_card_telemetry.csv is empty. "
            "Run tools/rebuild_deck_attributed_telemetry.py first."
        )

    analysis = build_attributed_outliers(
        deck_card_telemetry=telemetry,
        card_efficiency=efficiency,
        deck_baselines=baselines,
        min_draws=args.min_draws,
        min_uses=args.min_uses,
    )

    out = Path(args.output_dir)
    all_path = save_csv(out / "attributed_all_cards.csv", analysis["all_cards"])
    pos_path = save_csv(
        out / "attributed_positive_outliers.csv",
        analysis["positive_outliers"],
    )
    neg_path = save_csv(
        out / "attributed_negative_outliers.csv",
        analysis["negative_outliers"],
    )

    print("")
    print("=== M3.5.4b Attributed Card Outliers ===")
    print("")
    print("Positive:")
    for row in analysis["positive_outliers"][:10]:
        print(
            f"  {row['deck_id']} {row['card_id']} {row['name']}: "
            f"use={row['use_events']} "
            f"WR_used={row['win_rate_when_used']} "
            f"deck_WR={row['deck_baseline_win_rate']} "
            f"delta={row['win_rate_delta_vs_deck']} "
            f"method={row['attribution_method']}"
        )

    print("")
    print("Negative:")
    for row in analysis["negative_outliers"][:10]:
        print(
            f"  {row['deck_id']} {row['card_id']} {row['name']}: "
            f"use={row['use_events']} "
            f"WR_used={row['win_rate_when_used']} "
            f"delta={row['win_rate_delta_vs_deck']} "
            f"method={row['attribution_method']}"
        )

    print("")
    print("Outputs:")
    print("  all:", all_path)
    print("  positive:", pos_path)
    print("  negative:", neg_path)


if __name__ == "__main__":
    main()
