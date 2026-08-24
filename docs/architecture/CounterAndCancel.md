# Counter / Cancel — M1.4

M1.4 gives each Response Stack item an explicit `stack_item_id`.

A pending Stack item may be marked `cancelled`. Cancelled items remain in stack
history but skip effect resolution.

Resolution:

```text
StackItem
├─ cancelled → skip
├─ target invalid → fizzle
└─ otherwise → resolve
```

Telemetry:
- `stack_item_cancelled`
- `response_cancelled`
- `response_fizzled`
- `response_resolved`

The engine API is ready for future counter cards. The CSV operation that targets
a Stack item should be added only after its card-data schema is finalized.
