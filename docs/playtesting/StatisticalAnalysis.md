# M3.5.2 Statistical Analysis

M3.5.2 analyzes M3.5.1 mirrored game output without changing the simulation
engine.

Input:

```text
playtest_data/summaries/m3_5_1_mirrored_games.csv
```

Run:

```powershell
py tools/run_statistical_analysis.py
```

Outputs:

```text
playtest_data/analysis/m3_5_2/
├─ deck_overall.csv
├─ deck_by_seat.csv
├─ deck_by_pairing.csv
├─ heuristic_h2h_by_seat.csv
├─ heuristic_h2h_by_deck.csv
├─ pairing_health.csv
├─ summary.json
└─ REPORT.md
```

## Analyses

### Deck × Seat

Separates:

```text
D001 as P1
D001 as P2
D002 as P1
D002 as P2
```

This is the main check for distinguishing deck strength from first-player
advantage.

### Deck × Policy Pairing

For every policy pairing:

```text
random_vs_random
heuristic_vs_random
random_vs_heuristic
heuristic_vs_heuristic
```

the report calculates each deck's win rate.

### Heuristic vs Random Head-to-Head

Only cross-policy games are included:

```text
heuristic_vs_random
random_vs_heuristic
```

Same-policy games are excluded because they mathematically force that policy to
receive one win per finished game and therefore dilute the policy-strength
signal.

### Confidence intervals

M3.5.2 uses a 95% Wilson score interval for binomial win rates. This is more
useful than displaying only a raw percentage, especially for small smoke-test
samples.

Confidence intervals represent sampling uncertainty. They do not remove
systematic bias from card pools, bot policy design, or game-state coverage.
