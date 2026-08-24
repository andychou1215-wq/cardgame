# M3.5.4a Telemetry Metric Fix

M3.5.4a fixes metric semantics discovered during M3.5.4 analysis.

## Problem 1: Response cards showed zero plays

Response cards use:

```text
response_played
```

rather than:

```text
card_played
```

M3.5.4a now separates:

```text
normal_play_events
response_play_events
use_events = normal + response
```

## Problem 2: Play / Draw exceeded 100%

The previous metric was named:

```text
play_given_draw_rate
```

but the numerator included uses while the denominator only counted explicit
`card_drawn` events.

Initial hand and Mulligan acquisitions may not be represented in the event log,
so the ratio may exceed 1.

The corrected name is:

```text
uses_per_recorded_draw
```

It is a diagnostic ratio, not a probability.

## Acquisition completeness

The rebuilt telemetry reports whether these event families exist:

```text
initial_hand_event
mulligan_acquisition_event
recorded_draw_is_complete_hand_acquisition
```

If starting-hand and Mulligan acquisition events do not exist, the tool does
not pretend that recorded draws represent all cards obtained by the player.

## Compatibility

For M3.5.4 compatibility, the rebuilt CSV still emits deprecated aliases:

```text
draw_events
play_events
play_given_draw_rate
avg_play_turn
games_played
wins_when_played
win_rate_when_played
response_events
```

Their values now use corrected `use_events` semantics where appropriate.

## Run

```powershell
py tools/rebuild_card_telemetry.py
py tools/run_card_outliers.py
```
