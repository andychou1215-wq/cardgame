from src.playtest.deck_attribution import (
    attribute_events_to_decks,
    build_game_player_deck_map,
    build_static_membership,
)


def test_unique_card_uses_static_membership():
    efficiency = [
        {"deck_id": "D001", "card_id": "A"},
    ]
    membership = build_static_membership(efficiency)

    result = attribute_events_to_decks(
        [{"event_type": "card_played", "card_id": "A"}],
        membership,
        {},
    )

    assert result["events"][0]["deck_id"] == "D001"
    assert (
        result["events"][0]["attribution_method"]
        == "unique_static_membership"
    )


def test_shared_card_requires_game_player_mapping():
    efficiency = [
        {"deck_id": "D001", "card_id": "R1"},
        {"deck_id": "D002", "card_id": "R1"},
    ]
    membership = build_static_membership(efficiency)

    event = {
        "event_type": "response_played",
        "card_id": "R1",
        "game_id": "g1",
        "player_index": "1",
    }

    without_map = attribute_events_to_decks(
        [event], membership, {}
    )
    assert without_map["events"] == []
    assert without_map["counts"]["shared_unattributed"] == 1

    with_map = attribute_events_to_decks(
        [event],
        membership,
        {("g1", 1): "D002"},
    )
    assert with_map["events"][0]["deck_id"] == "D002"
    assert (
        with_map["events"][0]["attribution_method"]
        == "game_player_join"
    )


def test_game_summary_builds_player_deck_map():
    rows = [
        {
            "game_id": "g1",
            "deck_p1": "D001",
            "deck_p2": "D002",
        }
    ]

    mapping, diagnostics = build_game_player_deck_map(rows)

    assert mapping[("g1", 0)] == "D001"
    assert mapping[("g1", 1)] == "D002"
    assert diagnostics["supported"] is True
