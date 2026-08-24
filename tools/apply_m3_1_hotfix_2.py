from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "src/core/game.py"


def main():
    if not GAME.exists():
        raise SystemExit("src/core/game.py not found")

    text = GAME.read_text(encoding="utf-8")

    if "    def can_play_card(self, hand_index: int)" not in text:
        marker = "    def legal_play_targets(self, hand_index: int) -> list[TargetRef]:\n"
        if marker not in text:
            raise SystemExit("legal_play_targets() anchor not found")

        helper = (
            "    def can_play_card(self, hand_index: int) -> tuple[bool, str]:\n"
            "        if not self.game_started:\n"
            "            return False, \"請先完成雙方 Mulligan。\"\n"
            "        if self.pending_choice or self.pending_combat:\n"
            "            return False, \"請先完成目前等待中的效果或戰鬥結算。\"\n"
            "        player = self.active_player\n"
            "        if hand_index < 0 or hand_index >= len(player.hand):\n"
            "            return False, \"無效的手牌索引。\"\n"
            "        card = player.hand[hand_index]\n"
            "        if card.cost > player.mana:\n"
            "            return False, \"魔力不足。\"\n"
            "        if card.card_type == \"response\":\n"
            "            return False, \"Response 只能在對應的 Response Window 使用。\"\n"
            "        if card.card_type == \"unit\" and len(player.battlefield) >= BATTLEFIELD_LIMIT:\n"
            "            return False, f\"戰場已滿（Prototype 暫定 {BATTLEFIELD_LIMIT} 格）。\"\n"
            "        effects = self.data.effects_for(card.card_id, \"on_play\", \"none\")\n"
            "        for effect in effects:\n"
            "            if effect.target_required and not self._candidate_targets(\n"
            "                effect, card.instance_id, self.active_player_index, None\n"
            "            ):\n"
            "                return False, \"沒有合法目標，無法打出此卡。\"\n"
            "        return True, \"可打出。\"\n"
            "\n"
        )
        text = text.replace(marker, helper + marker, 1)
        GAME.write_text(text, encoding="utf-8")
        print("[OK] Added authoritative Game.can_play_card()")
    else:
        print("[SKIP] Game.can_play_card() already exists")

    checks = {
        "AI can_play_card": 'can_play = getattr(game, "can_play_card", None)' in (ROOT / "src/ai/legal_actions.py").read_text(encoding="utf-8"),
        "PendingChoice actor": 'getattr(queued, "source_player_index", None)' in (ROOT / "src/playtest/simulation.py").read_text(encoding="utf-8"),
        "Stall diagnostics": "describe_decision_state" in (ROOT / "src/playtest/simulation.py").read_text(encoding="utf-8"),
    }

    for name, ok in checks.items():
        print(("PASS" if ok else "FAIL") + ": " + name)

    if not all(checks.values()):
        raise SystemExit("Hotfix 2 files were not copied correctly.")

    print("")
    print("Run:")
    print("  py -m pytest -q")
    print("  py tools/run_simulation.py --games 10 --seed 42 --no-persist")


if __name__ == "__main__":
    main()
