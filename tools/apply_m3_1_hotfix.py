from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

def main():
    expected = [
        ROOT / "src/ai/actions.py",
        ROOT / "src/ai/legal_actions.py",
        ROOT / "src/ai/executor.py",
    ]
    missing = [str(p.relative_to(ROOT)) for p in expected if not p.exists()]
    if missing:
        raise SystemExit("M3 files missing: " + ", ".join(missing))

    # Files in this hotfix ZIP are already extracted directly over the repo.
    # This command is intentionally verification-only.
    text = (ROOT / "src/ai/legal_actions.py").read_text(encoding="utf-8")

    checks = [
        'card_type", "") == "response"',
        "game.legal_play_targets(hand_index)",
        "game.legal_attackers()",
        "game.legal_attack_targets()",
        "game.activated_options()",
    ]
    missing_checks = [x for x in checks if x not in text]
    if missing_checks:
        raise SystemExit(
            "Hotfix files were not copied over current M3 files. Missing: "
            + ", ".join(missing_checks)
        )

    print("M3.1 Legal Action hotfix verified.")
    print("Run:")
    print("  py -m pytest -q")
    print("  py tools/run_simulation.py --games 10 --seed 42 --no-persist")

if __name__ == "__main__":
    main()
