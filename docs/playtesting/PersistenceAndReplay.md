# Persistence and Replay — M2.3

`PlaytestStore` writes:

```text
playtest_data/
├─ raw/event_log.csv
├─ summaries/game_summary.csv
└─ replays/<game_id>.json
```

Replay JSON is currently an event record, not deterministic engine re-simulation.

M2.3 analytics add:
- matchup matrix
- games drawn / played per card
- response and transform usage
- win rate when played
- play-given-draw rate

`win_rate_when_played` is observational correlation, not causal power.

Future exact replay should reconstruct from:
rules/data version + seed + action sequence.
