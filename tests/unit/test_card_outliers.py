from src.playtest.card_outliers import build_card_outlier_analysis


def test_card_delta_is_relative_to_own_deck_baseline():
    telemetry = [
        {
            "card_id": "A",
            "draw_events": "20",
            "play_events": "10",
            "play_given_draw_rate": "0.5",
            "games_played": "10",
            "win_rate_when_played": "0.95",
            "avg_play_turn": "3",
            "response_events": "0",
            "transform_events": "0",
            "effect_damage_events": "0",
            "heal_events": "0",
        },
        {
            "card_id": "B",
            "draw_events": "20",
            "play_events": "10",
            "play_given_draw_rate": "0.5",
            "games_played": "10",
            "win_rate_when_played": "0.20",
            "avg_play_turn": "3",
            "response_events": "0",
            "transform_events": "0",
            "effect_damage_events": "0",
            "heal_events": "0",
        },
    ]

    efficiency = [
        {
            "deck_id": "D001",
            "card_id": "A",
            "name": "A",
            "type": "unit",
            "cost": "2",
            "quantity": "2",
            "front_stats_per_mana": "2.5",
            "keywords": "",
            "operations": "",
            "triggers": "",
        },
        {
            "deck_id": "D002",
            "card_id": "B",
            "name": "B",
            "type": "unit",
            "cost": "2",
            "quantity": "2",
            "front_stats_per_mana": "2.5",
            "keywords": "",
            "operations": "",
            "triggers": "",
        },
    ]

    analysis = build_card_outlier_analysis(
        card_telemetry=telemetry,
        card_efficiency=efficiency,
        deck_baselines={"D001": 0.90, "D002": 0.10},
        min_draws=10,
        min_plays=5,
    )

    rows = {
        r["card_id"]: r
        for r in analysis["all_cards"]
    }

    assert rows["A"]["win_rate_delta_vs_deck"] == 0.05
    assert rows["B"]["win_rate_delta_vs_deck"] == 0.10


def test_high_draw_low_play_rank():
    telemetry = [
        {
            "card_id": "A",
            "draw_events": "100",
            "play_events": "10",
            "play_given_draw_rate": "0.10",
            "win_rate_when_played": "0.5",
        },
        {
            "card_id": "B",
            "draw_events": "100",
            "play_events": "80",
            "play_given_draw_rate": "0.80",
            "win_rate_when_played": "0.5",
        },
    ]
    efficiency = [
        {"deck_id": "D1", "card_id": "A", "name": "A"},
        {"deck_id": "D1", "card_id": "B", "name": "B"},
    ]

    analysis = build_card_outlier_analysis(
        card_telemetry=telemetry,
        card_efficiency=efficiency,
        deck_baselines={"D1": 0.5},
        min_draws=10,
        min_plays=1,
    )

    assert analysis["high_draw_low_play"][0]["card_id"] == "A"
