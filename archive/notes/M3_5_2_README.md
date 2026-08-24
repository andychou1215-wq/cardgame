# M3.5.2

Adds:

- Deck × Seat analysis
- Deck × Policy Pairing analysis
- Heuristic vs Random true head-to-head
- Heuristic H2H by seat
- Heuristic H2H by controlled deck
- 95% Wilson confidence intervals
- Engine/pairing health summary
- Markdown report generation

Apply / verify:

```powershell
py tools/apply_m3_5_2.py
py -m pytest -q
```

Analyze the latest M3.5.1 mirrored run:

```powershell
py tools/run_statistical_analysis.py
```

For the more meaningful formal baseline, first run:

```powershell
py tools/run_mirrored_baseline.py --mirror-groups-per-pairing 100 --seed 42
py tools/run_statistical_analysis.py
```

This analyzes 800 mirrored games.
