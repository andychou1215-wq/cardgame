from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

root_noise = [
    "M1_M2_IMPLEMENTATION.md",
    "M1_1_M2_1_README.md",
    "M1_2_M2_2_README.md",
    "HOTFIX_NOTES.md",
    "M1_2_HOTFIX_NOTES.md",
    "M1_2_HOTFIX_V2_NOTES.md",
    "DECKOUT_HOTFIX_NOTES.md",
    "REPO_CLEANUP_V1.md",
    "repo_cleanup_report.json",
]

checks = {
    "archive/notes": (ROOT / "archive/notes").is_dir(),
    "tests/unit": (ROOT / "tests/unit").is_dir(),
    "tests/integration": (ROOT / "tests/integration").is_dir(),
    "tests/scenarios": (ROOT / "tests/scenarios").is_dir(),
    "EngineArchitecture.md": (ROOT / "docs/architecture/EngineArchitecture.md").exists(),
    "TimingAndPriority.md": (ROOT / "docs/architecture/TimingAndPriority.md").exists(),
    "Telemetry.md": (ROOT / "docs/playtesting/Telemetry.md").exists(),
    "PlaytestDashboard.md": (ROOT / "docs/playtesting/PlaytestDashboard.md").exists(),
    "apps/battle_app.py": (ROOT / "apps/battle_app.py").exists(),
    "apps/playtest_dashboard.py": (ROOT / "apps/playtest_dashboard.py").exists(),
}

print("=== Repo Cleanup v1.1 Audit ===")
failed = False

for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + f": {name}")
    failed |= not ok

remaining = [x for x in root_noise if (ROOT / x).exists()]
print(("PASS" if not remaining else "WARN") + f": root historical files remaining = {len(remaining)}")
for item in remaining:
    print("  -", item)

wrappers = [
    "tests/test_engine_v2.py",
    "tests/test_engine_v3.py",
    "tests/test_engine_v4.py",
    "tests/test_engine_v5.py",
]
for rel in wrappers:
    p = ROOT / rel
    if p.exists():
        text = p.read_text(encoding="utf-8")
        ok = "__test__ = False" in text
        print(("PASS" if ok else "WARN") + f": compatibility wrapper {rel}")

if failed:
    sys.exit(1)

print("\nStructure audit passed.")
