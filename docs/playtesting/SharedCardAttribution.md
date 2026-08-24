# M3.5.4b Shared Card / Deck Attribution

M3.5.4b fixes a deck-relative analytics problem for cards that appear in more
than one deck.

Example:

```text
R001 exists in D001 and D002
```

Card-only aggregation incorrectly produces one global R001 win rate and then
compares that same number against both deck baselines.

That can create contradictory false signals.

## Attribution rules

### Unique card

If a card appears in one deck only:

```text
card_id
→ static deck membership
```

No game metadata is required.

### Shared card

If a card appears in multiple decks:

```text
card_id + game_id + player_index
→ game/player deck mapping
→ deck_id
```

A shared-card event is only used for deck-relative analysis when this mapping
is available.

If historical data lacks deck assignment metadata, the shared event is written
to:

```text
unattributed_shared_cards.csv
```

and deliberately excluded from deck-relative ranking.

This is preferable to duplicating one global metric across multiple decks.

## Historical compatibility

The mapping builder looks for common P1/P2 deck fields such as:

```text
deck_p1 / deck_p2
p1_deck / p2_deck
player1_deck / player2_deck
deck1 / deck2
```

in game summary or mirrored detail data.

If none exist, shared cards remain unattributed.

## Run

```powershell
py tools/rebuild_deck_attributed_telemetry.py
py tools/run_attributed_card_outliers.py
```

Outputs:

```text
playtest_data/analysis/m3_5_4b/
├─ deck_card_telemetry.csv
├─ unattributed_shared_cards.csv
├─ attribution_diagnostics.json
├─ attributed_all_cards.csv
├─ attributed_positive_outliers.csv
└─ attributed_negative_outliers.csv
```
