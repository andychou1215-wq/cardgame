# M3.7.2 — Unit Stat Efficiency

## Goal

Test the hypothesis raised by M3.7.1:

> D001 has a worse mana curve, but may receive more base unit combat stats per Mana.

The first version deliberately does **not** assign arbitrary point values to
keywords or card effects.

## Core metrics

Per card / deck:

- Front ATK / Cost
- Front HP / Cost
- Front (ATK + HP) / Cost
- Back (ATK + HP) / Cost
- Transform ATK delta
- Transform HP delta
- Transform total-stat delta
- Transform stat gain %
- Front efficiency relative to same-cost unit baseline
- Effect count (annotation only)

## Why effects are not scored

Cards such as U012 can grant permanent ATK and Max HP to multiple allied units,
while U011 can spread Sanctuary-like protection. These are context-dependent
effects and should not be converted into a guessed fixed stat score in M3.7.2.

M3.7.2 therefore separates:
1. guaranteed printed body efficiency;
2. conditional Transform body value;
3. effect/keyword value (annotated, not scored).

## Files

Copy into the repository:

- `src/playtest/unit_stat_efficiency.py`
- `tools/balance-tools/m3_7_2_unit_stat_efficiency.py`
- `tests/balance/test_unit_stat_efficiency.py`

## Test

```powershell
py -m pytest tests/balance/test_unit_stat_efficiency.py -q
```

Expected:

```text
...                                                                      [100%]
3 passed
```

Then run the full suite:

```powershell
py -m pytest -q
```

## Run

```powershell
py tools/balance-tools/m3_7_2_unit_stat_efficiency.py
```

Outputs:

```text
playtest_data/analysis/m3_7_2/
├─ unit_stat_efficiency_by_card.csv
├─ unit_stat_efficiency_deck_summary.csv
├─ unit_stat_efficiency_cost_bands.csv
├─ unit_stat_efficiency_comparison.csv
├─ unit_stat_efficiency.json
└─ unit_stat_efficiency_report.txt
```

## Schema compatibility

The analyzer accepts the current project conventions:

- `cards.csv`: `id` is normalized to internal `card_id`
- `deck_cards.csv`: `deck_id, card_id, quantity`
- `unit_sides.csv`: requires `card_id, side` and accepts common stat aliases:
  - attack: `attack`, `atk`, `base_attack`
  - health: `health`, `hp`, `max_health`, `base_health`

This aliasing is limited to the analyzer boundary so the internal contract
remains `card_id / attack / health / quantity`.

## Interpretation

A positive `D001_minus_D002` for `avg_front_stats_per_mana` supports the
hypothesis that D001 converts Mana into more printed unit body despite having
the worse curve found in M3.7.1.

If D001 does not lead on base body efficiency, the next suspects become effect
packages, keywords, Transform payoff, and board-tempo conversion rather than
raw stats.
