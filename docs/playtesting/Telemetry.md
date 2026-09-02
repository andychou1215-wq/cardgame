# Playtest Telemetry

## Per-game outputs

### `event_log.csv`

Structured event stream. Common event types include:
- card_drawn
- draw
- mulligan
- card_played
- attack_declared
- response_played
- priority_pass
- priority_auto_pass
- combat_damage_leader
- combat_damage_unit
- effect_damage
- heal
- transform
- unit_died
- trigger
- state_based_check
- deck_out
- game_end

`card_drawn` includes initial-hand, Mulligan, turn-start, and effect draws.
The draw reason is stored in `metadata.reason`; `draw` is the aggregate event
for one draw operation.

Damage and healing events follow one amount contract:

- `amount` is the actual value applied to game state.
- `metadata.requested_amount` is the attempted value before caps or prevention.
- `metadata.blocked` is prevented combat damage.
- `metadata.overheal` is requested healing that could not be applied.
- `metadata.source_type` classifies combat/effect damage and effect,
  lifesteal, max-health-sync, or transform-max-health-sync healing.

Unit combat emits separate `combat_damage_unit` rows for the active attack and
counterattack. This preserves correct source-card and source-deck attribution.

### `game_summary.csv`

Cross-game summary fields include:
- game_id
- seed
- winner_index
- first_player_index
- turn_number
- leader HP
- deck IDs
- cards played
- attacks
- responses
- transforms
- deaths
- healing
- damage

## Directory convention

```text
playtest_data/
├─ raw/
└─ summaries/
```

Generated raw outputs should not be committed unless they are intentional fixtures.
