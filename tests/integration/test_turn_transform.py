from pathlib import Path

from src.core.game import Game, STARTING_HAND
from src.deck.loader import GameData
from src.effects.models import TargetRef
from tests.test_engine_v2 import make_repo


def start_game(game: Game) -> None:
    ok, _ = game.mulligan_hand([])
    assert ok
    ok, _ = game.mulligan_hand([])
    assert ok
    assert game.game_started


def test_mulligan_replaces_selected_cards_and_preserves_hand_size(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=10)
    assert not game.game_started
    first_player = game.players[0]
    before_ids = [c.instance_id for c in first_player.hand]
    selected = before_ids[:2]
    ok, _ = game.mulligan_hand(selected)
    assert ok
    assert len(first_player.hand) == STARTING_HAND
    assert game.mulligan_done[0]
    assert game.mulligan_player_index == 1
    assert not game.game_started
    ok, _ = game.mulligan_hand([])
    assert ok
    assert game.game_started
    assert all(game.mulligan_done)
    assert game.active_player.max_mana == 1


def test_shelter_restricts_unit_attack_targets(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=11)
    start_game(game)
    game.active_player_index = 0

    attacker = next(c for c in data.build_deck("D001") if c.card_id == "U001")
    shelter = next(c for c in data.build_deck("D002") if c.card_id == "U002")
    normal = next(c for c in data.build_deck("D002") if c.card_id == "U002")
    attacker.owner_index = 0
    attacker.entered_turn = 0
    shelter.owner_index = 1
    normal.owner_index = 1
    shelter.permanent_keywords.add("庇護")
    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [shelter, normal]

    targets = game.legal_attack_targets()
    assert [t.key for t in targets] == [TargetRef("unit", 1, shelter.instance_id).key]

    shelter.permanent_keywords.remove("庇護")
    targets = game.legal_attack_targets()
    keys = {t.key for t in targets}
    assert TargetRef("leader", 1).key in keys
    assert TargetRef("unit", 1, shelter.instance_id).key in keys
    assert TargetRef("unit", 1, normal.instance_id).key in keys


def test_actions_blocked_until_mulligan_finishes(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=12)
    ok, message = game.end_turn()
    assert not ok
    assert "Mulligan" in message
    assert game.legal_attackers() == []
    assert game.legal_attack_targets() == []
