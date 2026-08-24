from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "src/ai/heuristic_bot.py"

def main():
    if not BOT.exists():
        raise SystemExit("src/ai/heuristic_bot.py not found")

    text = BOT.read_text(encoding="utf-8")
    checks = {
        "single legal_actions enumeration": "action_count = len(actions)" in text,
        "score_action context": "action_count: int | None = None" in text,
        "no recursive END_TURN legal_actions": "if action_count == 1:" in text,
    }

    for name, ok in checks.items():
        print(("PASS" if ok else "FAIL") + ": " + name)

    if not all(checks.values()):
        sys.exit(1)

    print("M3.4 hotfix verified.")
    print("Run:")
    print("  py -m pytest -q")
    print("  py tools/run_baseline.py --games-per-pairing 10 --seed 42")

if __name__ == "__main__":
    main()
