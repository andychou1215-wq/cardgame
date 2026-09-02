from dataclasses import replace

import pandas as pd

from src.core.game import Game, QueuedEffect
from src.deck.loader import GameData
from src.effects.models import TargetRef
from src.playtest.damage_healing import analyze_damage_healing
from tests.integration.test_engine_core import make_repo


def make_game(tmp_path, seed=1):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=seed)
    return data, game


def start_game(game):
    assert game.mulligan_hand([])[0]
    assert game.mulligan_hand([])[0]
    game.active_player_index = 0


def metadata(event):
    return event.metadata or {}


def test_initial_hand_and_mulligan_draws_are_measured(tmp_path):
    _, game = make_game(tmp_path)

    initial_draws = [
        event
        for event in game.telemetry.events
        if event.event_type == "card_drawn"
        and metadata(event).get("reason") == "initial_hand"
    ]
    assert len(initial_draws) == 10
    assert {event.player_index for event in initial_draws} == {0, 1}

    returned_id = game.players[0].hand[0].instance_id
    assert game.mulligan_hand([returned_id])[0]

    mulligan_draws = [
        event
        for event in game.telemetry.events
        if event.event_type == "card_drawn"
        and metadata(event).get("reason") == "mulligan"
    ]
    mulligans = [
        event for event in game.telemetry.events
        if event.event_type == "mulligan"
    ]
    assert len(mulligan_draws) == 1
    assert mulligans[-1].amount == 1
    assert metadata(mulligans[-1]) == {
        "cards_returned": 1,
        "cards_drawn": 1,
    }


def test_combat_lifesteal_and_death_feed_damage_profile(tmp_path):
    data, game = make_game(tmp_path, seed=2)
    start_game(game)

    attacker = next(
        card for card in data.build_deck("D001")
        if card.card_id == "U001"
    )
    defender = next(
        card for card in data.build_deck("D002")
        if card.card_id == "U002"
    )
    attacker.owner_index = 0
    defender.owner_index = 1
    attacker.entered_turn = 0
    defender.entered_turn = 0
    attacker.permanent_keywords.add("吸血")
    attacker.take_damage(1)
    game.players[0].battlefield = [attacker]
    game.players[1].battlefield = [defender]

    assert game.declare_attack(
        attacker.instance_id,
        TargetRef("unit", 1, defender.instance_id),
    )[0]
    assert game.resolve_combat()[0]

    combat = [
        event for event in game.telemetry.events
        if event.event_type == "combat_damage_unit"
    ]
    heals = [
        event for event in game.telemetry.events
        if event.event_type == "heal"
        and metadata(event).get("source_type") == "lifesteal"
    ]
    deaths = [
        event for event in game.telemetry.events
        if event.event_type == "unit_died"
    ]

    assert len(combat) == 2
    assert {(event.player_index, event.amount) for event in combat} == {
        (0, 2),
        (1, 1),
    }
    assert len(heals) == 1
    assert heals[0].amount == 2
    assert metadata(heals[0])["requested_amount"] == 2
    assert deaths[-1].card_id == defender.card_id

    summary = game.telemetry.summary(game)
    summaries = pd.DataFrame([summary])
    events = pd.DataFrame(game.telemetry.rows())
    result = analyze_damage_healing(summaries, events)
    deck_profile = result["deck_summary"].set_index("deck_id")

    assert summary["combat_damage_to_unit"] == 3
    assert summary["healing_done"] == 2
    assert summary["units_died"] >= 1
    assert deck_profile.loc["D001", "avg_combat_damage_unit"] == 2
    assert deck_profile.loc["D001", "avg_lifesteal_healing"] == 2


def test_effect_damage_heal_and_game_end_capture_actual_amounts(tmp_path):
    data, game = make_game(tmp_path, seed=3)
    start_game(game)

    spell = next(
        card for card in data.build_deck("D001")
        if card.card_id == "S001"
    )
    base_effect = data.effects_for("S001", "on_play", "none")[0]

    game.players[0].leader_health = game.players[0].leader.max_health - 1
    heal_effect = replace(
        base_effect,
        operation="heal",
        value=3,
        target="ally_leader",
    )
    game._resolve_effect(
        QueuedEffect(heal_effect, spell.instance_id, 0),
        TargetRef("leader", 0),
    )

    game.players[1].leader_health = 1
    game._resolve_effect(
        QueuedEffect(base_effect, spell.instance_id, 0),
        TargetRef("leader", 1),
    )
    game._run_state_based_check()

    heal = next(
        event for event in game.telemetry.events
        if event.event_type == "heal"
        and metadata(event).get("source_type") == "effect"
    )
    damage = next(
        event for event in game.telemetry.events
        if event.event_type == "effect_damage"
        and event.target_kind == "leader"
    )
    game_end = [
        event for event in game.telemetry.events
        if event.event_type == "game_end"
    ]

    assert heal.amount == 1
    assert metadata(heal)["requested_amount"] == 3
    assert metadata(heal)["overheal"] == 2
    assert damage.amount == 1
    assert metadata(damage)["requested_amount"] == 2
    assert game_end[-1].player_index == 0
    assert metadata(game_end[-1])["reason"] == "leader_health"


def test_max_health_sync_sources_are_classified(tmp_path):
    data, game = make_game(tmp_path, seed=4)
    start_game(game)

    unit = next(
        card for card in data.build_deck("D001")
        if card.card_id == "U001"
    )
    unit.owner_index = 0
    unit.entered_turn = 0
    unit.take_damage(1)
    game.players[0].battlefield = [unit]

    base_effect = data.effects_for("S001", "on_play", "none")[0]
    max_health_effect = replace(
        base_effect,
        operation="modify_max_health",
        value=2,
        target="ally_unit",
        duration="permanent",
    )
    game._resolve_effect(
        QueuedEffect(max_health_effect, "buff-source", 0),
        TargetRef("unit", 0, unit.instance_id),
    )

    unit.back = replace(unit.back, max_health=unit.back.max_health + 2)
    game._transform(unit, 0)

    sync_heals = [
        event for event in game.telemetry.events
        if event.event_type == "heal"
        and metadata(event).get("source_type") in {
            "max_health_sync",
            "transform_max_health_sync",
        }
    ]
    assert [metadata(event)["source_type"] for event in sync_heals] == [
        "max_health_sync",
        "transform_max_health_sync",
    ]
    assert [event.amount for event in sync_heals] == [2, 2]
    assert all(event.target_instance_id == unit.instance_id for event in sync_heals)
