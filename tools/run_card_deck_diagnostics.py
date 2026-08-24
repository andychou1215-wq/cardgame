from __future__ import annotations

from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.playtest.card_deck_diagnostics import (
    run_card_deck_diagnostics,
    write_diagnostics_outputs,
)


def main():
    parser = argparse.ArgumentParser(
        description="M3.5.3 card/deck diagnostics"
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "playtest_data" / "analysis" / "m3_5_3"),
    )
    parser.add_argument("--event-log", default="")
    parser.add_argument("--game-summary", default="")
    args = parser.parse_args()

    result = run_card_deck_diagnostics(
        ROOT,
        event_log=args.event_log or None,
        game_summary=args.game_summary or None,
    )
    outputs = write_diagnostics_outputs(args.output_dir, result)

    print("")
    print("=== M3.5.3 Card / Deck Diagnostics ===")
    print("")
    print("Deck summary:")
    for row in result["deck_summary"]:
        print(
            f"  {row['deck_id']}: "
            f"cards={row['total_cards']} "
            f"avg_cost={row['avg_cost']:.2f} "
            f"units={row['units']} "
            f"responses={row['responses']} "
            f"unit_stats/mana={row['avg_unit_front_stats_per_mana']:.2f} "
            f"effects/card={row['avg_effects_per_card']:.2f} "
            f"keywords/card={row['avg_keywords_per_card']:.2f}"
        )

    print("")
    print("Top unit efficiency:")
    units = [
        row
        for row in result["card_efficiency"]
        if row["type"] == "unit"
        and row["front_stats_per_mana"] != ""
    ]
    units.sort(
        key=lambda row: float(row["front_stats_per_mana"]),
        reverse=True,
    )
    for row in units[:10]:
        print(
            f"  {row['deck_id']} {row['card_id']} {row['name']}: "
            f"cost={row['cost']} "
            f"ATK/HP={row['front_attack']}/{row['front_health']} "
            f"stats_per_mana={row['front_stats_per_mana']} "
            f"transform_gain={row['transform_total_stat_gain']}"
        )

    telemetry = result["telemetry"]
    print("")
    print("Telemetry:")
    print(f"  available={telemetry['available']}")
    if telemetry.get("reason"):
        print(f"  note={telemetry['reason']}")
    for key, value in telemetry.get("capabilities", {}).items():
        print(f"  {key}={value}")

    print("")
    print("Outputs:")
    for key, path in outputs.items():
        print(f"  {key}: {path}")


if __name__ == "__main__":
    main()
