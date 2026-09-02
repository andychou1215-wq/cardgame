# M3.7.5 — Damage / Healing Profile

## Goal

M3.7.3 found that D001 controls fewer units but produces substantially higher
average board ATK. M3.7.4 showed that D001 does not Transform more often.

M3.7.5 asks:

> Does D001 convert that offensive density into substantially more leader
> damage, and how much do healing / lifesteal / max-HP synchronized healing
> offset incoming pressure?

## Important

The recorder already knows the intended event names, but current core paths do
not consistently emit them. Apply `GAME_INSTRUMENTATION.md` before collecting
fresh telemetry.

## Metrics

Per deck / game:

- combat damage to leader
- effect damage to leader
- total leader damage
- combat damage to units
- effect damage to units
- total damage
- combat/effect share of leader damage
- leader healing
- unit healing
- lifesteal healing
- ordinary effect healing
- max-health synchronized healing
- Transform max-health synchronized healing
- overheal
- healing efficiency
- blocked combat damage
- top leader-damage source cards

## Tests

```powershell
py -m pytest tests/balance/test_damage_healing.py -q
```

Expected: 2 passed.

Then:

```powershell
py -m pytest -q
```

## Fresh mirrored simulation

Use a new tag:

```powershell
$commit = git rev-parse --short HEAD

py tools/run_simulation.py `
  --games 2500 `
  --seed 37511 `
  --deck1 D001 `
  --deck2 D002 `
  --rules-version "v0.1.1-M3.7.5" `
  --commit-hash $commit

py tools/run_simulation.py `
  --games 2500 `
  --seed 37522 `
  --deck1 D002 `
  --deck2 D001 `
  --rules-version "v0.1.1-M3.7.5" `
  --commit-hash $commit
```

Filter by `rules_version`, then filter the event log by those game IDs, exactly
as in M3.7.1–M3.7.4.

## Run analyzer

```powershell
py tools/balance-tools/m3_7_5_damage_healing.py `
  --summaries playtest_data/analysis/m3_7_5/m375_game_summary.csv `
  --events playtest_data/analysis/m3_7_5/m375_event_log.csv `
  --output playtest_data/analysis/m3_7_5
```

## Outputs

- `damage_healing_by_game.csv`
- `damage_healing_deck_summary.csv`
- `damage_sources.csv`
- `healing_sources.csv`
- `damage_healing_comparison.csv`
- `damage_healing_report.txt`

Delete the large `m375_event_log.csv` after successful aggregation. Do not
commit raw telemetry.
