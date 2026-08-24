# M3.5.1 — Seat / Deck Mirroring

Adds:
- mirrored deck seats
- paired game seeds
- deck win-rate summary
- policy win-rate summary
- pairing summary
- overall first-player rate

Run:

```powershell
py -m pytest -q
py tools/run_mirrored_baseline.py --mirror-groups-per-pairing 10 --seed 42
```

Expected smoke volume:

```text
80 games
```

If stable:

```powershell
py tools/run_mirrored_baseline.py --mirror-groups-per-pairing 100 --seed 42
```

Expected:

```text
800 games
```
