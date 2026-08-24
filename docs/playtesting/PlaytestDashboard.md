# Playtest Dashboard

Entry point:

```powershell
py -m streamlit run apps/playtest_dashboard.py
```

The dashboard can read:
- CSV files under `playtest_data/`
- manually uploaded `game_summary.csv`
- manually uploaded `event_log.csv`

Current metrics:
- games
- average turns
- P1/P2 win rate
- first-player win rate
- deck win rate
- card usage
- response usage
- transform/death counts
- event distribution
- game-length distribution
