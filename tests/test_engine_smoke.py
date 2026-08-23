"""Minimal smoke checks for pure engine helpers.

This file intentionally does not import Streamlit. Full integration tests need the repo CSV data.
"""
from src.cards.models import CardDefinition, UnitInstance, UnitSideDefinition


def test_unit_stats():
    definition = CardDefinition("U999", "Test", "unit", 1, "NEUTRAL")
    front = UnitSideDefinition("U999", "front", 2, 3)
    unit = UnitInstance(definition=definition, front=front)
    assert unit.attack == 2
    assert unit.current_health == 3
    unit.damage = 1
    assert unit.current_health == 2
