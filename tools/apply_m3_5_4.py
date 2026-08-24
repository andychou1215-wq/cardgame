from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    required = [
        ROOT / "src/playtest/card_outliers.py",
        ROOT / "tools/run_card_outliers.py",
        ROOT / "tests/unit/test_card_outliers.py",
    ]

    missing = [
        str(path.relative_to(ROOT))
        for path in required
        if not path.exists()
    ]

    if missing:
        raise SystemExit(
            "M3.5.4 files missing: " + ", ".join(missing)
        )

    print("M3.5.4 verified.")
    print("Run:")
    print("  py -m pytest -q")
    print("  py tools/run_card_outliers.py")


if __name__ == "__main__":
    main()
