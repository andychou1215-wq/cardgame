# Changelog

本檔案記錄 Card Game 專案的重要規則、資料與 Prototype 變更。

## Unreleased

### Player vs AI Playtest
- Streamlit Prototype 新增玩家對 Heuristic AI 模式；AI 自動處理 Mulligan、主回合、效果目標、Response Priority 與戰鬥結算。
- AI 模式採固定玩家視角並隱藏 AI 手牌內容，決策權回到玩家時立即停止自動推進。
- 新增局後 7 項好玩度問卷、U011 曝光統計與本機 CSV 保存；每局僅能提交一次。
- 修正 Heuristic AI 未偵測「多單位加總攻擊力達成斬殺」的問題：先前只有單一單位攻擊力足以單獨斬殺對方領袖時才會優先攻擊，現在會加總目前所有合法攻擊領袖的動作傷害，只要總和達到致死量就一律優先攻擊領袖，避免 AI 在能直接獲勝時仍選擇先進行場面交換。
- 局後問卷中 U011 手感、回報與暫時【庇護】三題，改為只在玩家本局實際抽到／打出／觸發翻面時才詢問；未接觸時記錄為空值而非預設 3 分，避免污染後續平衡分析資料。

### Deck Compliance
- D001、D002 測試牌組張數由 25 張補齊至 `docs/game-design/牌組構築.md` 規定的最低 35 張，同名卡上限仍維持 3 張。
  - D001：U004、U006、U011、U012、A001 由 2 張補至 3 張；新增中立卡 U005 x3、S001 x2。
  - D002：U009、U010、U013、S003、A002 由 2 張補至 3 張；新增中立卡 U001 x3、U006 x2。
  - 補牌全部取自現有 19 張卡池中「規則允許但該牌組尚未使用」的中立卡，未新增卡牌設計。
  - 在此之前累積的鏡像模擬與局後問卷資料，皆是在低於下限的 25 張牌組上取得，牌組張數會影響抽牌一致性與牌庫耗盡機率，後續平衡結論應以補牌後的新基準重新驗證，不宜直接沿用舊數據。

### Balance
- 以 1,000 組、2,000 場 Heuristic/Heuristic 鏡像測試複驗 U011 費用 8；D001 勝率為 51.2%，鏡像組層級 95% 信賴區間為 49.2%–53.2%。
- U011「遺跡石像」費用由 7 提高至 8；400 場鏡像測試中，同策略 D001 勝率由 79.5% 降至 72.5%，Heuristic/Heuristic 由 69% 降至 55%。
- 新增 U011 費用 8 的逐場配對分析報告；30 場勝負翻轉中有 24 場轉向 D002、6 場轉向 D001。
- U011「遺跡石像」反面翻面效果改為指定一個其他我方單位獲得【庇護】至對手回合結束，不再永久授予。
- 新增 U011 單變量 400 場鏡像測試報告；同策略 D001 勝率維持 79.5%，目前未觀察到可量測的整體削弱效果。
- U012「騎士團長」正面登場效果保留攻擊力與最大生命值 +1，但改為到本回合結束，不再永久累積。
- 新增 400 場鏡像測試報告；此改動僅使同策略 D001 勝率由 82.0% 降至 81.5%，下一輪應優先測試背面永久群體增益。

### Telemetry
- 補齊初始手牌、Mulligan、戰鬥／效果傷害、治療、單位死亡與對局結束事件。
- 傷害與治療統一記錄實際值、請求值、格擋量與溢補量。
- 區分效果、吸血、最大生命同步與 Transform 最大生命同步治療來源。
- 新增端到端量測覆蓋，確認事件可直接供 M3.7.5 分析器使用。
- 修正模擬器略過 Bot 策略的問題，讓 heuristic／random 配對使用實際策略選擇。

### Repository Cleanup v1.1
- 將 milestone / hotfix 說明文件移至 `archive/notes/`。
- 測試依 unit / integration / scenarios 重新分類。
- 保留 `test_engine_v2~v5` compatibility wrapper，避免 fixture imports 中斷。
- 移除已由 `apps/` 取代的根目錄 Streamlit launcher。
- 補充 Engine Architecture、Timing/Priority、Telemetry 與 Playtest Dashboard 文件。
- 清理一次性 repo cleanup report 並加入 `.gitignore`。

### Added

- 建立 Python + Streamlit 數位對戰 Prototype，作為主要 Playtest 環境。
- 建立可從 CSV 載入的卡牌、Unit 正反面、Effect、Leader、Faction 與 Deck 資料模型。
- 新增 `decks.csv` 與 `deck_cards.csv`，支援 D001 / D002 測試牌組。
- 新增 Leader 測試資料與 Leader HP / 勝負判定。
- 新增起手 5 張與一次性 Mulligan 流程。
- 新增 Unit 出牌、Mana 消耗、戰場、墓地與回合流程。
- 新增 Unit → Unit 與 Unit → Leader 戰鬥。
- 新增進場回合攻擊限制與每回合攻擊次數管理。
- 新增 Transform 系統與多種翻面條件：
  - `attack_count`
  - `kill_count`
  - `total_damage_taken`
  - `turn_count`
  - `total_damage_dealt`
  - `heal_count`
  - `unit_count_at_least`
  - `leader_health_at_or_below`
