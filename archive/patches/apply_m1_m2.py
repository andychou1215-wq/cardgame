from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "src/core/game.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Cannot find patch anchor: {label}")
    if text.count(old) != 1:
        raise RuntimeError(f"Patch anchor is not unique: {label}")
    return text.replace(old, new, 1)


def main() -> None:
    text = GAME.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "from src.effects.models import EffectDefinition, TargetRef\n",
        "from src.effects.models import EffectDefinition, TargetRef\n"
        "from src.core.events import TriggerEvent, TriggerQueue\n"
        "from src.playtest.telemetry import PlaytestRecorder\n",
        "imports",
    )

    text = replace_once(
        text,
        "        self.effect_queue: list[QueuedEffect] = []\n",
        "        self.effect_queue: list[QueuedEffect] = []\n"
        "        self.trigger_queue = TriggerQueue()\n"
        "        self.telemetry = PlaytestRecorder(seed=seed)\n",
        "Game.__init__ queues",
    )

    text = replace_once(
        text,
        "    def _queue_trigger(self, source: CardInstance, trigger: str, owner_index: int | None = None, trigger_target: TargetRef | None = None) -> None:\n"
        "        if owner_index is None:\n"
        "            owner_index = self.owner_of_card(source.instance_id)\n"
        "        side = source.current_side if isinstance(source, UnitInstance) else \"none\"\n"
        "        for effect in self.data.effects_for(source.card_id, trigger, side):\n"
        "            self.effect_queue.append(QueuedEffect(effect, source.instance_id, owner_index, trigger_target))\n",
        "    def _queue_trigger(self, source: CardInstance, trigger: str, owner_index: int | None = None, trigger_target: TargetRef | None = None) -> None:\n"
        "        if owner_index is None:\n"
        "            owner_index = self.owner_of_card(source.instance_id)\n"
        "        side = source.current_side if isinstance(source, UnitInstance) else \"none\"\n"
        "        self.trigger_queue.push(\n"
        "            TriggerEvent(\n"
        "                trigger=trigger,\n"
        "                source_id=source.instance_id,\n"
        "                card_id=source.card_id,\n"
        "                side=side,\n"
        "                owner_index=owner_index,\n"
        "                trigger_target=trigger_target,\n"
        "            )\n"
        "        )\n",
        "_queue_trigger",
    )

    text = replace_once(
        text,
        "                if self.effect_queue:\n"
        "                    queued = self.effect_queue.pop(0)\n",
        "                if self.trigger_queue:\n"
        "                    event = self.trigger_queue.pop()\n"
        "                    self.telemetry.record(\n"
        "                        \"trigger\",\n"
        "                        turn=self.turn_number,\n"
        "                        active_player=self.active_player_index,\n"
        "                        player_index=event.owner_index,\n"
        "                        card_id=event.card_id,\n"
        "                        source_id=event.source_id,\n"
        "                        target=event.trigger_target,\n"
        "                        metadata={\"trigger\": event.trigger, \"side\": event.side},\n"
        "                    )\n"
        "                    for effect in self.data.effects_for(event.card_id, event.trigger, event.side):\n"
        "                        self.effect_queue.append(\n"
        "                            QueuedEffect(\n"
        "                                effect,\n"
        "                                event.source_id,\n"
        "                                event.owner_index,\n"
        "                                event.trigger_target,\n"
        "                            )\n"
        "                        )\n"
        "                    continue\n"
        "                if self.effect_queue:\n"
        "                    queued = self.effect_queue.pop(0)\n",
        "process_effect_queue trigger drain",
    )

    # Basic M2 telemetry hooks.
    text = replace_once(
        text,
        "        self.log(f\"{player.name} 打出 {played.card_id} {played.name}，消耗 {played.cost} 魔力。\")\n",
        "        self.log(f\"{player.name} 打出 {played.card_id} {played.name}，消耗 {played.cost} 魔力。\")\n"
        "        self.telemetry.record(\n"
        "            \"card_played\", turn=self.turn_number, active_player=self.active_player_index,\n"
        "            player_index=self.active_player_index, card_id=played.card_id, source_id=played.instance_id,\n"
        "            metadata={\"card_type\": played.card_type, \"cost\": played.cost},\n"
        "        )\n",
        "card_played telemetry",
    )

    text = replace_once(
        text,
        "        self.log(f\"{self.active_player.name} 宣告 {attacker.card_id} {attacker.name} 攻擊 {target_name}。\")\n",
        "        self.log(f\"{self.active_player.name} 宣告 {attacker.card_id} {attacker.name} 攻擊 {target_name}。\")\n"
        "        self.telemetry.record(\n"
        "            \"attack_declared\", turn=self.turn_number, active_player=self.active_player_index,\n"
        "            player_index=self.active_player_index, card_id=attacker.card_id,\n"
        "            source_id=attacker.instance_id, target=defender,\n"
        "        )\n",
        "attack telemetry",
    )

    text = replace_once(
        text,
        "        self.log(f\"{player.name} 使用 Response {card.card_id} {card.name}。\")\n",
        "        self.log(f\"{player.name} 使用 Response {card.card_id} {card.name}。\")\n"
        "        self.telemetry.record(\n"
        "            \"response_played\", turn=self.turn_number, active_player=self.active_player_index,\n"
        "            player_index=defending_index, card_id=card.card_id, source_id=card.instance_id,\n"
        "            target=combat.defender,\n"
        "        )\n",
        "response telemetry",
    )

    text = replace_once(
        text,
        "            self.log(f\"{attacker.card_id} 對 {self.players[defender.player_index].leader.name} 造成 {amount} 點戰鬥傷害。\")\n",
        "            self.log(f\"{attacker.card_id} 對 {self.players[defender.player_index].leader.name} 造成 {amount} 點戰鬥傷害。\")\n"
        "            self.telemetry.record(\n"
        "                \"combat_damage_leader\", turn=self.turn_number, active_player=self.active_player_index,\n"
        "                player_index=combat.attacker_player_index, card_id=attacker.card_id,\n"
        "                source_id=attacker.instance_id, target=defender, amount=amount,\n"
        "            )\n",
        "combat leader damage telemetry",
    )

    text = replace_once(
        text,
        "            self.log(detail)\n",
        "            self.log(detail)\n"
        "            self.telemetry.record(\n"
        "                \"combat_damage_unit\", turn=self.turn_number, active_player=self.active_player_index,\n"
        "                player_index=combat.attacker_player_index, card_id=attacker.card_id,\n"
        "                source_id=attacker.instance_id, target=defender, amount=dealt_to_target,\n"
        "                metadata={\"counter_damage\": dealt_to_attacker},\n"
        "            )\n",
        "combat unit damage telemetry",
    )

    text = replace_once(
        text,
        "        self.log(f\"{unit.card_id} {unit.name} 達成翻面條件，翻至反面。\")\n",
        "        self.log(f\"{unit.card_id} {unit.name} 達成翻面條件，翻至反面。\")\n"
        "        self.telemetry.record(\n"
        "            \"transform\", turn=self.turn_number, active_player=self.active_player_index,\n"
        "            player_index=owner_index, card_id=unit.card_id, source_id=unit.instance_id,\n"
        "        )\n",
        "transform telemetry",
    )

    text = replace_once(
        text,
        "                self.log(f\"{effect.effect_id}: {self.describe_target(ref)} 回復 {healed} 點生命。\")\n",
        "                self.log(f\"{effect.effect_id}: {self.describe_target(ref)} 回復 {healed} 點生命。\")\n"
        "                if healed > 0:\n"
        "                    self.telemetry.record(\n"
        "                        \"heal\", turn=self.turn_number, active_player=self.active_player_index,\n"
        "                        player_index=queued.source_player_index, card_id=getattr(source, \"card_id\", \"\"),\n"
        "                        source_id=queued.source_id, target=ref, amount=healed,\n"
        "                        metadata={\"effect_id\": effect.effect_id},\n"
        "                    )\n",
        "effect heal telemetry",
    )

    text = replace_once(
        text,
        "                self.log(f\"{effect.effect_id}: 對 {self.describe_target(ref)} 造成 {dealt} 點傷害。\")\n",
        "                self.log(f\"{effect.effect_id}: 對 {self.describe_target(ref)} 造成 {dealt} 點傷害。\")\n"
        "                self.telemetry.record(\n"
        "                    \"effect_damage\", turn=self.turn_number, active_player=self.active_player_index,\n"
        "                    player_index=queued.source_player_index, card_id=getattr(source, \"card_id\", \"\"),\n"
        "                    source_id=queued.source_id, target=ref, amount=dealt,\n"
        "                    metadata={\"effect_id\": effect.effect_id},\n"
        "                )\n",
        "effect damage telemetry",
    )

    text = replace_once(
        text,
        "                self.log(f\"{unit.card_id} {unit.name} 生命值歸零，離開戰場。\")\n",
        "                self.log(f\"{unit.card_id} {unit.name} 生命值歸零，離開戰場。\")\n"
        "                self.telemetry.record(\n"
        "                    \"unit_died\", turn=self.turn_number, active_player=self.active_player_index,\n"
        "                    player_index=pidx, card_id=unit.card_id, source_id=unit.instance_id,\n"
        "                )\n",
        "death telemetry",
    )

    text = replace_once(
        text,
        "            self.log(f\"遊戲結束：{self.players[self.winner_index].name} 獲勝。\")\n",
        "            self.log(f\"遊戲結束：{self.players[self.winner_index].name} 獲勝。\")\n"
        "            self.telemetry.record(\n"
        "                \"game_end\", turn=self.turn_number, active_player=self.active_player_index,\n"
        "                player_index=self.winner_index,\n"
        "                metadata={\"winner_index\": self.winner_index},\n"
        "            )\n",
        "game end telemetry",
    )

    GAME.write_text(text, encoding="utf-8")
    print("Applied M1 + M2 patch to src/core/game.py")


if __name__ == "__main__":
    main()
