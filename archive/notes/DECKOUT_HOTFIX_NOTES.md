# Deck-out Loss Hotfix

規則：

- 對局正式開始後，玩家需要抽牌但牌庫已空 → 立即敗北。
- 抽到牌庫最後 1 張不會立刻敗北；是下一次「需要抽牌但無牌」時敗北。
- 多抽牌時逐張處理，若中途牌庫耗盡，第一個失敗的抽牌立即造成敗北。
- 起手 5 張與 Mulligan 屬於 setup，不套用 deck-out。

涵蓋：
- 回合開始抽牌
- effects.csv 的 draw 效果

套用：

```powershell
py tools/apply_deckout_hotfix.py
py -m pytest -q tests/test_deck_out.py
py -m pytest -q
```
