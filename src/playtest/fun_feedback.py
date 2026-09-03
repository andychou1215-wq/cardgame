from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


RATING_FIELDS = (
    "decision_depth",
    "u011_playability",
    "u011_payoff",
    "shelter_clarity",
    "fairness",
    "replay_desire",
    "overall_fun",
)


@dataclass(frozen=True)
class FunFeedback:
    game_id: str
    human_player_index: int
    human_deck: str
    ai_deck: str
    winner_index: int
    first_player_index: int | None
    turn_number: int
    human_won: bool
    decision_depth: int
    u011_playability: int
    u011_payoff: int
    shelter_clarity: int
    fairness: int
    replay_desire: int
    overall_fun: int
    u011_drawn: int = 0
    u011_played: int = 0
    u011_transformed: int = 0
    notes: str = ""
    submitted_at: str = ""

    def to_row(self) -> dict[str, object]:
        row = asdict(self)
        row["submitted_at"] = self.submitted_at or datetime.now(
            timezone.utc
        ).isoformat()
        row["human_won"] = str(self.human_won).lower()
        return row


def validate_feedback(feedback: FunFeedback) -> None:
    for field_name in RATING_FIELDS:
        value = getattr(feedback, field_name)
        if not 1 <= value <= 5:
            raise ValueError(f"{field_name} must be between 1 and 5")
    if feedback.human_player_index not in (0, 1):
        raise ValueError("human_player_index must be 0 or 1")


def append_fun_feedback(path: str | Path, feedback: FunFeedback) -> Path:
    validate_feedback(feedback)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = feedback.to_row()
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return path


def card_exposure(game, player_index: int, card_id: str) -> dict[str, int]:
    events = getattr(getattr(game, "telemetry", None), "events", [])
    return {
        "drawn": sum(
            event.event_type == "card_drawn"
            and event.player_index == player_index
            and event.card_id == card_id
            for event in events
        ),
        "played": sum(
            event.event_type == "card_played"
            and event.player_index == player_index
            and event.card_id == card_id
            for event in events
        ),
        "transformed": sum(
            event.event_type == "transform"
            and event.player_index == player_index
            and event.card_id == card_id
            for event in events
        ),
    }

