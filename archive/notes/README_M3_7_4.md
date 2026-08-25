# M3.7.4 — Transform Efficiency

## Question

M3.7.2 showed no printed-stat gain from Transform, while M3.7.3 showed D001
developing unusually high average board attack despite fewer units.

M3.7.4 tests whether Transform frequency / timing / on-flip triggers correlate
with that advantage.

## Existing telemetry is enough

The engine already records:

- `card_played`
- `transform`
- `trigger` with metadata `trigger=on_flip`

Therefore this first version does not require new simulation instrumentation.

## Metrics

Per card:

- unique played instances
- unique transformed instances
- Transform rate per play
- average Transform turn
- games with Transform
- win rate when that card transformed
- delta vs overall deck win rate
- on-flip trigger count
- on-flip trigger / transform

Per deck:

- total Transform rate per played card instance
- weighted average Transform turn
- number of transforming card types
- total on-flip trigger count
- outcome split:
  - games where deck transformed at least once
  - games where deck did not Transform

## Important statistical warning

`WR_when_transformed` is association, not proof of causal card strength.
A deck may Transform more often simply because it survives longer.

Use M3.7.4 as diagnosis, then combine with M3.7.3 board metrics and later
effect attribution.

## Tests

```powershell
py -m pytest tests/balance/test_transform_efficiency.py -q
```

Expected: 2 passed.

Then full regression:

```powershell
py -m pytest -q
```

## Run

Use a clean mirrored telemetry dataset:

```powershell
py tools/balance-tools/m3_7_4_transform_efficiency.py `
  --summaries playtest_data/analysis/m3_7_4/m374_game_summary.csv `
  --events playtest_data/analysis/m3_7_4/m374_event_log.csv `
  --output playtest_data/analysis/m3_7_4
```

If you still have the clean M3.7.3 5,000-game telemetry and it already contains
the built-in `transform` / `trigger` events, you may reuse it rather than run
another simulation.

## Outputs

- transform_by_card.csv
- transform_deck_summary.csv
- transform_by_game.csv
- transform_outcome_summary.csv
- transform_comparison.csv
- transform_report.txt

Do not commit the large raw event log. Commit only the aggregated outputs.
