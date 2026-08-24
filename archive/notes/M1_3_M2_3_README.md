# M1.3 + M2.3

M1.3:
- StackItem
- target revalidation
- fizzle semantics
- response-to-response trigger infrastructure
- response_resolved / response_fizzled telemetry

M2.3:
- PlaytestStore
- aggregate CSV persistence
- replay JSON/index foundation
- matchup matrix
- per-card draw/play/win association
- card_drawn telemetry when `_draw_cards()` is present

Apply:
```powershell
py tools/apply_m1_3_m2_3.py
py -m pytest -q
```

This pack does not force automatic save from the Streamlit game-end rerun yet; that hook should be added only after confirming the exact current UI lifecycle so completed games are not persisted twice.
