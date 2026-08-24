# M3.5.3

Adds Card / Deck Diagnostics without modifying the stable M3 simulation engine.

Apply / verify:

```powershell
py tools/apply_m3_5_3.py
py -m pytest -q
```

Run:

```powershell
py tools/run_card_deck_diagnostics.py
```

Primary outputs to inspect:

```text
deck_summary.csv
mana_curve.csv
card_efficiency.csv
effect_profile.csv
keyword_profile.csv
card_telemetry.csv
REPORT.md
```

Interpretation order:

1. Deck structural difference
2. Mana curve
3. Unit stats-per-mana
4. Transform gain
5. Keyword/effect density
6. Card telemetry
7. Only then propose balance changes
