# Card Game
現在版本: **v0.1.1**。  

一款原創 1v1 卡牌對決遊戲。

目前專案已從早期規則設計階段進入 **可執行 Prototype / 規則引擎開發階段**，以 CSV 作為卡牌與效果資料來源，並使用 Python + Streamlit 建立可互動的數位測試環境。

## 專案狀態

目前已具備可進行核心對戰測試的 Prototype，主要包含：

- 牌組載入、洗牌、起手牌與 Mulligan
- Leader、Mana、手牌、戰場與墓地狀態
- Unit 出牌與戰鬥
- Unit → Unit 與 Unit → Leader 攻擊
- 進場限制與每回合攻擊次數
- Transform（單位翻面）條件與效果
- Response Window
- `effects.csv` 驅動的卡牌效果結算
- 同批死亡與 `on_leave` 觸發時序
- 勝負判定
- Streamlit Hot-seat 雙人測試介面

目前不使用 Apocalypse 系統。

## 核心目標

- 建立原創且可擴充的 1v1 卡牌戰鬥系統
- 透過不同陣營建立明確的牌組策略與玩法特色
- 將卡牌、效果、牌組與規則資料結構化，供程式直接讀取
- 建立可重複測試的數位 Prototype，取代紙本 Playtest
- 逐步完善戰鬥時序、觸發規則與卡牌平衡
- 為後續 AI vs AI 模擬與大量對局統計保留擴充空間

## 已實作的核心規則

### 戰鬥

- Unit 可以攻擊敵方 Unit 或 Leader
- Unit 一般情況下進場當回合不能攻擊
- Unit 每回合原則上只能攻擊一次
- Unit 對 Unit 戰鬥時，雙方進行戰鬥傷害結算
- 傷害會保留，直到被治療、效果修改或單位離場
- Leader 生命值降至 0 時判定敗北

### Transform

目前 Prototype 支援多種翻面條件，包括：

- `attack_count`
- `kill_count`
- `total_damage_taken`
- `turn_count`
- `total_damage_dealt`
- `heal_count`
- `unit_count_at_least`
- `leader_health_at_or_below`

符合條件後，Unit 可翻至反面並觸發對應 `on_flip` 效果。

### 關鍵字

目前戰鬥引擎已支援：

- **〖迅擊〗**：允許符合規則的單位提早進行攻擊
- **〖庇護〗**：若防守方存在具有〖庇護〗的合法單位，敵方 Unit 必須優先攻擊這些單位
- **〖迴避〗**：持有〖迴避〗的單位不能成為敵方 Unit 的攻擊目標，但仍可被 Spell、Ability 或其他效果指定
- **〖格檔〗**：每次受到戰鬥傷害時，使該次傷害減少 1 點，最低為 0；不影響效果傷害
- **〖吸血〗**：Unit 透過主動攻擊實際造成傷害時，回復自身等量生命值

〖庇護〗與〖迴避〗不能同時存在於同一單位。

### 生命值

- Unit 的現有生命值與最大生命值分開記錄
- 治療只增加現有生命值，且不能超過最大生命值
- 最大生命值增加 X 點時，現有生命值同步增加 X 點
- 最大生命值降低時不會產生治療；若現有生命值超過新上限，則降至新的最大生命值
- 因 Transform 導致基礎最大生命值增加時，同樣套用上述規則

### Mulligan

- 雙方起手各抽 5 張牌
- 每位玩家有一次 Mulligan 機會
- 可選擇 0～5 張牌退回牌組
- 牌組重新洗牌後抽回等量卡牌
- 雙方完成 Mulligan 後才正式開始第一回合
- Prototype 於 Mulligan 完成後決定先手

## Effect 系統

卡牌效果主要由 `data/cards/effects.csv` 驅動，而不是直接依 `card_id` 在程式中硬編碼。

目前 Effect Resolver 支援的觸發時機包含：

- `on_play`
- `on_enter`
- `on_flip`
- `on_leave`
- `manual`
- `ally_becomes_attack_target`

目前支援的主要 operation 包含：

- `damage`
- `heal`
- `draw`
- `modify_attack`
- `modify_max_health`
- `add_keyword`

效果可搭配 `target`、`target_filter`、`sequence`、`duration`、`condition`、`parameter`、`usage_limit` 等欄位描述。

## 資料結構

```text
Card Game/
├─ data/
│  ├─ cards/
│  │  ├─ cards.csv
│  │  ├─ unit_sides.csv
│  │  └─ effects.csv
│  ├─ decks/
│  │  ├─ decks.csv
│  │  └─ deck_cards.csv
│  └─ factions/
│     ├─ factions.csv
│     └─ leader.csv
│
├─ docs/
│  └─ game-design/
│
├─ src/
│  ├─ cards/
│  ├─ core/
│  ├─ deck/
│  ├─ effects/
│  └─ ui/
│
├─ tests/
├─ streamlit_app.py
├─ requirements.txt
├─ CHANGELOG.md
└─ README.md
```

基本原則：

> 規則放 Markdown、卡牌與數值放 CSV、遊戲邏輯放 `src/`、自動測試放 `tests/`。

## 執行 Streamlit Prototype

建議使用 Python 虛擬環境：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

如果 PowerShell 執行原則阻止啟用虛擬環境，也可以直接使用：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

## 測試

執行自動測試：

```bash
python -m pytest -q
```

目前測試重點包含：

- Combat
- Transform
- Effect Resolver
- Spell target resolution
- Mulligan
- 〖庇護〗
- 〖迴避〗
- 〖格檔〗
- 〖吸血〗
- 最大生命值與治療規則
- 死亡與離場觸發時序

## 開發方向

近期優先事項：

1. 正規化 Event / Trigger Queue
2. 將 Combat、Targeting、Transform、Timing 等邏輯逐步從 `game.py` 拆分
3. 完善 Response Chain 與複數觸發的結算順序
4. 補齊牌庫耗盡、抽牌失敗等邊界規則
5. 建立 Playtest Log 與對局統計輸出
6. 建立簡易 Bot 與 AI vs AI 自動模擬
7. 依測試結果調整卡牌數值、費用與陣營特色

## 版本狀態

目前以 **Streamlit Prototype v5** 為主要可玩原型；正式語意化版本仍以 `CHANGELOG.md` 為準。
