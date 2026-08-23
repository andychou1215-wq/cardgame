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


@dataclass(frozen=True)
class UnitSideDefinition:
    card_id: str
    side: str
    attack: int
    max_health: int
    keywords: tuple[str, ...] = ()
    effect_text: str = ""


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
    attacks_made: int = 0

    @property
    def side_definition(self) -> UnitSideDefinition:
        side = self.front if self.current_side == "front" else self.back
        if side is None:
            raise ValueError(f"{self.card_id} 缺少 {self.current_side} 面資料")
        return side

    @property
    def attack(self) -> int:
        return self.side_definition.attack

    @property
    def max_health(self) -> int:
        return self.side_definition.max_health

    @property
    def current_health(self) -> int:
        return max(0, self.max_health - self.damage)

    @property
    def keywords(self) -> tuple[str, ...]:
        return self.side_definition.keywords
