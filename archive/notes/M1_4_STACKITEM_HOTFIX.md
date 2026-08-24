# M1.4 StackItem Compatibility Hotfix

Cause:

M1.4 inserted `stack_item_id` before the original M1.3 required fields.
That broke positional callers such as:

```python
StackItem("s", "R1", 1, [], "response_to_response")
```

Fix:

The required field order is restored:

```text
source_id
card_id
controller_index
effects
trigger
```

M1.4 fields follow afterward:

```text
stack_item_id=""
trigger_target=None
metadata={}
```

If `stack_item_id` is omitted, one is automatically generated.

The M1.4 engine already creates StackItem with keyword arguments, so this change
preserves both old and new call styles.
