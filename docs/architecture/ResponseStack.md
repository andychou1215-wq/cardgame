# Response Stack — M1.3

M1.3 adds `StackItem` snapshots and resolution-time target revalidation.

Flow:

```text
Response played
→ StackItem
→ priority continues
→ top item resolves
→ target revalidation
→ resolve OR fizzle
```

Recognized response triggers:
- `ally_becomes_attack_target`
- `before_combat_damage`
- `response_to_response`
- `priority`

A fizzled response is not an exception. It is logged as `response_fizzled`.

`StackItem` also has a `cancelled` state, but no counter/cancel card operation is enabled yet because that targeting rule still needs a formal spec.
