from __future__ import annotations

import random
from dataclasses import dataclass, field

from src.cards.models import CardInstance, TimedModifier, UnitInstance
from src.deck.loader import GameData, LeaderDefinition
from src.effects.models import EffectDefinition, TargetRef
from src.core.events import TriggerEvent, TriggerQueue
from src.core.state_based import StateBasedCheck
from src.core.priority import PriorityWindow
from src.playtest.telemetry import PlaytestRecorder


STARTING_HAND = 5
MAX_MANA = 10
BATTLEFIELD_LIMIT = 5


@dataclass
class PlayerState:
    name: str
    deck_id: str
    leader: LeaderDefinition
    deck: list[CardInstance]
    leader_health: int = 20
    hand: list[CardInstance] = field(default_factory=list)
    battlefield: list[UnitInstance] = field(default_factory=list)
    artifacts: list[CardInstance] = field(default_factory=list)
    graveyard: list[CardInstance] = field(default_factory=list)
    max_mana: int = 0
    mana: int = 0

    def __post_init__(self) -> None:
        self.leader_health = self.leader.max_health

    def draw(self, count: int = 1) -> int:
        drawn = 0
        for _ in range(count):
            if not self.deck:
                break
            self.hand.append(self.deck.pop())
            drawn += 1
        return drawn


@dataclass
class QueuedEffect:
    effect: EffectDefinition
    source_id: str
    source_player_index: int
    trigger_target: TargetRef | None = None


@dataclass
class PendingChoice:
    queued: QueuedEffect
    candidates: list[TargetRef]
    prompt: str


@dataclass
class PendingCombat:
    attacker_id: str
    defender: TargetRef
    attacker_player_index: int
    response_used: bool = False


