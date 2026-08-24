from pathlib import Path

from src.core.game import Game
from src.deck.loader import GameData
from tests.test_engine_v2 import make_repo
from tests.test_engine_v3 import start_game


def make_game(tmp_path: Path, seed: int = 700):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=seed)
    start_game(game)
    game.active_player_index = 0
    return data, game


def test_turn_start_empty_deck_causes_loss(tmp_path: Path):
    _, game = make_game(tmp_path)
    game.active_player_index = 1
    game.players[1].deck.clear()

    game._start_turn(initial=False)

    assert game.winner_index == 0
    assert any("牌組已無牌可抽" in line for line in game.log_entries)
    assert any(e.event_type == "deck_out" for e in game.telemetry.events)


def test_drawing_last_card_is_legal(tmp_path: Path):
    _, game = make_game(tmp_path)
    player = game.players[0]
    player.deck = player.deck[:1]

    drawn = game._draw_cards(0, 1, reason="test")

    assert drawn == 1
    assert len(player.deck) == 0
    assert game.winner_index is None


def test_multi_draw_loses_on_first_failed_draw(tmp_path: Path):
    _, game = make_game(tmp_path)
    player = game.players[0]
    player.deck = player.deck[:1]

    drawn = game._draw_cards(0, 2, reason="test_multi")

    assert drawn == 1
    assert game.winner_index == 1


def test_opponent_deck_out_awards_correct_winner(tmp_path: Path):
    _, game = make_game(tmp_path)
    game.players[1].deck.clear()

    drawn = game._draw_cards(1, 1, reason="test")

    assert drawn == 0
    assert game.winner_index == 0
