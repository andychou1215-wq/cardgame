# 卡牌對決 Streamlit Prototype v4

本版本加入 Mulligan、正式〖庇護〗攻擊限制，並保留 Combat、Transform、effects.csv Resolver。
現有遊戲不使用 Apocalypse 系統，因此 Prototype 不包含任何 Apocalypse 流程或入口。

## 已支援

- 兩副牌組載入與 Hot-seat 1v1
- 起手 5 張
- Mulligan：每位玩家一次，可更換任意張；退回牌組、洗牌、抽回等量
- 雙方 Mulligan 完成後隨機決定先手
- Mana 成長與回合開始抽牌
- Unit / Spell / Artifact / Response
- Unit 攻擊 Unit 或 Leader
- 單位互戰時雙方同時造成傷害與反擊
- 〖庇護〗：防守方存在〖庇護〗單位時，敵方 Unit 只能攻擊〖庇護〗單位
- Response Window
- Unit 死亡、墓地、on_leave
- Transform 條件與 on_flip
- effects.csv Resolver
- duration：instant / permanent / until_turn_end / until_attack_end / until_opponent_turn_end
- Game Log

## 執行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

若 PowerShell 不允許啟用虛擬環境：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

## Mulligan 規則（Prototype v4）

1. 雙方各抽 5 張起手牌。
2. Player 1 先進行 Mulligan，之後 Player 2。
3. 每位玩家可以選擇 0～5 張起手牌更換。
4. 被選中的牌退回牌組並重新洗牌。
5. 玩家抽回相同數量的牌，維持 5 張起手牌。
6. 每位玩家僅有一次 Mulligan 機會。
7. 雙方完成 Mulligan 後，系統隨機決定先手，第一回合正式開始。

## 〖庇護〗規則

只要防守方戰場上存在至少一個具有〖庇護〗的 Unit：

- 攻擊方 Unit 只能選擇具有〖庇護〗的敵方 Unit 作為攻擊目標。
- 敵方 Leader 不再是合法攻擊目標。
- 非〖庇護〗敵方 Unit 不再是合法攻擊目標。
- 若有多個〖庇護〗Unit，攻擊方可自由選擇其中一個。
- 當防守方戰場上不再存在〖庇護〗Unit 時，攻擊目標恢復為一般規則。

## 測試

```powershell
python -m pytest -q
```

目前回歸測試涵蓋：

- 基本 Game 初始化
- Combat + Transform + on_flip effect
- Spell targeting/effect resolver
- Mulligan
- Mulligan 完成前禁止一般遊戲操作
- 〖庇護〗合法攻擊目標限制


## v4：吸血、格檔、生命值與死亡時序

### 〖吸血〗
依目前 repo 的正式定義：單位透過**主動攻擊**實際造成傷害時，回復自身等量現有生命。

- 治療對象是攻擊單位本身，不是 Leader。
- 回復量以實際造成的傷害為準。
- 不超過自身最大生命值。
- 反擊傷害不觸發〖吸血〗。

### 〖格檔〗
目前 repo 的 `關鍵字系統.md` 尚未定義〖格檔〗，v4 Prototype 將它正式化為：

> 每次受到戰鬥傷害時，使該次傷害減少 1 點，最低降至 0。

- 可減少主動攻擊傷害與反擊傷害。
- 不會減少 Spell / Effect Resolver 的 `damage`。
- 若之後正式規則修改，只需要調整 `Game._combat_damage_to_unit()`。

### 生命值修正
舊版以 `max_health - damage` 推算現有生命，因此永久增加最大生命值時會同步提高畫面上的現有生命，看起來像額外治療。v4 改成獨立保存 `health`：

- `heal`：只增加現有生命，最多至最大生命。
- `modify_max_health`：只修改上限，不恢復現有生命。
- 最大生命的暫時效果到期時，若現有生命高於新上限，才會向下 clamp。
- 治療效果的玩家選擇目標會自動排除滿血單位，避免出現「回復 0 點」的無效選擇。

### 死亡與觸發時序
1. 傷害同時套用。
2. 〖格檔〗計算實際戰鬥傷害。
3. 主動攻擊者若有〖吸血〗，依實際傷害回復自身。
4. 判定擊殺與生命歸零。
5. 同批死亡單位全部先移出戰場並進墓地。
6. 依 Active Player → Non-Active Player 順序排入 `on_leave`。
7. 結算 `on_leave` 與後續 effects。
8. 再檢查 Transform、Leader 敗北與後續觸發。

## 測試

```powershell
python -m pytest -q
```

v4 目前測試包含：Combat、Transform、Spell Resolver、Mulligan、〖庇護〗、〖吸血〗、〖格檔〗、最大生命不等於治療，共 10 項通過。
