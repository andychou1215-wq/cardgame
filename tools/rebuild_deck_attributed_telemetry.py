from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.playtest.deck_attribution import (
    aggregate_deck_card_usage,
    attribute_events_to_decks,
    build_game_player_deck_map,
    build_static_membership,
    read_csv,
)


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
        description="M3.5.4b shared-card deck attribution"
    )
    p.add_argument(
        "--event-log",
        default=str(ROOT / "playtest_data" / "raw" / "event_log.csv"),
    )
    p.add_argument(
        "--game-summary",
        default=str(
            ROOT / "playtest_data" / "summaries" / "game_summary.csv"
        ),
    )
    p.add_argument(
        "--mirrored-games",
        default=str(
            ROOT
            / "playtest_data"
            / "summaries"
            / "m3_5_1_mirrored_games.csv"
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
        "--output-dir",
        default=str(
            ROOT
            / "playtest_data"
            / "analysis"
            / "m3_5_4b"
        ),
    )
    args = p.parse_args()

    events = read_csv(args.event_log)
    summaries = read_csv(args.game_summary)
    mirrored = read_csv(args.mirrored_games)
    efficiency = read_csv(args.card_efficiency)

    if not events:
        raise SystemExit("event_log.csv missing or empty")
    if not efficiency:
        raise SystemExit("card_efficiency.csv missing or empty; run M3.5.3")

    membership = build_static_membership(efficiency)

    deck_map, map_diagnostics = build_game_player_deck_map(
        summaries,
        mirrored,
    )

    attributed = attribute_events_to_decks(
        events,
        membership,
        deck_map,
    )

    deck_card_rows = aggregate_deck_card_usage(
        attributed["events"],
        summaries,
    )

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    telemetry_path = save_csv(
        out / "deck_card_telemetry.csv",
        deck_card_rows,
    )
    unresolved_path = save_csv(
        out / "unattributed_shared_cards.csv",
        attributed["unresolved_shared"],
    )

    diagnostics = {
        "game_player_deck_map": map_diagnostics,
        "attribution": {
            "counts": attributed["counts"],
            "capabilities": attributed["capabilities"],
        },
    }
    diagnostics_path = out / "attribution_diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(diagnostics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("")
    print("=== M3.5.4b Shared Card / Deck Attribution ===")
    print("")
    print("Game/player deck mapping:")
    print(f"  supported={map_diagnostics['supported']}")
    print(f"  mappings={len(deck_map)}")
    print(
        "  rows_with_deck_pair="
        f"{map_diagnostics['rows_with_deck_pair']}"
    )
    print(f"  conflicts={len(map_diagnostics['conflicts'])}")

    print("")
    print("Attribution:")
    for key, value in attributed["counts"].items():
        print(f"  {key}={value}")

    print("")
    if attributed["unresolved_shared"]:
        print("Unattributed shared cards:")
        for row in attributed["unresolved_shared"]:
            print(
                f"  {row['card_id']}: "
                f"decks={row['candidate_decks']} "
                f"events={row['events']} "
                f"reason={row['reason']}"
            )
        print("")
        print(
            "Shared cards above are intentionally EXCLUDED from "
            "deck-relative telemetry rather than duplicated across decks."
        )
    else:
        print("All shared-card events were attributed to a deck.")

    print("")
    print("Output:")
    print("  telemetry:", telemetry_path)
    print("  unresolved:", unresolved_path)
    print("  diagnostics:", diagnostics_path)


if __name__ == "__main__":
    main()
