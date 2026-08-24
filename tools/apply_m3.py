from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "src/core/game.py"

def main():
    if not GAME.exists():
        raise SystemExit("src/core/game.py not found")

    text = GAME.read_text(encoding="utf-8")
    if "def legal_actions(self, player_index" in text:
        print("M3 Game wrappers already present.")
        return

    # Insert before the first top-level class end is unsafe, so use a known method
    # anchor commonly present in current Game.
    anchors = [
        "    def _check_winner(self)",
        "    def log(self",
    ]
    pos = -1
    for anchor in anchors:
        pos = text.find(anchor)
        if pos != -1:
            break

    if pos == -1:
        raise SystemExit("Could not find safe Game method anchor")

    helper = (
        "    def legal_actions(self, player_index: int | None = None):\n"
        "        from src.ai.legal_actions import legal_actions\n"
        "        return legal_actions(self, player_index)\n"
        "\n"
        "    def execute_action(self, action):\n"
        "        from src.ai.executor import execute_action\n"
        "        return execute_action(self, action)\n"
        "\n"
    )

    text = text[:pos] + helper + text[pos:]
    GAME.write_text(text, encoding="utf-8")
    print("Added Game legal action wrappers.")
    print("Run: py -m pytest -q")
    print("Then: py tools/run_simulation.py --games 10 --seed 42")

if __name__ == "__main__":
    main()
