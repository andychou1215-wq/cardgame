from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "src/core/game.py"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


def main() -> None:
    if not GAME.exists():
        fail(f"找不到核心檔案：{GAME}")

    text = GAME.read_text(encoding="utf-8")

    insertion_marker = "    # ---------- Card play ----------\n"
    if "    def _draw_cards(\n" not in text:
        helper = (
            "    def _draw_cards(\n"
            "        self,\n"
            "        player_index: int,\n"
            "        count: int = 1,\n"
            "        *,\n"
            "        reason: str = \"effect\",\n"
            "    ) -> int:\n"
            "        if count <= 0 or self.winner_index is not None:\n"
            "            return 0\n"
            "        player = self.players[player_index]\n"
            "        drawn = 0\n"
            "        for _ in range(count):\n"
            "            if not player.deck:\n"
            "                self._declare_deck_out_loss(player_index, reason=reason)\n"
            "                break\n"
            "            player.hand.append(player.deck.pop())\n"
            "            drawn += 1\n"
            "        if drawn > 0 and hasattr(self, \"telemetry\"):\n"
            "            self.telemetry.record(\n"
            "                \"draw\",\n"
            "                turn=self.turn_number,\n"
            "                active_player=self.active_player_index,\n"
            "                player_index=player_index,\n"
            "                amount=drawn,\n"
            "                metadata={\"reason\": reason},\n"
            "            )\n"
            "        return drawn\n"
            "\n"
            "    def _declare_deck_out_loss(self, player_index: int, *, reason: str) -> None:\n"
            "        if self.winner_index is not None:\n"
            "            return\n"
            "        loser = self.players[player_index]\n"
            "        winner_index = 1 - player_index\n"
            "        winner = self.players[winner_index]\n"
            "        self.winner_index = winner_index\n"
            "        self.log(f\"{loser.name} 需要抽牌，但牌組已無牌可抽，因牌庫耗盡而敗北。\")\n"
            "        self.log(f\"遊戲結束：{winner.name} 獲勝。\")\n"
            "        if hasattr(self, \"telemetry\"):\n"
            "            self.telemetry.record(\n"
            "                \"deck_out\",\n"
            "                turn=self.turn_number,\n"
            "                active_player=self.active_player_index,\n"
            "                player_index=player_index,\n"
            "                metadata={\"reason\": reason, \"winner_index\": winner_index},\n"
            "            )\n"
            "            self.telemetry.record(\n"
            "                \"game_end\",\n"
            "                turn=self.turn_number,\n"
            "                active_player=self.active_player_index,\n"
            "                player_index=winner_index,\n"
            "                metadata={\"winner_index\": winner_index, \"reason\": \"deck_out\", \"loser_index\": player_index},\n"
            "            )\n"
            "\n"
        )
        if insertion_marker not in text:
            fail("找不到 Card play 區段。")
        text = text.replace(insertion_marker, helper + insertion_marker, 1)
        print("[OK] 已加入 deck-out draw helper")

    old_turn = (
        "        if not initial:\n"
        "            drawn = player.draw(1)\n"
        "            self.log(f\"{player.name} 回合開始，回復至 {player.mana}/{player.max_mana} 魔力並抽 {drawn} 張牌。\")\n"
    )
    new_turn = (
        "        if not initial:\n"
        "            drawn = self._draw_cards(self.active_player_index, 1, reason=\"turn_start\")\n"
        "            self.log(f\"{player.name} 回合開始，回復至 {player.mana}/{player.max_mana} 魔力並抽 {drawn} 張牌。\")\n"
        "            if self.winner_index is not None:\n"
        "                return\n"
    )
    if old_turn in text:
        text = text.replace(old_turn, new_turn, 1)
        print("[OK] 回合開始抽牌已接上 deck-out")
    elif 'reason="turn_start"' not in text:
        fail("找不到回合開始抽牌 anchor。")

    old_effect = (
        "            if effect.operation == \"draw\":\n"
        "                n = self.players[ref.player_index].draw(effect.value)\n"
        "                self.log(f\"{effect.effect_id}: {self.players[ref.player_index].name} 抽 {n} 張牌。\")\n"
    )
    new_effect = (
        "            if effect.operation == \"draw\":\n"
        "                n = self._draw_cards(ref.player_index, effect.value, reason=f\"effect:{effect.effect_id}\")\n"
        "                self.log(f\"{effect.effect_id}: {self.players[ref.player_index].name} 抽 {n} 張牌。\")\n"
        "                if self.winner_index is not None:\n"
        "                    return\n"
    )
    if old_effect in text:
        text = text.replace(old_effect, new_effect, 1)
        print("[OK] draw Effect 已接上 deck-out")
    elif 'reason=f"effect:{effect.effect_id}"' not in text:
        fail("找不到 draw effect anchor。")

    old_winner = (
        "    def _check_winner(self) -> None:\n"
        "        dead = [i for i, p in enumerate(self.players) if p.leader_health <= 0]\n"
    )
    new_winner = (
        "    def _check_winner(self) -> None:\n"
        "        if self.winner_index is not None:\n"
        "            return\n"
        "        dead = [i for i, p in enumerate(self.players) if p.leader_health <= 0]\n"
    )
    if old_winner in text:
        text = text.replace(old_winner, new_winner, 1)
        print("[OK] winner check 不會覆蓋 deck-out")

    GAME.write_text(text, encoding="utf-8")

    verify = GAME.read_text(encoding="utf-8")
    required = [
        "def _draw_cards(",
        "def _declare_deck_out_loss(",
        "reason=\"turn_start\"",
        "reason=f\"effect:{effect.effect_id}\"",
        "\"deck_out\"",
    ]
    missing = [x for x in required if x not in verify]
    if missing:
        fail(f"寫入後驗證失敗：{missing}")

    print("=== Deck-out hotfix applied and verified ===")
    print("py -m pytest -q tests/test_deck_out.py")
    print("py -m pytest -q")


if __name__ == "__main__":
    main()
