from src.playtest.telemetry_metrics import rebuild_card_usage_metrics


def test_response_is_counted_as_use():
    events = [
        {
            "event_type": "card_drawn",
            "card_id": "R1",
            "game_id": "g1",
            "player_index": "0",
            "turn_number": "1",
        },
        {
            "event_type": "response_played",
            "card_id": "R1",
            "game_id": "g1",
            "player_index": "0",
            "turn_number": "2",
        },
    ]
    summaries = [
        {"game_id": "g1", "winner_index": "0"}
    ]

    result = rebuild_card_usage_metrics(
        events,
        card_lookup={"R1": {"name": "Response"}},
        summary_rows=summaries,
    )
    row = result["cards"][0]

    assert row["normal_play_events"] == 0
    assert row["response_play_events"] == 1
    assert row["use_events"] == 1
    assert row["win_rate_when_used"] == 1.0


def test_uses_per_recorded_draw_may_exceed_one_and_is_not_probability():
    events = [
        {
            "event_type": "card_drawn",
            "card_id": "U1",
        },
        {
            "event_type": "card_played",
            "card_id": "U1",
        },
        {
            "event_type": "card_played",
            "card_id": "U1",
        },
    ]

    result = rebuild_card_usage_metrics(
        events,
        card_lookup={"U1": {"name": "Unit"}},
    )
    row = result["cards"][0]

    assert row["recorded_draw_events"] == 1
    assert row["use_events"] == 2
    assert row["uses_per_recorded_draw"] == 2.0
    assert (
        result["capabilities"][
            "recorded_draw_is_complete_hand_acquisition"
        ]
        is False
    )
