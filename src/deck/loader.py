from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.cards.models import CardDefinition, CardInstance, UnitInstance, UnitSideDefinition


@dataclass(frozen=True)
class DeckDefinition:
    deck_id: str
    name: str
    faction_id: str
    leader_id: str
    deck_type: str = "test"
    description: str = ""


@dataclass(frozen=True)
class LeaderDefinition:
    leader_id: str
    name: str
    faction_id: str
    max_health: int


class DataError(RuntimeError):
    pass


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise DataError(f"找不到資料檔：{path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except csv.Error as exc:
        raise DataError(f"CSV 解析失敗：{path}\n{exc}") from exc
    if not rows:
        raise DataError(f"CSV 沒有資料：{path}")
    return rows


def _int(value: str | None, default: int = 0) -> int:
    try:
        return int(float(value or default))
    except ValueError as exc:
        raise DataError(f"無法轉換成整數：{value!r}") from exc


def _first(row: dict[str, str], *keys: str, default: str = "") -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value.strip()
    return default


class GameData:
    """Loads the current repo CSV schema without coupling the engine to CSV rows."""

    def __init__(self, repo_root: str | Path):
        self.root = Path(repo_root)
        self.cards: dict[str, CardDefinition] = {}
        self.unit_sides: dict[tuple[str, str], UnitSideDefinition] = {}
        self.decks: dict[str, DeckDefinition] = {}
        self.deck_cards: dict[str, list[tuple[str, int]]] = {}
        self.leaders: dict[str, LeaderDefinition] = {}
        self._load_all()

    def _load_all(self) -> None:
        self._load_cards(self.root / "data/cards/cards.csv")
        self._load_unit_sides(self.root / "data/cards/unit_sides.csv")
        self._load_decks(self.root / "data/decks/decks.csv")
        self._load_deck_cards(self.root / "data/decks/deck_cards.csv")
        self._load_leaders(self.root / "data/factions/leader.csv")

    def _load_cards(self, path: Path) -> None:
        for row in _read_csv(path):
            card_id = _first(row, "id", "card_id")
            if not card_id:
                raise DataError(f"{path} 有缺少 id/card_id 的列")
            self.cards[card_id] = CardDefinition(
                card_id=card_id,
                name=_first(row, "name", default=card_id),
                card_type=_first(row, "type", "card_type").lower(),
                cost=_int(row.get("cost")),
                faction_id=_first(row, "faction_id", default="NEUTRAL"),
                effect_text=_first(row, "effect_text"),
                rarity=_first(row, "rarity"),
            )

    def _load_unit_sides(self, path: Path) -> None:
        for row in _read_csv(path):
            card_id = _first(row, "card_id", "id")
            side = _first(row, "side").lower()
            keywords = tuple(k.strip() for k in _first(row, "keywords").replace("|", ";").split(";") if k.strip())
            self.unit_sides[(card_id, side)] = UnitSideDefinition(
                card_id=card_id,
                side=side,
                attack=_int(row.get("attack")),
                max_health=_int(row.get("max_health")),
                keywords=keywords,
                effect_text=_first(row, "effect_text"),
            )

    def _load_decks(self, path: Path) -> None:
        for row in _read_csv(path):
            deck_id = _first(row, "deck_id", "id")
            self.decks[deck_id] = DeckDefinition(
                deck_id=deck_id,
                name=_first(row, "name", default=deck_id),
                faction_id=_first(row, "faction_id"),
                leader_id=_first(row, "leader_id"),
                deck_type=_first(row, "deck_type", default="test"),
                description=_first(row, "description"),
            )

    def _load_deck_cards(self, path: Path) -> None:
        for row in _read_csv(path):
            deck_id = _first(row, "deck_id")
            card_id = _first(row, "card_id")
            quantity = _int(row.get("quantity"), 1)
            self.deck_cards.setdefault(deck_id, []).append((card_id, quantity))

    def _load_leaders(self, path: Path) -> None:
        for row in _read_csv(path):
            leader_id = _first(row, "leader_id", "id")
            if not leader_id:
                continue
            # Different drafts may use hp / health / max_health.
            hp = _int(_first(row, "max_health", "health", "hp", default="20"), 20)
            self.leaders[leader_id] = LeaderDefinition(
                leader_id=leader_id,
                name=_first(row, "name", default=leader_id),
                faction_id=_first(row, "faction_id"),
                max_health=hp or 20,
            )

    def available_decks(self) -> list[DeckDefinition]:
        return list(self.decks.values())

    def build_deck(self, deck_id: str) -> list[CardInstance]:
        if deck_id not in self.deck_cards:
            raise DataError(f"牌組 {deck_id} 在 deck_cards.csv 沒有任何卡")
        result: list[CardInstance] = []
        for card_id, quantity in self.deck_cards[deck_id]:
            definition = self.cards.get(card_id)
            if definition is None:
                raise DataError(f"牌組 {deck_id} 引用了不存在的卡：{card_id}")
            for _ in range(quantity):
                if definition.card_type == "unit":
                    front = self.unit_sides.get((card_id, "front"))
                    back = self.unit_sides.get((card_id, "back"))
                    if front is None:
                        raise DataError(f"Unit {card_id} 缺少 front 資料")
                    result.append(UnitInstance(definition=definition, front=front, back=back))
                else:
                    result.append(CardInstance(definition=definition))
        return result

    def leader_for_deck(self, deck_id: str) -> LeaderDefinition:
        deck = self.decks[deck_id]
        leader = self.leaders.get(deck.leader_id)
        if leader is None:
            # MVP fallback keeps the prototype usable while leader.csv evolves.
            return LeaderDefinition(deck.leader_id or "UNKNOWN", deck.leader_id or "Leader", deck.faction_id, 20)
        return leader
