from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ROOT_MARKERS = ("README.md", "CHANGELOG.md", "src", "tests", "docs")


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


def ensure_repo() -> None:
    missing = [x for x in ROOT_MARKERS if not (ROOT / x).exists()]
    if missing:
        fail(f"這不像 cardgame repo 根目錄；缺少：{', '.join(missing)}")


def git_available() -> bool:
    try:
        subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True
    except Exception:
        return False


def git_dirty() -> bool:
    if not git_available():
        return False
    result = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return bool(result.stdout.strip())


def move(src_rel: str, dst_rel: str, *, dry_run: bool, use_git: bool) -> dict:
    src = ROOT / src_rel
    dst = ROOT / dst_rel

    if not src.exists():
        return {"action": "skip", "src": src_rel, "reason": "missing"}

    if dst.exists():
        return {"action": "skip", "src": src_rel, "dst": dst_rel, "reason": "destination exists"}

    if dry_run:
        return {"action": "move", "src": src_rel, "dst": dst_rel, "dry_run": True}

    dst.parent.mkdir(parents=True, exist_ok=True)
    if use_git:
        try:
            subprocess.run(
                ["git", "-C", str(ROOT), "mv", src_rel, dst_rel],
                check=True,
            )
        except subprocess.CalledProcessError:
            shutil.move(str(src), str(dst))
    else:
        shutil.move(str(src), str(dst))

    return {"action": "move", "src": src_rel, "dst": dst_rel}


def delete(rel: str, *, dry_run: bool, use_git: bool) -> dict:
    path = ROOT / rel
    if not path.exists():
        return {"action": "skip", "path": rel, "reason": "missing"}

    if dry_run:
        return {"action": "delete", "path": rel, "dry_run": True}

    if use_git:
        try:
            subprocess.run(["git", "-C", str(ROOT), "rm", "-f", rel], check=True)
            return {"action": "delete", "path": rel}
        except subprocess.CalledProcessError:
            pass

    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return {"action": "delete", "path": rel}


def append_gitignore(*, dry_run: bool) -> dict:
    path = ROOT / ".gitignore"
    wanted = [
        "repo_cleanup_report.json",
        "repo_cleanup_v1_1_report.json",
        "__pycache__/",
        "*.py[cod]",
        ".pytest_cache/",
        ".venv/",
        "venv/",
    ]

    current = path.read_text(encoding="utf-8") if path.exists() else ""
    existing = {line.strip() for line in current.splitlines()}
    missing = [x for x in wanted if x not in existing]

    if missing and not dry_run:
        with path.open("a", encoding="utf-8") as f:
            if current and not current.endswith("\n"):
                f.write("\n")
            f.write("\n# Repo cleanup / Python local output\n")
            for line in missing:
                f.write(x if False else line + "\n")

    return {"action": "gitignore", "added": missing, "dry_run": dry_run}


def write_file(rel: str, content: str, *, dry_run: bool, overwrite: bool = False) -> dict:
    path = ROOT / rel
    if path.exists() and not overwrite:
        return {"action": "skip", "path": rel, "reason": "exists"}

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    return {"action": "write", "path": rel, "dry_run": dry_run}


def make_wrapper(old_rel: str, new_module: str, *, dry_run: bool) -> dict:
    content = (
        '"""Compatibility wrapper created by Repo Cleanup v1.1.\n\n'
        f'Canonical module: {new_module}\n'
        'This module is intentionally excluded from pytest collection.\n'
        '"""\n'
        "__test__ = False\n\n"
        f"from {new_module} import *  # noqa: F401,F403\n"
    )
    return write_file(old_rel, content, dry_run=dry_run, overwrite=True)


