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


def test_u011_back_grants_shelter_until_opponent_turn_end():
    root = Path(__file__).resolve().parents[2]
    data = GameData(root)
    game = Game(data, "D001", "D002", seed=16)
    start_game(game)
    game.active_player_index = 0

    source = next(card for card in data.build_deck("D001") if card.card_id == "U011")
    ally = next(card for card in data.build_deck("D001") if card.card_id == "U001")
    for unit in (source, ally):
        unit.owner_index = 0
        unit.entered_turn = 0
    source.current_side = "back"
    game.players[0].battlefield = [source, ally]

    effect = data.effects_for("U011", "on_flip", "back")[0]
    assert effect.effect_id == "E018"
    assert effect.target == "other_ally_unit"
    assert effect.parameter == "庇護"
    assert effect.duration == "until_opponent_turn_end"

    target = TargetRef("unit", 0, ally.instance_id)
    game._resolve_effect(QueuedEffect(effect, source.instance_id, 0), target)

    assert ally.has_keyword("庇護")
    assert "庇護" not in ally.permanent_keywords
    assert source.has_keyword("庇護")

    assert game.end_turn()[0]
    assert ally.has_keyword("庇護")

    assert game.end_turn()[0]
    assert not ally.has_keyword("庇護")
    assert source.has_keyword("庇護")


def test_u012_front_effect_data_expires_at_turn_end():
    root = Path(__file__).resolve().parents[2]
    data = GameData(root)

    effects = data.effects_for("U012", "on_enter", "front")

    assert {effect.effect_id for effect in effects} == {"E019", "E020"}
    assert {effect.duration for effect in effects} == {"until_turn_end"}
    assert all("到本回合結束" in effect.effect_text for effect in effects)


def test_u012_transform_requires_three_units_and_one_with_shelter():
    root = Path(__file__).resolve().parents[2]
    data = GameData(root)
    game = Game(data, "D001", "D002", seed=15)
    start_game(game)
    game.active_player_index = 0

    source = next(card for card in data.build_deck("D001") if card.card_id == "U012")
    sheltered = next(card for card in data.build_deck("D001") if card.card_id == "U001")
    normal = next(card for card in data.build_deck("D001") if card.card_id == "U002")
    for unit in (source, sheltered, normal):
        unit.owner_index = 0
        unit.entered_turn = 0

    assert source.definition.transform_condition_target == "ally_units;keyword:庇護"
    assert source.definition.transform_condition_text == (
        "我方戰場上至少共有3個單位，且其中一個單位擁有【庇護】效果時翻至反面。"
    )

    game.players[0].battlefield = [source, sheltered]
    assert not game.check_transforms()
    assert source.current_side == "front"

    sheltered.permanent_keywords.discard("庇護")
    game.players[0].battlefield.append(normal)
    assert not game.check_transforms()
    assert source.current_side == "front"

    sheltered.permanent_keywords.add("庇護")
    assert game.check_transforms()
    assert source.current_side == "back"


def test_u012_back_shelter_extends_same_buff_without_stacking():
    root = Path(__file__).resolve().parents[2]
    data = GameData(root)
    game = Game(data, "D001", "D002", seed=14)
    start_game(game)
    game.active_player_index = 0

    source = next(card for card in data.build_deck("D001") if card.card_id == "U012")
    sheltered = next(card for card in data.build_deck("D001") if card.card_id == "U011")
    normal = next(card for card in data.build_deck("D001") if card.card_id == "U001")
    for unit in (source, sheltered, normal):
        unit.owner_index = 0
        unit.entered_turn = 0
    source.current_side = "back"
    source.permanent_keywords.add("庇護")
    game.players[0].battlefield = [source, sheltered, normal]

    sheltered_attack = sheltered.attack
    sheltered_health = sheltered.max_health
    normal_attack = normal.attack
    normal_health = normal.max_health

    effects = data.effects_for("U012", "on_flip", "back")
    assert [effect.effect_id for effect in effects] == ["E021", "E022", "E028", "E029"]
    for effect in effects:
        game._resolve_effect(QueuedEffect(effect, source.instance_id, 0), None)

    assert source.attack == 3
    assert source.max_health == 6
    assert sheltered.attack == sheltered_attack + 1
    assert sheltered.max_health == sheltered_health + 1
    assert normal.attack == normal_attack + 1
    assert normal.max_health == normal_health + 1
    sheltered_modifiers = [
        modifier
        for modifier in sheltered.timed_modifiers
        if modifier.kind in {"attack", "max_health"}
    ]
    assert len(sheltered_modifiers) == 2
    assert {modifier.duration for modifier in sheltered_modifiers} == {
        "until_opponent_turn_end"
    }
    extension_events = [
        event
        for event in game.telemetry.events
        if event.event_type == "modifier_extended"
    ]
    assert [event.metadata["kind"] for event in extension_events] == [
        "attack",
        "max_health",
    ]
    u012_heals = [
        event
        for event in game.telemetry.events
        if event.event_type == "heal" and event.card_id == "U012"
    ]
    assert len(u012_heals) == 2
    assert {event.metadata["effect_id"] for event in u012_heals} == {"E022"}

    assert game.end_turn()[0]
    assert source.attack == 3
    assert source.max_health == 6
    assert sheltered.attack == sheltered_attack + 1
    assert sheltered.max_health == sheltered_health + 1
    assert normal.attack == normal_attack
    assert normal.max_health == normal_health

    assert game.end_turn()[0]
    assert source.attack == 3
    assert source.max_health == 6
    assert sheltered.attack == sheltered_attack
    assert sheltered.max_health == sheltered_health
