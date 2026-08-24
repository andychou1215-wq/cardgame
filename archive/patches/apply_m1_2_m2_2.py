from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "src/core/game.py"
COMPONENTS = ROOT / "src/ui/components.py"
TELEMETRY = ROOT / "src/playtest/telemetry.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def patch_game() -> None:
    text = GAME.read_text(encoding="utf-8")

    if "from src.core.priority import PriorityWindow" not in text:
        if "from src.core.state_based import StateBasedCheck\n" in text:
            text = replace_once(
                text,
                "from src.core.state_based import StateBasedCheck\n",
                "from src.core.state_based import StateBasedCheck\nfrom src.core.priority import PriorityWindow\n",
                "priority import",
            )
        else:
            text = replace_once(
                text,
                "from src.effects.models import EffectDefinition, TargetRef\n",
                "from src.effects.models import EffectDefinition, TargetRef\nfrom src.core.priority import PriorityWindow\n",
                "priority import fallback",
            )

    if "self.priority_window: PriorityWindow | None = None" not in text:
        anchor = "        self.pending_combat: PendingCombat | None = None\n"
        text = replace_once(
            text,
            anchor,
            anchor
            + "        self.priority_window: PriorityWindow | None = None\n"
            + "        self.first_player_index: int | None = None\n",
            "priority init",
        )

    old = "            self.active_player_index = self.rng.randrange(2)\n            self.game_started = True\n"
    if old in text and "self.first_player_index = self.active_player_index" not in text:
        text = replace_once(
            text,
            old,
            "            self.active_player_index = self.rng.randrange(2)\n"
            "            self.first_player_index = self.active_player_index\n"
            "            self.game_started = True\n",
            "first player",
        )

    attack_anchor = (
        "        self.pending_combat = PendingCombat(attacker_id, defender, self.active_player_index)\n"
        "        target_name = self.describe_target(defender)\n"
    )
    if attack_anchor in text and 'reason="attack_declared"' not in text:
        text = replace_once(
            text,
            attack_anchor,
            "        self.pending_combat = PendingCombat(attacker_id, defender, self.active_player_index)\n"
            "        defending_index = 1 - self.active_player_index\n"
            "        self.priority_window = PriorityWindow(\n"
            "            first_player_index=defending_index,\n"
            '            reason="attack_declared",\n'
            "            trigger_target=defender,\n"
            "        )\n"
            "        target_name = self.describe_target(defender)\n",
            "open priority",
        )

    start = text.find("    def available_responses(")
    end = text.find("    def _combat_damage_to_unit(", start)
    if start == -1 or end == -1:
        raise RuntimeError("Could not locate response methods")

    if "    def pass_priority(self)" not in text[start:end]:
        response_methods = '''    def available_responses(self, player_index: int | None = None) -> list[tuple[int, CardInstance, EffectDefinition]]:
        combat = self.pending_combat
        window = self.priority_window
        if combat is None or window is None or not window.is_open:
            return []

        if player_index is None:
            player_index = window.current_player_index
        if player_index != window.current_player_index:
            return []

        player = self.players[player_index]
        result = []
        for idx, card in enumerate(player.hand):
            effects = self.data.response_effects_for(card.card_id, "ally_becomes_attack_target")
            if not effects or player.mana < card.cost:
                continue
            if combat.defender.kind == "unit" and combat.defender.player_index == player_index:
                for effect in effects:
                    result.append((idx, card, effect))
        return result

    def play_response(self, hand_index: int, player_index: int | None = None) -> tuple[bool, str]:
        combat = self.pending_combat
        window = self.priority_window
        if combat is None or window is None or not window.is_open:
            return False, "目前沒有開啟中的 Response / Priority Window。"

        if player_index is None:
            player_index = window.current_player_index
        if player_index != window.current_player_index:
            return False, "目前不是此玩家的 Priority。"

        legal_indices = {idx for idx, _, _ in self.available_responses(player_index)}
        if hand_index not in legal_indices:
            return False, "此卡不能在目前的 Priority Window 使用。"

        player = self.players[player_index]
        card = player.hand[hand_index]
        effects = self.data.response_effects_for(card.card_id, "ally_becomes_attack_target")
        if not effects:
            return False, "此卡沒有合法 Response 效果。"
        if card.cost > player.mana:
            return False, "魔力不足。"

        player.mana -= card.cost
        player.hand.pop(hand_index)
        player.graveyard.append(card)

        bundle = [
            QueuedEffect(effect, card.instance_id, player_index, trigger_target=combat.defender)
            for effect in effects
        ]
        window.add_response(player_index, bundle)

        self.log(
            f"{player.name} 使用 Response {card.card_id} {card.name}；"
            f"Priority 交給 {self.players[window.current_player_index].name}。"
        )
        if hasattr(self, "telemetry"):
            self.telemetry.record(
                "response_played",
                turn=self.turn_number,
                active_player=self.active_player_index,
                player_index=player_index,
                card_id=card.card_id,
                source_id=card.instance_id,
                target=combat.defender,
                metadata={"stack_size": window.stack_size},
            )
        return True, "Response 已加入 Stack，Priority 已交給對手。"

    def pass_priority(self) -> tuple[bool, str]:
        window = self.priority_window
        if self.pending_combat is None or window is None or not window.is_open:
            return False, "目前沒有可 Pass 的 Priority Window。"

        player_index = window.current_player_index
        player_name = self.players[player_index].name
        closed = window.pass_priority(player_index)

        if hasattr(self, "telemetry"):
            self.telemetry.record(
                "priority_pass",
                turn=self.turn_number,
                active_player=self.active_player_index,
                player_index=player_index,
                metadata={
                    "consecutive_passes": window.consecutive_passes,
                    "closed": closed,
                    "stack_size": window.stack_size,
                },
            )

        if not closed:
            self.log(
                f"{player_name} Pass Priority；"
                f"Priority 交給 {self.players[window.current_player_index].name}。"
            )
            return True, "已 Pass Priority。"

        self.log("雙方連續 Pass；Response Stack 開始逆序結算。")
        self._resolve_response_stack()
        return True, "雙方已 Pass，Response Stack 結算完成，可進入戰鬥結算。"

    def _resolve_response_stack(self) -> None:
        window = self.priority_window
        if window is None:
            return

        for bundle in window.drain_lifo():
            self.effect_queue.extend(bundle)

        if self.effect_queue:
            self.process_effect_queue()

        if hasattr(self, "_run_state_based_check"):
            self._run_state_based_check()
        else:
            self._handle_deaths()

    def priority_player_index(self) -> int | None:
        if self.priority_window is None or not self.priority_window.is_open:
            return None
        return self.priority_window.current_player_index

'''
        text = text[:start] + response_methods + text[end:]

    marker = "    def resolve_combat(self) -> tuple[bool, str]:\n        combat = self.pending_combat\n"
    if marker in text and "Priority Window 尚未關閉" not in text:
        text = replace_once(
            text,
            marker,
            marker
            + "        if self.priority_window is not None and self.priority_window.is_open:\n"
            + '            return False, "Priority Window 尚未關閉；需要雙方連續 Pass。"\n',
            "combat priority guard",
        )

    text = text.replace(
        '            self.pending_combat = None\n            return False, "攻擊者已離場，戰鬥取消。"\n',
        '            self.pending_combat = None\n            self.priority_window = None\n            return False, "攻擊者已離場，戰鬥取消。"\n',
    )
    text = text.replace(
        '                self.pending_combat = None\n                return False, "防守單位已離場，戰鬥取消。"\n',
        '                self.pending_combat = None\n                self.priority_window = None\n                return False, "防守單位已離場，戰鬥取消。"\n',
    )

    clear_anchor = "        self.pending_combat = None\n        self.process_effect_queue()\n"
    if clear_anchor in text and "        self.priority_window = None\n        self.process_effect_queue()\n" not in text:
        text = replace_once(
            text,
            clear_anchor,
            "        self.pending_combat = None\n"
            "        self.priority_window = None\n"
            "        self.process_effect_queue()\n",
            "clear priority after combat",
        )

    GAME.write_text(text, encoding="utf-8")
    print("Patched src/core/game.py")


