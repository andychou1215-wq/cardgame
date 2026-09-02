from pathlib import Path
import argparse
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.playtest.damage_healing import (
    analyze_damage_healing,
    export_analysis,
    render_report,
)


def read_csv(path):
    return pd.read_csv(path, encoding="utf-8-sig")


def main():
    p = argparse.ArgumentParser(description="M3.7.5 Damage / Healing Profile")
    p.add_argument("--summaries", required=True)
    p.add_argument("--events", required=True)
    p.add_argument("--output", default="playtest_data/analysis/m3_7_5")
    args = p.parse_args()

    result = analyze_damage_healing(
        read_csv(args.summaries),
        read_csv(args.events),
    )
    print(render_report(result))
    out = export_analysis(result, args.output)
    print()
    print(f"Exported M3.7.5 artifacts to: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
