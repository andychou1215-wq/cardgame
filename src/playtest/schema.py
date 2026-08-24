from __future__ import annotations

import pandas as pd


def normalize_cards(cards: pd.DataFrame) -> pd.DataFrame:
    """Return card data using the analyzer-internal ``card_id`` key.

    Project CSV schema uses ``id`` in cards.csv. Balance/playtest analyzers use
    ``card_id`` internally so joins with deck_cards.csv are consistent.
    """
    normalized = cards.copy()

    if "card_id" not in normalized.columns and "id" in normalized.columns:
        normalized = normalized.rename(columns={"id": "card_id"})

    if "card_id" not in normalized.columns:
        raise ValueError("cards missing required card identifier: id or card_id")

    return normalized


def normalize_deck_cards(deck_cards: pd.DataFrame) -> pd.DataFrame:
    """Validate the current project deck-card schema without legacy aliases."""
    normalized = deck_cards.copy()
    required = {"deck_id", "card_id", "quantity"}
    missing = sorted(required.difference(normalized.columns))
    if missing:
        raise ValueError(
            "deck_cards missing required columns: " + ", ".join(missing)
        )
    return normalized


def normalize_card_deck_inputs(
    cards: pd.DataFrame,
    deck_cards: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Normalize the two shared card/deck tables for analysis code."""
    return normalize_cards(cards), normalize_deck_cards(deck_cards)
