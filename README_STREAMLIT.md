# 卡牌對決 Streamlit Prototype v2

此版本在第一版 MVP 上加入 **Combat + Transform + effects.csv Resolver**。

## 已支援

- D001 / D002 牌組載入、洗牌、起手牌與 Hot-seat
- Leader HP、Mana、手牌、戰場、Artifact 區
- Unit / Spell / Artifact 出牌
- 單位攻擊單位或 Leader
- Response Window（目前可處理 R001 類型）
- 單位死亡、墓地、`on_leave`
- Transform 自動判定與 `on_flip`
- Transform counters：
  - `attack_count`
  - `kill_count`
  - `total_damage_taken`
  - `turn_count`
  - `total_damage_dealt`
  - `heal_count`
  - `unit_count_at_least`
  - `leader_health_at_or_below`
- effects.csv triggers：`on_play`、`on_enter`、`on_flip`、`on_leave`、`manual`、`ally_becomes_attack_target`
- operations：`damage`、`heal`、`draw`、`modify_attack`、`modify_max_health`、`add_keyword`
- durations：`instant`、`permanent`、`until_turn_end`、`until_attack_end`、`until_opponent_turn_end`
- `target_filter` 的 keyword / exclude:self 基本過濾
- 一回合一次 activated ability
- Game Log

## Prototype 假設

repo 的戰鬥規則目前明確定義：可攻擊敵方單位或玩家、傷害保留、每回合攻擊一次、剛進場不能攻擊。
但尚未明確寫出單位互打時是否會反擊，因此 v2 暫採「攻擊者與防守單位同時互相造成自身攻擊力的傷害」。此行為集中在 `Game.resolve_combat()`，之後規則確定時可以替換。

`迅擊` 在本 Prototype 暫視為「可在進場回合攻擊」。`庇護` 已能被效果系統辨識與加上，但其完整攻擊限制不在目前 repo 戰鬥規則文字內，因此 v2 不自行推定。

## 安裝

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

PowerShell 執行原則造成啟用失敗時：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

## 建議放置位置

將壓縮包內容直接合併到 cardgame repo 根目錄：

```text
cardgame/
├─ data/
├─ docs/
├─ src/
│  ├─ cards/
│  ├─ core/
│  ├─ deck/
│  ├─ effects/
│  └─ ui/
├─ tests/
├─ streamlit_app.py
├─ requirements.txt
└─ README_STREAMLIT.md
```

## 下一階段

建議依序補：庇護正式戰鬥規則、Artifact durability、Apocalypse、完整 Response chain、Mulligan、勝負/牌庫耗盡規則，以及 AI vs AI batch simulation。

## 隨附 effects.csv 修正

目前 repo 的 `unit_sides.csv` 對 U009「大樹守衛」寫的是翻面後同時獲得臨時〖庇護〗與「最大生命值永久 +1」，但目前 `effects.csv` 只有前一段效果。此 Prototype 在 `data/cards/effects.csv` 隨附 E027 作為第二段 `on_flip` effect，讓資料驅動結算與卡面文字一致。
