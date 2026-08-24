from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "src/core/game.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    text = GAME.read_text(encoding="utf-8")

    old = (
        "    def resolve_combat(self) -> tuple[bool, str]:\n"
        "        combat = self.pending_combat\n"
        "        if self.priority_window is not None and self.priority_window.is_open:\n"
        "            return False, \"Priority Window 尚未關閉；需要雙方連續 Pass。\"\n"
    )
    new = (
        "    def resolve_combat(self) -> tuple[bool, str]:\n"
        "        combat = self.pending_combat\n"
        "        if self.priority_window is not None and self.priority_window.is_open:\n"
        "            if self._priority_can_auto_pass():\n"
        "                self._auto_pass_empty_priority_window()\n"
        "            else:\n"
        "                return False, \"Priority Window 尚未關閉；需要雙方連續 Pass。\"\n"
    )

    if old in text:
        text = replace_once(text, old, new, "resolve_combat compatibility")
    elif "_priority_can_auto_pass()" not in text:
        raise RuntimeError("Could not find M1.2 resolve_combat priority guard")

    marker = "    def resolve_combat(self) -> tuple[bool, str]:\n"
    if "    def _priority_can_auto_pass(self) -> bool:\n" not in text:
        helper = (
            "    def _priority_can_auto_pass(self) -> bool:\n"
            "        window = self.priority_window\n"
            "        if self.pending_combat is None or window is None or not window.is_open:\n"
            "            return False\n"
            "\n"
            "        original = window.current_player_index\n"
            "        try:\n"
            "            for player_index in (0, 1):\n"
            "                window.current_player_index = player_index\n"
            "                if self.available_responses(player_index):\n"
            "                    return False\n"
            "            return True\n"
            "        finally:\n"
            "            window.current_player_index = original\n"
            "\n"
            "    def _auto_pass_empty_priority_window(self) -> None:\n"
            "        window = self.priority_window\n"
            "        if window is None or not window.is_open:\n"
            "            return\n"
            "\n"
            "        first = window.current_player_index\n"
            "        closed = window.pass_priority(first)\n"
            "        if not closed:\n"
            "            second = window.current_player_index\n"
            "            window.pass_priority(second)\n"
            "        else:\n"
            "            second = 1 - first\n"
            "\n"
            "        if hasattr(self, \"telemetry\"):\n"
            "            self.telemetry.record(\n"
            "                \"priority_auto_pass\",\n"
            "                turn=self.turn_number,\n"
            "                active_player=self.active_player_index,\n"
            "                metadata={\"reason\": \"no_legal_responses\", \"first_player\": first, \"second_player\": second},\n"
            "            )\n"
            "\n"
            "        self.log(\"雙方皆無合法 Response；自動視為連續 Pass。\")\n"
            "\n"
        )
        text = replace_once(text, marker, helper + marker, "auto-pass helpers")

    GAME.write_text(text, encoding="utf-8")
    print("Applied M1.2 backward-compatibility hotfix.")
    print("Run: py -m pytest -q")


if __name__ == "__main__":
    main()
