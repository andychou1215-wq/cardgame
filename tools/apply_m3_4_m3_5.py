from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI_INIT = ROOT / "src/ai/__init__.py"


def main():
    if not AI_INIT.exists():
        raise SystemExit("src/ai/__init__.py not found; M3 must be installed first.")

    text = AI_INIT.read_text(encoding="utf-8")
    lines = []

    if "from .heuristic_bot import HeuristicBot, HeuristicWeights" not in text:
        lines.append("from .heuristic_bot import HeuristicBot, HeuristicWeights")

    if lines:
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n".join(lines) + "\n"
        AI_INIT.write_text(text, encoding="utf-8")
        print("[OK] Updated src/ai/__init__.py")
    else:
        print("[SKIP] M3.4 exports already present")

    required = [
        ROOT / "src/ai/heuristic_bot.py",
        ROOT / "src/ai/policies.py",
        ROOT / "src/playtest/baseline.py",
        ROOT / "tools/run_baseline.py",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise SystemExit("Missing M3.4/M3.5 files: " + ", ".join(missing))

    print("M3.4 + M3.5 verified.")
    print("Run:")
    print("  py -m pytest -q")
    print("  py tools/run_baseline.py --games-per-pairing 10 --seed 42")


if __name__ == "__main__":
    main()
