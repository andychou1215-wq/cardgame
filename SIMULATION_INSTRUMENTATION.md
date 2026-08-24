# M3.7.3 simulation instrumentation

Add a board snapshot at the SAME location used for M3.7.1:
after the bot chooses END_TURN, but before execute_action(game, action).

Recommended helper in src/playtest/simulation.py:

```python
def _record_board_state_snapshot(game, actor):
    player = game.players[actor]

    # Adjust attribute names only if your Battlefield unit representation differs.
    units = list(getattr(player, "battlefield", []) or [])

    def unit_attack(unit):
        for name in ("attack", "atk", "current_attack"):
            if hasattr(unit, name):
                return int(getattr(unit, name) or 0)
        return 0

    def unit_health(unit):
        for name in ("health", "hp", "current_health"):
            if hasattr(unit, name):
                return int(getattr(unit, name) or 0)
        return 0

    # Prefer an explicit counter if one already exists.
    cards_played_total = int(
        getattr(player, "cards_played_total", 0) or 0
    )

    game.telemetry.record(
        "board_state_snapshot",
        turn=game.turn_number,
        active_player=game.active_player_index,
        player_index=actor,
        metadata={
            "unit_count": len(units),
            "board_attack": sum(unit_attack(u) for u in units),
            "board_health": sum(unit_health(u) for u in units),
            "cards_played_total": cards_played_total,
        },
    )
```

Then in the existing END_TURN block:

```python
if action.kind == END_TURN:
    # existing M3.7.1 turn_resource_snapshot
    ...

    # M3.7.3
    _record_board_state_snapshot(game, actor)
```

IMPORTANT:
`cards_played_total` needs a trustworthy cumulative value.
If PlayerState does not already maintain it, do NOT invent it.
Either:
1. add a small simulation-local counter keyed by player index and increment it
   whenever action.kind == PLAY_CARD; or
2. omit survival_conversion until the counter exists.

Recommended simulation-local approach:

```python
cards_played = [0, 0]
...
if action.kind == PLAY_CARD:
    cards_played[actor] += 1
...
if action.kind == END_TURN:
    _record_board_state_snapshot(
        game,
        actor,
        cards_played_total=cards_played[actor],
    )
```

and change the helper signature accordingly.

For M3.7.3, use fresh mirrored simulation telemetry, just like M3.7.1.
