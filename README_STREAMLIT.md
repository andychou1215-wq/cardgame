# Streamlit Prototype

這是一個放入現有 `cardgame` repo 根目錄即可執行的 MVP。

## MVP 已支援

- 從 `data/cards/cards.csv` 載入卡牌主資料
- 從 `data/cards/unit_sides.csv` 載入 Unit 正反面資料
- 從 `data/decks/decks.csv` / `deck_cards.csv` 建立牌組
- 從 `data/factions/leader.csv` 載入 Leader
- 選擇兩副測試牌組
- 洗牌與雙方 5 張起手牌
- Hot-seat 模式
- 每位玩家回合開始增加 1 最大魔力並回滿
- 非起始回合抽 1 張
- Unit 出牌與魔力扣除
- Battlefield 顯示
- Game Log
- End Turn

## 暫未支援

- Spell / Artifact / Response 結算
- `effects.csv` effect resolver
- 攻擊與死亡
- Transform 條件與翻面
- Apocalypse
- Mulligan
- 多人連線

## 安裝

在 repo 根目錄：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

若 PowerShell 阻擋啟用腳本，也可不啟用環境，直接：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

## 放入 repo 的方式

壓縮包內的：

```text
streamlit_app.py
requirements.txt
src/
```

直接合併到 `cardgame/` 根目錄即可。現有 `src/` 可直接合併；此 Prototype 新增：

```text
src/cards/models.py
src/deck/loader.py
src/core/game.py
src/ui/components.py
```

## Prototype 暫定規則

`src/core/game.py` 中有一個暫定值：

```python
BATTLEFIELD_LIMIT = 5
```

這只是 UI/MVP 防呆，不代表正式規則。等 repo 的戰場格數規則定案後再同步修改。

## 下一階段

建議依序加入：

1. 攻擊與死亡
2. Transform condition evaluator
3. `effects.csv` resolver（damage/heal/draw/modify/add_keyword）
4. Spell / Artifact
5. Response Window
6. Apocalypse
7. Playtest metrics / export log
