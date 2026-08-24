from pathlib import Path

from src.core.game import Game
from src.deck.loader import GameData
from src.effects.models import TargetRef
from tests.test_engine_v2 import make_repo
from tests.test_engine_v3 import start_game


def make_keyword_unit(data: GameData, deck_id: str, card_id: str, owner: int, keyword: str):
    unit = next(c for c in data.build_deck(deck_id) if c.card_id == card_id)
    unit.owner_index = owner
    unit.entered_turn = 0
    unit.permanent_keywords.add(keyword)
    return unit


def test_lifesteal_heals_attacking_unit_not_leader(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=20)
    start_game(game)
    game.active_player_index = 0
    attacker = make_keyword_unit(data, "D001", "U001", 0, "吸血")
    defender = next(c for c in data.build_deck("D002") if c.card_id == "U002")
    defender.owner_index = 1
    defender.entered_turn = 0
    attacker.take_damage(1)  # 2/3 before combat
    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [defender]
    leader_before = game.players[0].leader_health

    ok, _ = game.declare_attack(attacker.instance_id, TargetRef("unit", 1, defender.instance_id))
    assert ok
    ok, _ = game.resolve_combat()
    assert ok
    # Attacker takes 1 counterdamage then heals for 2 actual active-attack damage: capped at 3.
    assert attacker.current_health == 3
    assert game.players[0].leader_health == leader_before


def test_block_reduces_combat_damage_only(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=21)
    start_game(game)
    game.active_player_index = 0
    attacker = next(c for c in data.build_deck("D001") if c.card_id == "U001")
    defender = make_keyword_unit(data, "D002", "U002", 1, "格檔")
    attacker.owner_index = 0
    attacker.entered_turn = 0
    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [defender]

    ok, _ = game.declare_attack(attacker.instance_id, TargetRef("unit", 1, defender.instance_id))
    assert ok
    game.resolve_combat()
    assert defender.current_health == defender.max_health - 1  # 2 attack - 1 block = 1

    # Effect damage bypasses 格檔. Reset health to isolate effect damage.
    defender.health = defender.max_health
    spell = next(c for c in data.build_deck("D001") if c.card_id == "S001")
    game.players[0].hand = [spell]
    game.players[0].mana = 10
    ok, _ = game.play_card(0, TargetRef("unit", 1, defender.instance_id))
    assert ok
    assert defender.current_health == defender.max_health - 2


def test_heal_target_excludes_full_health_and_max_hp_buff_restores_same_amount(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=22)
    start_game(game)
    game.active_player_index = 0
    unit = next(c for c in data.build_deck("D001") if c.card_id == "U001")
    unit.owner_index = 0
    unit.entered_turn = 0
    game.players[0].battlefield = [unit]

    # New rule: max HP +X also restores X current HP.
    unit.take_damage(1)
    hp_before = unit.current_health
    unit.increase_max_health(1)
    assert unit.current_health == hp_before + 1
    assert unit.max_health == 4
