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
    current_durability: int | None = None

    def __post_init__(self) -> None:
        if self.card_type == "artifact" and self.current_durability is None:
            self.current_durability = max(0, self.definition.durability)

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
    health: int | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.health is None:
            self.health = self.max_health

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
        return max(0, min(self.health or 0, self.max_health))

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
        return self.entered_turn < current_turn or self.has_keyword("迅擊")

    def clamp_health(self) -> None:
        if self.health is None:
            self.health = self.max_health
        self.health = max(0, min(self.health, self.max_health))

    def heal(self, amount: int) -> int:
        self.clamp_health()
        before = self.current_health
        self.health = min(self.max_health, self.current_health + max(0, amount))
        return self.current_health - before

    def take_damage(self, amount: int) -> int:
        self.clamp_health()
        dealt = min(self.current_health, max(0, amount))
        self.health = max(0, self.current_health - dealt)
        self.total_damage_taken += dealt
        return dealt

    def increase_max_health(self, amount: int) -> int:
        """Change permanent max health.

        New game rule: when max health increases by X, current health also
        increases by X. A decrease never heals and current health is clamped
        to the new maximum.
        """
        before_health = self.current_health
        self.permanent_health_bonus += amount
        if amount > 0:
            self.health = before_health + amount
        self.clamp_health()
        return self.current_health - before_health

    def add_timed_max_health(self, amount: int, duration: str, source_player_index: int) -> int:
        """Add a temporary max-health modifier and heal by the positive increase."""
        before_health = self.current_health
        self.timed_modifiers.append(
            TimedModifier("max_health", amount, duration=duration, source_player_index=source_player_index)
        )
        if amount > 0:
            self.health = before_health + amount
        self.clamp_health()
        return self.current_health - before_health
