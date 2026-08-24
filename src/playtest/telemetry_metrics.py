from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import csv


def read_csv(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def rebuild_card_usage_metrics(
    event_rows: list[dict],
    *,
    card_lookup: dict[str, dict] | None = None,
    summary_rows: list[dict] | None = None,
) -> dict:
    """Build corrected usage metrics from raw telemetry events.

    Important semantics:

    - normal_play_events: `card_played`
    - response_play_events: `response_played`
    - use_events: normal + response usage
    - recorded_draw_events: only explicit `card_drawn`

    `uses_per_recorded_draw` is NOT a probability. It may exceed 1 when the
    telemetry log does not include all hand-acquisition sources such as initial
    hand or Mulligan replacement.
    """

    card_lookup = card_lookup or {}
    summary_rows = summary_rows or []

    event_type_col = _first_column(
        event_rows, ["event_type", "type", "event", "name"]
    )
    card_col = _first_column(
        event_rows, ["card_id", "source_card_id", "card"]
    )
    game_col = _first_column(
        event_rows, ["game_id", "match_id"]
    )
    player_col = _first_column(
        event_rows,
        ["player_index", "source_player_index", "controller_index", "side"],
    )
    turn_col = _first_column(event_rows, ["turn_number", "turn"])

    winner_map = _winner_map(summary_rows)

    capabilities = {
        "event_type": bool(event_type_col),
        "card_id": bool(card_col),
        "game_id": bool(game_col),
        "player_index": bool(player_col),
        "turn": bool(turn_col),
        "winner_join": bool(winner_map and game_col and player_col),
        "initial_hand_event": False,
        "mulligan_acquisition_event": False,
        "recorded_draw_is_complete_hand_acquisition": False,
    }

    if not event_type_col or not card_col:
        return {
            "available": False,
            "reason": "event log lacks event_type/card_id",
            "capabilities": capabilities,
            "cards": [],
        }

    seen_event_types = {
        str(row.get(event_type_col, "")).strip()
        for row in event_rows
    }

    initial_types = {
        "initial_hand_card",
        "starting_hand_card",
        "card_added_to_starting_hand",
    }
    mulligan_types = {
        "mulligan_card_drawn",
        "mulligan_replacement",
        "mulligan_card_added",
    }

    capabilities["initial_hand_event"] = bool(
        seen_event_types & initial_types
    )
    capabilities["mulligan_acquisition_event"] = bool(
        seen_event_types & mulligan_types
    )
    capabilities["recorded_draw_is_complete_hand_acquisition"] = (
        capabilities["initial_hand_event"]
        and capabilities["mulligan_acquisition_event"]
    )

    by_card = defaultdict(lambda: {
        "recorded_draw_events": 0,
        "initial_hand_events": 0,
        "mulligan_acquisition_events": 0,
        "normal_play_events": 0,
        "response_play_events": 0,
        "transform_events": 0,
        "effect_damage_events": 0,
        "heal_events": 0,
        "use_turn_total": 0,
        "use_turn_n": 0,
        "used_games": set(),
        "used_wins": set(),
    })

    for row in event_rows:
        card_id = str(row.get(card_col, "")).strip()
        if not card_id:
            continue

        event_type = str(row.get(event_type_col, "")).strip()
        metrics = by_card[card_id]

        if event_type == "card_drawn":
            metrics["recorded_draw_events"] += 1
        elif event_type in initial_types:
            metrics["initial_hand_events"] += 1
        elif event_type in mulligan_types:
            metrics["mulligan_acquisition_events"] += 1
        elif event_type == "card_played":
            metrics["normal_play_events"] += 1
            _record_use_context(
                metrics, row, game_col, player_col, turn_col, winner_map
            )
        elif event_type == "response_played":
            metrics["response_play_events"] += 1
            _record_use_context(
                metrics, row, game_col, player_col, turn_col, winner_map
            )
        elif event_type == "transform":
            metrics["transform_events"] += 1
        elif event_type == "effect_damage":
            metrics["effect_damage_events"] += 1
        elif event_type == "heal":
            metrics["heal_events"] += 1

    rows = []
    all_ids = sorted(set(card_lookup) | set(by_card))

    for card_id in all_ids:
        m = by_card[card_id]
        use_events = (
            m["normal_play_events"]
            + m["response_play_events"]
        )
        recorded_acquisitions = (
            m["recorded_draw_events"]
            + m["initial_hand_events"]
            + m["mulligan_acquisition_events"]
        )

        used_games = len(m["used_games"])

        rows.append({
            "card_id": card_id,
            "name": card_lookup.get(card_id, {}).get("name", ""),
            "recorded_draw_events": m["recorded_draw_events"],
            "initial_hand_events": m["initial_hand_events"],
            "mulligan_acquisition_events": m[
                "mulligan_acquisition_events"
            ],
            "recorded_hand_acquisitions": recorded_acquisitions,
            "normal_play_events": m["normal_play_events"],
            "response_play_events": m["response_play_events"],
            "use_events": use_events,
            "uses_per_recorded_draw": (
                round(
                    use_events / m["recorded_draw_events"],
                    4,
                )
                if m["recorded_draw_events"] else ""
            ),
            "uses_per_recorded_acquisition": (
                round(
                    use_events / recorded_acquisitions,
                    4,
                )
                if recorded_acquisitions else ""
            ),
            "avg_use_turn": (
                round(m["use_turn_total"] / m["use_turn_n"], 3)
                if m["use_turn_n"] else ""
            ),
            "games_used": used_games if game_col else "",
            "wins_when_used": (
                len(m["used_wins"])
                if capabilities["winner_join"] else ""
            ),
            "win_rate_when_used": (
                round(len(m["used_wins"]) / used_games, 4)
                if capabilities["winner_join"] and used_games
                else ""
            ),
            "transform_events": m["transform_events"],
            "effect_damage_events": m["effect_damage_events"],
            "heal_events": m["heal_events"],

            # Backward-compatibility aliases for M3.5.4.
            # These should be considered deprecated.
            "draw_events": m["recorded_draw_events"],
            "play_events": use_events,
            "play_given_draw_rate": (
                round(
                    use_events / m["recorded_draw_events"],
                    4,
                )
                if m["recorded_draw_events"] else ""
            ),
            "avg_play_turn": (
                round(m["use_turn_total"] / m["use_turn_n"], 3)
                if m["use_turn_n"] else ""
            ),
            "games_played": used_games if game_col else "",
            "wins_when_played": (
                len(m["used_wins"])
                if capabilities["winner_join"] else ""
            ),
            "win_rate_when_played": (
                round(len(m["used_wins"]) / used_games, 4)
                if capabilities["winner_join"] and used_games
                else ""
            ),
            "response_events": m["response_play_events"],
        })

    return {
        "available": True,
        "reason": "",
        "capabilities": capabilities,
        "cards": rows,
    }


def _record_use_context(
    metrics,
    row,
    game_col,
    player_col,
    turn_col,
    winner_map,
):
    if turn_col:
        turn = _int(row.get(turn_col))
        if turn is not None:
            metrics["use_turn_total"] += turn
            metrics["use_turn_n"] += 1

    if game_col:
        game_id = str(row.get(game_col, "")).strip()
        if game_id:
            metrics["used_games"].add(game_id)
            if winner_map and player_col:
                player_index = _player_index(row.get(player_col))
                if (
                    player_index is not None
                    and winner_map.get(game_id) == player_index
                ):
                    metrics["used_wins"].add(game_id)


def _winner_map(rows):
    if not rows:
        return {}

    game_col = _first_column(rows, ["game_id", "match_id"])
    winner_col = _first_column(
        rows,
        ["winner_index", "winner", "winning_player_index"],
    )
    if not game_col or not winner_col:
        return {}

    out = {}
    for row in rows:
        game_id = str(row.get(game_col, "")).strip()
        winner = _player_index(row.get(winner_col))
        if game_id and winner is not None:
            out[game_id] = winner
    return out


def _first_column(rows, candidates):
    if not rows:
        return None
    cols = set()
    for row in rows[:20]:
        cols.update(row.keys())
    for candidate in candidates:
        if candidate in cols:
            return candidate
    return None


def _player_index(value):
    if value in (None, ""):
        return None
    text = str(value).strip().lower()
    if text in {"0", "p1", "player1", "player_1"}:
        return 0
    if text in {"1", "p2", "player2", "player_2"}:
        return 1
    try:
        value = int(text)
        return value if value in (0, 1) else None
    except ValueError:
        return None


def _int(value):
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
