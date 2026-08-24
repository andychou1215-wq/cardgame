from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import csv
import json
from typing import Iterable


STATIC_FILES = {
    "cards": Path("data/cards/cards.csv"),
    "unit_sides": Path("data/cards/unit_sides.csv"),
    "effects": Path("data/cards/effects.csv"),
    "deck_cards": Path("data/decks/deck_cards.csv"),
    "decks": Path("data/decks/decks.csv"),
}


def run_card_deck_diagnostics(
    root: str | Path,
    *,
    event_log: str | Path | None = None,
    game_summary: str | Path | None = None,
) -> dict:
    root = Path(root)

    tables = {
        name: read_csv_tolerant(root / rel)
        for name, rel in STATIC_FILES.items()
    }

    static = build_static_diagnostics(tables)

    event_path = (
        Path(event_log)
        if event_log
        else root / "playtest_data" / "raw" / "event_log.csv"
    )
    summary_path = (
        Path(game_summary)
        if game_summary
        else root / "playtest_data" / "summaries" / "game_summary.csv"
    )

    telemetry = build_telemetry_diagnostics(
        event_path if event_path.exists() else None,
        summary_path if summary_path.exists() else None,
        static["card_lookup"],
    )

    return {
        **static,
        "telemetry": telemetry,
    }


