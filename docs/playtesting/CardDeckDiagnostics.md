# M3.5.3 Card / Deck Diagnostics

M3.5.3 answers:

> Is the deck imbalance caused by the whole deck's structural efficiency or by
> a small number of cards/effects?

It does not modify game rules or bot policy.

## Static sources

```text
data/cards/cards.csv
data/cards/unit_sides.csv
data/cards/effects.csv
data/decks/deck_cards.csv
data/decks/decks.csv
```

## Static diagnostics

- weighted average mana cost
- mana curve
- card-type distribution
- front-side unit `(ATK + HP) / Mana`
- back-side transform stat gain
- transform density
- keyword density
- effect density
- operation distribution
- trigger distribution

## Telemetry diagnostics

When `playtest_data/raw/event_log.csv` exists, the analyzer capability-detects
its schema and attempts:

- draw count
- play count
- play / draw rate
- average play turn
- response frequency
- transform frequency
- effect-damage event count
- heal event count
- win rate when played, only when game/player/winner fields can be joined

Missing fields are explicitly marked unavailable.

`win_rate_when_played` is association, not causal proof of card power.

## Run

```powershell
py tools/run_card_deck_diagnostics.py
```

Outputs:

```text
playtest_data/analysis/m3_5_3/
├─ deck_summary.csv
├─ mana_curve.csv
├─ card_efficiency.csv
├─ effect_profile.csv
├─ keyword_profile.csv
├─ card_telemetry.csv
├─ telemetry_capabilities.json
├─ data_quality.csv
└─ REPORT.md
```

Use the deck-level outputs first. Only after identifying structural differences
should individual cards be proposed for balance changes.
