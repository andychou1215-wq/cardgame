from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.playtest.statistical_analysis import (
    analyze_mirrored_games,
    load_mirrored_games,
    render_markdown_report,
    save_csv,
)


def main():
    parser = argparse.ArgumentParser(description="M3.5.2 statistical analysis")
    parser.add_argument(
        "--input",
        default=str(
            ROOT
            / "playtest_data"
            / "summaries"
            / "m3_5_1_mirrored_games.csv"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "playtest_data" / "analysis" / "m3_5_2"),
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    rows = load_mirrored_games(input_path)
    analysis = analyze_mirrored_games(rows)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    save_csv(out / "deck_overall.csv", analysis["deck_overall"])
    save_csv(out / "deck_by_seat.csv", analysis["deck_by_seat"])
    save_csv(out / "deck_by_pairing.csv", analysis["deck_by_pairing"])
    save_csv(
        out / "heuristic_h2h_by_seat.csv",
        analysis["policy_head_to_head"]["by_seat"],
    )
    save_csv(
        out / "heuristic_h2h_by_deck.csv",
        analysis["policy_head_to_head"]["by_deck"],
    )
    save_csv(out / "pairing_health.csv", analysis["pairing_health"])

    summary_json = {
        "overall": analysis["overall"],
        "heuristic_head_to_head": analysis["policy_head_to_head"]["overall"],
    }
    (out / "summary.json").write_text(
        json.dumps(summary_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = render_markdown_report(analysis)
    (out / "REPORT.md").write_text(report, encoding="utf-8")

    overall = analysis["overall"]
    h2h = analysis["policy_head_to_head"]["overall"]

    print("")
    print("=== M3.5.2 Statistical Analysis ===")
    print(
        f"P1 WR={overall['p1_win_rate']:.1%} "
        f"(95% CI {overall['p1_ci_low']:.1%}-"
        f"{overall['p1_ci_high']:.1%})"
    )

    print("")
    print("Deck overall:")
    for row in analysis["deck_overall"]:
        print(
            f"  {row['deck']}: "
            f"{row['win_rate']:.1%} "
            f"({row['wins']}/{row['games']}; "
            f"95% CI {row['ci_low']:.1%}-{row['ci_high']:.1%})"
        )

    print("")
    print("Deck x Seat:")
    for row in analysis["deck_by_seat"]:
        print(
            f"  {row['deck']} as {row['seat']}: "
            f"{row['win_rate']:.1%} "
            f"({row['wins']}/{row['games']}; "
            f"95% CI {row['ci_low']:.1%}-{row['ci_high']:.1%})"
        )

    print("")
    print(
        "Heuristic vs Random H2H: "
        f"{h2h['heuristic_win_rate']:.1%} "
        f"({h2h['heuristic_wins']}/{h2h['games']}; "
        f"95% CI {h2h['ci_low']:.1%}-{h2h['ci_high']:.1%})"
    )

    print("")
    print("Output:", out)
    print("Report:", out / "REPORT.md")


if __name__ == "__main__":
    main()
