from __future__ import annotations

from pathlib import Path
import json
import pandas as pd


def _require_columns(df: pd.DataFrame, columns: list[str], name: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {', '.join(missing)}")


def _parse_metadata(value):
    if isinstance(value, dict):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return {}
    text = str(value).strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def build_board_snapshots(events: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        events,
        ["game_id", "event_type", "turn", "player_index", "metadata"],
        "events",
    )

    rows = []
    for _, event in events.iterrows():
        if str(event["event_type"]) != "board_state_snapshot":
            continue

        meta = _parse_metadata(event["metadata"])
        rows.append(
            {
                "game_id": event["game_id"],
                "turn": int(event["turn"]),
                "player_index": int(event["player_index"]),
                "unit_count": int(meta.get("unit_count", 0) or 0),
                "board_attack": float(meta.get("board_attack", 0) or 0),
                "board_health": float(meta.get("board_health", 0) or 0),
                "cards_played_total": int(meta.get("cards_played_total", 0) or 0),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "game_id",
                "turn",
                "player_index",
                "unit_count",
                "board_attack",
                "board_health",
                "cards_played_total",
            ]
        )

    return (
        pd.DataFrame(rows)
        .sort_values(["game_id", "turn", "player_index"])
        .reset_index(drop=True)
    )


def attach_decks(
    snapshots: pd.DataFrame,
    summaries: pd.DataFrame,
) -> pd.DataFrame:
    if snapshots.empty:
        return snapshots.copy()

    _require_columns(
        summaries,
        ["game_id", "deck_id_p1", "deck_id_p2"],
        "summaries",
    )

    mapping = summaries[
        ["game_id", "deck_id_p1", "deck_id_p2"]
    ].drop_duplicates("game_id")

    merged = snapshots.merge(mapping, on="game_id", how="left")

    merged["deck_id"] = merged.apply(
        lambda r: r["deck_id_p1"]
        if int(r["player_index"]) == 0
        else r["deck_id_p2"],
        axis=1,
    )
    return merged


def build_deck_tempo_summary(
    snapshots_with_decks: pd.DataFrame,
) -> pd.DataFrame:
    df = snapshots_with_decks.copy()
    if df.empty:
        return pd.DataFrame()

    df["survival_conversion"] = df.apply(
        lambda r: (
            r["unit_count"] / r["cards_played_total"]
            if r["cards_played_total"] > 0
            else float("nan")
        ),
        axis=1,
    )

    rows = []
    for deck_id, g in df.groupby("deck_id"):
        early = g[g["turn"] <= 3]

        rows.append(
            {
                "deck_id": deck_id,
                "snapshots": len(g),
                "avg_unit_count": g["unit_count"].mean(),
                "avg_board_attack": g["board_attack"].mean(),
                "avg_board_health": g["board_health"].mean(),
                "avg_survival_conversion": g["survival_conversion"].mean(),
                "avg_unit_count_t1_3": early["unit_count"].mean(),
                "avg_board_attack_t1_3": early["board_attack"].mean(),
                "avg_board_health_t1_3": early["board_health"].mean(),
            }
        )

    return pd.DataFrame(rows).sort_values("deck_id").reset_index(drop=True)


def build_game_advantage_table(
    snapshots_with_decks: pd.DataFrame,
) -> pd.DataFrame:
    df = snapshots_with_decks.copy()
    if df.empty:
        return pd.DataFrame()

    # Compare the two players at the same global turn.
    pivot = df.pivot_table(
        index=["game_id", "turn"],
        columns="player_index",
        values=["unit_count", "board_attack", "board_health"],
        aggfunc="last",
    )

    rows = []
    for (game_id, turn), row in pivot.iterrows():
        try:
            p0_units = float(row[("unit_count", 0)])
            p1_units = float(row[("unit_count", 1)])
            p0_atk = float(row[("board_attack", 0)])
            p1_atk = float(row[("board_attack", 1)])
            p0_hp = float(row[("board_health", 0)])
            p1_hp = float(row[("board_health", 1)])
        except Exception:
            continue

        def leader(a, b):
            if a > b:
                return 0
            if b > a:
                return 1
            return None

        rows.append(
            {
                "game_id": game_id,
                "turn": int(turn),
                "unit_advantage_player": leader(p0_units, p1_units),
                "attack_advantage_player": leader(p0_atk, p1_atk),
                "health_advantage_player": leader(p0_hp, p1_hp),
                "unit_delta_p0_minus_p1": p0_units - p1_units,
                "attack_delta_p0_minus_p1": p0_atk - p1_atk,
                "health_delta_p0_minus_p1": p0_hp - p1_hp,
            }
        )

    return pd.DataFrame(rows)


def build_first_advantage_summary(
    advantage: pd.DataFrame,
    summaries: pd.DataFrame,
) -> pd.DataFrame:
    if advantage.empty:
        return pd.DataFrame()

    _require_columns(
        summaries,
        ["game_id", "deck_id_p1", "deck_id_p2"],
        "summaries",
    )
    deck_map = summaries.set_index("game_id")[["deck_id_p1", "deck_id_p2"]]

    rows = []
    for game_id, g in advantage.groupby("game_id"):
        if game_id not in deck_map.index:
            continue

        deck_p1 = deck_map.loc[game_id, "deck_id_p1"]
        deck_p2 = deck_map.loc[game_id, "deck_id_p2"]

        for metric, col in [
            ("unit", "unit_advantage_player"),
            ("attack", "attack_advantage_player"),
            ("health", "health_advantage_player"),
        ]:
            non_ties = g[g[col].notna()].sort_values("turn")
            if non_ties.empty:
                continue
            first = non_ties.iloc[0]
            player = int(first[col])
            deck = deck_p1 if player == 0 else deck_p2
            rows.append(
                {
                    "game_id": game_id,
                    "metric": metric,
                    "first_advantage_turn": int(first["turn"]),
                    "advantage_player_index": player,
                    "advantage_deck_id": deck,
                }
            )

    return pd.DataFrame(rows)


def summarize_first_advantage(
    first_advantage: pd.DataFrame,
) -> pd.DataFrame:
    if first_advantage.empty:
        return pd.DataFrame()

    return (
        first_advantage.groupby(["metric", "advantage_deck_id"], as_index=False)
        .agg(
            games_with_first_advantage=("game_id", "nunique"),
            avg_first_advantage_turn=("first_advantage_turn", "mean"),
        )
        .sort_values(["metric", "advantage_deck_id"])
        .reset_index(drop=True)
    )


def build_deck_comparison(deck_summary: pd.DataFrame) -> pd.DataFrame:
    if deck_summary.empty:
        return pd.DataFrame()

    ids = set(deck_summary["deck_id"])
    if not {"D001", "D002"}.issubset(ids):
        return pd.DataFrame()

    x = deck_summary.set_index("deck_id")
    d1 = x.loc["D001"]
    d2 = x.loc["D002"]

    metrics = [
        "avg_unit_count",
        "avg_board_attack",
        "avg_board_health",
        "avg_survival_conversion",
        "avg_unit_count_t1_3",
        "avg_board_attack_t1_3",
        "avg_board_health_t1_3",
    ]

    return pd.DataFrame(
        [
            {
                "metric": metric,
                "D001": d1[metric],
                "D002": d2[metric],
                "D001_minus_D002": d1[metric] - d2[metric],
            }
            for metric in metrics
        ]
    )


def analyze_tempo_board(
    summaries: pd.DataFrame,
    events: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    snapshots = build_board_snapshots(events)
    snapshots_with_decks = attach_decks(snapshots, summaries)
    deck_summary = build_deck_tempo_summary(snapshots_with_decks)
    advantage = build_game_advantage_table(snapshots_with_decks)
    first_advantage = build_first_advantage_summary(advantage, summaries)
    first_advantage_summary = summarize_first_advantage(first_advantage)
    comparison = build_deck_comparison(deck_summary)

    return {
        "snapshots": snapshots_with_decks,
        "deck_summary": deck_summary,
        "advantage": advantage,
        "first_advantage": first_advantage,
        "first_advantage_summary": first_advantage_summary,
        "comparison": comparison,
    }


def _fmt(value, digits=3):
    if pd.isna(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def render_report(result: dict[str, pd.DataFrame]) -> str:
    lines = ["=== M3.7.3 Tempo / Board Development ===", ""]
    summary = result["deck_summary"]
    comparison = result["comparison"]
    first = result["first_advantage_summary"]

    if summary.empty:
        lines.append(
            "runtime telemetry unavailable: board_state_snapshot events not found"
        )
        return "\n".join(lines)

    for _, r in summary.iterrows():
        lines.extend(
            [
                f"Deck: {r['deck_id']}",
                f"  avg_unit_count={_fmt(r['avg_unit_count'])}",
                f"  avg_board_attack={_fmt(r['avg_board_attack'])}",
                f"  avg_board_health={_fmt(r['avg_board_health'])}",
                f"  avg_survival_conversion={_fmt(r['avg_survival_conversion'])}",
                "  early T1-T3:",
                f"    avg_unit_count={_fmt(r['avg_unit_count_t1_3'])}",
                f"    avg_board_attack={_fmt(r['avg_board_attack_t1_3'])}",
                f"    avg_board_health={_fmt(r['avg_board_health_t1_3'])}",
                "",
            ]
        )

    if not comparison.empty:
        lines.append("=== Board Comparison (D001 - D002) ===")
        for _, r in comparison.iterrows():
            lines.append(f"  {r['metric']}: {_fmt(r['D001_minus_D002'])}")
        lines.append("")

    if not first.empty:
        lines.append("=== First Board Advantage ===")
        for _, r in first.iterrows():
            lines.append(
                f"  {r['metric']} {r['advantage_deck_id']}: "
                f"games={int(r['games_with_first_advantage'])} "
                f"avg_turn={_fmt(r['avg_first_advantage_turn'])}"
            )

    lines.extend(
        [
            "",
            "Interpretation:",
            "  survival_conversion = surviving unit count / cumulative cards played.",
            "  Positive D001-D002 board deltas indicate stronger board conversion for D001.",
            "  This analyzer requires board_state_snapshot telemetry from new simulations.",
        ]
    )
    return "\n".join(lines)


def export_analysis(
    result: dict[str, pd.DataFrame],
    output_dir: str | Path,
) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    names = {
        "snapshots": "board_snapshots.csv",
        "deck_summary": "tempo_deck_summary.csv",
        "advantage": "board_advantage_by_turn.csv",
        "first_advantage": "first_board_advantage.csv",
        "first_advantage_summary": "first_board_advantage_summary.csv",
        "comparison": "tempo_comparison.csv",
    }
    for key, filename in names.items():
        result[key].to_csv(output / filename, index=False, encoding="utf-8-sig")

    (output / "tempo_report.txt").write_text(
        render_report(result),
        encoding="utf-8",
    )
    return output