def build_static_diagnostics(tables: dict[str, list[dict]]) -> dict:
    cards = tables["cards"]
    sides = tables["unit_sides"]
    effects = tables["effects"]
    deck_cards = tables["deck_cards"]
    decks = tables["decks"]

    cards_by_id = {
        row.get("id", "").strip(): row
        for row in cards
        if row.get("id", "").strip()
    }

    side_map: dict[str, list[dict]] = defaultdict(list)
    for row in sides:
        card_id = row.get("card_id", "").strip()
        if card_id:
            side_map[card_id].append(row)

    effect_map: dict[str, list[dict]] = defaultdict(list)
    for row in effects:
        card_id = row.get("card_id", "").strip()
        if card_id:
            effect_map[card_id].append(row)

    decks_by_id = {
        row.get("deck_id", "").strip(): row
        for row in decks
        if row.get("deck_id", "").strip()
    }

    membership: dict[str, list[dict]] = defaultdict(list)
    for row in deck_cards:
        deck_id = row.get("deck_id", "").strip()
        card_id = row.get("card_id", "").strip()
        if not deck_id or not card_id:
            continue
        membership[deck_id].append({
            "card_id": card_id,
            "quantity": _int(row.get("quantity"), 0),
        })

    card_rows = []
    for deck_id, members in sorted(membership.items()):
        for member in members:
            card_id = member["card_id"]
            quantity = member["quantity"]
            card = cards_by_id.get(card_id, {})
            card_sides = side_map.get(card_id, [])
            card_effects = effect_map.get(card_id, [])

            front, back = _front_back(card_sides)
            cost = _int(card.get("cost"), 0)
            front_atk = _int(front.get("attack") if front else None, 0)
            front_hp = _int(front.get("max_health") if front else None, 0)
            back_atk = _int(back.get("attack") if back else None, 0)
            back_hp = _int(back.get("max_health") if back else None, 0)

            keyword_set = set()
            for side in card_sides:
                keyword_set.update(_split_tokens(side.get("keywords", "")))

            operations = sorted(
                {
                    e.get("operation", "").strip()
                    for e in card_effects
                    if e.get("operation", "").strip()
                }
            )
            triggers = sorted(
                {
                    e.get("trigger", "").strip()
                    for e in card_effects
                    if e.get("trigger", "").strip()
                }
            )

            card_rows.append({
                "deck_id": deck_id,
                "deck_name": decks_by_id.get(deck_id, {}).get("name", ""),
                "card_id": card_id,
                "name": card.get("name", ""),
                "type": card.get("type", ""),
                "faction_id": card.get("faction_id", ""),
                "rarity": card.get("rarity", ""),
                "quantity": quantity,
                "cost": cost,
                "front_attack": front_atk if front else "",
                "front_health": front_hp if front else "",
                "front_stats_per_mana": (
                    round((front_atk + front_hp) / cost, 3)
                    if front and cost > 0
                    else ""
                ),
                "back_attack": back_atk if back else "",
                "back_health": back_hp if back else "",
                "transform_attack_gain": (
                    back_atk - front_atk if front and back else ""
                ),
                "transform_health_gain": (
                    back_hp - front_hp if front and back else ""
                ),
                "transform_total_stat_gain": (
                    (back_atk + back_hp) - (front_atk + front_hp)
                    if front and back
                    else ""
                ),
                "transform_condition": card.get(
                    "transform_condition_type", ""
                ),
                "keyword_count": len(keyword_set),
                "keywords": "|".join(sorted(keyword_set)),
                "effect_count": len(card_effects),
                "operations": "|".join(operations),
                "triggers": "|".join(triggers),
            })

    deck_rows = []
    mana_rows = []
    effect_profile_rows = []
    keyword_profile_rows = []

    for deck_id, members in sorted(membership.items()):
        expanded = []
        for member in members:
            row = next(
                (
                    r
                    for r in card_rows
                    if r["deck_id"] == deck_id
                    and r["card_id"] == member["card_id"]
                ),
                None,
            )
            if row:
                expanded.extend([row] * member["quantity"])

        total = len(expanded)
        unit_rows = [r for r in expanded if r["type"] == "unit"]

        costs = [r["cost"] for r in expanded]
        types = Counter(r["type"] for r in expanded)
        transformable = [
            r for r in unit_rows if r.get("transform_condition")
        ]

        unit_eff = [
            float(r["front_stats_per_mana"])
            for r in unit_rows
            if r["front_stats_per_mana"] != ""
        ]

        deck_rows.append({
            "deck_id": deck_id,
            "deck_name": decks_by_id.get(deck_id, {}).get("name", ""),
            "faction_id": decks_by_id.get(deck_id, {}).get("faction_id", ""),
            "total_cards": total,
            "unique_cards": len(members),
            "avg_cost": round(sum(costs) / total, 3) if total else 0.0,
            "units": types.get("unit", 0),
            "spells": types.get("spell", 0),
            "artifacts": types.get("artifact", 0),
            "responses": types.get("response", 0),
            "other_cards": total
            - types.get("unit", 0)
            - types.get("spell", 0)
            - types.get("artifact", 0)
            - types.get("response", 0),
            "transformable_units": len(transformable),
            "avg_unit_front_stats_per_mana": (
                round(sum(unit_eff) / len(unit_eff), 3)
                if unit_eff else 0.0
            ),
            "avg_effects_per_card": (
                round(
                    sum(r["effect_count"] for r in expanded) / total,
                    3,
                )
                if total else 0.0
            ),
            "avg_keywords_per_card": (
                round(
                    sum(r["keyword_count"] for r in expanded) / total,
                    3,
                )
                if total else 0.0
            ),
        })

        buckets = Counter(_mana_bucket(cost) for cost in costs)
        for bucket in ("0-1", "2", "3", "4", "5", "6+"):
            mana_rows.append({
                "deck_id": deck_id,
                "bucket": bucket,
                "cards": buckets.get(bucket, 0),
                "share": (
                    round(buckets.get(bucket, 0) / total, 4)
                    if total else 0.0
                ),
            })

        op_counter = Counter()
        trigger_counter = Counter()
        keyword_counter = Counter()

        for r in expanded:
            for op in _split_tokens(r["operations"]):
                op_counter[op] += 1
            for trigger in _split_tokens(r["triggers"]):
                trigger_counter[trigger] += 1
            for keyword in _split_tokens(r["keywords"]):
                keyword_counter[keyword] += 1

        for op, count in sorted(op_counter.items()):
            effect_profile_rows.append({
                "deck_id": deck_id,
                "dimension": "operation",
                "value": op,
                "card_copies": count,
            })

        for trigger, count in sorted(trigger_counter.items()):
            effect_profile_rows.append({
                "deck_id": deck_id,
                "dimension": "trigger",
                "value": trigger,
                "card_copies": count,
            })

        for keyword, count in sorted(keyword_counter.items()):
            keyword_profile_rows.append({
                "deck_id": deck_id,
                "keyword": keyword,
                "card_copies": count,
            })

    return {
        "card_lookup": cards_by_id,
        "card_efficiency": card_rows,
        "deck_summary": deck_rows,
        "mana_curve": mana_rows,
        "effect_profile": effect_profile_rows,
        "keyword_profile": keyword_profile_rows,
        "data_quality": static_data_quality(tables),
    }


