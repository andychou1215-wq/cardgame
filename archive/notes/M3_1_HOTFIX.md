# M3.1 Legal Action Hotfix

Fixes the first 10-game simulation failures:

- targeted cards now use `legal_play_targets(hand_index)`
- Response cards are excluded from normal Main Phase play
- attacks now use `legal_attackers()` and `legal_attack_targets()`
- activated abilities are included in M3 action space
- pending target choices use the queued effect's source player

After extraction:

```powershell
py tools/apply_m3_1_hotfix.py
py -m pytest -q
py tools/run_simulation.py --games 10 --seed 42 --no-persist
```
