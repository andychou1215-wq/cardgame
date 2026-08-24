# M3.5.2 Statistical Analysis

## Engine / simulation health

- Games: 800
- Finished: 800 (100.0%)
- Invalid legal action: 0
- Stalled: 0
- Action limit: 0
- Average turns: 12.49
- Average actions: 154.17

## Seat signal

- P1 win rate: 52.0% (95% CI 48.5%–55.4%)

## Deck overall

| Deck | Wins | Games | Win Rate | 95% CI |
|---|---:|---:|---:|---:|
| D001 | 714 | 800 | 89.2% | 86.9%–91.2% |
| D002 | 86 | 800 | 10.8% | 8.8%–13.1% |

## Deck × Seat

| Deck | Seat | Wins | Games | Win Rate | 95% CI |
|---|---|---:|---:|---:|---:|
| D001 | P1 | 365 | 400 | 91.2% | 88.1%–93.6% |
| D001 | P2 | 349 | 400 | 87.2% | 83.6%–90.2% |
| D002 | P1 | 51 | 400 | 12.8% | 9.8%–16.4% |
| D002 | P2 | 35 | 400 | 8.8% | 6.4%–11.9% |

## Heuristic vs Random — head-to-head only

- Heuristic win rate: 49.5% (198/400, 95% CI 44.6%–54.4%)

### By Heuristic seat

| Heuristic Seat | Wins | Games | Win Rate | 95% CI |
|---|---:|---:|---:|---:|
| P1 | 102 | 200 | 51.0% | 44.1%–57.8% |
| P2 | 96 | 200 | 48.0% | 41.2%–54.9% |

### By deck controlled by Heuristic

| Heuristic Deck | Wins | Games | Win Rate | 95% CI |
|---|---:|---:|---:|---:|
| D001 | 182 | 200 | 91.0% | 86.2%–94.2% |
| D002 | 16 | 200 | 8.0% | 5.0%–12.6% |

## Interpretation guidance

- Seat balance: treat P1 rate as a seat signal only after deck mirroring.
- Deck strength: compare both overall deck rate and Deck × Seat rows.
- Policy strength: use cross-policy H-vs-R only; exclude R-vs-R and H-vs-H.
- Confidence intervals describe sampling uncertainty, not all sources of bias.
- Do not rebalance individual cards from one aggregate result; use card-level telemetry next.
