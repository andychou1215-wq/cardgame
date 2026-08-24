# M3.5.2 Statistical Analysis

## Engine / simulation health

- Games: 800
- Finished: 800 (100.0%)
- Invalid legal action: 0
- Stalled: 0
- Action limit: 0
- Average turns: 12.48
- Average actions: 153.52

## Seat signal

- P1 win rate: 51.0% (95% CI 47.5%–54.5%)

## Deck overall

| Deck | Wins | Games | Win Rate | 95% CI |
|---|---:|---:|---:|---:|
| D001 | 718 | 800 | 89.8% | 87.5%–91.7% |
| D002 | 82 | 800 | 10.2% | 8.3%–12.5% |

## Deck × Seat

| Deck | Seat | Wins | Games | Win Rate | 95% CI |
|---|---|---:|---:|---:|---:|
| D001 | P1 | 363 | 400 | 90.8% | 87.5%–93.2% |
| D001 | P2 | 355 | 400 | 88.8% | 85.3%–91.5% |
| D002 | P1 | 45 | 400 | 11.2% | 8.5%–14.7% |
| D002 | P2 | 37 | 400 | 9.2% | 6.8%–12.5% |

## Heuristic vs Random — head-to-head only

- Heuristic win rate: 48.5% (194/400, 95% CI 43.6%–53.4%)

### By Heuristic seat

| Heuristic Seat | Wins | Games | Win Rate | 95% CI |
|---|---:|---:|---:|---:|
| P1 | 98 | 200 | 49.0% | 42.2%–55.9% |
| P2 | 96 | 200 | 48.0% | 41.2%–54.9% |

### By deck controlled by Heuristic

| Heuristic Deck | Wins | Games | Win Rate | 95% CI |
|---|---:|---:|---:|---:|
| D001 | 178 | 200 | 89.0% | 83.9%–92.6% |
| D002 | 16 | 200 | 8.0% | 5.0%–12.6% |

## Interpretation guidance

- Seat balance: treat P1 rate as a seat signal only after deck mirroring.
- Deck strength: compare both overall deck rate and Deck × Seat rows.
- Policy strength: use cross-policy H-vs-R only; exclude R-vs-R and H-vs-H.
- Confidence intervals describe sampling uncertainty, not all sources of bias.
- Do not rebalance individual cards from one aggregate result; use card-level telemetry next.
