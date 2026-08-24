from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class PlaytestEvent:
    seq: int
    event_type: str
    turn: int
    active_player: int
    player_index: int | None = None
    card_id: str = ""
    source_id: str = ""
    target_kind: str = ""
    target_player_index: int | None = None
    target_instance_id: str = ""
    amount: int | None = None
    metadata: dict[str, Any] | None = None


class PlaytestRecorder:
    EVENT_FIELDS = [
        "game_id", "seq", "event_type", "turn", "active_player",
        "player_index", "card_id", "source_id", "target_kind",
        "target_player_index", "target_instance_id", "amount", "metadata",
    ]

    def __init__(self, seed: int | None = None, game_id: str | None = None) -> None:
        self.game_id = game_id or uuid4().hex
        self.seed = seed
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.events: list[PlaytestEvent] = []

    def record(
        self,
        event_type: str,
        *,
        turn: int,
        active_player: int,
        player_index: int | None = None,
        card_id: str = "",
        source_id: str = "",
        target: Any | None = None,
        amount: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            PlaytestEvent(
                seq=len(self.events) + 1,
                event_type=event_type,
                turn=turn,
                active_player=active_player,
                player_index=player_index,
                card_id=card_id,
                source_id=source_id,
                target_kind=getattr(target, "kind", "") if target is not None else "",
                target_player_index=getattr(target, "player_index", None) if target is not None else None,
                target_instance_id=(getattr(target, "instance_id", "") or "") if target is not None else "",
                amount=amount,
                metadata=metadata or {},
            )
        )

    def summary(self, game: Any | None = None) -> dict[str, Any]:
        counts: dict[str, int] = {}
        sums: dict[str, int] = {}
        for event in self.events:
            counts[event.event_type] = counts.get(event.event_type, 0) + 1
            if event.amount is not None:
                sums[event.event_type] = sums.get(event.event_type, 0) + event.amount

        result: dict[str, Any] = {
            "game_id": self.game_id,
            "seed": self.seed,
            "created_at": self.created_at,
            "event_count": len(self.events),
            "cards_played": counts.get("card_played", 0),
            "responses_played": counts.get("response_played", 0),
            "attacks_declared": counts.get("attack_declared", 0),
            "transforms": counts.get("transform", 0),
            "units_died": counts.get("unit_died", 0),
            "triggers_queued": counts.get("trigger", 0),
            "state_based_passes": counts.get("state_based_check", 0),
            "cards_drawn": sums.get("draw", 0),
            "healing_done": sums.get("heal", 0),
            "combat_damage_to_leader": sums.get("combat_damage_leader", 0),
            "combat_damage_to_unit": sums.get("combat_damage_unit", 0),
            "effect_damage": sums.get("effect_damage", 0),
        }

        if game is not None:
            result.update(
                {
                    "winner_index": game.winner_index,
                    "turn_number": game.turn_number,
                    "active_player_index": game.active_player_index,
                    "leader_hp_p1": game.players[0].leader_health,
                    "leader_hp_p2": game.players[1].leader_health,
                    "deck_id_p1": game.players[0].deck_id,
                    "deck_id_p2": game.players[1].deck_id,
                    "hand_p1": len(game.players[0].hand),
                    "hand_p2": len(game.players[1].hand),
                    "battlefield_p1": len(game.players[0].battlefield),
                    "battlefield_p2": len(game.players[1].battlefield),
                }
            )
        return result

    def rows(self) -> list[dict[str, Any]]:
        rows = []
        for event in self.events:
            row = asdict(event)
            row["game_id"] = self.game_id
            row["metadata"] = json.dumps(row["metadata"] or {}, ensure_ascii=False, sort_keys=True)
            rows.append(row)
        return rows

    def events_csv_text(self) -> str:
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=self.EVENT_FIELDS)
        writer.writeheader()
        writer.writerows(self.rows())
        return out.getvalue()

    def summary_csv_text(self, game: Any | None = None) -> str:
        row = self.summary(game)
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)
        return out.getvalue()

    def export_csv(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.events_csv_text(), encoding="utf-8-sig")
        return path

    def export_summary_csv(self, path: str | Path, game: Any | None = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.summary_csv_text(game), encoding="utf-8-sig")
        return path

    def export_json(self, path: str | Path, game: Any | None = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"game": self.summary(game), "events": self.rows()}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path


def append_game_summary(path: str | Path, recorder: PlaytestRecorder, game: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = recorder.summary(game)
    exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return path


def append_event_log(path: str | Path, recorder: PlaytestRecorder) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=recorder.EVENT_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerows(recorder.rows())
    return path
