# M3.4 + M3.5

## M3.4
Adds `HeuristicBot` with explainable weighted action scoring.

## M3.5
Adds standard four-pairing balance baseline:
- random vs random
- heuristic vs random
- random vs heuristic
- heuristic vs heuristic

Run tests:

```powershell
py -m pytest -q
```

Smoke baseline:

```powershell
py tools/run_baseline.py --games-per-pairing 10 --seed 42
```

Then:

```powershell
py tools/run_baseline.py --games-per-pairing 100 --seed 42
```

Use `--persist` only for baseline runs you intentionally want added to the M2
playtest data store.
