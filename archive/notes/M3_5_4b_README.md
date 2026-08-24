# M3.5.4b

Fixes shared-card deck attribution.

Problem observed:

```text
D002 R001 delta +69.1%
D001 R001 delta -10.4%
```

Both were derived from the same global R001 telemetry and therefore were not
valid deck-relative conclusions.

M3.5.4b:

- identifies shared cards from static deck membership;
- attributes shared events only through `game_id + player_index -> deck_id`;
- keeps unique cards attributable through static membership;
- excludes unresolved shared cards instead of duplicating them;
- produces deck+card keyed telemetry and outlier files.

Apply:

```powershell
py tools/apply_m3_5_4b.py
py -m pytest -q
```

Rebuild:

```powershell
py tools/rebuild_deck_attributed_telemetry.py
```

Then:

```powershell
py tools/run_attributed_card_outliers.py
```

If historical summaries do not contain P1/P2 deck assignments, R001 may appear
in `unattributed_shared_cards.csv`. That is expected and safer than false
attribution.
