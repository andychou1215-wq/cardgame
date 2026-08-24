# M3.7.1 — Mana Curve Analysis implementation

## Files

- `src/playtest/mana_curve.py`: static + telemetry-backed curve analyzer.
- `tools/balance-tools/m3_7_1_mana_curve.py`: CLI/export entry point.
- `tests/balance/test_mana_curve.py`: core regression tests.
- `SIMULATION_INSTRUMENTATION.patch`: minimal `simulation.py` instrumentation required for runtime mana/dead-hand telemetry.

## Metrics

### Static

- deck size
- cards/copies by cost
- average / weighted median cost
- number of cards with cost <= 1/2/3
- probability that a 5-card opening hand contains >=1 card with cost <= turn mana (`opening_cost_playability_t1/t2/t3`)

The opening-hand metric is deliberately **cost-only**. It does not claim that a spell with target/board-state requirements is actually legal to play.

### Runtime telemetry

`turn_resource_snapshot` is emitted immediately before an AI chooses `END_TURN`.

- `avg_unused_mana`
- `mana_efficiency = sum(mana_spent) / sum(max_mana)`
- `dead_hand_rate`
- `avg_first_card_player_turn`
- `avg_cards_played_by_player_turn_3`

`dead_hand` means: hand is non-empty, mana remains, and the already-generated `legal_actions` list contains no `PLAY_CARD` or `ACTIVATE_ABILITY` action. Therefore target/board/usage constraints are included in the signal.

## Run

Static-only:

```bash
python tools/balance-tools/m3_7_1_mana_curve.py
```

With fresh telemetry:

```bash
python tools/balance-tools/m3_7_1_mana_curve.py \
  --summaries playtest_data/raw/<run>_game_summary.csv \
  --events playtest_data/raw/<run>_event_log.csv \
  --output playtest_data/analysis/m3_7_1
```

Exports:

- `mana_curve_by_cost.csv`
- `mana_curve_deck_summary.csv`
- `mana_curve_comparison.csv`
- `mana_curve.json`
- `mana_curve_report.txt`

## Validation

```bash
python -m pytest tests/balance/test_mana_curve.py -q
```
