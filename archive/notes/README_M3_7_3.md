# M3.7.3 — Tempo / Board Development

Question:

> D002 plays earlier and uses Mana better. Why does that not convert into winning board presence?

Metrics:

- average surviving unit count
- average board ATK
- average board HP
- T1–T3 board unit / ATK / HP
- first unit-count advantage
- first ATK advantage
- first HP advantage
- cards-played -> surviving-unit conversion

This requires NEW `board_state_snapshot` events.
Do not reuse old telemetry that predates the instrumentation.

## Files

- `src/playtest/tempo_board.py`
- `tools/balance-tools/m3_7_3_tempo_board.py`
- `tests/balance/test_tempo_board.py`
- `SIMULATION_INSTRUMENTATION.md`

## Tests

```powershell
py -m pytest tests/balance/test_tempo_board.py -q
```

Expected: 2 passed.

Then:

```powershell
py -m pytest -q
```

## Analyzer

After a fresh mirrored simulation:

```powershell
py tools/balance-tools/m3_7_3_tempo_board.py `
  --summaries playtest_data/analysis/m3_7_3/m373_game_summary.csv `
  --events playtest_data/analysis/m3_7_3/m373_event_log.csv `
  --output playtest_data/analysis/m3_7_3
```

Important:
Raw M3.7.3 event logs can become hundreds of MB.
Keep raw event logs out of Git; commit only the aggregated analysis outputs.
