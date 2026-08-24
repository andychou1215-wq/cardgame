# Cardgame Repo Cleanup v1

這個整理包根據目前公開 `main` 的 repo 結構設計。

## 目標

不改遊戲規則，只整理：

- root application entry points
- historical patch scripts
- Python caches
- `.gitignore`
- documentation index / architecture docs
- playtest output directories
- future test categorization directories

## 為什麼暫時不直接搬 `test_engine_v2/v3/v4/v5.py`

目前新的 tests 會 import：

```python
from tests.test_engine_v2 import make_repo
from tests.test_engine_v3 import start_game
from tests.test_engine_v4 import make_keyword_unit
```

若直接把舊測試檔搬到子資料夾，會讓 pytest/import 立即失效。

所以 v1 只建立：

```text
tests/
├─ unit/
├─ integration/
├─ scenarios/
├─ fixtures/
└─ TEST_MIGRATION.json
```

正式測試拆分應在下一個獨立 commit 做。

## 使用方式

把這個 ZIP 的內容解壓到 repo 根目錄。

### 1. 先 dry-run

```powershell
py tools/repo_cleanup_v1.py
```

不會修改任何檔案，只列出預計動作。

### 2. 確認 Git 工作區乾淨

```powershell
git status
```

最好先 commit 目前進度。

### 3. 正式套用

```powershell
py tools/repo_cleanup_v1.py --apply
```

若你明確知道目前未提交內容要一起保留：

```powershell
py tools/repo_cleanup_v1.py --apply --allow-dirty
```

### 4. 驗證目錄

```powershell
py tools/audit_repo_structure.py
```

### 5. 回歸測試

```powershell
py -m pytest -q
```

### 6. 檢查 Git move

```powershell
git status
```

## 預計整理後

```text
cardgame/
├─ apps/
│  ├─ battle_app.py
│  └─ playtest_dashboard.py
├─ archive/
│  ├─ patches/
│  └─ deprecated/
├─ assets/
├─ data/
├─ docs/
│  ├─ architecture/
│  ├─ playtesting/
│  └─ ui-ux/
├─ playtest_data/
│  ├─ raw/
│  └─ summaries/
├─ src/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ scenarios/
│  └─ fixtures/
├─ tools/
│  ├─ repo_cleanup_v1.py
│  └─ audit_repo_structure.py
├─ .gitignore
├─ CHANGELOG.md
├─ LICENSE
├─ README.md
└─ requirements.txt
```

原本的 `streamlit_app.py` / `playtest_dashboard.py` 在 v1 會保留小型 compatibility wrapper，
因此舊啟動指令暫時仍可使用；正式入口改為 `apps/`。
