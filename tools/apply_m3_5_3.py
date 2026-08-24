from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    required = [
        ROOT / "src/playtest/card_deck_diagnostics.py",
        ROOT / "tools/run_card_deck_diagnostics.py",
        ROOT / "tests/unit/test_card_deck_diagnostics.py",
    ]

    missing = [
        str(path.relative_to(ROOT))
        for path in required
        if not path.exists()
    ]

    if missing:
        raise SystemExit(
            "M3.5.3 files missing: " + ", ".join(missing)
        )

    static_files = [
        ROOT / "data/cards/cards.csv",
        ROOT / "data/cards/unit_sides.csv",
        ROOT / "data/cards/effects.csv",
        ROOT / "data/decks/deck_cards.csv",
        ROOT / "data/decks/decks.csv",
    ]
    missing_data = [
        str(path.relative_to(ROOT))
        for path in static_files
        if not path.exists()
    ]

    if missing_data:
        raise SystemExit(
            "Required static data missing: " + ", ".join(missing_data)
        )

    print("M3.5.3 verified.")
    print("Run:")
    print("  py -m pytest -q")
    print("  py tools/run_card_deck_diagnostics.py")


if __name__ == "__main__":
    main()