- 新增 Effect Resolver，從 `effects.csv` 依 `card_id + side + trigger + sequence` 載入並結算效果。
- 新增 Effect trigger：
  - `on_play`
  - `on_enter`
  - `on_flip`
  - `on_leave`
  - `manual`
  - `ally_becomes_attack_target`
- 新增 Effect operation：
  - `damage`
  - `heal`
  - `draw`
  - `modify_attack`
  - `modify_max_health`
  - `add_keyword`
- 新增 Response Window 與 Response 卡牌測試流程。
- 新增〖庇護〗攻擊目標限制。
- 新增〖吸血〗：Unit 主動攻擊造成實際傷害時回復自身等量生命。
- 新增〖格檔〗：每次受到戰鬥傷害時減少 1 點傷害，最低為 0。
- 新增〖迴避〗：持有者不能成為敵方 Unit 的攻擊目標。
- 新增〖庇護〗與〖迴避〗互斥檢查。
- 新增 Game Log，協助追蹤出牌、攻擊、翻面、治療、死亡與效果結算。
- 新增多項自動測試，涵蓋 Combat、Transform、Mulligan、Effect Resolver、關鍵字與生命值規則。

### Changed

- 專案階段由「早期規則設計」進入「可執行 Prototype / 規則引擎開發」。
- `effects.csv` 擴充為可描述 condition、target/filter、parameter、duration、usage limit、optional 與 failure behavior 的資料結構。
- 多段卡牌效果改以 `sequence` 拆成多筆 Effect，而非將多個 operation 塞在同一筆資料。
- Unit 現有生命值與最大生命值改為分開管理。
- 最大生命值增加 X 點時，現有生命值同步增加 X 點。
- 因 Transform 導致基礎最大生命值增加時，同樣同步增加現有生命值。
- Heal 只在實際恢復生命時才視為成功治療，滿血 Unit 不再作為一般 Heal 效果的有效目標。
- 戰鬥死亡處理改為同批判定與同時離場後，再依時序處理 `on_leave`。
- 同批死亡觸發順序採 Active Player → Non-Active Player。
- 〖吸血〗以實際造成的主動攻擊傷害計算治療量。
- 〖格檔〗只影響戰鬥傷害，不影響 Effect Damage。
- 〖迴避〗只限制敵方 Unit 的攻擊，不阻止 Spell、Ability 或其他效果指定。
- S003「精靈鼓舞」費用由 3 調整為 4。
- U009「大樹守衛」翻面獎勵增加最大生命值永久 +1。
- U013「聖獸」翻面條件文字調整為與 `leader_health_at_or_below` 一致。
- A002「世界樹」調整為 F002 陣營卡牌。

### Fixed

- 修正 U009 卡面效果與 `effects.csv` 不同步的問題，補上翻面後最大生命值永久 +1 的 Effect。
- 修正舊生命值模型中「提高最大生命值會因 damage 差值而產生不明確生命變化」的問題。
- 修正滿血單位仍可被治療並產生 `回復 0 點生命` Log 的問題。
- 修正死亡觸發可能在同批死亡單位尚未全部離場前提前結算的時序問題。
- 修正攻擊合法目標未完整考慮〖庇護〗與〖迴避〗交互作用的問題。
- 移除不應提交至版本控制的 Python cache 檔案，並建議由 `.gitignore` 排除。

### Removed

- 現有遊戲設計不再使用 Apocalypse 系統；Prototype 與後續規則引擎不再以 Apocalypse 作為對戰機制。
- 取消以 CLI 作為主要 Playtest 介面的規劃，改以 Streamlit Prototype 為主。

## v0.1.0

- 建立專案資料夾架構。
- 建立初版遊戲設計文件。
- 將目前完整專案狀態定義為 v0.1.0。
- 建立目前核心規則、卡牌資料、戰鬥系統與 Prototype 基準。
- `cards.csv`、`unit_sides.csv`、`effects.csv` 等現有資料皆以此版本作為後續 Balance Patch 比較基準。

## v0.1.1

### 卡牌平衡
- S002「神聖防禦」費用：3 → 4。
- U011「遺跡石像」正反面生命值：8 → 7。
- A002「世界樹」啟動能力魔力消耗：2 → 1。
- U013「聖獸」翻面治療領袖：3 → 4。

### 驗證
- 完整測試套件：86 passed。
- 完成 800 場 mirrored post-patch simulation。
- 所有對局正常完成，invalid / stalled / limit 均為 0。
- Card attribution conservation 驗證通過，unknown_card = 0、conflicts = 0。

### 平衡調查結果
- D001 勝率：約 89.75% → 89.25%。
- D002 勝率：約 10.25% → 10.75%。
- Balance Patch v1 未造成過度修正，但 deck-level 差距仍然明顯。
- 後續將優先分析 Mana Curve、Stat Efficiency、Tempo、Transform Efficiency 與 AI-by-Deck 表現。
