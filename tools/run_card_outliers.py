from __future__ import annotations

from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.playtest.card_outliers import (
    build_card_outlier_analysis,
    load_csv,
    load_deck_baselines,
    save_analysis_outputs,
)


def main():
    parser = argparse.ArgumentParser(
        description="M3.5.4 card performance / outlier diagnostics"
    )
    parser.add_argument(
        "--card-telemetry",
        default=str(
            ROOT
            / "playtest_data"
            / "analysis"
            / "m3_5_3"
            / "card_telemetry.csv"
        ),
    )
    parser.add_argument(
        "--card-efficiency",
        default=str(
            ROOT
            / "playtest_data"
            / "analysis"
            / "m3_5_3"
            / "card_efficiency.csv"
        ),
    )
    parser.add_argument(
        "--deck-overall",
        default=str(
            ROOT
            / "playtest_data"
            / "analysis"
            / "m3_5_2"
            / "deck_overall.csv"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(
            ROOT
            / "playtest_data"
            / "analysis"
            / "m3_5_4"
        ),
    )
    parser.add_argument("--min-draws", type=int, default=10)
    parser.add_argument("--min-plays", type=int, default=5)
    args = parser.parse_args()

    telemetry = load_csv(args.card_telemetry)
    efficiency = load_csv(args.card_efficiency)
    baselines = load_deck_baselines(args.deck_overall)

    if not telemetry:
        raise SystemExit(
            "card_telemetry.csv missing or empty. "
            "Run M3.5.3 after persisted simulation data."
        )

    if not efficiency:
        raise SystemExit(
            "card_efficiency.csv missing or empty. "
            "Run M3.5.3 first."
        )

    if not baselines:
        raise SystemExit(
            "deck_overall.csv missing or empty. "
            "Run M3.5.2 first."
        )

    analysis = build_card_outlier_analysis(
        card_telemetry=telemetry,
        card_efficiency=efficiency,
        deck_baselines=baselines,
        min_draws=args.min_draws,
        min_plays=args.min_plays,
    )

    outputs = save_analysis_outputs(
        args.output_dir,
        analysis,
        baselines,
    )

    print("")
    print("=== M3.5.4 Card Performance / Outlier Diagnostics ===")

    print("")
    print("Positive outliers:")
    for row in analysis["positive_outliers"][:10]:
        delta = row["win_rate_delta_vs_deck"]
        print(
            f"  {row['deck_id']} {row['card_id']} {row['name']}: "
            f"play={row['play_events']} "
            f"draw={row['draw_events']} "
            f"play/draw={row['play_given_draw_rate']} "
            f"WR_played={row['win_rate_when_played']} "
            f"deck_WR={row['deck_baseline_win_rate']} "
            f"delta={delta} "
            f"score={row['outlier_score']}"
        )

    print("")
    print("Negative outliers:")
    for row in analysis["negative_outliers"][:10]:
        print(
            f"  {row['deck_id']} {row['card_id']} {row['name']}: "
            f"play={row['play_events']} "
            f"draw={row['draw_events']} "
            f"play/draw={row['play_given_draw_rate']} "
            f"delta={row['win_rate_delta_vs_deck']} "
            f"score={row['outlier_score']}"
        )

    print("")
    print("High draw / low play:")
    for row in analysis["high_draw_low_play"][:10]:
        print(
            f"  {row['deck_id']} {row['card_id']} {row['name']}: "
            f"draw={row['draw_events']} "
            f"play={row['play_events']} "
            f"play/draw={row['play_given_draw_rate']} "
            f"avg_turn={row['avg_play_turn']}"
        )

    print("")
    print("Outputs:")
    for name, path in outputs.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
