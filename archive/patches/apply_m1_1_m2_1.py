from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "src/core/game.py"
APP = ROOT / "streamlit_app.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def patch_game() -> None:
    text = GAME.read_text(encoding="utf-8")

    if "from src.core.events import TriggerEvent, TriggerQueue" not in text:
        text = replace_once(
            text,
            "from src.effects.models import EffectDefinition, TargetRef\n",
            "from src.effects.models import EffectDefinition, TargetRef\n"
            "from src.core.events import TriggerEvent, TriggerQueue\n"
            "from src.core.state_based import StateBasedCheck\n"
            "from src.playtest.telemetry import PlaytestRecorder\n",
            "imports",
        )

    if "self.trigger_queue = TriggerQueue()" not in text:
        text = replace_once(
            text,
            "        self.effect_queue: list[QueuedEffect] = []\n",
            "        self.effect_queue: list[QueuedEffect] = []\n"
            "        self.trigger_queue = TriggerQueue()\n"
            "        self.state_based = StateBasedCheck()\n"
            "        self.telemetry = PlaytestRecorder(seed=seed)\n",
            "Game.__init__",
        )

    old = "\n".join([
        "    def _queue_trigger(self, source: CardInstance, trigger: str, owner_index: int | None = None, trigger_target: TargetRef | None = None) -> None:",
        "        if owner_index is None:",
        "            owner_index = self.owner_of_card(source.instance_id)",
        '        side = source.current_side if isinstance(source, UnitInstance) else "none"',
        "        for effect in self.data.effects_for(source.card_id, trigger, side):",
        "            self.effect_queue.append(QueuedEffect(effect, source.instance_id, owner_index, trigger_target))",
        "",
    ])
    new = "\n".join([
        "    def _queue_trigger(self, source: CardInstance, trigger: str, owner_index: int | None = None, trigger_target: TargetRef | None = None) -> None:",
        "        if owner_index is None:",
        "            owner_index = self.owner_of_card(source.instance_id)",
        '        side = source.current_side if isinstance(source, UnitInstance) else "none"',
        "        self.trigger_queue.push(",
        "            TriggerEvent(",
        "                trigger=trigger,",
        "                source_id=source.instance_id,",
        "                card_id=source.card_id,",
        "                side=side,",
        "                owner_index=owner_index,",
        "                trigger_target=trigger_target,",
        "            )",
        "        )",
        "",
    ])
    if old in text:
        text = replace_once(text, old, new, "_queue_trigger")

    if "                if self.trigger_queue:\n" not in text:
        old = "                if self.effect_queue:\n                    queued = self.effect_queue.pop(0)\n"
        new = "\n".join([
            "                if self.trigger_queue:",
            "                    event = self.trigger_queue.pop()",
            "                    self.telemetry.record(",
            '                        "trigger",',
            "                        turn=self.turn_number,",
            "                        active_player=self.active_player_index,",
            "                        player_index=event.owner_index,",
            "                        card_id=event.card_id,",
            "                        source_id=event.source_id,",
            "                        target=event.trigger_target,",
            '                        metadata={"trigger": event.trigger, "side": event.side},',
            "                    )",
            "                    for effect in self.data.effects_for(event.card_id, event.trigger, event.side):",
            "                        self.effect_queue.append(",
            "                            QueuedEffect(effect, event.source_id, event.owner_index, event.trigger_target)",
            "                        )",
            "                    continue",
            "                if self.effect_queue:",
            "                    queued = self.effect_queue.pop(0)",
            "",
        ])
        text = replace_once(text, old, new, "trigger queue drain")

    if "    def _run_state_based_check(self):\n" not in text:
        marker = "    def resolve_pending_choice(self, target: TargetRef) -> tuple[bool, str]:\n"
        helper = "\n".join([
            "    def _run_state_based_check(self):",
            "        result = self.state_based.run_once(self)",
            "        self.telemetry.record(",
            '            "state_based_check",',
            "            turn=self.turn_number,",
            "            active_player=self.active_player_index,",
            '            metadata={"changed": result.changed, "deaths": result.deaths, "transforms": result.transforms, "winner_changed": result.winner_changed},',
            "        )",
            "        return result",
            "",
            "",
        ])
        text = replace_once(text, marker, helper + marker, "state-based helper")

    old_idle = "\n".join([
        "                # No queued effects: resolve state-based deaths, then transforms.",
        "                if self._handle_deaths():",
        "                    continue",
        "                if self.check_transforms():",
        "                    continue",
        "                break",
        "",
    ])
    new_idle = "\n".join([
        "                # No queued work: run one authoritative state-based checkpoint.",
        "                state = self._run_state_based_check()",
        "                if state.changed:",
        "                    continue",
        "                break",
        "",
    ])
    if old_idle in text:
        text = replace_once(text, old_idle, new_idle, "idle state-based block")

    text = text.replace("                        self._handle_deaths()\n", "                        self._run_state_based_check()\n")
    text = text.replace("                            self._handle_deaths()\n", "                            self._run_state_based_check()\n")
    text = text.replace(
        "        self._handle_deaths()\n        self.process_effect_queue()\n        return True, \"效果目標已選擇並完成結算。\"\n",
        "        self._run_state_based_check()\n        self.process_effect_queue()\n        return True, \"效果目標已選擇並完成結算。\"\n",
    )
    text = text.replace(
        "        self._handle_deaths()\n        self.process_effect_queue()\n        return True, \"Response 已使用。\"\n",
        "        self._run_state_based_check()\n        self.process_effect_queue()\n        return True, \"Response 已使用。\"\n",
    )
    text = text.replace(
        "        # State-based deaths are collected simultaneously, then on_leave triggers are queued.\n        self._handle_deaths()\n",
        "        # Central state-based checkpoint handles simultaneous deaths before later trigger chains.\n        self._run_state_based_check()\n",
    )

    hooks = [
        (
            '"card_played"',
            '        self.log(f"{player.name} 打出 {played.card_id} {played.name}，消耗 {played.cost} 魔力。")\n',
            '        self.log(f"{player.name} 打出 {played.card_id} {played.name}，消耗 {played.cost} 魔力。")\n'
            '        self.telemetry.record("card_played", turn=self.turn_number, active_player=self.active_player_index, player_index=self.active_player_index, card_id=played.card_id, source_id=played.instance_id)\n',
        ),
        (
            '"attack_declared"',
            '        self.log(f"{self.active_player.name} 宣告 {attacker.card_id} {attacker.name} 攻擊 {target_name}。")\n',
            '        self.log(f"{self.active_player.name} 宣告 {attacker.card_id} {attacker.name} 攻擊 {target_name}。")\n'
            '        self.telemetry.record("attack_declared", turn=self.turn_number, active_player=self.active_player_index, player_index=self.active_player_index, card_id=attacker.card_id, source_id=attacker.instance_id, target=defender)\n',
        ),
        (
            '"response_played"',
            '        self.log(f"{player.name} 使用 Response {card.card_id} {card.name}。")\n',
            '        self.log(f"{player.name} 使用 Response {card.card_id} {card.name}。")\n'
            '        self.telemetry.record("response_played", turn=self.turn_number, active_player=self.active_player_index, player_index=defending_index, card_id=card.card_id, source_id=card.instance_id, target=combat.defender)\n',
        ),
        (
            '"transform"',
            '        self.log(f"{unit.card_id} {unit.name} 達成翻面條件，翻至反面。")\n',
            '        self.log(f"{unit.card_id} {unit.name} 達成翻面條件，翻至反面。")\n'
            '        self.telemetry.record("transform", turn=self.turn_number, active_player=self.active_player_index, player_index=owner_index, card_id=unit.card_id, source_id=unit.instance_id)\n',
        ),
    ]
    for event_name, anchor, replacement in hooks:
        if event_name not in text and anchor in text:
            text = replace_once(text, anchor, replacement, f"telemetry {event_name}")

    GAME.write_text(text, encoding="utf-8")
    print("Patched src/core/game.py")


def patch_streamlit() -> None:
    if not APP.exists():
        return
    text = APP.read_text(encoding="utf-8")
    if "from src.ui.playtest_panel import playtest_data_panel" not in text:
        text = replace_once(
            text,
            "from src.deck.loader import DataError, GameData\n",
            "from src.deck.loader import DataError, GameData\nfrom src.ui.playtest_panel import playtest_data_panel\n",
            "Streamlit import",
        )
    if "playtest_data_panel(game)" not in text:
        text = replace_once(
            text,
            'with st.expander("Prototype 規則假設 / 已知限制"):\n',
            'playtest_data_panel(game)\n\nwith st.expander("Prototype 規則假設 / 已知限制"):\n',
            "Playtest panel",
        )
    text = text.replace("Streamlit Prototype v4", "Streamlit Prototype v5")
    APP.write_text(text, encoding="utf-8")
    print("Patched streamlit_app.py")


if __name__ == "__main__":
    patch_game()
    patch_streamlit()
    print("M1.1 + M2.1 cumulative patch complete.")
