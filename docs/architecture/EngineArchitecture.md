# Engine Architecture

## Current engine layers

```text
Game orchestration
→ Trigger Queue
→ Effect Queue
→ State-Based Check
→ Priority / Response Window
→ Combat resolution
→ Telemetry
```

### `src/core/`

Responsible for:
- game lifecycle
- turn orchestration
- trigger/event queue
- state-based actions
- priority windows

### `src/combat/`

Responsible for:
- legal attack targets
- combat damage
- combat-only keyword interaction

### `src/effects/`

Responsible for:
- effect definitions
- effect target resolution
- effect operations

### `src/playtest/`

Responsible for:
- structured telemetry
- scenario catalog
- cross-game analytics

## Rule implementation principle

Gameplay rules belong in the engine, not in Streamlit UI.

The UI may display legal choices, but it should not independently decide:
- winner
- legal attack target
- damage amount
- death
- deck-out
- transform
- response legality
