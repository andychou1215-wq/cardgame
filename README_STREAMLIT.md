# 卡牌對決 Streamlit Prototype v3

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

## Mulligan 規則（Prototype v3）

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
