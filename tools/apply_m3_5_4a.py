from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    required = [
        ROOT / "src/playtest/telemetry_metrics.py",
        ROOT / "tools/rebuild_card_telemetry.py",
        ROOT / "tests/unit/test_telemetry_metrics.py",
    ]

    missing = [
        str(p.relative_to(ROOT))
        for p in required
        if not p.exists()
    ]

    if missing:
        raise SystemExit(
            "M3.5.4a files missing: " + ", ".join(missing)
        )

    print("M3.5.4a verified.")
    print("Run:")
    print("  py -m pytest -q")
    print("  py tools/rebuild_card_telemetry.py")
    print("  py tools/run_card_outliers.py")


if __name__ == "__main__":
    main()
