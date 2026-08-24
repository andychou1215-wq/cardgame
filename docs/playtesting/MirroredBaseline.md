# Mirrored Baseline — M3.5.1

M3.5.1 separates three effects that were previously confounded:

```text
seat / first-player effect
deck strength
bot policy strength
```

For every mirror group, two games are run with the same game seed:

```text
A: D001 as P1, D002 as P2
B: D002 as P1, D001 as P2
```

The policy seat remains fixed inside one pairing. This lets the analysis compare
deck seats without changing the bot assignment at the same time.

Standard policy pairings remain:

- Random vs Random
- Heuristic vs Random
- Random vs Heuristic
- Heuristic vs Heuristic

Recommended smoke test:

```powershell
py tools/run_mirrored_baseline.py --mirror-groups-per-pairing 10 --seed 42
```

This means:

```text
4 policy pairings
× 10 mirror groups
× 2 games
= 80 games
```

A stronger baseline:

```powershell
py tools/run_mirrored_baseline.py --mirror-groups-per-pairing 100 --seed 42
```

Total:

```text
800 games
```

Outputs:

```text
m3_5_1_mirrored_games.csv
m3_5_1_pairing_summary.csv
m3_5_1_deck_summary.csv
m3_5_1_policy_summary.csv
m3_5_1_overall.json
```

Interpretation:

- Overall P1 win rate → seat/first-player signal
- Deck summary → deck-strength signal
- Policy summary → policy-strength signal
- Pairing summary → interaction between policy seats

Do not conclude balance from the 10-group smoke run. Use it to validate the
pipeline first, then move to 100+ mirror groups per pairing.
