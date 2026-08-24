from pathlib import Path

from src.core.game import Game
from src.deck.loader import GameData
from src.effects.models import TargetRef
from tests.test_engine_v2 import make_repo
from tests.test_engine_v3 import start_game


def make_game(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=500)
    start_game(game)
    game.active_player_index = 0
    return data, game


def put_basic_combat(data, game):
    attacker = next(c for c in data.build_deck("D001") if c.card_id == "U001")
    defender = next(c for c in data.build_deck("D002") if c.card_id == "U002")
    attacker.owner_index = 0
    defender.owner_index = 1
    attacker.entered_turn = 0
    defender.entered_turn = 0
    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [defender]
    return attacker, defender


def test_direct_resolve_auto_passes_when_no_responses(tmp_path: Path):
    data, game = make_game(tmp_path)
    attacker, defender = put_basic_combat(data, game)

    ok, _ = game.declare_attack(
        attacker.instance_id,
        TargetRef("unit", 1, defender.instance_id),
    )
    assert ok
    assert game.priority_window is not None
    assert game.priority_window.is_open

    ok, _ = game.resolve_combat()
    assert ok
    assert game.pending_combat is None


def test_auto_pass_closes_empty_window(tmp_path: Path):
    data, game = make_game(tmp_path)
    attacker, defender = put_basic_combat(data, game)

    game.declare_attack(
        attacker.instance_id,
        TargetRef("unit", 1, defender.instance_id),
    )

    assert game._priority_can_auto_pass()
    game._auto_pass_empty_priority_window()
    assert not game.priority_window.is_open
    assert game.priority_window.consecutive_passes == 2
