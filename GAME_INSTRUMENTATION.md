# Game Telemetry Instrumentation

The core engine emits the complete event contract consumed by the playtest
and balance analyzers. Event `amount` always means the actual amount applied
to game state; attempted values and prevented values live in `metadata`.

## Draw and lifecycle events

- `card_drawn`: one row per card, including `initial_hand`, `mulligan`,
  `turn_start`, and effect draws through `metadata.reason`.
- `draw`: aggregate number of cards drawn by one draw operation.
- `mulligan`: cards returned and redrawn.
- `unit_died`: one row per unit moved from battlefield to graveyard.
- `game_end`: winner and terminal reason for both leader-health and deck-out
  endings.

## Damage events

- `combat_damage_leader`
- `combat_damage_unit`: active attack and counterattack are separate rows.
- `effect_damage`

Every damage event identifies the source player/card, the target, the actual
damage in `amount`, and includes:

- `source_type`
- `requested_amount`
- `blocked`
- `effect_id` or `combat_role` when applicable

## Healing events

All healing uses the single `heal` event with one of these
`metadata.source_type` values:

- `effect`
- `lifesteal`
- `max_health_sync`
- `transform_max_health_sync`

Each event records actual healing in `amount`, plus `requested_amount` and
`overheal`. Zero-actual lifesteal and effect heals are intentionally retained
so overheal analysis remains possible.

## Validation

The integration coverage in
`tests/integration/test_telemetry_coverage.py` proves initial-hand and Mulligan
draws, combat and counterattack damage, effect damage, every healing source,
unit death, leader-health game end, summary aggregation, and the M3.7.5
damage/healing analyzer contract.

Run:

```powershell
py -3 -m pytest -q
```

Before producing a large balance baseline, run a small simulation and confirm
that damage, healing, death, snapshot, and game-end event counts are non-zero.
