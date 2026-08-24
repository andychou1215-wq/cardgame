from __future__ import annotations

import csv
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
    """Structured playtest telemetry for manual and automated matches."""

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
                target_instance_id=getattr(target, "instance_id", "") or "" if target is not None else "",
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
            "event_count": len(self.events),
            "cards_played": counts.get("card_played", 0),
            "responses_played": counts.get("response_played", 0),
            "attacks_declared": counts.get("attack_declared", 0),
            "transforms": counts.get("transform", 0),
            "units_died": counts.get("unit_died", 0),
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
                    "leader_hp_p1": game.players[0].leader_health,
                    "leader_hp_p2": game.players[1].leader_health,
                    "deck_id_p1": game.players[0].deck_id,
                    "deck_id_p2": game.players[1].deck_id,
                }
            )
        return result

    def rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for event in self.events:
            row = asdict(event)
            row["game_id"] = self.game_id
            row["metadata"] = json.dumps(row["metadata"] or {}, ensure_ascii=False, sort_keys=True)
            rows.append(row)
        return rows

    def export_json(self, path: str | Path, game: Any | None = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "game": self.summary(game),
            "created_at": self.created_at,
            "events": self.rows(),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def export_csv(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = self.rows()
        fieldnames = [
            "game_id",
            "seq",
            "event_type",
            "turn",
            "active_player",
            "player_index",
            "card_id",
            "source_id",
            "target_kind",
            "target_player_index",
            "target_instance_id",
            "amount",
            "metadata",
        ]
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path
