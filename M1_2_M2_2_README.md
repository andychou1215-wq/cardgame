# M1.2 + M2.2

## M1.2

Response Window is upgraded to alternating Priority:

Attack declaration → defender priority → Response/Pass → opponent priority → two consecutive Passes → LIFO stack resolution → combat.

Current `ally_becomes_attack_target` data still only permits the attacked Unit controller to use that response type. The other player still receives Priority and can Pass. Future response trigger types can reuse the same engine.

## M2.2

Adds a cross-game dashboard and analytics for:

- game count
- average turns
- P1/P2 win rate
- first-player win rate
- deck win rate
- card plays / responses / transforms / deaths
- event distribution
- game-length distribution

Data can be read from `playtest_data/` or uploaded manually.

## Apply

This expects M1.1 + M2.1 + hotfix to already be in your local repo.

```powershell
py tools/apply_m1_2_m2_2.py
py -m pytest -q
```

Run game:

```powershell
py -m streamlit run streamlit_app.py
```

Run analytics dashboard:

```powershell
py -m streamlit run playtest_dashboard.py
```
