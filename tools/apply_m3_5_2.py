from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    required = [
        ROOT / "src/playtest/statistical_analysis.py",
        ROOT / "tools/run_statistical_analysis.py",
        ROOT / "tests/unit/test_statistical_analysis.py",
    ]

    missing = [
        str(path.relative_to(ROOT))
        for path in required
        if not path.exists()
    ]
    if missing:
        raise SystemExit(
            "M3.5.2 files missing: " + ", ".join(missing)
        )

    print("M3.5.2 verified.")
    print("Run:")
    print("  py -m pytest -q")
    print("  py tools/run_statistical_analysis.py")


if __name__ == "__main__":
    main()