def build_telemetry_diagnostics(
    event_path: Path | None,
    summary_path: Path | None,
    card_lookup: dict[str, dict],
) -> dict:
    if event_path is None:
        return {
            "available": False,
            "reason": "event_log.csv not found",
            "capabilities": {},
            "card_metrics": [],
        }

    events = read_csv_tolerant(event_path)
    summaries = (
        read_csv_tolerant(summary_path)
        if summary_path is not None
        else []
    )

    if not events:
        return {
            "available": False,
            "reason": "event_log.csv is empty",
            "capabilities": {},
            "card_metrics": [],
        }

    event_type_col = _first_column(
        events, ["event_type", "type", "event", "name"]
    )
    card_col = _first_column(
        events, ["card_id", "source_card_id", "card"]
    )
    game_col = _first_column(
        events, ["game_id", "match_id"]
    )
    player_col = _first_column(
        events,
        ["player_index", "source_player_index", "controller_index", "side"],
    )
    turn_col = _first_column(events, ["turn_number", "turn"])

    capabilities = {
        "event_type": bool(event_type_col),
        "card_id": bool(card_col),
        "game_id": bool(game_col),
        "player_index": bool(player_col),
        "turn": bool(turn_col),
        "winner_join": False,
    }

    if not event_type_col or not card_col:
        return {
            "available": True,
            "reason": (
                "event log exists but lacks event_type/card_id columns; "
                "card telemetry metrics unavailable"
            ),
            "capabilities": capabilities,
            "card_metrics": [],
        }

    winner_map = _winner_map(summaries)
    capabilities["winner_join"] = bool(winner_map and game_col and player_col)

    by_card: dict[str, dict] = defaultdict(
        lambda: {
            "draw_events": 0,
            "play_events": 0,
            "response_events": 0,
            "transform_events": 0,
            "effect_damage_events": 0,
            "heal_events": 0,
            "play_turn_total": 0,
            "play_turn_n": 0,
            "played_games": set(),
            "played_wins": set(),
        }
    )

    for row in events:
        card_id = str(row.get(card_col, "")).strip()
        if not card_id:
            continue

        et = str(row.get(event_type_col, "")).strip()
        m = by_card[card_id]

        if et == "card_drawn":
            m["draw_events"] += 1
        elif et == "card_played":
            m["play_events"] += 1
            if turn_col:
                turn = _int(row.get(turn_col), None)
                if turn is not None:
                    m["play_turn_total"] += turn
                    m["play_turn_n"] += 1

            if game_col:
                gid = str(row.get(game_col, "")).strip()
                if gid:
                    m["played_games"].add(gid)
                    if capabilities["winner_join"]:
                        pidx = _player_index(row.get(player_col))
                        if (
                            pidx is not None
                            and winner_map.get(gid) == pidx
                        ):
                            m["played_wins"].add(gid)

        elif et == "response_played":
            m["response_events"] += 1
        elif et == "transform":
            m["transform_events"] += 1
        elif et == "effect_damage":
            m["effect_damage_events"] += 1
        elif et == "heal":
            m["heal_events"] += 1

    rows = []
    all_ids = sorted(set(card_lookup) | set(by_card))
    for card_id in all_ids:
        m = by_card[card_id]
        played_games = len(m["played_games"])
        rows.append({
            "card_id": card_id,
            "name": card_lookup.get(card_id, {}).get("name", ""),
            "draw_events": m["draw_events"],
            "play_events": m["play_events"],
            "response_events": m["response_events"],
            "transform_events": m["transform_events"],
            "effect_damage_events": m["effect_damage_events"],
            "heal_events": m["heal_events"],
            "play_given_draw_rate": (
                round(m["play_events"] / m["draw_events"], 4)
                if m["draw_events"] else ""
            ),
            "avg_play_turn": (
                round(m["play_turn_total"] / m["play_turn_n"], 3)
                if m["play_turn_n"] else ""
            ),
            "games_played": played_games if game_col else "",
            "wins_when_played": (
                len(m["played_wins"])
                if capabilities["winner_join"] else ""
            ),
            "win_rate_when_played": (
                round(len(m["played_wins"]) / played_games, 4)
                if capabilities["winner_join"] and played_games
                else ""
            ),
        })

    return {
        "available": True,
        "reason": "",
        "capabilities": capabilities,
        "card_metrics": rows,
    }


