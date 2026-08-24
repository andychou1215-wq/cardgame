from src.playtest.card_outliers_attributed import build_attributed_outliers


def test_shared_card_rows_are_not_duplicated_by_analyzer():
    telemetry = [
        {
            "deck_id": "D002",
            "card_id": "R1",
            "recorded_draw_events": "20",
            "use_events": "10",
            "uses_per_recorded_draw": "0.5",
            "games_used": "10",
            "win_rate_when_used": "0.8",
            "attribution_method": "game_player_join",
        }
    ]

    efficiency = [
        {"deck_id": "D001", "card_id": "R1", "name": "Shared"},
        {"deck_id": "D002", "card_id": "R1", "name": "Shared"},
    ]

    result = build_attributed_outliers(
        deck_card_telemetry=telemetry,
        card_efficiency=efficiency,
        deck_baselines={"D001": 0.9, "D002": 0.1},
        min_draws=1,
        min_uses=1,
    )

    assert len(result["all_cards"]) == 1
    row = result["all_cards"][0]
    assert row["deck_id"] == "D002"
    assert row["win_rate_delta_vs_deck"] == 0.7