def test_migrations(*, dry_run: bool, use_git: bool) -> list[dict]:
    actions: list[dict] = []

    mapping = [
        ("tests/test_engine_smoke.py", "tests/integration/test_game_smoke.py", None),
        ("tests/test_engine_v2.py", "tests/integration/test_engine_core.py", "tests.integration.test_engine_core"),
        ("tests/test_engine_v3.py", "tests/integration/test_turn_transform.py", "tests.integration.test_turn_transform"),
        ("tests/test_engine_v4.py", "tests/unit/test_keywords.py", "tests.unit.test_keywords"),
        ("tests/test_engine_v5.py", "tests/unit/test_health_keywords.py", "tests.unit.test_health_keywords"),
        ("tests/test_playtest_scenarios.py", "tests/scenarios/test_core_scenarios.py", None),
        ("tests/test_priority_window.py", "tests/unit/test_priority.py", None),
        ("tests/test_priority_compatibility.py", "tests/integration/test_priority_compatibility.py", None),
        ("tests/test_deck_out.py", "tests/unit/test_deck_out.py", None),
        ("tests/test_playtest_analytics.py", "tests/unit/test_playtest_analytics.py", None),
        ("tests/test_m1_m2_infrastructure.py", "tests/integration/test_m1_m2_infrastructure.py", None),
        ("tests/test_m1_1_m2_1_infrastructure.py", "tests/integration/test_m1_1_m2_1_infrastructure.py", None),
    ]

    for old_rel, new_rel, wrapper_module in mapping:
        src_exists = (ROOT / old_rel).exists()
        dst_exists = (ROOT / new_rel).exists()

        if src_exists and not dst_exists:
            actions.append(move(old_rel, new_rel, dry_run=dry_run, use_git=use_git))
            if wrapper_module:
                actions.append(make_wrapper(old_rel, wrapper_module, dry_run=dry_run))
        elif wrapper_module and dst_exists and not src_exists:
            actions.append(make_wrapper(old_rel, wrapper_module, dry_run=dry_run))
        else:
            actions.append({
                "action": "skip",
                "src": old_rel,
                "dst": new_rel,
                "reason": "source missing or destination already exists",
            })

    return actions


def archive_root_notes(*, dry_run: bool, use_git: bool) -> list[dict]:
    notes = [
        "M1_M2_IMPLEMENTATION.md",
        "M1_1_M2_1_README.md",
        "M1_2_M2_2_README.md",
        "HOTFIX_NOTES.md",
        "M1_2_HOTFIX_NOTES.md",
        "M1_2_HOTFIX_V2_NOTES.md",
        "DECKOUT_HOTFIX_NOTES.md",
        "REPO_CLEANUP_V1.md",
    ]

    actions = []
    for name in notes:
        actions.append(
            move(
                name,
                f"archive/notes/{name}",
                dry_run=dry_run,
                use_git=use_git,
            )
        )
    return actions


def remove_root_wrappers(*, dry_run: bool, use_git: bool) -> list[dict]:
    actions = []

    checks = [
        ("streamlit_app.py", "apps/battle_app.py"),
        ("playtest_dashboard.py", "apps/playtest_dashboard.py"),
    ]

    for old, canonical in checks:
        if (ROOT / canonical).exists():
            actions.append(delete(old, dry_run=dry_run, use_git=use_git))
        else:
            actions.append({
                "action": "keep",
                "path": old,
                "reason": f"{canonical} 尚不存在",
            })
    return actions


ARCH_DOC = """# Engine Architecture

## Current engine layers

```text
Game orchestration
→ Trigger Queue
→ Effect Queue
→ State-Based Check
→ Priority / Response Window
→ Combat resolution
→ Telemetry
```

### `src/core/`

Responsible for:
- game lifecycle
- turn orchestration
- trigger/event queue
- state-based actions
- priority windows

### `src/combat/`

Responsible for:
- legal attack targets
- combat damage
- combat-only keyword interaction

### `src/effects/`

Responsible for:
- effect definitions
- effect target resolution
- effect operations

### `src/playtest/`

Responsible for:
- structured telemetry
- scenario catalog
- cross-game analytics

## Rule implementation principle

Gameplay rules belong in the engine, not in Streamlit UI.

The UI may display legal choices, but it should not independently decide:
- winner
- legal attack target
- damage amount
- death
- deck-out
- transform
- response legality
"""

TIMING_DOC = """# Timing and Priority

## Trigger resolution

```text
Rules event
→ TriggerQueue
→ EffectQueue
→ Effect resolution
→ State-Based Check
```

Trigger events snapshot source identity and side so `on_leave` and `on_flip`
remain deterministic after the source moves or transforms.

## State-Based Check priority

1. simultaneous lethal Unit collection
2. enqueue `on_leave` using AP/NAP order
3. Transform checks
4. winner check

## Combat Priority Window

```text
Attack declared
→ defender gets Priority
→ Response / Pass
→ opponent gets Priority
→ ...
→ two consecutive Passes
→ Response stack resolves LIFO
→ combat resolves
```

If neither player has a legal Response, legacy direct `resolve_combat()` may
auto-pass the empty window.

## Deck-out

After setup, if a required draw cannot be completed because the deck is empty,
that player immediately loses.

Drawing the final card is legal; the loss happens on the next failed required draw.
"""

TELEMETRY_DOC = """# Playtest Telemetry

## Per-game outputs

### `event_log.csv`

Structured event stream. Common event types include:
- card_played
- attack_declared
- response_played
- priority_pass
- priority_auto_pass
- combat_damage_leader
- combat_damage_unit
- effect_damage
- heal
- transform
- unit_died
- trigger
- state_based_check
- deck_out
- game_end

### `game_summary.csv`

Cross-game summary fields include:
- game_id
- seed
- winner_index
- first_player_index
- turn_number
- leader HP
- deck IDs
- cards played
- attacks
- responses
- transforms
- deaths
- healing
- damage

## Directory convention

```text
playtest_data/
├─ raw/
└─ summaries/
```

Generated raw outputs should not be committed unless they are intentional fixtures.
"""

