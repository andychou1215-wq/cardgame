from __future__ import annotations

import random
from dataclasses import dataclass, field

from src.cards.models import CardInstance, UnitInstance
from src.deck.loader import GameData, LeaderDefinition


STARTING_HAND = 5
MAX_MANA = 10
# Prototype-only assumption. Change once the battlefield slot rule is finalized.
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


class Game:
    def __init__(self, data: GameData, deck1_id: str, deck2_id: str, seed: int | None = None):
        self.data = data
        self.rng = random.Random(seed)
        self.turn_number = 1
        self.active_player_index = 0
        self.log_entries: list[str] = []
        self.players = [
            self._make_player("Player 1", deck1_id),
            self._make_player("Player 2", deck2_id),
        ]
        self._start_game()

    def _make_player(self, name: str, deck_id: str) -> PlayerState:
        deck = self.data.build_deck(deck_id)
        self.rng.shuffle(deck)
        return PlayerState(name=name, deck_id=deck_id, leader=self.data.leader_for_deck(deck_id), deck=deck)

    @property
    def active_player(self) -> PlayerState:
        return self.players[self.active_player_index]

    @property
    def inactive_player(self) -> PlayerState:
        return self.players[1 - self.active_player_index]

    def _start_game(self) -> None:
        for player in self.players:
            player.draw(STARTING_HAND)
        self._start_turn(initial=True)
        self.log("遊戲開始。雙方各抽 5 張起手牌。")

    def _start_turn(self, initial: bool = False) -> None:
        player = self.active_player
        player.max_mana = min(MAX_MANA, player.max_mana + 1)
        player.mana = player.max_mana
        if not initial:
            drawn = player.draw(1)
            self.log(f"{player.name} 回合開始，回復至 {player.mana}/{player.max_mana} 魔力並抽 {drawn} 張牌。")
        else:
            self.log(f"{player.name} 先手，魔力 {player.mana}/{player.max_mana}。")

    def play_card(self, hand_index: int) -> tuple[bool, str]:
        player = self.active_player
        if hand_index < 0 or hand_index >= len(player.hand):
            return False, "無效的手牌索引。"
        card = player.hand[hand_index]
        if card.cost > player.mana:
            return False, f"魔力不足：需要 {card.cost}，目前只有 {player.mana}。"

        if card.card_type != "unit":
            return False, f"MVP 目前只支援 Unit 出牌；{card.card_type} 會在效果引擎階段加入。"
        if len(player.battlefield) >= BATTLEFIELD_LIMIT:
            return False, f"戰場已滿（Prototype 暫定 {BATTLEFIELD_LIMIT} 格）。"

        player.mana -= card.cost
        played = player.hand.pop(hand_index)
        assert isinstance(played, UnitInstance)
        played.entered_turn = self.turn_number
        player.battlefield.append(played)
        self.log(f"{player.name} 打出 {played.card_id} {played.name}，消耗 {played.cost} 魔力。")
        return True, "出牌成功。"

    def end_turn(self) -> None:
        ending = self.active_player
        self.log(f"{ending.name} 結束回合。")
        self.active_player_index = 1 - self.active_player_index
        if self.active_player_index == 0:
            self.turn_number += 1
        self._start_turn()

    def log(self, message: str) -> None:
        self.log_entries.append(message)
        self.log_entries = self.log_entries[-200:]
