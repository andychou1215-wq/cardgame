from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import json

import pandas as pd


def _require_columns(df: pd.DataFrame, columns: Iterable[str], name: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {', '.join(missing)}")


def _pick_column(df: pd.DataFrame, candidates: list[str], label: str) -> str:
    for column in candidates:
        if column in df.columns:
            return column
    raise ValueError(
        f"unit_sides missing {label}; expected one of: {', '.join(candidates)}"
    )


def normalize_unit_stat_inputs(
    cards: pd.DataFrame,
    unit_sides: pd.DataFrame,
    deck_cards: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cards = cards.copy()
    unit_sides = unit_sides.copy()
    deck_cards = deck_cards.copy()

    # Project external schema: cards.csv uses `id`.
    if "card_id" not in cards.columns and "id" in cards.columns:
        cards = cards.rename(columns={"id": "card_id"})

    # Keep the analyzer tolerant of the historical type naming only at the
    # boundary. Internal schema always uses `card_type`.
    if "card_type" not in cards.columns and "type" in cards.columns:
        cards = cards.rename(columns={"type": "card_type"})

    _require_columns(cards, ["card_id", "cost"], "cards")
    _require_columns(unit_sides, ["card_id", "side"], "unit_sides")
    _require_columns(deck_cards, ["deck_id", "card_id", "quantity"], "deck_cards")

    attack_col = _pick_column(
        unit_sides,
        ["attack", "atk", "base_attack"],
        "attack column",
    )
    health_col = _pick_column(
        unit_sides,
        ["health", "hp", "max_health", "base_health"],
        "health column",
    )

    rename = {}
    if attack_col != "attack":
        rename[attack_col] = "attack"
    if health_col != "health":
        rename[health_col] = "health"
    if rename:
        unit_sides = unit_sides.rename(columns=rename)

    unit_sides["side"] = unit_sides["side"].astype(str).str.lower()
    unit_sides["attack"] = pd.to_numeric(unit_sides["attack"], errors="raise")
    unit_sides["health"] = pd.to_numeric(unit_sides["health"], errors="raise")
    cards["cost"] = pd.to_numeric(cards["cost"], errors="raise")
    deck_cards["quantity"] = pd.to_numeric(
        deck_cards["quantity"], errors="raise"
    ).astype(int)

    return cards, unit_sides, deck_cards


def build_unit_efficiency_table(
    cards: pd.DataFrame,
    unit_sides: pd.DataFrame,
    deck_cards: pd.DataFrame,
    effects: pd.DataFrame | None = None,
) -> pd.DataFrame:
    cards, unit_sides, deck_cards = normalize_unit_stat_inputs(
        cards, unit_sides, deck_cards
    )

    # unit_sides is authoritative for "is a unit"; this avoids relying on
    # localized/type spelling in cards.csv.
    side_cards = set(unit_sides["card_id"].astype(str))
    unit_cards = cards[cards["card_id"].astype(str).isin(side_cards)].copy()

    base_cols = ["card_id", "cost"]
    for optional in ["name", "card_type"]:
        if optional in unit_cards.columns:
            base_cols.append(optional)

    units = deck_cards.merge(
        unit_cards[base_cols],
        on="card_id",
        how="inner",
        validate="many_to_one",
    )

    sides = unit_sides[["card_id", "side", "attack", "health"]].copy()
    pivot = sides.pivot_table(
        index="card_id",
        columns="side",
        values=["attack", "health"],
        aggfunc="first",
    )
    pivot.columns = [f"{side}_{stat}" for stat, side in pivot.columns]
    pivot = pivot.reset_index()

    result = units.merge(pivot, on="card_id", how="left", validate="many_to_one")

    for side in ("front", "back"):
        atk = f"{side}_attack"
        hp = f"{side}_health"
        if atk not in result.columns:
            result[atk] = pd.NA
        if hp not in result.columns:
            result[hp] = pd.NA

        result[f"{side}_total_stats"] = (
            pd.to_numeric(result[atk], errors="coerce")
            + pd.to_numeric(result[hp], errors="coerce")
        )

        # Cost 0 units are treated as undefined efficiency rather than inf.
        denom = result["cost"].where(result["cost"] > 0)
        result[f"{side}_attack_per_mana"] = result[atk] / denom
        result[f"{side}_health_per_mana"] = result[hp] / denom
        result[f"{side}_stats_per_mana"] = (
            result[f"{side}_total_stats"] / denom
        )

    result["transform_attack_delta"] = (
        result["back_attack"] - result["front_attack"]
    )
    result["transform_health_delta"] = (
        result["back_health"] - result["front_health"]
    )
    result["transform_total_stat_delta"] = (
        result["back_total_stats"] - result["front_total_stats"]
    )

    front_total = result["front_total_stats"].where(
        result["front_total_stats"] != 0
    )
    result["transform_stat_gain_pct"] = (
        result["transform_total_stat_delta"] / front_total
    )

    # Effects are annotated, not converted into arbitrary stat points.
    if effects is not None and not effects.empty and "card_id" in effects.columns:
        effect_counts = (
            effects.groupby("card_id")
            .size()
            .rename("effect_count")
            .reset_index()
        )
        result = result.merge(effect_counts, on="card_id", how="left")
        result["effect_count"] = result["effect_count"].fillna(0).astype(int)
    else:
        result["effect_count"] = 0

    # Relative-to-cost-band baseline. Compare front body only, because back body
    # is conditional on Transform.
    band = (
        result.drop_duplicates(["card_id", "cost"])
        .groupby("cost", as_index=False)
        .agg(
            cost_band_mean_front_stats_per_mana=(
                "front_stats_per_mana",
                "mean",
            ),
            cost_band_median_front_stats_per_mana=(
                "front_stats_per_mana",
                "median",
            ),
        )
    )
    result = result.merge(band, on="cost", how="left")
    result["front_efficiency_vs_cost_band"] = (
        result["front_stats_per_mana"]
        - result["cost_band_mean_front_stats_per_mana"]
    )

    sort_cols = ["deck_id", "cost", "card_id"]
    return result.sort_values(sort_cols).reset_index(drop=True)


def build_deck_unit_summary(unit_table: pd.DataFrame) -> pd.DataFrame:
    if unit_table.empty:
        return pd.DataFrame()

    rows = []
    for deck_id, group in unit_table.groupby("deck_id"):
        weights = group["quantity"].astype(float)
        total_copies = float(weights.sum())

        def weighted_mean(column: str) -> float:
            valid = group[column].notna()
            if not valid.any():
                return float("nan")
            w = weights[valid]
            return float((group.loc[valid, column] * w).sum() / w.sum())

        rows.append(
            {
                "deck_id": deck_id,
                "unit_copies": int(total_copies),
                "unique_units": int(group["card_id"].nunique()),
                "avg_unit_cost": weighted_mean("cost"),
                "avg_front_attack": weighted_mean("front_attack"),
                "avg_front_health": weighted_mean("front_health"),
                "avg_front_total_stats": weighted_mean("front_total_stats"),
                "avg_front_stats_per_mana": weighted_mean(
                    "front_stats_per_mana"
                ),
                "avg_back_stats_per_mana": weighted_mean(
                    "back_stats_per_mana"
                ),
                "avg_transform_total_stat_delta": weighted_mean(
                    "transform_total_stat_delta"
                ),
                "avg_front_efficiency_vs_cost_band": weighted_mean(
                    "front_efficiency_vs_cost_band"
                ),
            }
        )

    return pd.DataFrame(rows).sort_values("deck_id").reset_index(drop=True)


def build_cost_band_summary(unit_table: pd.DataFrame) -> pd.DataFrame:
    if unit_table.empty:
        return pd.DataFrame()

    rows = (
        unit_table.groupby(["deck_id", "cost"], as_index=False)
        .apply(
            lambda g: pd.Series(
                {
                    "unit_copies": int(g["quantity"].sum()),
                    "unique_units": int(g["card_id"].nunique()),
                    "weighted_front_stats_per_mana": float(
                        (g["front_stats_per_mana"] * g["quantity"]).sum()
                        / g["quantity"].sum()
                    ),
                    "weighted_front_total_stats": float(
                        (g["front_total_stats"] * g["quantity"]).sum()
                        / g["quantity"].sum()
                    ),
                }
            ),
            include_groups=False,
        )
        .reset_index(drop=True)
    )
    return rows


def build_deck_comparison(deck_summary: pd.DataFrame) -> pd.DataFrame:
    if {"D001", "D002"}.issubset(set(deck_summary.get("deck_id", []))):
        d1 = deck_summary.set_index("deck_id").loc["D001"]
        d2 = deck_summary.set_index("deck_id").loc["D002"]
        metrics = [
            "avg_unit_cost",
            "avg_front_attack",
            "avg_front_health",
            "avg_front_total_stats",
            "avg_front_stats_per_mana",
            "avg_back_stats_per_mana",
            "avg_transform_total_stat_delta",
            "avg_front_efficiency_vs_cost_band",
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
    return pd.DataFrame()


def analyze_unit_stat_efficiency(
    cards: pd.DataFrame,
    unit_sides: pd.DataFrame,
    deck_cards: pd.DataFrame,
    effects: pd.DataFrame | None = None,
) -> dict[str, pd.DataFrame]:
    unit_table = build_unit_efficiency_table(
        cards, unit_sides, deck_cards, effects=effects
    )
    deck_summary = build_deck_unit_summary(unit_table)
    cost_bands = build_cost_band_summary(unit_table)
    comparison = build_deck_comparison(deck_summary)
    return {
        "unit_table": unit_table,
        "deck_summary": deck_summary,
        "cost_bands": cost_bands,
        "comparison": comparison,
    }


def _fmt(value, digits=3) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def render_report(result: dict[str, pd.DataFrame]) -> str:
    deck_summary = result["deck_summary"]
    comparison = result["comparison"]
    unit_table = result["unit_table"]

    lines = ["=== M3.7.2 Unit Stat Efficiency ===", ""]

    for _, row in deck_summary.iterrows():
        deck_id = row["deck_id"]
        lines.extend(
            [
                f"Deck: {deck_id}",
                f"  unit_copies={int(row['unit_copies'])}",
                f"  unique_units={int(row['unique_units'])}",
                f"  avg_unit_cost={_fmt(row['avg_unit_cost'])}",
                f"  avg_front_stats_per_mana={_fmt(row['avg_front_stats_per_mana'])}",
                f"  avg_back_stats_per_mana={_fmt(row['avg_back_stats_per_mana'])}",
                f"  avg_transform_total_stat_delta={_fmt(row['avg_transform_total_stat_delta'])}",
                f"  avg_front_efficiency_vs_cost_band={_fmt(row['avg_front_efficiency_vs_cost_band'])}",
                "",
            ]
        )

        top = (
            unit_table[unit_table["deck_id"] == deck_id]
            .sort_values(
                ["front_efficiency_vs_cost_band", "front_stats_per_mana"],
                ascending=False,
            )
            .head(5)
        )
        lines.append("  top front-body efficiency:")
        for _, card in top.iterrows():
            name = card.get("name", "")
            label = f"{card['card_id']} {name}".strip()
            lines.append(
                "    "
                f"{label}: cost={_fmt(card['cost'], 0)} "
                f"front={_fmt(card['front_attack'],0)}/{_fmt(card['front_health'],0)} "
                f"SPM={_fmt(card['front_stats_per_mana'])} "
                f"vs_band={_fmt(card['front_efficiency_vs_cost_band'])} "
                f"effects={int(card['effect_count'])}"
            )
        lines.append("")

    if not comparison.empty:
        lines.append("=== Deck Comparison (D001 - D002) ===")
        for _, row in comparison.iterrows():
            lines.append(
                f"  {row['metric']}: {_fmt(row['D001_minus_D002'])}"
            )

    lines.extend(
        [
            "",
            "Interpretation note:",
            "  Base stat efficiency uses (ATK + HP) / card Cost.",
            "  Effects and keywords are annotated but NOT assigned arbitrary point values.",
            "  Back-side efficiency is conditional value and should not be treated as guaranteed on-play value.",
        ]
    )
    return "\n".join(lines)


def export_analysis(
    result: dict[str, pd.DataFrame],
    output_dir: str | Path,
) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    result["unit_table"].to_csv(
        output / "unit_stat_efficiency_by_card.csv",
        index=False,
        encoding="utf-8-sig",
    )
    result["deck_summary"].to_csv(
        output / "unit_stat_efficiency_deck_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    result["cost_bands"].to_csv(
        output / "unit_stat_efficiency_cost_bands.csv",
        index=False,
        encoding="utf-8-sig",
    )
    result["comparison"].to_csv(
        output / "unit_stat_efficiency_comparison.csv",
        index=False,
        encoding="utf-8-sig",
    )

    report = render_report(result)
    (output / "unit_stat_efficiency_report.txt").write_text(
        report,
        encoding="utf-8",
    )

    payload = {
        key: frame.where(pd.notna(frame), None).to_dict(orient="records")
        for key, frame in result.items()
    }
    (output / "unit_stat_efficiency.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output
