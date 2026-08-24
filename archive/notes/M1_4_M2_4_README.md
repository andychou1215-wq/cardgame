# M1.4 + M2.4

M1.4:
- explicit `stack_item_id`
- stack target/cancel manager
- cancelled items skip resolution
- cancellation telemetry

M2.4:
- idempotent game-end persistence guard
- rules/commit version comparison
- balance report CSV export
- dashboard integration

Apply:

```powershell
py tools/apply_m1_4_m2_4.py
py -m pytest -q
```
