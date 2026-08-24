# Balance Baseline — M3.5

Standard M3.5 baseline runs four pairings:

```text
Random vs Random
Heuristic vs Random
Random vs Heuristic
Heuristic vs Heuristic
```

Recommended smoke run:

```powershell
py tools/run_baseline.py --games-per-pairing 10
```

Stable baseline:

```powershell
py tools/run_baseline.py --games-per-pairing 100
```

Larger baseline:

```powershell
py tools/run_baseline.py --games-per-pairing 1000
```

Outputs:

```text
playtest_data/summaries/m3_baseline_games.csv
playtest_data/summaries/m3_baseline_summary.csv
```

Metrics:
- finished games
- P1/P2 win rate
- average turns
- average actions
- stalled
- invalid legal actions
- action limit

The first interpretation rule is:

> Heuristic-vs-Random performance tests policy strength; Random-vs-Random is the
> cleaner structural balance signal.

Do not treat Heuristic-vs-Heuristic win rate as a final competitive metagame.
