from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


TURN_RESOURCE_EVENT = "turn_resource_snapshot"
CARD_PLAY_EVENT = "card_played"


@dataclass
class ManaCurveResult:
    curve_by_cost: pd.DataFrame
    deck_summary: pd.DataFrame
    comparison: pd.DataFrame
    report: str


def _require_columns(df: pd.DataFrame, columns: Iterable[str], name: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {', '.join(missing)}")


def _to_int_series(series: pd.Series, name: str) -> pd.Series:
    converted = pd.to_numeric(series, errors="coerce")
    if converted.isna().any():
        bad = series[converted.isna()].astype(str).unique().tolist()[:5]
        raise ValueError(f"{name} contains non-numeric values: {bad}")
    return converted.astype(int)


def _weighted_median(costs: pd.Series, weights: pd.Series) -> float:
    order = costs.argsort(kind="stable")
    c = costs.iloc[order].reset_index(drop=True)
    w = weights.iloc[order].reset_index(drop=True)
    half = w.sum() / 2
    cum = w.cumsum()
    idx = int((cum >= half).idxmax())
    if w.sum() % 2 == 1 or cum.iloc[idx] > half or idx + 1 >= len(c):
        return float(c.iloc[idx])
    return float(c.iloc[idx : idx + 2].mean())


def probability_at_least_one(total: int, successes: int, draws: int) -> float:
    """Hypergeometric P(X >= 1) without replacement."""
    if total <= 0 or draws <= 0 or successes <= 0:
        return 0.0
    draws = min(draws, total)
    successes = min(successes, total)
    failures = total - successes
    if failures < draws:
        return 1.0
    return 1.0 - (math.comb(failures, draws) / math.comb(total, draws))

def _normalize_card_schema(
    cards: pd.DataFrame,
    deck_cards: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cards = cards.copy()
    deck_cards = deck_cards.copy()

    if "card_id" not in cards.columns and "id" in cards.columns:
        cards = cards.rename(columns={"id": "card_id"})

    return cards, deck_cards


def build_deck_curve(cards, deck_cards):
    cards, deck_cards = _normalize_card_schema(
        cards,
        deck_cards,
    )

    _require_columns(cards, ["card_id", "cost"], "cards")
    _require_columns(
        deck_cards,
        ["deck_id", "card_id", "quantity"],
        "deck_cards",
    )

    merged = deck_cards.merge(
        cards[["card_id", "cost"]],
        on="card_id",
        how="left",
        validate="many_to_one",
    )

    if merged["cost"].isna().any():
        missing = sorted(
            merged.loc[merged["cost"].isna(), "card_id"]
            .astype(str)
            .unique()
        )
        raise ValueError(
            "deck_cards references unknown cards: "
            + ", ".join(missing)
        )

    merged["cost"] = pd.to_numeric(
        merged["cost"],
        errors="raise",
    ).astype(int)

    merged["quantity"] = pd.to_numeric(
        merged["quantity"],
        errors="raise",
    ).astype(int)

    curve = (
        merged.groupby(["deck_id", "cost"], as_index=False)["quantity"]
        .sum()
        .rename(columns={"quantity": "copies"})
        .sort_values(["deck_id", "cost"])
        .reset_index(drop=True)
    )

    totals = (
        curve.groupby("deck_id")["copies"]
        .transform("sum")
    )

    curve["share"] = curve["copies"] / totals

    return curve

def build_static_summary(
    cards,
    deck_cards,
    opening_hand_size=5,
    early_turns: tuple[int, ...] = (1, 2, 3),
):
    cards, deck_cards = _normalize_card_schema(
        cards,
        deck_cards,
    )

    _require_columns(cards, ["card_id", "cost"], "cards")
    _require_columns(
        deck_cards,
        ["deck_id", "card_id", "quantity"],
        "deck_cards",
    )

    card_costs = cards[["card_id", "cost"]].copy()
    card_costs["cost"] = _to_int_series(card_costs["cost"], "cards.cost")
    dc = deck_cards[["deck_id", "card_id", "quantity"]].copy()
    dc["quantity"] = _to_int_series(dc["quantity"], "deck_cards.quantity")
    merged = dc.merge(card_costs, on="card_id", how="left", validate="many_to_one")
    if merged["cost"].isna().any():
        missing = merged.loc[merged["cost"].isna(), "card_id"].unique().tolist()
        raise ValueError(f"deck_cards references unknown cards: {missing}")

    rows: list[dict] = []
    for deck_id, group in merged.groupby("deck_id", sort=True):
        total = int(group["quantity"].sum())
        weighted_sum = float((group["cost"] * group["quantity"]).sum())
        row = {
            "deck_id": deck_id,
            "deck_size": total,
            "average_cost": weighted_sum / total if total else float("nan"),
            "median_cost": _weighted_median(group["cost"], group["quantity"]),
        }
        for turn in early_turns:
            eligible = int(group.loc[group["cost"] <= turn, "quantity"].sum())
            row[f"cards_cost_le_{turn}"] = eligible
            row[f"opening_cost_playability_t{turn}"] = probability_at_least_one(
                total=total,
                successes=eligible,
                draws=opening_hand_size,
            )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("deck_id").reset_index(drop=True)


def _parse_metadata(value) -> dict:
    if isinstance(value, dict):
        return value
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return {}
    text = str(value).strip()
    if not text:
        return {}
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        return {}


def _player_deck_map(summaries: pd.DataFrame) -> pd.DataFrame:
    _require_columns(summaries, ["game_id", "deck_id_p1", "deck_id_p2"], "summaries")
    p1 = summaries[["game_id", "deck_id_p1"]].rename(columns={"deck_id_p1": "deck_id"})
    p1["player_index"] = 0
    p2 = summaries[["game_id", "deck_id_p2"]].rename(columns={"deck_id_p2": "deck_id"})
    p2["player_index"] = 1
    return pd.concat([p1, p2], ignore_index=True)


def build_telemetry_summary(summaries: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    if summaries is None or events is None or summaries.empty or events.empty:
        return pd.DataFrame()
    _require_columns(events, ["game_id", "event_type", "turn", "player_index"], "events")

    deck_map = _player_deck_map(summaries)
    snapshots = events.loc[events["event_type"] == TURN_RESOURCE_EVENT].copy()
    if snapshots.empty:
        return pd.DataFrame()

    if "metadata" not in snapshots.columns:
        raise ValueError("events missing metadata required for turn_resource_snapshot")

    meta = snapshots["metadata"].map(_parse_metadata)
    snapshots["max_mana"] = meta.map(lambda d: d.get("max_mana"))
    snapshots["mana_remaining"] = meta.map(lambda d: d.get("mana_remaining"))
    snapshots["mana_spent"] = meta.map(lambda d: d.get("mana_spent"))
    snapshots["dead_hand"] = meta.map(lambda d: bool(d.get("dead_hand", False)))
    snapshots["spend_actions_available"] = meta.map(lambda d: d.get("spend_actions_available", 0))

    for col in ["max_mana", "mana_remaining", "mana_spent", "spend_actions_available"]:
        snapshots[col] = pd.to_numeric(snapshots[col], errors="coerce")

    snapshots = snapshots.merge(deck_map, on=["game_id", "player_index"], how="left", validate="many_to_one")
    snapshots = snapshots.dropna(subset=["deck_id", "max_mana", "mana_remaining", "mana_spent"])
    snapshots = snapshots.sort_values(["game_id", "player_index", "turn"], kind="stable")
    snapshots["player_turn_number"] = snapshots.groupby(["game_id", "player_index"]).cumcount() + 1

    # Main-phase card plays can be mapped to the player's own turn number by matching global turn.
    play_events = events.loc[events["event_type"] == CARD_PLAY_EVENT, ["game_id", "turn", "player_index"]].copy()
    turn_map = snapshots[["game_id", "turn", "player_index", "player_turn_number", "deck_id"]].drop_duplicates()
    play_events = play_events.merge(turn_map, on=["game_id", "turn", "player_index"], how="left")

    rows: list[dict] = []
    for deck_id, group in snapshots.groupby("deck_id", sort=True):
        available = float(group["max_mana"].sum())
        spent = float(group["mana_spent"].sum())
        pg = play_events.loc[play_events["deck_id"] == deck_id].copy()

        per_game_player = group[["game_id", "player_index"]].drop_duplicates()
        gp_quantity = len(per_game_player)
        if not pg.empty:
            first_turns = pg.groupby(["game_id", "player_index"])["player_turn_number"].min()
            early_quantitys = (
                pg.loc[pg["player_turn_number"] <= 3]
                .groupby(["game_id", "player_index"])
                .size()
            )
            avg_first = float(first_turns.mean())
            avg_early = float(early_quantitys.reindex(pd.MultiIndex.from_frame(per_game_player), fill_value=0).mean())
        else:
            avg_first = float("nan")
            avg_early = 0.0 if gp_quantity else float("nan")

        rows.append(
            {
                "deck_id": deck_id,
                "turn_snapshots": int(len(group)),
                "avg_unused_mana": float(group["mana_remaining"].mean()),
                "mana_efficiency": spent / available if available > 0 else float("nan"),
                "dead_hand_rate": float(group["dead_hand"].mean()),
                "avg_first_card_player_turn": avg_first,
                "avg_cards_played_by_player_turn_3": avg_early,
            }
        )
    return pd.DataFrame(rows).sort_values("deck_id").reset_index(drop=True)


def build_comparison(deck_summary: pd.DataFrame, deck_order: tuple[str, str] = ("D001", "D002")) -> pd.DataFrame:
    if deck_summary.empty or any(d not in set(deck_summary["deck_id"]) for d in deck_order):
        return pd.DataFrame(columns=["metric", deck_order[0], deck_order[1], "delta_first_minus_second"])
    indexed = deck_summary.set_index("deck_id")
    metrics = [c for c in deck_summary.columns if c != "deck_id"]
    rows = []
    for metric in metrics:
        a = indexed.at[deck_order[0], metric]
        b = indexed.at[deck_order[1], metric]
        try:
            delta = float(a) - float(b)
        except (TypeError, ValueError):
            continue
        rows.append({"metric": metric, deck_order[0]: a, deck_order[1]: b, "delta_first_minus_second": delta})
    return pd.DataFrame(rows)


def _fmt(value, percent: bool = False) -> str:
    if pd.isna(value):
        return "N/A"
    if percent:
        return f"{float(value):.2%}"
    if isinstance(value, (int,)):
        return str(value)
    return f"{float(value):.3f}"


def render_report(deck_summary: pd.DataFrame) -> str:
    lines = ["=== M3.7.1 Mana Curve Analysis ===", ""]
    telemetry_cols = {
        "avg_unused_mana",
        "mana_efficiency",
        "dead_hand_rate",
        "avg_first_card_player_turn",
        "avg_cards_played_by_player_turn_3",
    }
    for _, row in deck_summary.sort_values("deck_id").iterrows():
        lines += [
            f"Deck: {row['deck_id']}",
            f"  deck_size={int(row['deck_size'])}",
            f"  average_cost={_fmt(row['average_cost'])}",
            f"  median_cost={_fmt(row['median_cost'])}",
            "  opening cost-only playability:",
            f"    T1={_fmt(row.get('opening_cost_playability_t1'), True)}",
            f"    T2={_fmt(row.get('opening_cost_playability_t2'), True)}",
            f"    T3={_fmt(row.get('opening_cost_playability_t3'), True)}",
        ]
        if telemetry_cols.issubset(set(deck_summary.columns)):
            lines += [
                "  runtime telemetry:",
                f"    avg_unused_mana={_fmt(row['avg_unused_mana'])}",
                f"    mana_efficiency={_fmt(row['mana_efficiency'], True)}",
                f"    dead_hand_rate={_fmt(row['dead_hand_rate'], True)}",
                f"    avg_first_card_player_turn={_fmt(row['avg_first_card_player_turn'])}",
                f"    avg_cards_played_by_player_turn_3={_fmt(row['avg_cards_played_by_player_turn_3'])}",
            ]
        else:
            lines += ["  runtime telemetry: unavailable (run new simulations with turn_resource_snapshot events)"]
        lines.append("")

    if {"D001", "D002"}.issubset(set(deck_summary["deck_id"])):
        idx = deck_summary.set_index("deck_id")
        d1, d2 = idx.loc["D001"], idx.loc["D002"]
        lines += [
            "=== Curve Comparison ===",
            f"  average_cost_delta(D001-D002)={_fmt(d1['average_cost'] - d2['average_cost'])}",
            f"  T1_opening_playability_delta={_fmt(d1['opening_cost_playability_t1'] - d2['opening_cost_playability_t1'], True)}",
            f"  T2_opening_playability_delta={_fmt(d1['opening_cost_playability_t2'] - d2['opening_cost_playability_t2'], True)}",
            f"  T3_opening_playability_delta={_fmt(d1['opening_cost_playability_t3'] - d2['opening_cost_playability_t3'], True)}",
        ]
        if telemetry_cols.issubset(set(deck_summary.columns)):
            lines += [
                f"  mana_efficiency_delta={_fmt(d1['mana_efficiency'] - d2['mana_efficiency'], True)}",
                f"  dead_hand_rate_delta={_fmt(d1['dead_hand_rate'] - d2['dead_hand_rate'], True)}",
            ]
    return "\n".join(lines).rstrip() + "\n"


def analyze_mana_curve(
    cards: pd.DataFrame,
    deck_cards: pd.DataFrame,
    summaries: pd.DataFrame | None = None,
    events: pd.DataFrame | None = None,
    opening_hand_size: int = 5,
) -> ManaCurveResult:
    curve = build_deck_curve(cards, deck_cards)
    static = build_static_summary(cards, deck_cards, opening_hand_size=opening_hand_size)
    telemetry = build_telemetry_summary(summaries, events) if summaries is not None and events is not None else pd.DataFrame()
    summary = static.merge(telemetry, on="deck_id", how="left") if not telemetry.empty else static
    comparison = build_comparison(summary)
    report = render_report(summary)
    return ManaCurveResult(curve_by_cost=curve, deck_summary=summary, comparison=comparison, report=report)


def export_result(result: ManaCurveResult, output_dir: str | Path) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result.curve_by_cost.to_csv(out / "mana_curve_by_cost.csv", index=False)
    result.deck_summary.to_csv(out / "mana_curve_deck_summary.csv", index=False)
    result.comparison.to_csv(out / "mana_curve_comparison.csv", index=False)
    (out / "mana_curve_report.txt").write_text(result.report, encoding="utf-8")
    def json_records(frame: pd.DataFrame) -> list[dict]:
        # Round-trip through pandas JSON so NaN becomes JSON null rather than
        # the non-standard JavaScript token NaN.
        return json.loads(frame.to_json(orient="records", force_ascii=False))

    payload = {
        "curve_by_cost": json_records(result.curve_by_cost),
        "deck_summary": json_records(result.deck_summary),
        "comparison": json_records(result.comparison),
    }
    (out / "mana_curve.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    return out
