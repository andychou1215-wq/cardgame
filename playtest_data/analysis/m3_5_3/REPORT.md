# M3.5.3 Card / Deck Diagnostics

## Deck structural summary

| Deck | Cards | Avg Cost | Units | Spells | Artifacts | Responses | Transformable | Unit Stats/Mana | Effects/Card | Keywords/Card |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| D001 | 25 | 3.16 | 17 | 3 | 2 | 3 | 17 | 2.03 | 1.24 | 0.28 |
| D002 | 25 | 2.80 | 15 | 5 | 2 | 3 | 15 | 2.09 | 1.48 | 0.12 |

## Mana curve

| Deck | 0-1 | 2 | 3 | 4 | 5 | 6+ |
|---|---:|---:|---:|---:|---:|---:|
| D001 | 3 | 9 | 4 | 5 | 0 | 4 |
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
| D001 | U004 帝國盾衛 | 3 | 1 | 4 | 1.667 | 0 |
| D002 | U013 聖獸 | 6 | 3 | 7 | 1.667 | 0 |
| D001 | U011 遺跡石像 | 7 | 4 | 7 | 1.571 | 0 |
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
| S001 全力一擊 | 1813 | 2025 | 1.1169 | 7.518 | 0 | 0 | 0.1003 |
| U007 小精靈 | 1762 | 2008 | 1.1396 | 6.678 | 0 | 1455 | 0.1048 |
| U005 報童 | 1755 | 1945 | 1.1083 | 6.911 | 0 | 1286 | 0.1023 |
| U008 精靈遊俠 | 1801 | 1880 | 1.0439 | 6.999 | 0 | 539 | 0.1087 |
| U002 帝國騎士 | 1125 | 1444 | 1.2836 | 6.641 | 0 | 324 | 0.9031 |
| U003 游擊小隊 | 1116 | 1436 | 1.2867 | 6.62 | 0 | 31 | 0.8908 |
| U001 哥布林 | 1042 | 1380 | 1.3244 | 5.964 | 0 | 533 | 0.9051 |
| S003 精靈鼓舞 | 1217 | 1142 | 0.9384 | 8.49 | 0 | 0 | 0.1137 |
| U010 慈愛精靈 | 1195 | 1132 | 0.9473 | 7.635 | 0 | 101 | 0.0902 |
| A002 世界樹 | 1191 | 1051 | 0.8825 | 8.986 | 0 | 0 | 0.0882 |
| U009 大樹守衛 | 1211 | 1009 | 0.8332 | 9.081 | 0 | 479 | 0.0882 |
| A001 石中劍 | 722 | 923 | 1.2784 | 7.372 | 0 | 0 | 0.8961 |
| U004 帝國盾衛 | 732 | 919 | 1.2555 | 7.471 | 0 | 778 | 0.9193 |
| U013 聖獸 | 1236 | 871 | 0.7047 | 9.542 | 0 | 363 | 0.0877 |
| U006 飛龍 | 687 | 867 | 1.262 | 7.882 | 0 | 236 | 0.9112 |
| U012 騎士團長 | 739 | 823 | 1.1137 | 9.163 | 0 | 556 | 0.9322 |
| U011 遺跡石像 | 759 | 725 | 0.9552 | 9.939 | 0 | 508 | 0.9507 |
| S002 神聖防禦 | 1056 | 706 | 0.6686 | 9.952 | 0 | 0 | 0.9721 |
| R001 反擊風暴 | 2924 | 0 | 0.0 |  | 2239 | 0 |  |

## Interpretation

- High printed stat efficiency is a diagnostic signal, not proof of an OP card.
- `win_rate_when_played` is correlation, not causal card strength.
- Compare D001 and D002 at deck level before changing individual cards.
- Cards with high draw but low play can indicate cost/target/tempo problems.
- Cards with high play plus unusually high win-when-played deserve targeted review.
- Missing telemetry fields are reported as unavailable rather than inferred.
