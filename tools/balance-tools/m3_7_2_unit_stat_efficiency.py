from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.playtest.unit_stat_efficiency import (
    analyze_unit_stat_efficiency,
    export_analysis,
    render_report,
)


def _read(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="M3.7.2 Unit Stat Efficiency diagnostics"
    )
    parser.add_argument(
        "--cards",
        default="data/cards/cards.csv",
    )
    parser.add_argument(
        "--unit-sides",
        default="data/cards/unit_sides.csv",
    )
    parser.add_argument(
        "--deck-cards",
        default="data/decks/deck_cards.csv",
    )
    parser.add_argument(
        "--effects",
        default="data/cards/effects.csv",
    )
    parser.add_argument(
        "--output",
        default="playtest_data/analysis/m3_7_2",
    )
    args = parser.parse_args()

    cards = _read(args.cards)
    unit_sides = _read(args.unit_sides)
    deck_cards = _read(args.deck_cards)

    effects_path = Path(args.effects)
    effects = _read(effects_path) if effects_path.exists() else None

    result = analyze_unit_stat_efficiency(
        cards,
        unit_sides,
        deck_cards,
        effects=effects,
    )
    print(render_report(result))
    out = export_analysis(result, args.output)
    print()
    print(f"Exported M3.7.2 artifacts to: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
