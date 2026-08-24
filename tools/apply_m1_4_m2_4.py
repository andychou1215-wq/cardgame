from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
STACK = ROOT / "src/core/stack.py"
GAME = ROOT / "src/core/game.py"
DASH = ROOT / "apps/playtest_dashboard.py"
if not DASH.exists(): DASH = ROOT / "playtest_dashboard.py"

def fail(msg):
    print("[ERROR]", msg)
    sys.exit(1)

def patch_stack():
    if not STACK.exists(): fail('src/core/stack.py missing; apply M1.3 first')
    text = STACK.read_text(encoding="utf-8")
    if "stack_item_id:" not in text:
        anchor = "    source_id: str\n"
        if anchor not in text: fail('StackItem source_id anchor missing')
        text = text.replace(anchor, "    stack_item_id: str\n" + anchor, 1)
    STACK.write_text(text, encoding="utf-8")

def patch_game():
    if not GAME.exists(): fail('src/core/game.py missing')
    text = GAME.read_text(encoding="utf-8")
    if "from src.core.stack_manager import StackManager" not in text:
        anchor = "from src.core.stack import StackItem, validate_target_ref\n"
        if anchor not in text: fail('M1.3 stack import missing')
        text = text.replace(anchor, anchor + "from src.core.stack_manager import StackManager\nfrom src.core.stack_target import StackTargetRef\n", 1)

    old = "        stack_item = StackItem(\n            source_id=card.instance_id,\n"
    if old in text:
        new = "        stack_item = StackItem(\n            stack_item_id=f\"stk-{self.turn_number}-{len(window.stack)+1}-{card.instance_id}\",\n            source_id=card.instance_id,\n"
        text = text.replace(old, new, 1)

    marker = "        for item in window.drain_lifo():\n"
    if marker in text and 'item.status == "cancelled"' not in text:
        cancelled = (
            "            if item.status == \"cancelled\":\n"
            "                self.log(f\"Response {item.card_id} 已被取消，不進行結算。\")\n"
            "                if hasattr(self, \"telemetry\"):\n"
            "                    self.telemetry.record(\n"
            "                        \"response_cancelled\",\n"
            "                        turn=self.turn_number,\n"
            "                        active_player=self.active_player_index,\n"
            "                        player_index=item.controller_index,\n"
            "                        card_id=item.card_id,\n"
            "                        source_id=item.source_id,\n"
            "                        metadata={\"stack_item_id\": item.stack_item_id, \"reason\": item.result_reason},\n"
            "                    )\n"
            "                continue\n"
        )
        text = text.replace(marker, marker + cancelled, 1)

    insert = "    def priority_player_index(self) -> int | None:\n"
    if "    def cancel_stack_item(" not in text and insert in text:
        helper = (
            "    def pending_stack_items(self):\n"
            "        window = self.priority_window\n"
            "        return [] if window is None else StackManager(window).pending_items()\n"
            "\n"
            "    def cancel_stack_item(self, stack_item_id: str, *, reason: str = \"countered\"):\n"
            "        window = self.priority_window\n"
            "        if window is None:\n"
            "            return False, \"目前沒有 Priority Window。\"\n"
            "        ok = StackManager(window).cancel(stack_item_id, reason)\n"
            "        if not ok:\n"
            "            return False, \"找不到可取消的 Stack Item。\"\n"
            "        if hasattr(self, \"telemetry\"):\n"
            "            self.telemetry.record(\n"
            "                \"stack_item_cancelled\",\n"
            "                turn=self.turn_number,\n"
            "                active_player=self.active_player_index,\n"
            "                metadata={\"stack_item_id\": stack_item_id, \"reason\": reason},\n"
            "            )\n"
            "        return True, \"Stack Item 已取消。\"\n"
            "\n"
        )
        text = text.replace(insert, helper + insert, 1)

    GAME.write_text(text, encoding="utf-8")

def patch_dashboard():
    if not DASH.exists(): return
    text = DASH.read_text(encoding="utf-8")
    imp = "from src.ui.advanced_playtest_panel import render_m2_4_dashboard\n"
    if imp not in text:
        lines = text.splitlines()
        idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "): idx = i + 1
        lines.insert(idx, imp.rstrip())
        text = "\n".join(lines) + "\n"
    if "render_m2_4_dashboard(analytics)" not in text:
        text += "\ntry:\n    render_m2_4_dashboard(analytics)\nexcept NameError:\n    pass\n"
    DASH.write_text(text, encoding="utf-8")

def main():
    patch_stack()
    patch_game()
    patch_dashboard()
    print("M1.4 + M2.4 patch applied.")
    print("Run: py -m pytest -q")

if __name__ == "__main__":
    main()
