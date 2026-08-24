# M3.4 Hotfix

Root cause of the failing unit test:

`HeuristicBot.score_action()` recursively called `legal_actions()` when scoring
`END_TURN`.

Fix:

```text
choose_action()
→ legal_actions() once
→ action_count
→ score_action(..., action_count=...)
```

This removes repeated legal-action enumeration and makes action scoring easier
to unit test with lightweight game doubles.

Apply / verify:

```powershell
py tools/apply_m3_4_hotfix.py
py -m pytest -q
py tools/run_baseline.py --games-per-pairing 10 --seed 42
```
