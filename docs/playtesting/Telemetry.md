# Playtest Telemetry

## Per-game outputs

### `event_log.csv`

Structured event stream. Common event types include:
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
