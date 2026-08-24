# Heuristic Bot — M3.4

M3.4 keeps legality and policy separate:

```text
Game
→ legal_actions()
→ HeuristicBot.score_action()
→ choose highest score
→ execute_action()
```

The first heuristic policy values:

- lethal leader attacks
- favorable unit trades
- playing cards
- using mana
- activated abilities
- responses
- attacking the leader

It penalizes:

- ending the turn while useful actions remain
- unfavorable combat trades
- unnecessary priority pass

Weights live in `HeuristicWeights`, so future tuning does not require rewriting
the policy.

This bot is intentionally shallow. It does not search future turns.
