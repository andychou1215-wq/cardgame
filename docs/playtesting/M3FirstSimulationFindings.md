# M3 First Simulation Findings

First 10 Random Bot games:

```text
finished: 0
stalled: 0
invalid_legal_action: 10
action_limit: 0
```

The failures identified three Legal Action API defects:

1. targeted cards were offered without `legal_play_targets(hand_index)`;
2. Response cards were offered as normal `play_card` actions;
3. attack legality was duplicated in AI instead of using `Game.legal_attackers()`.

The hotfix changes M3's design rule to:

> AI enumerates decisions from authoritative Game legal helpers whenever such
> helpers already exist.

It also adds activated abilities to the action space using:
- `activated_options()`
- `legal_activation_targets()`
- `activate()`

Acceptance target for the next 10-game smoke run:

```text
invalid_legal_action: 0
```

Other statuses may still expose new engine/action-space gaps and should be fixed
before interpreting Random Bot balance data.
