from pathlib import Path

from src.core.game import Game
from src.deck.loader import GameData
from src.effects.models import TargetRef
from tests.test_engine_v2 import make_repo
from tests.test_engine_v3 import start_game
from tests.test_engine_v4 import make_keyword_unit


def test_evasion_removes_unit_from_attack_targets(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=30)
    start_game(game)
    game.active_player_index = 0

    attacker = next(c for c in data.build_deck("D001") if c.card_id == "U001")
    evasive = make_keyword_unit(data, "D002", "U002", 1, "迴避")
    normal = next(c for c in data.build_deck("D002") if c.card_id == "U002")
    attacker.owner_index = 0
    attacker.entered_turn = 0
    normal.owner_index = 1
    normal.entered_turn = 0

    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [evasive, normal]

    keys = {t.key for t in game.legal_attack_targets()}
    assert TargetRef("unit", 1, evasive.instance_id).key not in keys
    assert TargetRef("unit", 1, normal.instance_id).key in keys
    assert TargetRef("leader", 1).key in keys


def test_shelter_still_has_priority_when_another_unit_has_evasion(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=31)
    start_game(game)
    game.active_player_index = 0

    attacker = next(c for c in data.build_deck("D001") if c.card_id == "U001")
    shelter = make_keyword_unit(data, "D002", "U002", 1, "庇護")
    evasive = make_keyword_unit(data, "D002", "U002", 1, "迴避")
    attacker.owner_index = 0
    attacker.entered_turn = 0

    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [shelter, evasive]

    assert [t.key for t in game.legal_attack_targets()] == [
        TargetRef("unit", 1, shelter.instance_id).key
    ]


def test_max_health_increase_also_heals_same_amount(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    unit = next(c for c in data.build_deck("D001") if c.card_id == "U001")

    unit.take_damage(2)
    before_hp = unit.current_health
    before_max = unit.max_health

    healed = unit.increase_max_health(2)

    assert unit.max_health == before_max + 2
    assert unit.current_health == before_hp + 2
    assert healed == 2


def test_timed_max_health_increase_also_heals_same_amount(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    unit = next(c for c in data.build_deck("D001") if c.card_id == "U001")

    unit.take_damage(1)
    before_hp = unit.current_health
    before_max = unit.max_health

    healed = unit.add_timed_max_health(1, "until_turn_end", 0)

    assert unit.max_health == before_max + 1
    assert unit.current_health == before_hp + 1
    assert healed == 1
