import json

import pandas as pd
import pytest


@pytest.fixture
def sample_cards() -> pd.DataFrame:
    """Small card table using the real project cards.csv schema."""
    return pd.DataFrame(
        [
            {"id": "A", "cost": 1},
            {"id": "B", "cost": 2},
            {"id": "C", "cost": 4},
        ]
    )


@pytest.fixture
def sample_deck_cards() -> pd.DataFrame:
    """Small deck table using the real project deck_cards.csv schema."""
    return pd.DataFrame(
        [
            {"deck_id": "D001", "card_id": "A", "quantity": 2},
            {"deck_id": "D001", "card_id": "B", "quantity": 2},
            {"deck_id": "D001", "card_id": "C", "quantity": 1},
            {"deck_id": "D002", "card_id": "A", "quantity": 1},
            {"deck_id": "D002", "card_id": "B", "quantity": 1},
            {"deck_id": "D002", "card_id": "C", "quantity": 3},
        ]
    )


@pytest.fixture
def mana_curve_runtime_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    summaries = pd.DataFrame(
        [
            {"game_id": "G1", "deck_id_p1": "D001", "deck_id_p2": "D002"},
        ]
    )
    events = pd.DataFrame(
        [
            {
                "game_id": "G1",
                "event_type": "card_played",
                "turn": 1,
                "player_index": 0,
                "metadata": "{}",
            },
            {
                "game_id": "G1",
                "event_type": "turn_resource_snapshot",
                "turn": 1,
                "player_index": 0,
                "metadata": json.dumps(
                    {
                        "max_mana": 1,
                        "mana_remaining": 0,
                        "mana_spent": 1,
                        "dead_hand": False,
                        "spend_actions_available": 0,
                    }
                ),
            },
            {
                "game_id": "G1",
                "event_type": "turn_resource_snapshot",
                "turn": 2,
                "player_index": 1,
                "metadata": json.dumps(
                    {
                        "max_mana": 1,
                        "mana_remaining": 1,
                        "mana_spent": 0,
                        "dead_hand": True,
                        "spend_actions_available": 0,
                    }
                ),
            },
            {
                "game_id": "G1",
                "event_type": "card_played",
                "turn": 3,
                "player_index": 0,
                "metadata": "{}",
            },
            {
                "game_id": "G1",
                "event_type": "turn_resource_snapshot",
                "turn": 3,
                "player_index": 0,
                "metadata": json.dumps(
                    {
                        "max_mana": 2,
                        "mana_remaining": 1,
                        "mana_spent": 1,
                        "dead_hand": False,
                        "spend_actions_available": 0,
                    }
                ),
            },
            {
                "game_id": "G1",
                "event_type": "turn_resource_snapshot",
                "turn": 4,
                "player_index": 1,
                "metadata": json.dumps(
                    {
                        "max_mana": 2,
                        "mana_remaining": 0,
                        "mana_spent": 2,
                        "dead_hand": False,
                        "spend_actions_available": 0,
                    }
                ),
            },
        ]
    )
    return summaries, events