def patch_telemetry() -> None:
    if not TELEMETRY.exists():
        return
    text = TELEMETRY.read_text(encoding="utf-8")
    anchor = '                    "winner_index": game.winner_index,\n'
    if anchor in text and '"first_player_index"' not in text:
        text = replace_once(
            text,
            anchor,
            anchor + '                    "first_player_index": getattr(game, "first_player_index", None),\n',
            "telemetry first player",
        )
        TELEMETRY.write_text(text, encoding="utf-8")
        print("Patched src/playtest/telemetry.py")


def patch_components() -> None:
    text = COMPONENTS.read_text(encoding="utf-8")
    start = text.find("def response_window(game: Game) -> None:")
    end = text.find("\ndef sidebar(game: Game) -> None:", start)
    if start == -1 or end == -1:
        raise RuntimeError("Could not locate response_window")

    replacement = '''def response_window(game: Game) -> None:
    combat = game.pending_combat
    if combat is None:
        return

    attacker = game.find_unit(combat.attacker_id)
    st.warning(
        f"Response / Priority Window："
        f"{attacker.card_id if attacker else '?'} 攻擊 "
        f"{game.describe_target(combat.defender)}"
    )

    window = getattr(game, "priority_window", None)
    if window is None:
        st.error("Priority Window 尚未初始化。")
        return

    if window.is_open:
        pidx = window.current_player_index
        player = game.players[pidx]
        st.info(
            f"目前 Priority：{player.name} · "
            f"Stack {window.stack_size} · "
            f"連續 Pass {window.consecutive_passes}/2"
        )

        responses = game.available_responses(pidx)
        if responses:
            st.write(f"{player.name} 可以使用：")
            cols = st.columns(min(3, len(responses)))
            for n, (hand_idx, card, effect) in enumerate(responses):
                with cols[n % len(cols)]:
                    st.markdown(card_html(card), unsafe_allow_html=True)
                    if st.button(
                        "加入 Response Stack",
                        key=f"response_{pidx}_{card.instance_id}",
                    ):
                        ok, message = game.play_response(hand_idx, pidx)
                        st.session_state["flash"] = ("success" if ok else "error", message)
                        st.rerun()
        else:
            st.caption(f"{player.name} 目前沒有合法 Response。")

        if st.button(
            f"{player.name} — Pass Priority",
            type="primary",
            use_container_width=True,
        ):
            ok, message = game.pass_priority()
            st.session_state["flash"] = ("success" if ok else "error", message)
            st.rerun()
        return

    st.success("雙方已連續 Pass；Response Stack 已結算。")
    if st.button("進入戰鬥結算", type="primary", use_container_width=True):
        ok, message = game.resolve_combat()
        st.session_state["flash"] = ("success" if ok else "error", message)
        st.rerun()

'''
    text = text[:start] + replacement + text[end+1:]
    COMPONENTS.write_text(text, encoding="utf-8")
    print("Patched src/ui/components.py")


if __name__ == "__main__":
    patch_game()
    patch_telemetry()
    patch_components()
    print("M1.2 + M2.2 patch complete.")
