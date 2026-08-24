from __future__ import annotations

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

checks = {
    "apps directory": (ROOT / "apps").is_dir(),
    "architecture docs": (ROOT / "docs/architecture").is_dir(),
    "playtesting docs": (ROOT / "docs/playtesting").is_dir(),
    "archive patches": (ROOT / "archive/patches").is_dir(),
    "playtest raw": (ROOT / "playtest_data/raw").is_dir(),
    "playtest summaries": (ROOT / "playtest_data/summaries").is_dir(),
    ".gitignore": (ROOT / ".gitignore").exists(),
    "repo structure doc": (ROOT / "docs/architecture/RepoStructure.md").exists(),
    "test migration manifest": (ROOT / "tests/TEST_MIGRATION.json").exists(),
}

cache_dirs = [
    str(p.relative_to(ROOT))
    for p in ROOT.rglob("__pycache__")
    if ".git" not in p.parts
]
apply_scripts = [
    str(p.relative_to(ROOT))
    for p in (ROOT / "tools").glob("apply*.py")
] if (ROOT / "tools").exists() else []

print("=== Repo Cleanup Audit ===")
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + f": {name}")

print(f"{'PASS' if not cache_dirs else 'WARN'}: __pycache__ remaining = {len(cache_dirs)}")
for item in cache_dirs[:10]:
    print("  -", item)

print(f"{'PASS' if not apply_scripts else 'WARN'}: active tools/apply*.py = {len(apply_scripts)}")
for item in apply_scripts:
    print("  -", item)

if all(checks.values()) and not apply_scripts:
    print("\nStructure audit passed.")
else:
    print("\nStructure audit has warnings/failures; inspect above.")
