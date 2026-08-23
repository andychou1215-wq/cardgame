from src.cards.models import CardDefinition, UnitInstance, UnitSideDefinition


def test_unit_stats_and_explicit_health():
    definition = CardDefinition("U999", "Test", "unit", 1, "NEUTRAL")
    front = UnitSideDefinition("U999", "front", 2, 3)
    unit = UnitInstance(definition=definition, front=front)
    assert unit.attack == 2
    assert unit.current_health == 3
    assert unit.take_damage(1) == 1
    assert unit.current_health == 2
    assert unit.heal(1) == 1
    assert unit.current_health == 3


def test_max_health_increase_does_not_heal():
    definition = CardDefinition("U998", "Test", "unit", 1, "NEUTRAL")
    front = UnitSideDefinition("U998", "front", 2, 3)
    unit = UnitInstance(definition=definition, front=front)
    unit.take_damage(2)
    assert unit.current_health == 1
    unit.increase_max_health(2)
    assert unit.max_health == 5
    assert unit.current_health == 1
