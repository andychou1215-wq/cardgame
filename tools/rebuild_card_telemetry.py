from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.playtest.telemetry_metrics import (
    read_csv,
    rebuild_card_usage_metrics,
)


def _card_lookup():
    path = ROOT / "data" / "cards" / "cards.csv"
    rows = read_csv(path)
    return {
        row.get("id", "").strip(): row
        for row in rows
        if row.get("id", "").strip()
    }


def _save_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser(
        description="M3.5.4a rebuild corrected card telemetry"
    )
    p.add_argument(
        "--event-log",
        default=str(
            ROOT / "playtest_data" / "raw" / "event_log.csv"
        ),
    )
    p.add_argument(
        "--game-summary",
        default=str(
            ROOT / "playtest_data" / "summaries" / "game_summary.csv"
        ),
    )
    p.add_argument(
        "--output",
        default=str(
            ROOT
            / "playtest_data"
            / "analysis"
            / "m3_5_3"
            / "card_telemetry.csv"
        ),
    )
    p.add_argument(
        "--capabilities",
        default=str(
            ROOT
            / "playtest_data"
            / "analysis"
            / "m3_5_3"
            / "telemetry_capabilities.json"
        ),
    )
    args = p.parse_args()

    event_rows = read_csv(args.event_log)
    if not event_rows:
        raise SystemExit("event_log.csv missing or empty")

    summary_rows = read_csv(args.game_summary)

    result = rebuild_card_usage_metrics(
        event_rows,
        card_lookup=_card_lookup(),
        summary_rows=summary_rows,
    )

    output_path = Path(args.output)
    _save_csv(output_path, result["cards"])

    capabilities_path = Path(args.capabilities)
    capabilities_path.parent.mkdir(parents=True, exist_ok=True)
    capabilities_path.write_text(
        json.dumps(
            {
                "available": result["available"],
                "reason": result["reason"],
                "capabilities": result["capabilities"],
                "metric_semantics": {
                    "normal_play_events": "card_played",
                    "response_play_events": "response_played",
                    "use_events": "normal_play_events + response_play_events",
                    "recorded_draw_events": "explicit card_drawn only",
                    "uses_per_recorded_draw": (
                        "diagnostic ratio, not probability; may exceed 1 "
                        "when initial-hand/Mulligan acquisitions are not logged"
                    ),
                    "uses_per_recorded_acquisition": (
                        "use_events divided by all acquisition event types "
                        "currently present in telemetry"
                    ),
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("")
    print("=== M3.5.4a Telemetry Metric Fix ===")
    caps = result["capabilities"]
    for key, value in caps.items():
        print(f"{key}: {value}")

    print("")
    print("Cards with response usage:")
    response_cards = sorted(
        [
            row
            for row in result["cards"]
            if int(row["response_play_events"] or 0) > 0
        ],
        key=lambda row: int(row["response_play_events"] or 0),
        reverse=True,
    )
    for row in response_cards[:10]:
        print(
            f"  {row['card_id']} {row['name']}: "
            f"response={row['response_play_events']} "
            f"normal={row['normal_play_events']} "
            f"use={row['use_events']} "
            f"recorded_draw={row['recorded_draw_events']} "
            f"uses/recorded_draw={row['uses_per_recorded_draw']}"
        )

    print("")
    print("Output:", output_path)
    print("Capabilities:", capabilities_path)
    print("")
    print("Next:")
    print("  py tools/run_card_outliers.py")


if __name__ == "__main__":
    main()
