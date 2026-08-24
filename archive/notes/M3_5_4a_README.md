# M3.5.4a

Fixes telemetry metric semantics before M3.6 balance work.

Changes:

- Response usage is counted.
- Normal play and Response play are separated.
- Unified `use_events` is added.
- `Play/Draw` is renamed conceptually to `uses_per_recorded_draw`.
- Starting-hand and Mulligan acquisition coverage is capability-detected.
- Legacy M3.5.4 columns remain for compatibility.

Apply:

```powershell
py tools/apply_m3_5_4a.py
py -m pytest -q
```

Rebuild telemetry:

```powershell
py tools/rebuild_card_telemetry.py
```

Then rerun outliers:

```powershell
py tools/run_card_outliers.py
```

Do not interpret ratios above 1 as probabilities unless complete hand
acquisition telemetry exists.
