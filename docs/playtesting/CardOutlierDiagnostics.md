# M3.5.4 Card Performance / Outlier Diagnostics

M3.5.4 compares each card against its own deck's baseline win rate.

This matters because a card in an 89.8% deck should not be called overpowered
merely because its win-when-played rate is around 90%.

## Main metric

```text
win_rate_delta_vs_deck
=
win_rate_when_played
-
deck_baseline_win_rate
```

Examples:

```text
D001 baseline = 89.8%
Card A WR played = 91.0%
Delta = +1.2 percentage points
```

This is much less suspicious than:

```text
Card B WR played = 98.0%
Delta = +8.2 percentage points
```

For D002:

```text
D002 baseline = 10.2%
Card C WR played = 22.0%
Delta = +11.8 percentage points
```

Even though 22% looks weak in absolute terms, it may be one of D002's strongest
cards relative to its deck environment.

## Outputs

```text
playtest_data/analysis/m3_5_4/
├─ all_cards.csv
├─ positive_outliers.csv
├─ negative_outliers.csv
├─ high_draw_low_play.csv
├─ high_usage.csv
├─ response_frequency.csv
├─ transform_frequency.csv
├─ effect_damage_frequency.csv
├─ heal_frequency.csv
└─ REPORT.md
```

## Outlier score

The score combines:

- delta vs own deck baseline
- draw/play sample volume
- play-after-draw rate

It is intended for triage only.

It is not a causal card-power estimate.

## Recommended interpretation

Positive outlier:
- high volume
- high play-after-draw
- positive deck-relative delta
- inspect effect/keyword/cost manually

Negative outlier:
- may be inefficient
- may be a desperation play
- may be used too late
- inspect average play turn

High draw / low play:
- expensive
- conditional
- target constrained
- bad tempo
- or current bot undervalues / cannot sequence it well
