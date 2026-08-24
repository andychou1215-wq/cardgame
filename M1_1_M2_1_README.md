# M1.1 + M2.1 Cumulative Implementation Pack

Target: public `main` reviewed on 2026-08-24.

This pack is cumulative: copy it over the current repo even if the previous M1/M2 pack was not applied.

## M1.1

- `TriggerQueue` between rules triggers and `EffectQueue`
- trigger side snapshot for `on_leave` / `on_flip`
- single `StateBasedCheck` checkpoint
- state order: simultaneous deaths → transform AP/NAP → winner
- Combat / Response / effect resolution converge on the same checkpoint

## M2.1

- 10 core Playtest scenarios (S001–S010)
- structured event telemetry
- `event_log.csv`
- `game_summary.csv`
- cross-game append helpers for future simulations
- Streamlit `📊 Playtest Data` panel
- CSV download buttons

## Apply

```bash
python tools/apply_m1_1_m2_1.py
pytest -q
streamlit run streamlit_app.py
```

## Acceptance

Existing `test_engine_smoke.py` through `test_engine_v5.py` should remain green, plus:

```bash
pytest -q tests/test_m1_1_m2_1_infrastructure.py
pytest -q tests/test_playtest_scenarios.py
```

## Scenarios

- S001 庇護限制攻擊目標
- S002 迴避不能被 Unit 攻擊
- S003 庇護 + 迴避
- S004 格檔減少戰鬥傷害
- S005 格檔不減效果傷害
- S006 吸血
- S007 最大生命 +X 同步治療
- S008 同批死亡
- S009 AP/NAP on_leave
- S010 Transform → on_flip back-side snapshot

## Scope boundary

M1.1 does not yet implement a full multi-response priority/stack system. That should be M1.2.
