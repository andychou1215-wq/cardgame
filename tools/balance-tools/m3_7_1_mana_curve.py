from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.playtest.mana_curve import analyze_mana_curve, export_result


def _read_many(paths: list[str] | None) -> pd.DataFrame | None:
    if not paths:
        return None
    frames = [pd.read_csv(p) for p in paths]
    return pd.concat(frames, ignore_index=True) if frames else None


def main() -> int:
    parser = argparse.ArgumentParser(description="M3.7.1 Mana Curve Analysis")
    parser.add_argument("--cards", default="data/cards/cards.csv")
    parser.add_argument("--deck-cards", default="data/decks/deck_cards.csv")
    parser.add_argument("--summaries", nargs="*", help="One or more game_summary CSV files")
    parser.add_argument("--events", nargs="*", help="One or more event_log CSV files")
    parser.add_argument("--opening-hand-size", type=int, default=5)
    parser.add_argument("--output", default="playtest_data/analysis/m3_7_1")
    args = parser.parse_args()

    cards = pd.read_csv(args.cards)
    deck_cards = pd.read_csv(args.deck_cards)
    summaries = _read_many(args.summaries)
    events = _read_many(args.events)

    if (summaries is None) != (events is None):
        parser.error("--summaries and --events must be provided together")

    result = analyze_mana_curve(
        cards,
        deck_cards,
        summaries=summaries,
        events=events,
        opening_hand_size=args.opening_hand_size,
    )
    out = export_result(result, args.output)
    print(result.report)
    print(f"Exported M3.7.1 artifacts to: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
