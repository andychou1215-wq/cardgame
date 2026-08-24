# M1.2 Backward-Compatibility Hotfix

The five reported failures share one cause: combat never resolved.

M1.2 made `resolve_combat()` reject combat whenever the new Priority Window was
still open, while older tests still use:

```python
game.declare_attack(...)
game.resolve_combat()
```

The hotfix keeps both behaviors:

- If neither player has a legal Response, direct `resolve_combat()` automatically
  counts as two consecutive Priority passes and combat resolves.
- If either player has a legal Response, direct combat remains blocked until the
  Priority Window is handled explicitly.

This means old combat tests remain valid without weakening meaningful Response
decisions.

Apply:

```powershell
py tools/apply_m1_2_hotfix.py
py -m pytest -q
```
