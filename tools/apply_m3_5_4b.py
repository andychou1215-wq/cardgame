from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    required = [
        ROOT / "src/playtest/deck_attribution.py",
        ROOT / "src/playtest/card_outliers_attributed.py",
        ROOT / "tools/rebuild_deck_attributed_telemetry.py",
        ROOT / "tools/run_attributed_card_outliers.py",
        ROOT / "tests/unit/test_deck_attribution.py",
    ]

    missing = [
        str(path.relative_to(ROOT))
        for path in required
        if not path.exists()
    ]

    if missing:
        raise SystemExit(
            "M3.5.4b files missing: " + ", ".join(missing)
        )

    print("M3.5.4b verified.")
    print("Run:")
    print("  py -m pytest -q")
    print("  py tools/rebuild_deck_attributed_telemetry.py")
    print("  py tools/run_attributed_card_outliers.py")


if __name__ == "__main__":
    main()
