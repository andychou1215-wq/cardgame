# Legal Action API — M3

M3 introduces one decision boundary for UI, bots, tests, and future networking.

```text
Game state
→ legal_actions(game, player)
→ GameAction[]
→ choose
→ execute_action(game, action)
→ new state
```

Action kinds:
- play_card
- declare_attack
- play_response
- pass_priority
- resolve_combat
- end_turn
- choose_target

`execute_action()` uses public Game APIs only.

If `legal_actions()` returns an action rejected by the engine, batch simulation
records `invalid_legal_action`; this is considered an API defect rather than
something the bot should silently retry.
