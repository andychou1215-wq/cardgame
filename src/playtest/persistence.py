from __future__ import annotations
import csv, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

class PlaytestStore:
    def __init__(self, root: str | Path = "playtest_data") -> None:
        self.root = Path(root)
        self.raw_dir = self.root / "raw"
        self.summary_dir = self.root / "summaries"
        self.replay_dir = self.root / "replays"
        for d in (self.raw_dir, self.summary_dir, self.replay_dir):
            d.mkdir(parents=True, exist_ok=True)

    def save_game(self, recorder: Any, game: Any, *, rules_version: str = "", commit_hash: str = "") -> dict[str, str]:
        summary = recorder.summary(game)
        summary["rules_version"] = rules_version
        summary["commit_hash"] = commit_hash
        gid = summary["game_id"]
        sp = self.summary_dir / "game_summary.csv"
        ep = self.raw_dir / "event_log.csv"
        rp = self.replay_dir / f"{gid}.json"
        self._append_row(sp, summary)
        self._append_rows(ep, recorder.rows())
        rp.write_text(json.dumps({
            "game": summary,
            "events": recorder.rows(),
            "saved_at": datetime.now(timezone.utc).isoformat()
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"game_id": gid, "summary": str(sp), "events": str(ep), "replay": str(rp)}

    def replay_index(self) -> list[dict[str, Any]]:
        out = []
        for p in sorted(self.replay_dir.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            g = data.get("game", {})
            out.append({
                "game_id": g.get("game_id", p.stem),
                "winner_index": g.get("winner_index"),
                "turn_number": g.get("turn_number"),
                "seed": g.get("seed"),
                "deck_id_p1": g.get("deck_id_p1", ""),
                "deck_id_p2": g.get("deck_id_p2", ""),
                "rules_version": g.get("rules_version", ""),
                "commit_hash": g.get("commit_hash", ""),
                "path": str(p),
            })
        return out

    @staticmethod
    def _append_row(path: Path, row: dict[str, Any]) -> None:
        exists = path.exists() and path.stat().st_size > 0
        with path.open("a", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            if not exists: w.writeheader()
            w.writerow(row)

    @staticmethod
    def _append_rows(path: Path, rows: list[dict[str, Any]]) -> None:
        if not rows: return
        exists = path.exists() and path.stat().st_size > 0
        with path.open("a", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            if not exists: w.writeheader()
            w.writerows(rows)
