# M3.5.3 Card / Deck Diagnostics

## Deck structural summary

| Deck | Cards | Avg Cost | Units | Spells | Artifacts | Responses | Transformable | Unit Stats/Mana | Effects/Card | Keywords/Card |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| D001 | 25 | 3.04 | 17 | 3 | 2 | 3 | 17 | 2.04 | 1.24 | 0.28 |
| D002 | 25 | 2.80 | 15 | 5 | 2 | 3 | 15 | 2.09 | 1.48 | 0.12 |

## Mana curve

| Deck | 0-1 | 2 | 3 | 4 | 5 | 6+ |
|---|---:|---:|---:|---:|---:|---:|
| D001 | 3 | 9 | 7 | 2 | 0 | 4 |
| D002 | 6 | 9 | 2 | 2 | 4 | 2 |

## Highest front-side unit stat efficiency

| Deck | Card | Cost | ATK | HP | (ATK+HP)/Mana | Transform Gain |
|---|---|---:|---:|---:|---:|---:|
| D001 | U001 哥布林 | 1 | 1 | 2 | 3.0 | 0 |
| D002 | U007 小精靈 | 1 | 1 | 2 | 3.0 | 0 |
| D001 | U002 帝國騎士 | 2 | 2 | 3 | 2.5 | 0 |
| D002 | U008 精靈遊俠 | 2 | 2 | 3 | 2.5 | 0 |
| D001 | U006 飛龍 | 4 | 3 | 5 | 2.0 | 0 |
| D002 | U005 報童 | 1 | 1 | 1 | 2.0 | 0 |
| D001 | U011 遺跡石像 | 7 | 4 | 8 | 1.714 | 0 |
| D001 | U004 帝國盾衛 | 3 | 1 | 4 | 1.667 | 0 |
| D002 | U013 聖獸 | 6 | 3 | 7 | 1.667 | 0 |
| D001 | U003 游擊小隊 | 2 | 2 | 1 | 1.5 | 0 |
| D001 | U012 騎士團長 | 6 | 3 | 6 | 1.5 | 0 |
| D002 | U009 大樹守衛 | 5 | 2 | 5 | 1.4 | 0 |
| D002 | U010 慈愛精靈 | 3 | 1 | 3 | 1.333 | 0 |

## Telemetry capability

- Available: True
- `event_type`: yes
- `card_id`: yes
- `game_id`: yes
- `player_index`: yes
- `turn`: yes
- `winner_join`: yes

## Card telemetry

| Card | Draw | Play | Play/Draw | Avg Play Turn | Response | Transform | Win When Played |
|---|---:|---:|---:|---:|---:|---:|---:|
| S001 全力一擊 | 2459 | 2757 | 1.1212 | 7.3 | 0 | 0 | 0.0892 |
| U007 小精靈 | 2410 | 2670 | 1.1079 | 6.622 | 0 | 1908 | 0.0952 |
| U005 報童 | 2347 | 2658 | 1.1325 | 6.492 | 0 | 1750 | 0.094 |
| U008 精靈遊俠 | 2449 | 2536 | 1.0355 | 6.776 | 0 | 706 | 0.0999 |
| U001 哥布林 | 1478 | 1940 | 1.3126 | 6.114 | 0 | 809 | 0.9122 |
| U002 帝國騎士 | 1556 | 1891 | 1.2153 | 7.034 | 0 | 439 | 0.9036 |
| U003 游擊小隊 | 1485 | 1884 | 1.2687 | 6.849 | 0 | 56 | 0.9039 |
| S003 精靈鼓舞 | 1655 | 1573 | 0.9505 | 8.155 | 0 | 0 | 0.1033 |
| U010 慈愛精靈 | 1656 | 1560 | 0.942 | 7.574 | 0 | 132 | 0.0821 |
| A002 世界樹 | 1645 | 1417 | 0.8614 | 8.699 | 0 | 0 | 0.0826 |
| U009 大樹守衛 | 1653 | 1347 | 0.8149 | 8.816 | 0 | 593 | 0.0813 |
| S002 神聖防禦 | 1474 | 1286 | 0.8725 | 9.901 | 0 | 0 | 0.9651 |
| A001 石中劍 | 1006 | 1269 | 1.2614 | 7.646 | 0 | 0 | 0.8956 |
| U006 飛龍 | 1017 | 1222 | 1.2016 | 8.157 | 0 | 329 | 0.9309 |
| U013 聖獸 | 1663 | 1199 | 0.721 | 9.156 | 0 | 505 | 0.0844 |
| U004 帝國盾衛 | 960 | 1192 | 1.2417 | 7.42 | 0 | 1012 | 0.9279 |
| U012 騎士團長 | 988 | 1113 | 1.1265 | 9.412 | 0 | 804 | 0.9376 |
| U011 遺跡石像 | 1034 | 1012 | 0.9787 | 9.912 | 0 | 748 | 0.9585 |
| R001 反擊風暴 | 3882 | 0 | 0.0 |  | 3022 | 0 |  |

## Interpretation

- High printed stat efficiency is a diagnostic signal, not proof of an OP card.
- `win_rate_when_played` is correlation, not causal card strength.
- Compare D001 and D002 at deck level before changing individual cards.
- Cards with high draw but low play can indicate cost/target/tempo problems.
- Cards with high play plus unusually high win-when-played deserve targeted review.
- Missing telemetry fields are reported as unavailable rather than inferred.