def static_data_quality(tables: dict[str, list[dict]]) -> list[dict]:
    issues = []

    cards = tables["cards"]
    card_ids = [
        row.get("id", "").strip()
        for row in cards
        if row.get("id", "").strip()
    ]
    duplicates = [
        cid for cid, n in Counter(card_ids).items() if n > 1
    ]
    if duplicates:
        issues.append({
            "severity": "warning",
            "area": "cards",
            "issue": "duplicate card ids",
            "details": "|".join(sorted(duplicates)),
        })

    known = set(card_ids)
    for table_name, id_col in (
        ("unit_sides", "card_id"),
        ("effects", "card_id"),
        ("deck_cards", "card_id"),
    ):
        unknown = sorted(
            {
                row.get(id_col, "").strip()
                for row in tables[table_name]
                if row.get(id_col, "").strip()
                and row.get(id_col, "").strip() not in known
            }
        )
        if unknown:
            issues.append({
                "severity": "warning",
                "area": table_name,
                "issue": "unknown card ids",
                "details": "|".join(unknown),
            })

    if not issues:
        issues.append({
            "severity": "info",
            "area": "static_data",
            "issue": "no structural reference issues detected",
            "details": "",
        })

    return issues


def render_diagnostics_report(result: dict) -> str:
    lines = [
        "# M3.5.3 Card / Deck Diagnostics",
        "",
        "## Deck structural summary",
        "",
        "| Deck | Cards | Avg Cost | Units | Spells | Artifacts | Responses | "
        "Transformable | Unit Stats/Mana | Effects/Card | Keywords/Card |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in result["deck_summary"]:
        lines.append(
            f"| {row['deck_id']} | {row['total_cards']} | "
            f"{row['avg_cost']:.2f} | {row['units']} | {row['spells']} | "
            f"{row['artifacts']} | {row['responses']} | "
            f"{row['transformable_units']} | "
            f"{row['avg_unit_front_stats_per_mana']:.2f} | "
            f"{row['avg_effects_per_card']:.2f} | "
            f"{row['avg_keywords_per_card']:.2f} |"
        )

    lines += [
        "",
        "## Mana curve",
        "",
        "| Deck | 0-1 | 2 | 3 | 4 | 5 | 6+ |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    curve = defaultdict(dict)
    for row in result["mana_curve"]:
        curve[row["deck_id"]][row["bucket"]] = row["cards"]
    for deck_id in sorted(curve):
        b = curve[deck_id]
        lines.append(
            f"| {deck_id} | {b.get('0-1',0)} | {b.get('2',0)} | "
            f"{b.get('3',0)} | {b.get('4',0)} | {b.get('5',0)} | "
            f"{b.get('6+',0)} |"
        )

    lines += [
        "",
        "## Highest front-side unit stat efficiency",
        "",
        "| Deck | Card | Cost | ATK | HP | (ATK+HP)/Mana | Transform Gain |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    efficiency = [
        row for row in result["card_efficiency"]
        if row["type"] == "unit"
        and row["front_stats_per_mana"] != ""
    ]
    efficiency.sort(
        key=lambda r: float(r["front_stats_per_mana"]),
        reverse=True,
    )
    for row in efficiency[:15]:
        lines.append(
            f"| {row['deck_id']} | {row['card_id']} {row['name']} | "
            f"{row['cost']} | {row['front_attack']} | {row['front_health']} | "
            f"{row['front_stats_per_mana']} | "
            f"{row['transform_total_stat_gain']} |"
        )

    telemetry = result["telemetry"]
    lines += [
        "",
        "## Telemetry capability",
        "",
        f"- Available: {telemetry['available']}",
    ]
    if telemetry.get("reason"):
        lines.append(f"- Note: {telemetry['reason']}")

    for key, value in telemetry.get("capabilities", {}).items():
        lines.append(f"- `{key}`: {'yes' if value else 'no'}")

    if telemetry.get("card_metrics"):
        lines += [
            "",
            "## Card telemetry",
            "",
            "| Card | Draw | Play | Play/Draw | Avg Play Turn | Response | "
            "Transform | Win When Played |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        metrics = sorted(
            telemetry["card_metrics"],
            key=lambda r: (
                r["play_events"],
                r["transform_events"],
                r["response_events"],
            ),
            reverse=True,
        )
        for row in metrics[:30]:
            lines.append(
                f"| {row['card_id']} {row['name']} | {row['draw_events']} | "
                f"{row['play_events']} | {row['play_given_draw_rate']} | "
                f"{row['avg_play_turn']} | {row['response_events']} | "
                f"{row['transform_events']} | "
                f"{row['win_rate_when_played']} |"
            )

    lines += [
        "",
        "## Interpretation",
        "",
        "- High printed stat efficiency is a diagnostic signal, not proof of an OP card.",
        "- `win_rate_when_played` is correlation, not causal card strength.",
        "- Compare D001 and D002 at deck level before changing individual cards.",
        "- Cards with high draw but low play can indicate cost/target/tempo problems.",
        "- Cards with high play plus unusually high win-when-played deserve targeted review.",
        "- Missing telemetry fields are reported as unavailable rather than inferred.",
        "",
    ]

    return "\n".join(lines)


def write_diagnostics_outputs(output_dir: str | Path, result: dict) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "deck_summary": save_csv(
            output_dir / "deck_summary.csv",
            result["deck_summary"],
        ),
        "mana_curve": save_csv(
            output_dir / "mana_curve.csv",
            result["mana_curve"],
        ),
        "card_efficiency": save_csv(
            output_dir / "card_efficiency.csv",
            result["card_efficiency"],
        ),
        "effect_profile": save_csv(
            output_dir / "effect_profile.csv",
            result["effect_profile"],
        ),
        "keyword_profile": save_csv(
            output_dir / "keyword_profile.csv",
            result["keyword_profile"],
        ),
        "data_quality": save_csv(
            output_dir / "data_quality.csv",
            result["data_quality"],
        ),
    }

    telemetry = result["telemetry"]
    outputs["card_telemetry"] = save_csv(
        output_dir / "card_telemetry.csv",
        telemetry.get("card_metrics", []),
    )

    capability_path = output_dir / "telemetry_capabilities.json"
    capability_path.write_text(
        json.dumps(
            {
                "available": telemetry.get("available", False),
                "reason": telemetry.get("reason", ""),
                "capabilities": telemetry.get("capabilities", {}),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    outputs["telemetry_capabilities"] = capability_path

    report_path = output_dir / "REPORT.md"
    report_path.write_text(
        render_diagnostics_report(result),
        encoding="utf-8",
    )
    outputs["report"] = report_path

    return outputs


def save_csv(path: str | Path, rows: list[dict]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return path

    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

    return path


def read_csv_tolerant(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for raw in reader:
            row = {}
            for key, value in raw.items():
                if key is None:
                    # Ignore malformed surplus CSV columns instead of letting
                    # them poison the schema.
                    continue
                row[str(key).strip()] = (
                    value.strip() if isinstance(value, str) else value
                )
            rows.append(row)
        return rows


def _front_back(rows: list[dict]) -> tuple[dict | None, dict | None]:
    if not rows:
        return None, None

    by_side = {
        str(r.get("side", "")).strip().lower(): r
        for r in rows
    }

    front = (
        by_side.get("front")
        or by_side.get("正面")
        or rows[0]
    )
    back = (
        by_side.get("back")
        or by_side.get("反面")
        or (rows[1] if len(rows) > 1 else None)
    )
    return front, back


def _mana_bucket(cost: int) -> str:
    if cost <= 1:
        return "0-1"
    if cost in (2, 3, 4, 5):
        return str(cost)
    return "6+"


def _split_tokens(value: str | None) -> list[str]:
    if not value:
        return []
    text = str(value).replace(",", "|").replace(";", "|")
    return [part.strip() for part in text.split("|") if part.strip()]


def _int(value, default=0):
    try:
        if value in ("", None):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _first_column(rows: list[dict], candidates: list[str]) -> str | None:
    if not rows:
        return None
    columns = set()
    for row in rows[:20]:
        columns.update(row.keys())
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _winner_map(rows: list[dict]) -> dict[str, int]:
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
        gid = str(row.get(game_col, "")).strip()
        winner = _player_index(row.get(winner_col))
        if gid and winner is not None:
            out[gid] = winner
    return out


def _player_index(value) -> int | None:
    if value in (None, ""):
        return None
    text = str(value).strip().lower()
    if text in {"0", "p1", "player1", "player_1"}:
        return 0
    if text in {"1", "p2", "player2", "player_2"}:
        return 1
    try:
        number = int(text)
        if number in (0, 1):
            return number
    except ValueError:
        pass
    return None
