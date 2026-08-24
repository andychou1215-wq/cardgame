# M3.5.4

Adds deck-relative card performance diagnostics.

Prerequisites:

```text
M3.5.2 deck_overall.csv
M3.5.3 card_telemetry.csv
M3.5.3 card_efficiency.csv
```

Apply:

```powershell
py tools/apply_m3_5_4.py
py -m pytest -q
```

Run:

```powershell
py tools/run_card_outliers.py
```

Primary outputs:

```text
positive_outliers.csv
negative_outliers.csv
high_draw_low_play.csv
response_frequency.csv
transform_frequency.csv
REPORT.md
```

Use `win_rate_delta_vs_deck`, not raw `win_rate_when_played`, when comparing
cards from D001 and D002.
