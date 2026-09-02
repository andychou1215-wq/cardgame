from dataclasses import replace
from pathlib import Path

from src.core.game import Game, QueuedEffect, STARTING_HAND
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


def test_until_turn_end_group_stats_expire_together(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=13)
    start_game(game)
    game.active_player_index = 0

    source = next(
        card for card in data.build_deck("D001")
        if card.card_id == "U001"
    )
    ally = next(
        card for card in data.build_deck("D001")
        if card.card_id == "U001"
    )
    source.owner_index = 0
    ally.owner_index = 0
    source.entered_turn = 0
    ally.entered_turn = 0
    game.players[0].battlefield = [source, ally]

    base_effect = data.effects_for("S001", "on_play", "none")[0]
    attack_effect = replace(
        base_effect,
        target="all_other_ally_units",
        target_required=False,
        operation="modify_attack",
        value=1,
        duration="until_turn_end",
    )
    health_effect = replace(
        attack_effect,
        operation="modify_max_health",
    )

    attack_before = ally.attack
    max_health_before = ally.max_health
    health_before = ally.current_health

    game._resolve_effect(
        QueuedEffect(attack_effect, source.instance_id, 0),
        None,
    )
    game._resolve_effect(
        QueuedEffect(health_effect, source.instance_id, 0),
        None,
    )

    assert source.attack == attack_before
    assert ally.attack == attack_before + 1
    assert ally.max_health == max_health_before + 1
    assert ally.current_health == health_before + 1

    assert game.end_turn()[0]

    assert ally.attack == attack_before
    assert ally.max_health == max_health_before
    assert ally.current_health == health_before


def test_u012_front_effect_data_expires_at_turn_end():
    root = Path(__file__).resolve().parents[2]
    data = GameData(root)

    effects = data.effects_for("U012", "on_enter", "front")

    assert {effect.effect_id for effect in effects} == {"E019", "E020"}
    assert {effect.duration for effect in effects} == {"until_turn_end"}
    assert all("到本回合結束" in effect.effect_text for effect in effects)
