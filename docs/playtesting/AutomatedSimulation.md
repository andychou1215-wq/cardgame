# Automated Simulation — M3

Start with:

```powershell
py tools/run_simulation.py --games 10 --seed 42
```

Then:

```powershell
py tools/run_simulation.py --games 100 --seed 42
```

Statuses:
- finished
- stalled
- invalid_legal_action
- action_limit

Random Bot is not intended to measure competitive skill. It is intended to find:
- impossible states
- non-terminating games
- legal-action gaps
- first-player structural advantage
- dead / never-used cards
- extreme game length
- broken matchup asymmetry

Only after this baseline is stable should a Heuristic Bot be added.