class Game:
    def __init__(self, data: GameData, deck1_id: str, deck2_id: str, seed: int | None = None):
        self.data = data
        self.rng = random.Random(seed)
        self.turn_number = 1
        self.active_player_index = 0
        self.log_entries: list[str] = []
        self.effect_queue: list[QueuedEffect] = []
        self.trigger_queue = TriggerQueue()
        self.state_based = StateBasedCheck()
        self.telemetry = PlaytestRecorder(seed=seed)
        self.pending_choice: PendingChoice | None = None
        self.pending_combat: PendingCombat | None = None
        self.priority_window: PriorityWindow | None = None
        self.first_player_index: int | None = None
        self.usage_counts: dict[tuple[str, str, int, int], int] = {}
        self.winner_index: int | None = None
        self._processing_effects = False
        self.mulligan_done = [False, False]
        self.mulligan_player_index = 0
        self.game_started = False
        self.players = [
            self._make_player("Player 1", deck1_id, 0),
            self._make_player("Player 2", deck2_id, 1),
        ]
        self._start_game()

    def _make_player(self, name: str, deck_id: str, player_index: int) -> PlayerState:
        deck = self.data.build_deck(deck_id)
        for card in deck:
            if isinstance(card, UnitInstance):
                card.owner_index = player_index
        self.rng.shuffle(deck)
        return PlayerState(name=name, deck_id=deck_id, leader=self.data.leader_for_deck(deck_id), deck=deck)

    @property
    def active_player(self) -> PlayerState:
        return self.players[self.active_player_index]

    @property
    def inactive_player(self) -> PlayerState:
        return self.players[1 - self.active_player_index]

    @property
    def is_blocked(self) -> bool:
        return (not self.game_started) or self.pending_choice is not None or self.pending_combat is not None or self.winner_index is not None

    def _start_game(self) -> None:
        for player in self.players:
            player.draw(STARTING_HAND)
        self.log("雙方各抽 5 張起手牌，進入 Mulligan 階段。")

    def mulligan_hand(self, selected_instance_ids: list[str]) -> tuple[bool, str]:
        if self.game_started:
            return False, "Mulligan 階段已結束。"
        pidx = self.mulligan_player_index
        if self.mulligan_done[pidx]:
            return False, "此玩家已完成 Mulligan。"
        player = self.players[pidx]
        selected = set(selected_instance_ids)
        invalid = selected - {c.instance_id for c in player.hand}
        if invalid:
            return False, "Mulligan 選擇包含不在起手牌中的卡。"

        returned = [c for c in player.hand if c.instance_id in selected]
        player.hand = [c for c in player.hand if c.instance_id not in selected]
        player.deck.extend(returned)
        self.rng.shuffle(player.deck)
        drawn = player.draw(len(returned))
        self.mulligan_done[pidx] = True
        self.log(f"{player.name} 完成 Mulligan：更換 {len(returned)} 張，抽回 {drawn} 張。")

        if all(self.mulligan_done):
            self.active_player_index = self.rng.randrange(2)
            self.first_player_index = self.active_player_index
            self.game_started = True
            self._start_turn(initial=True)
            self.log(f"Mulligan 完成；隨機決定 {self.active_player.name} 為先手。")
            return True, "雙方 Mulligan 完成，對局正式開始。"

        self.mulligan_player_index = 1 - pidx
        return True, f"{player.name} Mulligan 完成，請交給下一位玩家。"

    def _start_turn(self, initial: bool = False) -> None:
        player = self.active_player
        for unit in player.battlefield:
            unit.attacks_this_turn = 0
            if unit.entered_turn < self.turn_number:
                unit.survived_turns += 1
        player.max_mana = min(MAX_MANA, player.max_mana + 1)
        player.mana = player.max_mana
        if not initial:
            drawn = player.draw(1)
            self.log(f"{player.name} 回合開始，回復至 {player.mana}/{player.max_mana} 魔力並抽 {drawn} 張牌。")
        else:
            self.log(f"{player.name} 先手，魔力 {player.mana}/{player.max_mana}。")
        self.check_transforms()

    # ---------- Card play ----------
    def legal_play_targets(self, hand_index: int) -> list[TargetRef]:
        player = self.active_player
        if hand_index < 0 or hand_index >= len(player.hand):
            return []
        card = player.hand[hand_index]
        effects = self.data.effects_for(card.card_id, "on_play", "none")
        for effect in effects:
            if effect.target_required:
                return self._candidate_targets(effect, card.instance_id, self.active_player_index, None)
        return []

    def play_card(self, hand_index: int, target: TargetRef | None = None) -> tuple[bool, str]:
        if not self.game_started:
            return False, "請先完成雙方 Mulligan。"
        if self.pending_choice or self.pending_combat:
            return False, "請先完成目前等待中的效果或戰鬥結算。"
        player = self.active_player
        if hand_index < 0 or hand_index >= len(player.hand):
            return False, "無效的手牌索引。"
        card = player.hand[hand_index]
        if card.cost > player.mana:
            return False, f"魔力不足：需要 {card.cost}，目前只有 {player.mana}。"
        if card.card_type == "response":
            return False, "Response 只能在對應的 Response Window 使用。"

        if card.card_type == "unit" and len(player.battlefield) >= BATTLEFIELD_LIMIT:
            return False, f"戰場已滿（Prototype 暫定 {BATTLEFIELD_LIMIT} 格）。"

        on_play = self.data.effects_for(card.card_id, "on_play", "none")
        for effect in on_play:
            if effect.target_required:
                candidates = self._candidate_targets(effect, card.instance_id, self.active_player_index, None)
                if not candidates:
                    return False, "沒有合法目標，無法打出此卡。"
                if target is None:
                    return False, "此卡需要先選擇合法目標。"
                if target.key not in {c.key for c in candidates}:
                    return False, "選擇的目標不合法。"
                break

        player.mana -= card.cost
        played = player.hand.pop(hand_index)
        self.log(f"{player.name} 打出 {played.card_id} {played.name}，消耗 {played.cost} 魔力。")
        self.telemetry.record("card_played", turn=self.turn_number, active_player=self.active_player_index, player_index=self.active_player_index, card_id=played.card_id, source_id=played.instance_id)

        if played.card_type == "unit":
            assert isinstance(played, UnitInstance)
            played.entered_turn = self.turn_number
            played.owner_index = self.active_player_index
            player.battlefield.append(played)
            self.enqueue_trigger(played, "on_enter")
            self.check_transforms()
        elif played.card_type == "artifact":
            player.artifacts.append(played)
        elif played.card_type == "spell":
            self._enqueue_card_effects(played, "on_play", selected_target=target)
            player.graveyard.append(played)
        else:
            # Generic non-unit played card; execute on_play then move to graveyard.
            self._enqueue_card_effects(played, "on_play", selected_target=target)
            player.graveyard.append(played)

        if played.card_type != "spell" and on_play:
            self._enqueue_card_effects(played, "on_play", selected_target=target)
        self.process_effect_queue()
        return True, "出牌成功。"

    # ---------- Activated abilities ----------
    def activated_options(self) -> list[tuple[CardInstance, EffectDefinition]]:
        result: list[tuple[CardInstance, EffectDefinition]] = []
        p = self.active_player
        for card in [*p.battlefield, *p.artifacts]:
            side = card.current_side if isinstance(card, UnitInstance) else "none"
            for effect in self.data.activated_effects_for(card.card_id, side):
                if self.can_activate(card, effect):
                    result.append((card, effect))
        return result

    def can_activate(self, card: CardInstance, effect: EffectDefinition) -> bool:
        if self.active_player.mana < effect.mana_cost:
            return False
        if effect.usage_limit_type == "per_turn" and effect.usage_limit_count:
            key = (card.instance_id, effect.effect_id, self.turn_number, self.active_player_index)
            if self.usage_counts.get(key, 0) >= effect.usage_limit_count:
                return False
        if effect.target_required and not self._candidate_targets(effect, card.instance_id, self.active_player_index, None):
            return False
        return True

    def legal_activation_targets(self, card: CardInstance, effect: EffectDefinition) -> list[TargetRef]:
        return self._candidate_targets(effect, card.instance_id, self.active_player_index, None)

    def activate(self, source_id: str, effect_id: str, target: TargetRef | None = None) -> tuple[bool, str]:
        if not self.game_started:
            return False, "請先完成雙方 Mulligan。"
        if self.pending_choice or self.pending_combat:
            return False, "請先完成目前等待中的效果或戰鬥結算。"
        source = self.find_card_in_play(source_id)
        effect = self.data.effects.get(effect_id)
        if source is None or effect is None:
            return False, "找不到能力來源或效果。"
        if source not in [*self.active_player.battlefield, *self.active_player.artifacts]:
            return False, "只能啟動目前玩家控制的卡牌能力。"
        if not self.can_activate(source, effect):
            return False, "目前無法啟動此能力。"
        candidates = self._candidate_targets(effect, source_id, self.active_player_index, None)
        if effect.target_required:
            if target is None or target.key not in {c.key for c in candidates}:
                return False, "請選擇合法目標。"

        self.active_player.mana -= effect.mana_cost
        if effect.usage_limit_type == "per_turn":
            key = (source.instance_id, effect.effect_id, self.turn_number, self.active_player_index)
            self.usage_counts[key] = self.usage_counts.get(key, 0) + 1
        self.log(f"{self.active_player.name} 啟動 {source.card_id} 的 {effect.effect_id}。")
        self._resolve_effect(QueuedEffect(effect, source.instance_id, self.active_player_index), target)
        self.process_effect_queue()
        return True, "能力已結算。"

    # ---------- Combat ----------
    def legal_attackers(self) -> list[UnitInstance]:
        if not self.game_started:
            return []
        return [u for u in self.active_player.battlefield if u.can_attack(self.turn_number)]

    def legal_attack_targets(self) -> list[TargetRef]:
        """Return legal targets for an enemy Unit attack.

        Repo keyword rules:
        - 〖迴避〗 units cannot be attacked by enemy Unit cards.
        - If one or more attackable 〖庇護〗 units exist, only those units may be attacked.
        - 〖庇護〗 and 〖迴避〗 are mutually exclusive by card/effect design.
        """
        if not self.game_started:
            return []
        opponent_index = 1 - self.active_player_index
        opponent_units = list(self.inactive_player.battlefield)

        attackable_units = [u for u in opponent_units if not u.has_keyword("迴避")]
        sheltered = [u for u in attackable_units if u.has_keyword("庇護")]

        if sheltered:
            return [TargetRef("unit", opponent_index, u.instance_id) for u in sheltered]

        targets = [TargetRef("unit", opponent_index, u.instance_id) for u in attackable_units]
        targets.append(TargetRef("leader", opponent_index))
        return targets

    def declare_attack(self, attacker_id: str, defender: TargetRef) -> tuple[bool, str]:
        if self.pending_choice or self.pending_combat:
            return False, "目前已有等待中的結算。"
        attacker = self.find_unit(attacker_id)
        if attacker is None or attacker not in self.active_player.battlefield:
            return False, "找不到攻擊者。"
        if not attacker.can_attack(self.turn_number):
            return False, "此單位本回合不能攻擊。"
        if defender.key not in {t.key for t in self.legal_attack_targets()}:
            return False, "攻擊目標不合法。"
        self.pending_combat = PendingCombat(attacker_id, defender, self.active_player_index)
        defending_index = 1 - self.active_player_index
        self.priority_window = PriorityWindow(
            first_player_index=defending_index,
            reason="attack_declared",
            trigger_target=defender,
        )
        target_name = self.describe_target(defender)
        self.log(f"{self.active_player.name} 宣告 {attacker.card_id} {attacker.name} 攻擊 {target_name}。")
        self.telemetry.record("attack_declared", turn=self.turn_number, active_player=self.active_player_index, player_index=self.active_player_index, card_id=attacker.card_id, source_id=attacker.instance_id, target=defender)
        return True, "已進入 Response Window。"

    def available_responses(self, player_index: int | None = None) -> list[tuple[int, CardInstance, EffectDefinition]]:
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

    def _combat_damage_to_unit(self, target: UnitInstance, raw_amount: int) -> tuple[int, int]:
        """Return (actual damage, blocked damage). 〖格檔〗 only reduces combat damage by 1."""
        blocked = 1 if target.has_keyword("格檔") and raw_amount > 0 else 0
        actual = target.take_damage(max(0, raw_amount - blocked))
        return actual, blocked

    def _apply_lifesteal(self, attacker: UnitInstance, damage_dealt: int) -> int:
        """Repo rule: 〖吸血〗 heals the attacking unit for damage dealt by its active attack."""
        if damage_dealt <= 0 or not attacker.has_keyword("吸血"):
            return 0
        healed = attacker.heal(damage_dealt)
        if healed > 0:
            self.log(f"〖吸血〗：{attacker.card_id} {attacker.name} 回復 {healed} 點生命。")
        else:
            self.log(f"〖吸血〗：{attacker.card_id} {attacker.name} 已滿生命，未回復生命。")
        return healed

    def _priority_can_auto_pass(self) -> bool:
        window = self.priority_window
        if self.pending_combat is None or window is None or not window.is_open:
            return False

        original = window.current_player_index
        try:
            for player_index in (0, 1):
                window.current_player_index = player_index
                if self.available_responses(player_index):
                    return False
            return True
        finally:
            window.current_player_index = original

    def _auto_pass_empty_priority_window(self) -> None:
        window = self.priority_window
        if window is None or not window.is_open:
            return

        first = window.current_player_index
        closed = window.pass_priority(first)
        if not closed:
            second = window.current_player_index
            window.pass_priority(second)
        else:
            second = 1 - first

        if hasattr(self, "telemetry"):
            self.telemetry.record(
                "priority_auto_pass",
                turn=self.turn_number,
                active_player=self.active_player_index,
                metadata={"reason": "no_legal_responses", "first_player": first, "second_player": second},
            )

        self.log("雙方皆無合法 Response；自動視為連續 Pass。")

    def resolve_combat(self) -> tuple[bool, str]:
        combat = self.pending_combat
        if self.priority_window is not None and self.priority_window.is_open:
            if self._priority_can_auto_pass():
                self._auto_pass_empty_priority_window()
            else:
                return False, "Priority Window 尚未關閉；需要雙方連續 Pass。"
        if combat is None:
            return False, "沒有等待中的戰鬥。"
        attacker = self.find_unit(combat.attacker_id)
        if attacker is None:
            self.pending_combat = None
            self.priority_window = None
            return False, "攻擊者已離場，戰鬥取消。"
        defender = combat.defender
        attacker.attacks_this_turn += 1
        attacker.attacks_made += 1

        if defender.kind == "leader":
            amount = min(attacker.attack, self.players[defender.player_index].leader_health)
            self.players[defender.player_index].leader_health -= amount
            attacker.total_damage_dealt += amount
            self.log(f"{attacker.card_id} 對 {self.players[defender.player_index].leader.name} 造成 {amount} 點戰鬥傷害。")
            self._apply_lifesteal(attacker, amount)
        else:
            target = self.find_unit(defender.instance_id)
            if target is None:
                self.pending_combat = None
                self.priority_window = None
                return False, "防守單位已離場，戰鬥取消。"

            # Snapshot combat stats before simultaneous damage.
            attacker_raw = attacker.attack
            defender_raw = target.attack
            dealt_to_target, blocked_by_target = self._combat_damage_to_unit(target, attacker_raw)
            dealt_to_attacker, blocked_by_attacker = self._combat_damage_to_unit(attacker, defender_raw)
            attacker.total_damage_dealt += dealt_to_target
            target.total_damage_dealt += dealt_to_attacker

            detail = f"{attacker.card_id} ↔ {target.card_id}：造成 {dealt_to_target} / {dealt_to_attacker} 點戰鬥傷害。"
            self.log(detail)
            if blocked_by_target:
                self.log(f"〖格檔〗：{target.card_id} 減少 {blocked_by_target} 點戰鬥傷害。")
            if blocked_by_attacker:
                self.log(f"〖格檔〗：{attacker.card_id} 減少 {blocked_by_attacker} 點反擊傷害。")

            # 〖吸血〗 only belongs to the unit making the active attack; counterattack does not trigger it.
            self._apply_lifesteal(attacker, dealt_to_target)

            if target.current_health <= 0:
                attacker.kills += 1
            if attacker.current_health <= 0:
                target.kills += 1

        # Central state-based checkpoint handles simultaneous deaths before later trigger chains.
        self._run_state_based_check()
        self._expire_modifiers("until_attack_end")
        self.pending_combat = None
        self.priority_window = None
        self.process_effect_queue()
        self._check_winner()
        return True, "戰鬥結算完成。"

    # ---------- Transform ----------
    def check_transforms(self) -> bool:
        changed = False
        # Active player first, then non-active player, matching trigger ordering.
        order = [self.active_player_index, 1 - self.active_player_index]
        for pidx in order:
            player = self.players[pidx]
            for unit in list(player.battlefield):
                if unit.current_side != "front" or unit.back is None:
                    continue
                if self._transform_condition_met(unit, pidx):
                    self._transform(unit, pidx)
                    changed = True
        if changed and not self._processing_effects:
            self.process_effect_queue()
        return changed

    def _transform_condition_met(self, unit: UnitInstance, owner_index: int) -> bool:
        d = unit.definition
        t = d.transform_condition_type
        value = d.transform_condition_value
        if not t:
            return False
        if t == "attack_count":
            return unit.attacks_made >= value
        if t == "kill_count":
            return unit.kills >= value
        if t == "total_damage_taken":
            return unit.total_damage_taken >= value
        if t == "turn_count":
            return unit.survived_turns >= value
        if t == "total_damage_dealt":
            return unit.total_damage_dealt >= value
        if t == "heal_count":
            return unit.heal_count >= value
        if t == "unit_count_at_least":
            return len(self.players[owner_index].battlefield) >= value
        if t == "leader_health_at_or_below":
            return self.players[owner_index].leader_health <= value
        return False

    def _transform(self, unit: UnitInstance, owner_index: int) -> None:
        before_max = unit.max_health
        before_health = unit.current_health
        unit.current_side = "back"
        after_max = unit.max_health
        max_increase = max(0, after_max - before_max)
        if max_increase > 0:
            unit.health = before_health + max_increase
        unit.clamp_health()
        self.log(f"{unit.card_id} {unit.name} 達成翻面條件，翻至反面。")
        self.telemetry.record("transform", turn=self.turn_number, active_player=self.active_player_index, player_index=owner_index, card_id=unit.card_id, source_id=unit.instance_id)
        if max_increase > 0:
            self.log(
                f"{unit.card_id} 翻面使最大生命值增加 {max_increase}，"
                f"同步回復 {unit.current_health - before_health} 點現有生命。"
            )
        self._queue_trigger(unit, "on_flip", owner_index=owner_index)

    # ---------- Effects ----------
    def _queue_trigger(self, source: CardInstance, trigger: str, owner_index: int | None = None, trigger_target: TargetRef | None = None) -> None:
        if owner_index is None:
            owner_index = self.owner_of_card(source.instance_id)
        side = source.current_side if isinstance(source, UnitInstance) else "none"
        self.trigger_queue.push(
            TriggerEvent(
                trigger=trigger,
                source_id=source.instance_id,
                card_id=source.card_id,
                side=side,
                owner_index=owner_index,
                trigger_target=trigger_target,
            )
        )

    def enqueue_trigger(self, source: CardInstance, trigger: str, owner_index: int | None = None, trigger_target: TargetRef | None = None) -> None:
        self._queue_trigger(source, trigger, owner_index, trigger_target)
        if not self._processing_effects:
            self.process_effect_queue()

    def _enqueue_card_effects(self, card: CardInstance, trigger: str, selected_target: TargetRef | None = None) -> None:
        owner = self.active_player_index
        effects = self.data.effects_for(card.card_id, trigger, "none")
        for effect in effects:
            q = QueuedEffect(effect, card.instance_id, owner)
            if selected_target is not None and effect.target_required:
                self._resolve_effect(q, selected_target)
                selected_target = None
            else:
                self.effect_queue.append(q)

    def process_effect_queue(self) -> None:
        if self.pending_choice or self._processing_effects:
            return
        self._processing_effects = True
        try:
            guard = 0
            while guard < 200 and not self.pending_choice:
                guard += 1
                if self.trigger_queue:
                    event = self.trigger_queue.pop()
                    self.telemetry.record(
                        "trigger",
                        turn=self.turn_number,
                        active_player=self.active_player_index,
                        player_index=event.owner_index,
                        card_id=event.card_id,
                        source_id=event.source_id,
                        target=event.trigger_target,
                        metadata={"trigger": event.trigger, "side": event.side},
                    )
                    for effect in self.data.effects_for(event.card_id, event.trigger, event.side):
                        self.effect_queue.append(
                            QueuedEffect(effect, event.source_id, event.owner_index, event.trigger_target)
                        )
                    continue
                if self.effect_queue:
                    queued = self.effect_queue.pop(0)
                    effect = queued.effect
                    candidates = self._candidate_targets(effect, queued.source_id, queued.source_player_index, queued.trigger_target)
                    if effect.target in {"all_ally_units", "all_other_ally_units"}:
                        self._resolve_effect(queued, None)
                        self._run_state_based_check()
                        continue
                    if effect.target_required:
                        if not candidates:
                            self.log(f"{effect.effect_id} 沒有合法目標。")
                            if effect.failure_behavior == "stop":
                                self.effect_queue.clear()
                            continue
                        if len(candidates) == 1:
                            self._resolve_effect(queued, candidates[0])
                            self._run_state_based_check()
                        else:
                            self.pending_choice = PendingChoice(queued, candidates, effect.effect_text or "選擇效果目標")
                            break
                    else:
                        target = candidates[0] if len(candidates) == 1 else None
                        self._resolve_effect(queued, target)
                        self._run_state_based_check()
                    continue

                # No queued work: run one authoritative state-based checkpoint.
                state = self._run_state_based_check()
                if state.changed:
                    continue
                break
            self._check_winner()
        finally:
            self._processing_effects = False

    def _run_state_based_check(self):
        result = self.state_based.run_once(self)
        self.telemetry.record(
            "state_based_check",
            turn=self.turn_number,
            active_player=self.active_player_index,
            metadata={"changed": result.changed, "deaths": result.deaths, "transforms": result.transforms, "winner_changed": result.winner_changed},
        )
        return result

    def resolve_pending_choice(self, target: TargetRef) -> tuple[bool, str]:
        pending = self.pending_choice
        if pending is None:
            return False, "目前沒有等待選擇的效果。"
        if target.key not in {c.key for c in pending.candidates}:
            return False, "選擇的目標不合法。"
        self.pending_choice = None
        self._resolve_effect(pending.queued, target)
        self._run_state_based_check()
        self.process_effect_queue()
        return True, "效果目標已選擇並完成結算。"

    def _resolve_effect(self, queued: QueuedEffect, selected_target: TargetRef | None) -> None:
        effect = queued.effect
        refs = self._targets_for_resolution(effect, queued.source_id, queued.source_player_index, queued.trigger_target, selected_target)
        source = self.find_unit(queued.source_id)
        if not refs and effect.target_required:
            self.log(f"{effect.effect_id} 結算失敗：沒有合法目標。")
            return
        for ref in refs:
            if effect.operation == "draw":
                n = self.players[ref.player_index].draw(effect.value)
                self.log(f"{effect.effect_id}: {self.players[ref.player_index].name} 抽 {n} 張牌。")
            elif effect.operation == "heal":
                if ref.kind == "leader":
                    p = self.players[ref.player_index]
                    before = p.leader_health
                    p.leader_health = min(p.leader.max_health, p.leader_health + effect.value)
                    healed = p.leader_health - before
                else:
                    target = self.find_unit(ref.instance_id)
                    healed = target.heal(effect.value) if target else 0
                if source is not None and healed > 0:
                    source.heal_count += 1
                self.log(f"{effect.effect_id}: {self.describe_target(ref)} 回復 {healed} 點生命。")
            elif effect.operation == "damage":
                if ref.kind == "leader":
                    p = self.players[ref.player_index]
                    p.leader_health = max(0, p.leader_health - effect.value)
                    dealt = effect.value
                else:
                    target = self.find_unit(ref.instance_id)
                    dealt = target.take_damage(effect.value) if target else 0
                if source is not None:
                    source.total_damage_dealt += dealt
                    target_unit = self.find_unit(ref.instance_id) if ref.kind == "unit" else None
                    if target_unit is not None and target_unit.current_health <= 0:
                        source.kills += 1
                self.log(f"{effect.effect_id}: 對 {self.describe_target(ref)} 造成 {dealt} 點傷害。")
            elif effect.operation in {"modify_attack", "modify_max_health"}:
                target = self.find_unit(ref.instance_id)
                if target is None:
                    continue
                kind = "attack" if effect.operation == "modify_attack" else "max_health"
                healed_with_max_hp = 0
                if effect.duration == "permanent":
                    if kind == "attack":
                        target.permanent_attack_bonus += effect.value
                    else:
                        healed_with_max_hp = target.increase_max_health(effect.value)
                else:
                    if kind == "max_health":
                        healed_with_max_hp = target.add_timed_max_health(
                            effect.value, effect.duration, queued.source_player_index
                        )
                    else:
                        target.timed_modifiers.append(TimedModifier(kind, effect.value, duration=effect.duration, source_player_index=queued.source_player_index))
                self.log(f"{effect.effect_id}: {target.card_id} {kind} {effect.value:+d} ({effect.duration})。")
                if kind == "max_health" and effect.value > 0:
                    self.log(
                        f"{effect.effect_id}: 最大生命值增加同步使 {target.card_id} "
                        f"回復 {healed_with_max_hp} 點現有生命。"
                    )
            elif effect.operation == "add_keyword":
                target = self.find_unit(ref.instance_id)
                if target is None:
                    continue
                if effect.parameter in {"庇護", "迴避"}:
                    opposite = "迴避" if effect.parameter == "庇護" else "庇護"
                    if target.has_keyword(opposite):
                        self.log(
                            f"{effect.effect_id}: {target.card_id} 已具有〖{opposite}〗，"
                            f"依規則不能再獲得〖{effect.parameter}〗。"
                        )
                        continue
                if effect.duration == "permanent":
                    target.permanent_keywords.add(effect.parameter)
                else:
                    target.timed_modifiers.append(TimedModifier("keyword", keyword=effect.parameter, duration=effect.duration, source_player_index=queued.source_player_index))
                self.log(f"{effect.effect_id}: {target.card_id} 獲得〖{effect.parameter}〗 ({effect.duration})。")
            else:
                self.log(f"⚠ {effect.effect_id}: 尚未支援 operation={effect.operation}")

    def _targets_for_resolution(self, effect: EffectDefinition, source_id: str, source_player_index: int, trigger_target: TargetRef | None, selected: TargetRef | None) -> list[TargetRef]:
        if selected is not None:
            return [selected]
        if effect.target == "all_ally_units":
            units = list(self.players[source_player_index].battlefield)
            if effect.operation == "add_keyword" and effect.parameter in {"庇護", "迴避"}:
                opposite = "迴避" if effect.parameter == "庇護" else "庇護"
                units = [u for u in units if not u.has_keyword(opposite)]
            return [TargetRef("unit", source_player_index, u.instance_id) for u in units]
        if effect.target == "all_other_ally_units":
            units = [u for u in self.players[source_player_index].battlefield if u.instance_id != source_id]
            if effect.operation == "add_keyword" and effect.parameter in {"庇護", "迴避"}:
                opposite = "迴避" if effect.parameter == "庇護" else "庇護"
                units = [u for u in units if not u.has_keyword(opposite)]
            return [TargetRef("unit", source_player_index, u.instance_id) for u in units]
        candidates = self._candidate_targets(effect, source_id, source_player_index, trigger_target)
        return candidates[:1] if candidates else []

    def _candidate_targets(self, effect: EffectDefinition, source_id: str, source_player_index: int, trigger_target: TargetRef | None) -> list[TargetRef]:
        opponent = 1 - source_player_index
        t = effect.target
        if t == "self":
            unit = self.find_unit(source_id)
            return [TargetRef("unit", source_player_index, source_id)] if unit else []
        if t == "self_player":
            return [TargetRef("player", source_player_index)]
        if t == "self_leader":
            return [TargetRef("leader", source_player_index)]
        if t == "opponent_leader":
            return [TargetRef("leader", opponent)]
        if t == "trigger_target":
            return [trigger_target] if trigger_target else []
        if t in {"ally_unit", "other_ally_unit", "all_ally_units", "all_other_ally_units"}:
            units = list(self.players[source_player_index].battlefield)
        elif t == "opponent_unit":
            units = list(self.players[opponent].battlefield)
        else:
            units = []
        refs = []
        filters = self._parse_filter(effect.target_filter)
        for u in units:
            if t in {"other_ally_unit", "all_other_ally_units"} and u.instance_id == source_id:
                continue
            if filters.get("exclude") == "self" and u.instance_id == source_id:
                continue
            keyword = filters.get("keyword")
            if keyword and not u.has_keyword(keyword):
                continue
            # 〖庇護〗 and 〖迴避〗 are mutually exclusive by keyword rule.
            if effect.operation == "add_keyword":
                if effect.parameter == "庇護" and u.has_keyword("迴避"):
                    continue
                if effect.parameter == "迴避" and u.has_keyword("庇護"):
                    continue

            # Healing a full-health unit is not a legal target; this prevents no-op heals
            # and makes heal_count track successful healing events only.
            if effect.operation == "heal" and u.current_health >= u.max_health:
                continue
            refs.append(TargetRef("unit", u.owner_index, u.instance_id))
        return refs

    @staticmethod
    def _parse_filter(raw: str) -> dict[str, str]:
        result: dict[str, str] = {}
        for part in raw.split(";"):
            if ":" in part:
                key, value = part.split(":", 1)
                result[key.strip()] = value.strip()
        return result

    # ---------- Death / expiration / winner ----------
    def _handle_deaths(self) -> bool:
        """Move all lethal units simultaneously, then queue on_leave in AP/NAP order."""
        deaths: list[tuple[int, UnitInstance]] = []
        order = [self.active_player_index, 1 - self.active_player_index]
        for pidx in order:
            for unit in list(self.players[pidx].battlefield):
                if unit.current_health <= 0:
                    deaths.append((pidx, unit))
        if not deaths:
            return False

        # First move every dead unit out of battlefield so all simultaneous deaths see the same state.
        for pidx, unit in deaths:
            player = self.players[pidx]
            if unit in player.battlefield:
                player.battlefield.remove(unit)
                player.graveyard.append(unit)
                self.log(f"{unit.card_id} {unit.name} 生命值歸零，離開戰場。")

        # Then queue all leave triggers in active-player/non-active-player order.
        for pidx, unit in deaths:
            self._queue_trigger(unit, "on_leave", owner_index=pidx)
        return True

    def _expire_modifiers(self, duration: str, ending_player_index: int | None = None) -> None:
        for pidx, player in enumerate(self.players):
            for unit in player.battlefield:
                kept = []
                for m in unit.timed_modifiers:
                    expire = m.duration == duration
                    if duration == "until_opponent_turn_end" and ending_player_index is not None:
                        expire = m.duration == duration and ending_player_index == 1 - m.source_player_index
                    if not expire:
                        kept.append(m)
                unit.timed_modifiers = kept
                unit.clamp_health()

    def _check_winner(self) -> None:
        dead = [i for i, p in enumerate(self.players) if p.leader_health <= 0]
        if dead:
            self.winner_index = 1 - dead[0]
            self.log(f"遊戲結束：{self.players[self.winner_index].name} 獲勝。")

    def end_turn(self) -> tuple[bool, str]:
        if not self.game_started:
            return False, "請先完成雙方 Mulligan。"
        if self.pending_choice or self.pending_combat:
            return False, "請先完成目前等待中的效果或戰鬥。"
        if self.winner_index is not None:
            return False, "遊戲已結束。"
        ending_index = self.active_player_index
        ending = self.active_player
        self.log(f"{ending.name} 結束回合。")
        self._expire_modifiers("until_turn_end")
        self._expire_modifiers("until_opponent_turn_end", ending_player_index=ending_index)
        self.active_player_index = 1 - self.active_player_index
        if self.active_player_index == 0:
            self.turn_number += 1
        self._start_turn()
        return True, "回合結束。"

    def log(self, message: str) -> None:
        self.log_entries.append(message)
        self.log_entries = self.log_entries[-300:]

    # ---------- Lookup / display ----------
    def find_unit(self, instance_id: str) -> UnitInstance | None:
        for player in self.players:
            for unit in player.battlefield:
                if unit.instance_id == instance_id:
                    return unit
        return None

    def find_card_in_play(self, instance_id: str) -> CardInstance | None:
        for player in self.players:
            for card in [*player.battlefield, *player.artifacts]:
                if card.instance_id == instance_id:
                    return card
        return None

    def owner_of_card(self, instance_id: str) -> int:
        for pidx, player in enumerate(self.players):
            for card in [*player.battlefield, *player.artifacts, *player.hand, *player.graveyard]:
                if card.instance_id == instance_id:
                    return pidx
        return self.active_player_index

    def describe_target(self, ref: TargetRef) -> str:
        if ref.kind == "leader":
            return self.players[ref.player_index].leader.name
        if ref.kind == "player":
            return self.players[ref.player_index].name
        unit = self.find_unit(ref.instance_id)
        return f"{unit.card_id} {unit.name}" if unit else ref.instance_id
