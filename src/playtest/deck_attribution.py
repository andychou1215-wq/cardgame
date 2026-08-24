from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import csv


P1_DECK_COLUMNS = (
    "deck_p1",
    "p1_deck",
    "player1_deck",
    "player_1_deck",
    "deck1",
)
P2_DECK_COLUMNS = (
    "deck_p2",
    "p2_deck",
    "player2_deck",
    "player_2_deck",
    "deck2",
)


def read_csv(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_static_membership(card_efficiency_rows: list[dict]) -> dict[str, set[str]]:
    membership: dict[str, set[str]] = defaultdict(set)

    for row in card_efficiency_rows:
        card_id = str(row.get("card_id", "")).strip()
        deck_id = str(row.get("deck_id", "")).strip()
        if card_id and deck_id:
            membership[card_id].add(deck_id)

    return dict(membership)


def build_game_player_deck_map(
    *sources: list[dict],
) -> tuple[dict[tuple[str, int], str], dict]:
    """Build (game_id, player_index) -> deck_id mapping.

    Supported sources may be game summaries or future mirrored game detail,
    provided they expose game_id + P1/P2 deck columns.
    """

    mapping: dict[tuple[str, int], str] = {}
    diagnostics = {
        "rows_examined": 0,
        "rows_with_game_id": 0,
        "rows_with_deck_pair": 0,
        "conflicts": [],
        "supported": False,
    }

    for rows in sources:
        if not rows:
            continue

        game_col = _first_column(rows, ("game_id", "match_id"))
        p1_col = _first_column(rows, P1_DECK_COLUMNS)
        p2_col = _first_column(rows, P2_DECK_COLUMNS)

        if not game_col or not p1_col or not p2_col:
            continue

        diagnostics["supported"] = True

        for row in rows:
            diagnostics["rows_examined"] += 1
            game_id = str(row.get(game_col, "")).strip()
            if not game_id:
                continue
            diagnostics["rows_with_game_id"] += 1

            p1_deck = str(row.get(p1_col, "")).strip()
            p2_deck = str(row.get(p2_col, "")).strip()

            if p1_deck and p2_deck:
                diagnostics["rows_with_deck_pair"] += 1

            for player_index, deck_id in ((0, p1_deck), (1, p2_deck)):
                if not deck_id:
                    continue

                key = (game_id, player_index)
                previous = mapping.get(key)
                if previous and previous != deck_id:
                    diagnostics["conflicts"].append(
                        {
                            "game_id": game_id,
                            "player_index": player_index,
                            "previous_deck": previous,
                            "new_deck": deck_id,
                        }
                    )
                    continue

                mapping[key] = deck_id

    return mapping, diagnostics


def attribute_events_to_decks(
    event_rows: list[dict],
    membership: dict[str, set[str]],
    game_player_deck_map: dict[tuple[str, int], str],
) -> dict:
    event_type_col = _first_column(
        event_rows, ("event_type", "type", "event", "name")
    )
    card_col = _first_column(
        event_rows, ("card_id", "source_card_id", "card")
    )
    game_col = _first_column(event_rows, ("game_id", "match_id"))
    player_col = _first_column(
        event_rows,
        (
            "player_index",
            "source_player_index",
            "controller_index",
            "side",
        ),
    )

    attributed = []
    unresolved_shared = defaultdict(lambda: {
        "events": 0,
        "event_types": defaultdict(int),
        "reason": "",
    })

    counts = {
        "total_card_events": 0,
        "unique_membership_inferred": 0,
        "game_player_attributed": 0,
        "shared_unattributed": 0,
        "unknown_card": 0,
    }

    if not event_type_col or not card_col:
        return {
            "events": [],
            "unresolved_shared": [],
            "counts": counts,
            "capabilities": {
                "event_type": bool(event_type_col),
                "card_id": bool(card_col),
                "game_id": bool(game_col),
                "player_index": bool(player_col),
                "game_player_deck_map": bool(game_player_deck_map),
            },
        }

    for row in event_rows:
        card_id = str(row.get(card_col, "")).strip()
        if not card_id:
            continue

        counts["total_card_events"] += 1
        decks = membership.get(card_id, set())
        deck_id = ""
        attribution_method = ""

        if len(decks) == 1:
            deck_id = next(iter(decks))
            attribution_method = "unique_static_membership"
            counts["unique_membership_inferred"] += 1

        elif len(decks) > 1:
            game_id = (
                str(row.get(game_col, "")).strip()
                if game_col else ""
            )
            player_index = (
                _player_index(row.get(player_col))
                if player_col else None
            )

            if (
                game_id
                and player_index is not None
                and (game_id, player_index) in game_player_deck_map
            ):
                candidate = game_player_deck_map[(game_id, player_index)]
                if candidate in decks:
                    deck_id = candidate
                    attribution_method = "game_player_join"
                    counts["game_player_attributed"] += 1

            if not deck_id:
                counts["shared_unattributed"] += 1
                item = unresolved_shared[card_id]
                item["events"] += 1
                event_type = str(row.get(event_type_col, "")).strip()
                item["event_types"][event_type] += 1
                item["reason"] = (
                    "shared card requires game_id + player_index -> deck mapping"
                )
                continue

        else:
            counts["unknown_card"] += 1
            continue

        enriched = dict(row)
        enriched["deck_id"] = deck_id
        enriched["attribution_method"] = attribution_method
        attributed.append(enriched)

    unresolved_rows = []
    for card_id, item in sorted(unresolved_shared.items()):
        unresolved_rows.append({
            "card_id": card_id,
            "candidate_decks": "|".join(sorted(membership.get(card_id, set()))),
            "events": item["events"],
            "event_types": "|".join(
                f"{event_type}:{count}"
                for event_type, count in sorted(item["event_types"].items())
            ),
            "reason": item["reason"],
        })

    return {
        "events": attributed,
        "unresolved_shared": unresolved_rows,
        "counts": counts,
        "capabilities": {
            "event_type": bool(event_type_col),
            "card_id": bool(card_col),
            "game_id": bool(game_col),
            "player_index": bool(player_col),
            "game_player_deck_map": bool(game_player_deck_map),
        },
    }


def aggregate_deck_card_usage(
    attributed_events: list[dict],
    summary_rows: list[dict],
) -> list[dict]:
    if not attributed_events:
        return []

    event_type_col = _first_column(
        attributed_events, ("event_type", "type", "event", "name")
    )
    card_col = _first_column(
        attributed_events, ("card_id", "source_card_id", "card")
    )
    game_col = _first_column(
        attributed_events, ("game_id", "match_id")
    )
    player_col = _first_column(
        attributed_events,
        (
            "player_index",
            "source_player_index",
            "controller_index",
            "side",
        ),
    )
    turn_col = _first_column(
        attributed_events, ("turn_number", "turn")
    )

    winner_map = _winner_map(summary_rows)

    metrics = defaultdict(lambda: {
        "recorded_draw_events": 0,
        "normal_play_events": 0,
        "response_play_events": 0,
        "transform_events": 0,
        "effect_damage_events": 0,
        "heal_events": 0,
        "use_turn_total": 0,
        "use_turn_n": 0,
        "used_games": set(),
        "used_wins": set(),
        "attribution_methods": set(),
    })

    for row in attributed_events:
        deck_id = str(row.get("deck_id", "")).strip()
        card_id = str(row.get(card_col, "")).strip()
        if not deck_id or not card_id:
            continue

        key = (deck_id, card_id)
        m = metrics[key]
        event_type = str(row.get(event_type_col, "")).strip()

        m["attribution_methods"].add(
            str(row.get("attribution_method", "")).strip()
        )

        if event_type == "card_drawn":
            m["recorded_draw_events"] += 1

        elif event_type == "card_played":
            m["normal_play_events"] += 1
            _record_use(
                m, row, game_col, player_col, turn_col, winner_map
            )

        elif event_type == "response_played":
            m["response_play_events"] += 1
            _record_use(
                m, row, game_col, player_col, turn_col, winner_map
            )

        elif event_type == "transform":
            m["transform_events"] += 1

        elif event_type == "effect_damage":
            m["effect_damage_events"] += 1

        elif event_type == "heal":
            m["heal_events"] += 1

    rows = []
    for (deck_id, card_id), m in sorted(metrics.items()):
        use_events = (
            m["normal_play_events"] + m["response_play_events"]
        )
        used_games = len(m["used_games"])

        rows.append({
            "deck_id": deck_id,
            "card_id": card_id,
            "recorded_draw_events": m["recorded_draw_events"],
            "normal_play_events": m["normal_play_events"],
            "response_play_events": m["response_play_events"],
            "use_events": use_events,
            "uses_per_recorded_draw": (
                round(use_events / m["recorded_draw_events"], 4)
                if m["recorded_draw_events"] else ""
            ),
            "avg_use_turn": (
                round(m["use_turn_total"] / m["use_turn_n"], 3)
                if m["use_turn_n"] else ""
            ),
            "games_used": used_games if game_col else "",
            "wins_when_used": (
                len(m["used_wins"])
                if winner_map and game_col and player_col else ""
            ),
            "win_rate_when_used": (
                round(len(m["used_wins"]) / used_games, 4)
                if winner_map and game_col and player_col and used_games
                else ""
            ),
            "transform_events": m["transform_events"],
            "effect_damage_events": m["effect_damage_events"],
            "heal_events": m["heal_events"],
            "attribution_method": "|".join(
                sorted(x for x in m["attribution_methods"] if x)
            ),
        })

    return rows


def _record_use(m, row, game_col, player_col, turn_col, winner_map):
    if turn_col:
        turn = _int(row.get(turn_col))
        if turn is not None:
            m["use_turn_total"] += turn
            m["use_turn_n"] += 1

    if game_col:
        game_id = str(row.get(game_col, "")).strip()
        if game_id:
            m["used_games"].add(game_id)
            if winner_map and player_col:
                player_index = _player_index(row.get(player_col))
                if (
                    player_index is not None
                    and winner_map.get(game_id) == player_index
                ):
                    m["used_wins"].add(game_id)


def _winner_map(rows):
    game_col = _first_column(rows, ("game_id", "match_id"))
    winner_col = _first_column(
        rows, ("winner_index", "winner", "winning_player_index")
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
    columns = set()
    for row in rows[:50]:
        columns.update(row.keys())
    for candidate in candidates:
        if candidate in columns:
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
        number = int(text)
        return number if number in (0, 1) else None
    except ValueError:
        return None


def _int(value):
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
