# M3.1 Hotfix 2

Second 10-game smoke run:

```text
finished: 5
stalled: 2
invalid_legal_action: 3
action_limit: 0
```

Fixes:

1. Battlefield capacity:
   - `BATTLEFIELD_LIMIT` is a module constant, not a Game instance attribute.
   - Adds authoritative `Game.can_play_card(hand_index)`.
   - AI uses it before emitting `play_card`.

2. False stalled PendingChoice:
   - `PendingChoice` has no `player_index`.
   - Decision owner is `pending.queued.source_player_index`.
   - Simulation now uses the same owner rule as Legal Action API.

3. Diagnostics:
   - stalled/invalid/action-limit results now include decision state:
     pending choice / combat / main phase, actor, effect, candidates, mana, etc.

Apply:

```powershell
py tools/apply_m3_1_hotfix_2.py
py -m pytest -q
py tools/run_simulation.py --games 10 --seed 42 --no-persist
```

Primary next acceptance target:

```text
invalid_legal_action: 0
stalled: 0
```
