# M1 + M2 Implementation Pack

This pack is designed against the public `main` branch structure reviewed on 2026-08-24.

## M1 — Rules Stabilization foundation

Adds:

- `src/core/events.py`
  - `TriggerEvent`
  - FIFO `TriggerQueue`
- Trigger source-side snapshotting
- Trigger Queue → Effect Queue separation
- Keeps existing simultaneous death collection and AP/NAP enqueue order
- Keeps existing Response Window and Effect Resolver behavior

The intent is deliberately conservative: M1 does **not** rewrite combat or effect resolution.
It introduces the queue boundary needed for later response chains and more trigger types.

## M2 — Digital Playtest foundation

Adds:

- `src/playtest/telemetry.py`
  - structured events
  - game summary
  - JSON export
  - CSV export
- `src/playtest/scenarios.py`
  - reusable arrange / act / verify scenarios
- `tests/test_m1_m2_infrastructure.py`

Initial telemetry events patched into `Game`:

- `card_played`
- `attack_declared`
- `response_played`
- `combat_damage_leader`
- `combat_damage_unit`
- `effect_damage`
- `heal`
- `transform`
- `unit_died`
- `trigger`
- `game_end`

## Apply

Copy this pack over the repository root, then run:

```bash
python tools/apply_m1_m2.py
pytest -q
```

The apply script uses exact anchors and stops if the reviewed `game.py` no longer matches,
instead of silently corrupting a newer version.

## Suggested next tests

1. simultaneous lethal units queue `on_leave` in AP/NAP order
2. `on_leave` source resolves after leaving the battlefield
3. transform queues `on_flip` using the back-side snapshot
4. a trigger that causes lethal damage performs state-based death before the next trigger chain
5. telemetry export matches final winner / turn / HP state

## Next M1 increment

After this foundation passes the existing suite:

- formal `StateBasedCheck` loop object
- multi-response chain / priority passing
- deck exhaustion rule
- deterministic trigger ordering inside each controller
