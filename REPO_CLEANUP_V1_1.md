# Repo Cleanup v1.1

這一版接續 Repo Cleanup v1，重點是開始真正收斂歷史檔案與 tests。

## 會處理

### 根目錄歷史文件

以下移至：

```text
archive/notes/
```

包括：

- M1_M2_IMPLEMENTATION.md
- M1_1_M2_1_README.md
- M1_2_M2_2_README.md
- HOTFIX_NOTES.md
- M1_2_HOTFIX_NOTES.md
- M1_2_HOTFIX_V2_NOTES.md
- DECKOUT_HOTFIX_NOTES.md
- REPO_CLEANUP_V1.md

### Cleanup report

刪除：

```text
repo_cleanup_report.json
```

並加入 `.gitignore`。

### Tests

搬移成：

```text
tests/
├─ unit/
├─ integration/
└─ scenarios/
```

其中 `test_engine_v2~v5.py` 會留下 `__test__ = False` compatibility wrapper，
因為其他測試仍可能 import：

```python
tests.test_engine_v2
tests.test_engine_v3
tests.test_engine_v4
```

這些 wrapper 不會被 pytest 當成正式測試重複收集。

### Streamlit root launcher

若以下正式入口存在：

```text
apps/battle_app.py
apps/playtest_dashboard.py
```

則刪除根目錄舊 wrapper：

```text
streamlit_app.py
playtest_dashboard.py
```

### 正式文件

建立 / 更新：

```text
docs/architecture/EngineArchitecture.md
docs/architecture/TimingAndPriority.md
docs/playtesting/Telemetry.md
docs/playtesting/PlaytestDashboard.md
```

並更新 `CHANGELOG.md`。

## 執行

先 dry-run：

```powershell
py tools/repo_cleanup_v1_1.py
```

正式套用：

```powershell
py tools/repo_cleanup_v1_1.py --apply
```

如果 working tree 仍有修改且你確定要保留：

```powershell
py tools/repo_cleanup_v1_1.py --apply --allow-dirty
```

完成後：

```powershell
py tools/audit_repo_v1_1.py
py -m pytest -q
git status
```

## 預期根目錄

```text
README.md
CHANGELOG.md
LICENSE
requirements.txt

apps/
archive/
assets/
data/
docs/
playtest_data/
src/
tests/
tools/
```

`repo_cleanup_v1_1_report.json` 只供本機確認，已加入 `.gitignore`。
