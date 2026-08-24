# Timing and Priority

## Trigger resolution

```text
Rules event
→ TriggerQueue
→ EffectQueue
→ Effect resolution
→ State-Based Check
```

Trigger events snapshot source identity and side so `on_leave` and `on_flip`
remain deterministic after the source moves or transforms.

## State-Based Check priority

1. simultaneous lethal Unit collection
2. enqueue `on_leave` using AP/NAP order
3. Transform checks
4. winner check

## Combat Priority Window

```text
Attack declared
→ defender gets Priority
→ Response / Pass
→ opponent gets Priority
→ ...
→ two consecutive Passes
→ Response stack resolves LIFO
→ combat resolves
```

If neither player has a legal Response, legacy direct `resolve_combat()` may
auto-pass the empty window.

## Deck-out

After setup, if a required draw cannot be completed because the deck is empty,
that player immediately loses.

Drawing the final card is legal; the loss happens on the next failed required draw.