DASHBOARD_DOC = """# Playtest Dashboard

Entry point:

```powershell
py -m streamlit run apps/playtest_dashboard.py
```

The dashboard can read:
- CSV files under `playtest_data/`
- manually uploaded `game_summary.csv`
- manually uploaded `event_log.csv`

Current metrics:
- games
- average turns
- P1/P2 win rate
- first-player win rate
- deck win rate
- card usage
- response usage
- transform/death counts
- event distribution
- game-length distribution
"""


def update_changelog(*, dry_run: bool) -> dict:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    marker = "## Unreleased\n"

    entry = (
        "\n### Repository Cleanup v1.1\n"
        "- 將 milestone / hotfix 說明文件移至 `archive/notes/`。\n"
        "- 測試依 unit / integration / scenarios 重新分類。\n"
        "- 保留 `test_engine_v2~v5` compatibility wrapper，避免 fixture imports 中斷。\n"
        "- 移除已由 `apps/` 取代的根目錄 Streamlit launcher。\n"
        "- 補充 Engine Architecture、Timing/Priority、Telemetry 與 Playtest Dashboard 文件。\n"
        "- 清理一次性 repo cleanup report 並加入 `.gitignore`。\n"
    )

    if "### Repository Cleanup v1.1" in text:
        return {"action": "skip", "path": "CHANGELOG.md", "reason": "entry exists"}

    if marker in text:
        updated = text.replace(marker, marker + entry, 1)
    else:
        updated = (
            "# Changelog\n\n"
            "## Unreleased\n"
            + entry
            + "\n"
            + text
        )

    if not dry_run:
        path.write_text(updated, encoding="utf-8")

    return {"action": "update", "path": "CHANGELOG.md", "dry_run": dry_run}


def main() -> None:
    parser = argparse.ArgumentParser(description="Cardgame Repo Cleanup v1.1")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()

    ensure_repo()

    dry_run = not args.apply
    use_git = git_available()

    if args.apply and use_git and git_dirty() and not args.allow_dirty:
        fail(
            "Git working tree 有未提交變更。請先 commit/stash，"
            "或確認後使用 --allow-dirty。"
        )

    actions: list[dict] = []

    for rel in [
        "archive/notes",
        "tests/unit",
        "tests/integration",
        "tests/scenarios",
        "tests/fixtures",
        "docs/architecture",
        "docs/playtesting",
    ]:
        if not dry_run:
            (ROOT / rel).mkdir(parents=True, exist_ok=True)
        actions.append({"action": "mkdir", "path": rel, "dry_run": dry_run})

    actions.extend(archive_root_notes(dry_run=dry_run, use_git=use_git))

    actions.append(delete("repo_cleanup_report.json", dry_run=dry_run, use_git=use_git))
    actions.append(append_gitignore(dry_run=dry_run))

    actions.extend(test_migrations(dry_run=dry_run, use_git=use_git))
    actions.extend(remove_root_wrappers(dry_run=dry_run, use_git=use_git))

    actions.append(
        write_file(
            "docs/architecture/EngineArchitecture.md",
            ARCH_DOC,
            dry_run=dry_run,
            overwrite=True,
        )
    )
    actions.append(
        write_file(
            "docs/architecture/TimingAndPriority.md",
            TIMING_DOC,
            dry_run=dry_run,
            overwrite=True,
        )
    )
    actions.append(
        write_file(
            "docs/playtesting/Telemetry.md",
            TELEMETRY_DOC,
            dry_run=dry_run,
            overwrite=True,
        )
    )
    actions.append(
        write_file(
            "docs/playtesting/PlaytestDashboard.md",
            DASHBOARD_DOC,
            dry_run=dry_run,
            overwrite=True,
        )
    )

    actions.append(update_changelog(dry_run=dry_run))

    report = {
        "cleanup": "Repo Cleanup v1.1",
        "date": str(date.today()),
        "mode": "dry-run" if dry_run else "apply",
        "actions": actions,
    }

    if not dry_run:
        (ROOT / "repo_cleanup_v1_1_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if dry_run:
        print("\nDRY RUN 完成。確認後執行：")
        print("  py tools/repo_cleanup_v1_1.py --apply")
    else:
        print("\nRepo Cleanup v1.1 已套用。")
        print("請依序執行：")
        print("  py tools/audit_repo_v1_1.py")
        print("  py -m pytest -q")
        print("  git status")


if __name__ == "__main__":
    main()
