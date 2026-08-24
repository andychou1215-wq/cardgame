from pathlib import Path

from src.core.game import Game
from src.core.state_based import StateBasedCheck
from src.deck.loader import GameData
from src.effects.models import TargetRef
from tests.test_engine_v2 import make_repo
from tests.test_engine_v3 import start_game
from tests.test_engine_v4 import make_keyword_unit


def make_game(tmp_path: Path, seed: int):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=seed)
    start_game(game)
    game.active_player_index = 0
    return data, game


def normal_unit(data, deck_id, card_id, owner):
    unit = next(c for c in data.build_deck(deck_id) if c.card_id == card_id)
    unit.owner_index = owner
    unit.entered_turn = 0
    return unit


def test_s001_shelter_restricts_targets(tmp_path: Path):
    data, game = make_game(tmp_path, 101)
    attacker = normal_unit(data, "D001", "U001", 0)
    shelter = make_keyword_unit(data, "D002", "U002", 1, "庇護")
    normal = normal_unit(data, "D002", "U002", 1)
    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [shelter, normal]

    assert [t.key for t in game.legal_attack_targets()] == [
        TargetRef("unit", 1, shelter.instance_id).key
    ]


def test_s002_evasion_is_not_attackable(tmp_path: Path):
    data, game = make_game(tmp_path, 102)
    attacker = normal_unit(data, "D001", "U001", 0)
    evasive = make_keyword_unit(data, "D002", "U002", 1, "迴避")
    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [evasive]

    keys = {t.key for t in game.legal_attack_targets()}
    assert TargetRef("unit", 1, evasive.instance_id).key not in keys
    assert TargetRef("leader", 1).key in keys


def test_s003_shelter_keeps_priority_with_evasion(tmp_path: Path):
    data, game = make_game(tmp_path, 103)
    attacker = normal_unit(data, "D001", "U001", 0)
    shelter = make_keyword_unit(data, "D002", "U002", 1, "庇護")
    evasive = make_keyword_unit(data, "D002", "U002", 1, "迴避")
    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [shelter, evasive]

    assert [t.key for t in game.legal_attack_targets()] == [
        TargetRef("unit", 1, shelter.instance_id).key
    ]


def test_s004_block_reduces_combat_damage(tmp_path: Path):
    data, game = make_game(tmp_path, 104)
    attacker = normal_unit(data, "D001", "U001", 0)
    defender = make_keyword_unit(data, "D002", "U002", 1, "格檔")
    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [defender]

    defender_before = defender.current_health
    attack_before_combat = attacker.attack

    ok, _ = game.declare_attack(
        attacker.instance_id,
        TargetRef("unit", 1, defender.instance_id),
    )
    assert ok

    ok, _ = game.resolve_combat()
    assert ok

    # Important: attacker may Transform / gain attack after combat.
    # The expected damage must use the attack value at combat declaration,
    # not attacker.attack after all post-combat state changes.
    expected_damage = max(0, attack_before_combat - 1)
    assert defender.current_health == defender_before - expected_damage


def test_s005_block_does_not_reduce_effect_damage(tmp_path: Path):
    data, game = make_game(tmp_path, 105)
    defender = make_keyword_unit(data, "D002", "U002", 1, "格檔")
    game.players[1].battlefield = [defender]

    spell = next(c for c in data.build_deck("D001") if c.card_id == "S001")
    game.players[0].hand = [spell]
    game.players[0].mana = 10
    before = defender.current_health

    ok, _ = game.play_card(0, TargetRef("unit", 1, defender.instance_id))
    assert ok
    assert defender.current_health == before - 2


def test_s006_lifesteal_heals_attacker(tmp_path: Path):
    data, game = make_game(tmp_path, 106)
    attacker = make_keyword_unit(data, "D001", "U001", 0, "吸血")
    defender = normal_unit(data, "D002", "U002", 1)

    attacker.take_damage(1)
    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [defender]
    leader_before = game.players[0].leader_health

    ok, _ = game.declare_attack(
        attacker.instance_id,
        TargetRef("unit", 1, defender.instance_id),
    )
    assert ok
    game.resolve_combat()

    assert attacker.current_health == attacker.max_health
    assert game.players[0].leader_health == leader_before


def test_s007_max_health_increase_heals_same_amount(tmp_path: Path):
    data, _ = make_game(tmp_path, 107)
    unit = normal_unit(data, "D001", "U001", 0)
    unit.take_damage(2)

    before_hp = unit.current_health
    before_max = unit.max_health
    healed = unit.increase_max_health(2)

    assert unit.max_health == before_max + 2
    assert unit.current_health == before_hp + 2
    assert healed == 2


def test_s008_simultaneous_deaths_leave_together(tmp_path: Path):
    data, game = make_game(tmp_path, 108)

    # Use cards that are guaranteed by the existing test fixture.
    # The previous version incorrectly assumed U007 existed in make_repo().
    a = normal_unit(data, "D001", "U001", 0)
    b = normal_unit(data, "D002", "U002", 1)

    game.players[0].battlefield = [a]
    game.players[1].battlefield = [b]
    a.health = 0
    b.health = 0

    assert game._handle_deaths()
    assert not game.players[0].battlefield
    assert not game.players[1].battlefield
    assert a in game.players[0].graveyard
    assert b in game.players[1].graveyard


def test_s009_ap_nap_on_leave_trigger_order(tmp_path: Path):
    data, game = make_game(tmp_path, 109)

    ap = normal_unit(data, "D001", "U001", 0)
    nap = normal_unit(data, "D002", "U002", 1)

    game.players[0].battlefield = [ap]
    game.players[1].battlefield = [nap]
    ap.health = 0
    nap.health = 0

    game._handle_deaths()

    queued = game.trigger_queue.snapshot()
    assert len(queued) >= 2
    assert [e.owner_index for e in queued[:2]] == [0, 1]
    assert [e.source_id for e in queued[:2]] == [
        ap.instance_id,
        nap.instance_id,
    ]


def test_s010_transform_queues_back_side_snapshot(tmp_path: Path):
    data, game = make_game(tmp_path, 110)
    unit = normal_unit(data, "D001", "U001", 0)
    assert unit.back is not None

    game.players[0].battlefield = [unit]
    game._transform(unit, 0)

    assert unit.current_side == "back"
    event = game.trigger_queue.snapshot()[-1]
    assert event.trigger == "on_flip"
    assert event.source_id == unit.instance_id
    assert event.side == "back"


def test_state_based_checkpoint_prioritizes_death(tmp_path: Path):
    data, game = make_game(tmp_path, 111)

    # Again use a card guaranteed to exist in the fixture.
    unit = normal_unit(data, "D001", "U001", 0)
    game.players[0].battlefield = [unit]
    unit.health = 0

    result = StateBasedCheck().run_once(game)

    assert result.changed
    assert result.deaths
