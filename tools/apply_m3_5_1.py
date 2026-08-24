from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    required = [
        ROOT / "src/playtest/mirrored_baseline.py",
        ROOT / "tools/run_mirrored_baseline.py",
        ROOT / "tests/unit/test_mirrored_baseline.py",
    ]

    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise SystemExit(
            "M3.5.1 files missing: " + ", ".join(missing)
        )

    print("M3.5.1 verified.")
    print("Run:")
    print("  py -m pytest -q")
    print(
        "  py tools/run_mirrored_baseline.py "
        "--mirror-groups-per-pairing 10 --seed 42"
    )

if __name__ == "__main__":
    main()
