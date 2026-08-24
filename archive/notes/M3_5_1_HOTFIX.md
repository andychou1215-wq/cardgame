# M3.5.1 Hotfix

Problem:

A deck or policy with zero wins disappeared from summary output because
`_rate_by_value()` discovered values only from `winning_deck` / `winning_bot`.

Fix:

Summary dimensions are now discovered from all participants:

```text
deck_p1 + deck_p2
bot_p1 + bot_p2
```

Wins are still counted from:

```text
winning_deck
winning_bot
```

This guarantees zero-win rows remain visible with:

```text
wins = 0
win_rate = 0.0
```

Apply:

```powershell
py tools/apply_m3_5_1_hotfix.py
py -m pytest -q
py tools/run_mirrored_baseline.py --mirror-groups-per-pairing 10 --seed 42
```
