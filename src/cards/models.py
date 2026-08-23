from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class CardDefinition:
    card_id: str
    name: str
    card_type: str
    cost: int
    faction_id: str
    effect_text: str = ""
    rarity: str = ""
    transform_condition_type: str = ""
    transform_condition_target: str = ""
    transform_condition_value: int = 0
    transform_condition_text: str = ""
    durability: int = 0


@dataclass(frozen=True)
class UnitSideDefinition:
    card_id: str
    side: str
    attack: int
    max_health: int
    keywords: tuple[str, ...] = ()
    effect_text: str = ""


@dataclass
class TimedModifier:
    kind: str  # attack / max_health / keyword
    value: int = 0
    keyword: str = ""
    duration: str = "instant"
    source_player_index: int = 0


@dataclass
class CardInstance:
    definition: CardDefinition
    instance_id: str = field(default_factory=lambda: uuid4().hex[:10])

    @property
    def card_id(self) -> str:
        return self.definition.card_id

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def card_type(self) -> str:
        return self.definition.card_type

    @property
    def cost(self) -> int:
        return self.definition.cost


@dataclass
class UnitInstance(CardInstance):
    front: UnitSideDefinition | None = None
    back: UnitSideDefinition | None = None
    current_side: str = "front"
    damage: int = 0
    entered_turn: int = 0
    owner_index: int = -1

    # Transform counters.
    attacks_made: int = 0
    kills: int = 0
    total_damage_taken: int = 0
    total_damage_dealt: int = 0
    heal_count: int = 0
    survived_turns: int = 0

    # Runtime state.
    attacks_this_turn: int = 0
    permanent_attack_bonus: int = 0
    permanent_health_bonus: int = 0
    permanent_keywords: set[str] = field(default_factory=set)
    timed_modifiers: list[TimedModifier] = field(default_factory=list)

    @property
    def side_definition(self) -> UnitSideDefinition:
        side = self.front if self.current_side == "front" else self.back
        if side is None:
            raise ValueError(f"{self.card_id} 缺少 {self.current_side} 面資料")
        return side

    @property
    def attack(self) -> int:
        temp = sum(m.value for m in self.timed_modifiers if m.kind == "attack")
        return max(0, self.side_definition.attack + self.permanent_attack_bonus + temp)

    @property
    def max_health(self) -> int:
        temp = sum(m.value for m in self.timed_modifiers if m.kind == "max_health")
        return max(1, self.side_definition.max_health + self.permanent_health_bonus + temp)

    @property
    def current_health(self) -> int:
        return max(0, self.max_health - self.damage)

    @property
    def keywords(self) -> tuple[str, ...]:
        values = set(self.side_definition.keywords) | self.permanent_keywords
        values.update(m.keyword for m in self.timed_modifiers if m.kind == "keyword" and m.keyword)
        return tuple(sorted(values))

    @property
    def is_transformed(self) -> bool:
        return self.current_side == "back"

    def has_keyword(self, keyword: str) -> bool:
        return keyword in self.keywords

    def can_attack(self, current_turn: int) -> bool:
        if self.attacks_this_turn >= 1:
            return False
        # Repo rule: newly entered units cannot attack unless a card effect permits it.
        # Current data uses 迅擊 as that permission in the prototype.
        return self.entered_turn < current_turn or self.has_keyword("迅擊")

    def heal(self, amount: int) -> int:
        before = self.current_health
        self.damage = max(0, self.damage - max(0, amount))
        return self.current_health - before

    def take_damage(self, amount: int) -> int:
        dealt = max(0, amount)
        self.damage += dealt
        self.total_damage_taken += dealt
        return dealt
