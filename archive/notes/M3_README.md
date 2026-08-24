# M3 — Automated Playtesting

Included:
- M3.1 Legal Action API
- M3.2 Random Bot
- M3.3 Batch Simulation foundation

Apply:

```powershell
py tools/apply_m3.py
py -m pytest -q
py tools/run_simulation.py --games 10 --seed 42
```

The first expected debugging cycle is to fix any `invalid_legal_action` result.
That feedback is the purpose of M3.1.
