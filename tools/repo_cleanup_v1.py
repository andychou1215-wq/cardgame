from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


ROOT_MARKERS = ("README.md", "src", "tests", "data", "docs")


def repo_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    missing = [name for name in ROOT_MARKERS if not (root / name).exists()]
    if missing:
        raise SystemExit(
            "此工具必須放在 cardgame repo 的 tools/ 下執行。"
            f"缺少：{', '.join(missing)}"
        )
    return root


def git_available(root: Path) -> bool:
    try:
        subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True
    except Exception:
        return False


def git_dirty(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def move_file(root: Path, src: Path, dst: Path, *, use_git: bool, dry_run: bool) -> dict:
    if not src.exists():
        return {"action": "skip", "src": str(src.relative_to(root)), "reason": "missing"}

    if dst.exists():
        return {
            "action": "skip",
            "src": str(src.relative_to(root)),
            "dst": str(dst.relative_to(root)),
            "reason": "destination exists",
        }

    dst.parent.mkdir(parents=True, exist_ok=True)

    if dry_run:
        return {
            "action": "move",
            "src": str(src.relative_to(root)),
            "dst": str(dst.relative_to(root)),
            "dry_run": True,
        }

    if use_git:
        try:
            subprocess.run(
                ["git", "-C", str(root), "mv", str(src.relative_to(root)), str(dst.relative_to(root))],
                check=True,
            )
        except subprocess.CalledProcessError:
            shutil.move(str(src), str(dst))
    else:
        shutil.move(str(src), str(dst))

    return {
        "action": "move",
        "src": str(src.relative_to(root)),
        "dst": str(dst.relative_to(root)),
    }


def remove_cache_dirs(root: Path, *, dry_run: bool) -> list[dict]:
    removed = []
    for name in ("__pycache__", ".pytest_cache"):
        for path in sorted(root.rglob(name), key=lambda p: len(p.parts), reverse=True):
            if ".git" in path.parts:
                continue
            item = {"action": "remove_cache", "path": str(path.relative_to(root))}
            removed.append(item)
            if not dry_run and path.exists():
                shutil.rmtree(path)
    return removed


def ensure_text(path: Path, content: str, *, dry_run: bool) -> dict:
    if path.exists():
        return {"action": "skip", "path": str(path), "reason": "exists"}
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return {"action": "create", "path": str(path), "dry_run": dry_run}


def append_gitignore(root: Path, *, dry_run: bool) -> dict:
    path = root / ".gitignore"
    wanted = [
        "__pycache__/",
        "*.py[cod]",
        ".pytest_cache/",
        ".venv/",
        "venv/",
        ".idea/",
        ".vscode/",
        ".DS_Store",
        "Thumbs.db",
        "playtest_data/raw/*.csv",
        "playtest_data/raw/*.json",
    ]

    current = path.read_text(encoding="utf-8") if path.exists() else ""
    existing = {line.strip() for line in current.splitlines()}
    missing = [line for line in wanted if line not in existing]

    if missing and not dry_run:
        with path.open("a", encoding="utf-8") as f:
            if current and not current.endswith("\n"):
                f.write("\n")
            if current:
                f.write("\n# Python / local development / playtest output\n")
            for line in missing:
                f.write(line + "\n")

    return {
        "action": "update_gitignore",
        "missing_added": missing,
        "dry_run": dry_run,
    }


def create_dirs(root: Path, *, dry_run: bool) -> list[dict]:
    dirs = [
        "apps",
        "archive/patches",
        "archive/deprecated",
        "docs/architecture",
        "docs/playtesting",
        "playtest_data/raw",
        "playtest_data/summaries",
        "tests/unit",
        "tests/integration",
        "tests/scenarios",
        "tests/fixtures",
    ]
    actions = []
    for rel in dirs:
        p = root / rel
        actions.append({"action": "mkdir", "path": rel, "dry_run": dry_run})
        if not dry_run:
            p.mkdir(parents=True, exist_ok=True)
            keep = p / ".gitkeep"
            if not any(p.iterdir()):
                keep.write_text("", encoding="utf-8")
    return actions


def write_compat_wrapper(root: Path, target_module: str, old_path: Path, *, dry_run: bool) -> dict:
    wrapper = (
        '"""Deprecated compatibility launcher.\n\n'
        f'Use: py -m streamlit run {target_module.replace(".", "/")}.py\n'
        '"""\n'
        "from pathlib import Path\n"
        "import runpy\n\n"
        f'runpy.run_path(str(Path(__file__).parent / "{target_module.replace(".", "/")}.py"), run_name="__main__")\n'
    )
    if not dry_run:
        old_path.write_text(wrapper, encoding="utf-8")
    return {"action": "compat_wrapper", "path": str(old_path.relative_to(root)), "dry_run": dry_run}


def main() -> None:
    parser = argparse.ArgumentParser(description="Cardgame Repo Cleanup v1")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="真的執行搬移；未加時只顯示 dry-run。",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="允許在 git working tree 有未提交變更時執行。",
    )
    args = parser.parse_args()

    dry_run = not args.apply
    root = repo_root()
    use_git = git_available(root)

    if args.apply and use_git and git_dirty(root) and not args.allow_dirty:
        raise SystemExit(
            "Git working tree 目前有未提交變更。\n"
            "為避免整理時混入其他修改，請先 commit/stash，"
            "或確認後加 --allow-dirty。"
        )

    actions: list[dict] = []
    actions.extend(create_dirs(root, dry_run=dry_run))
    actions.extend(remove_cache_dirs(root, dry_run=dry_run))
    actions.append(append_gitignore(root, dry_run=dry_run))

    # Root application files -> apps/.
    app_moves = [
        (root / "streamlit_app.py", root / "apps/battle_app.py", "apps.battle_app"),
        (root / "playtest_dashboard.py", root / "apps/playtest_dashboard.py", "apps.playtest_dashboard"),
    ]
    for src, dst, module in app_moves:
        existed = src.exists()
        result = move_file(root, src, dst, use_git=use_git, dry_run=dry_run)
        actions.append(result)
        if existed and result.get("action") == "move":
            actions.append(
                write_compat_wrapper(root, module, src, dry_run=dry_run)
            )

    # Streamlit documentation.
    actions.append(
        move_file(
            root,
            root / "README_STREAMLIT.md",
            root / "docs/ui-ux/StreamlitPrototype.md",
            use_git=use_git,
            dry_run=dry_run,
        )
    )

    # Historical patch/apply scripts should not stay in active tools/.
    tools = root / "tools"
    if tools.exists():
        for src in sorted(tools.glob("apply*.py")):
            actions.append(
                move_file(
                    root,
                    src,
                    root / "archive/patches" / src.name,
                    use_git=use_git,
                    dry_run=dry_run,
                )
            )

    docs_index = """# Documentation Index

## Game Design

主要遊戲規則、戰鬥、資源、牌組與關鍵字請見 `game-design/`。

## Cards

卡牌類型、設計原則與數值規範請見 `cards/`。

## Factions

陣營設定請見 `factions/`。

## Architecture

程式實作與規則引擎文件請見 `architecture/`。

建議維護：
- `RepoStructure.md`
- `EngineArchitecture.md`
- `TimingAndPriority.md`
- `DataSchema.md`

## Playtesting

測試流程、Scenario、Telemetry 與跨場統計文件請見 `playtesting/`。

## UI / UX

Streamlit Prototype 與介面設計文件請見 `ui-ux/`。

## Archive

已棄用或歷史設計不應混在目前規則文件中，請移至 repo 根目錄的 `archive/`。
"""
    if not (root / "docs/README.md").exists():
        if not dry_run:
            (root / "docs/README.md").write_text(docs_index, encoding="utf-8")
        actions.append({"action": "create", "path": "docs/README.md", "dry_run": dry_run})

    repo_structure = """# Repository Structure

```text
cardgame/
├─ apps/                 # Streamlit entry points
├─ archive/              # historical patches / deprecated designs
├─ assets/               # art / UI / audio assets
├─ data/                 # cards / effects / decks / factions / keywords / balance
├─ docs/                 # design + architecture + playtest documentation
├─ playtest_data/        # generated playtest outputs
├─ src/                  # game engine source
├─ tests/                # regression, scenario and future categorized tests
├─ tools/                # long-lived developer tools only
├─ CHANGELOG.md
├─ LICENSE
├─ README.md
└─ requirements.txt
```

## Source boundaries

- `src/core/`: game orchestration, events, priority, state-based checks
- `src/combat/`: combat, damage and legal targeting
- `src/cards/`: definitions / instances / transforms
- `src/effects/`: effect models and resolver
- `src/deck/`: data loading / validation
- `src/playtest/`: telemetry, scenarios and analytics
- `src/ai/`: bots / policies
- `src/ui/`: reusable Streamlit UI components

## Tests

The repository currently has historical `test_engine_v2.py` through `v5.py`.
Do **not** move them blindly because newer tests import helper fixtures from those modules.

Migration should happen in a separate commit:

1. extract `make_repo`, `start_game`, `make_keyword_unit` into `tests/conftest.py`
   or `tests/fixtures/`;
2. update imports;
3. run the full suite;
4. then split tests into `unit/`, `integration/`, and `scenarios/`.
"""
    if not (root / "docs/architecture/RepoStructure.md").exists():
        if not dry_run:
            (root / "docs/architecture/RepoStructure.md").write_text(repo_structure, encoding="utf-8")
        actions.append({"action": "create", "path": "docs/architecture/RepoStructure.md", "dry_run": dry_run})

    migration = {
        "generated_at": datetime.now().isoformat(),
        "phase": "Repo Cleanup v1",
        "safe_now": [
            "remove __pycache__ / .pytest_cache",
            "add/update .gitignore",
            "move app entry points under apps/",
            "keep root compatibility launchers",
            "move README_STREAMLIT.md under docs/ui-ux/",
            "archive apply*.py scripts",
            "create architecture/playtesting/playtest_data/test category directories",
        ],
        "deferred_test_migration": {
            "reason": "historical tests import fixtures from other test_engine_vN modules",
            "target": {
                "test_engine_smoke.py": "tests/integration/test_game_smoke.py",
                "test_engine_v2.py": "split: combat/effects + fixtures",
                "test_engine_v3.py": "split: turn/transform + fixtures",
                "test_engine_v4.py": "tests/unit/test_keywords.py",
                "test_engine_v5.py": "tests/unit/test_health_and_keywords.py",
                "test_playtest_scenarios.py": "tests/scenarios/test_core_scenarios.py",
                "test_priority_window.py": "tests/unit/test_priority.py",
                "test_priority_compatibility.py": "tests/integration/test_priority_compatibility.py",
                "test_deck_out.py": "tests/unit/test_deck_out.py",
            },
        },
    }
    if not dry_run:
        (root / "tests/TEST_MIGRATION.json").write_text(
            json.dumps(migration, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    actions.append({"action": "create", "path": "tests/TEST_MIGRATION.json", "dry_run": dry_run})

    report = {
        "repo": str(root),
        "mode": "dry-run" if dry_run else "apply",
        "git_available": use_git,
        "actions": actions,
    }

    report_path = root / "repo_cleanup_report.json"
    if not dry_run:
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if dry_run:
        print("\nDRY RUN only. 確認後執行：")
        print("  py tools/repo_cleanup_v1.py --apply")
    else:
        print("\nRepo Cleanup v1 完成。建議現在執行：")
        print("  py -m pytest -q")
        print("  git status")
        print("確認測試通過後再 commit。")


if __name__ == "__main__":
    main()
