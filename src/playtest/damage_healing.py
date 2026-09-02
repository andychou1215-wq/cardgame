from __future__ import annotations

from pathlib import Path
import json
import pandas as pd


DAMAGE_EVENTS = {
    "combat_damage_leader",
    "combat_damage_unit",
    "effect_damage",
}
HEAL_EVENT = "heal"


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


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def attach_source_deck(events: pd.DataFrame, summaries: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        events,
        [
            "game_id", "event_type", "turn", "player_index",
            "target_kind", "target_player_index", "amount", "metadata",
        ],
        "events",
    )
    _require_columns(
        summaries,
        ["game_id", "deck_id_p1", "deck_id_p2", "winner_index"],
        "summaries",
    )

    mapping = summaries[
        ["game_id", "deck_id_p1", "deck_id_p2", "winner_index"]
    ].drop_duplicates("game_id")

    out = events.merge(mapping, on="game_id", how="inner")
    out = out[out["player_index"].notna()].copy()
    out["player_index"] = pd.to_numeric(
        out["player_index"], errors="coerce"
    ).astype("Int64")
    out = out[out["player_index"].isin([0, 1])].copy()
    out["player_index"] = out["player_index"].astype(int)

    out["deck_id"] = out.apply(
        lambda r: r["deck_id_p1"]
        if r["player_index"] == 0
        else r["deck_id_p2"],
        axis=1,
    )
    out["won"] = (
        pd.to_numeric(out["winner_index"], errors="coerce")
        == out["player_index"]
    )
    out["amount"] = _numeric(out["amount"])
    out["metadata_obj"] = out["metadata"].apply(_parse_metadata)
    return out


def build_profile_events(
    summaries: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    attached = attach_source_deck(events, summaries)
    relevant = attached[
        attached["event_type"].isin(DAMAGE_EVENTS | {HEAL_EVENT})
    ].copy()

    if relevant.empty:
        return relevant

    relevant["source_type"] = relevant["metadata_obj"].apply(
        lambda m: str(m.get("source_type", "")) or "unspecified"
    )
    relevant["requested_amount"] = relevant.apply(
        lambda r: float(
            r["metadata_obj"].get("requested_amount", r["amount"]) or 0
        ),
        axis=1,
    )
    relevant["overheal"] = relevant.apply(
        lambda r: float(
            r["metadata_obj"].get(
                "overheal",
                max(0.0, r["requested_amount"] - r["amount"])
                if r["event_type"] == HEAL_EVENT
                else 0.0,
            ) or 0
        ),
        axis=1,
    )
    relevant["blocked"] = relevant["metadata_obj"].apply(
        lambda m: float(m.get("blocked", 0) or 0)
    )

    # effect_damage can target either leader or unit.
    relevant["damage_channel"] = ""
    dmg = relevant["event_type"].isin(DAMAGE_EVENTS)
    relevant.loc[dmg, "damage_channel"] = relevant.loc[dmg].apply(
        lambda r: (
            "combat_leader"
            if r["event_type"] == "combat_damage_leader"
            else "combat_unit"
            if r["event_type"] == "combat_damage_unit"
            else "effect_leader"
            if str(r["target_kind"]) == "leader"
            else "effect_unit"
            if str(r["target_kind"]) == "unit"
            else "effect_other"
        ),
        axis=1,
    )

    relevant["heal_channel"] = ""
    heal_mask = relevant["event_type"] == HEAL_EVENT
    relevant.loc[heal_mask, "heal_channel"] = relevant.loc[heal_mask].apply(
        lambda r: (
            f"{r['source_type']}_leader"
            if str(r["target_kind"]) == "leader"
            else f"{r['source_type']}_unit"
            if str(r["target_kind"]) == "unit"
            else f"{r['source_type']}_other"
        ),
        axis=1,
    )

    return relevant.reset_index(drop=True)


def _game_players(summaries: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in summaries.iterrows():
        winner = pd.to_numeric(pd.Series([r["winner_index"]]), errors="coerce").iloc[0]
        for pidx, deck_col in [(0, "deck_id_p1"), (1, "deck_id_p2")]:
            rows.append(
                {
                    "game_id": r["game_id"],
                    "player_index": pidx,
                    "deck_id": r[deck_col],
                    "won": bool(pd.notna(winner) and int(winner) == pidx),
                }
            )
    return pd.DataFrame(rows)


def build_game_profile(
    summaries: pd.DataFrame,
    profile_events: pd.DataFrame,
) -> pd.DataFrame:
    base = _game_players(summaries)
    metric_columns = [
        "combat_damage_leader",
        "combat_damage_unit",
        "effect_damage_leader",
        "effect_damage_unit",
        "total_leader_damage",
        "total_unit_damage",
        "total_damage",
        "leader_healing",
        "unit_healing",
        "total_healing",
        "lifesteal_healing",
        "effect_healing",
        "max_health_sync_healing",
        "transform_max_health_sync_healing",
        "overheal",
        "blocked_combat_damage",
    ]

    if profile_events.empty:
        for col in metric_columns:
            base[col] = 0.0
        return base

    rows = []
    for (game_id, player_index), g in profile_events.groupby(
        ["game_id", "player_index"]
    ):
        dmg = g[g["event_type"].isin(DAMAGE_EVENTS)]
        heal = g[g["event_type"] == HEAL_EVENT]

        def damage_amount(channel: str) -> float:
            return float(
                dmg.loc[dmg["damage_channel"] == channel, "amount"].sum()
            )

        def heal_source(source_type: str) -> float:
            return float(
                heal.loc[heal["source_type"] == source_type, "amount"].sum()
            )

        combat_leader = damage_amount("combat_leader")
        combat_unit = damage_amount("combat_unit")
        effect_leader = damage_amount("effect_leader")
        effect_unit = damage_amount("effect_unit")

        leader_healing = float(
            heal.loc[heal["target_kind"].astype(str) == "leader", "amount"].sum()
        )
        unit_healing = float(
            heal.loc[heal["target_kind"].astype(str) == "unit", "amount"].sum()
        )

        rows.append(
            {
                "game_id": game_id,
                "player_index": int(player_index),
                "combat_damage_leader": combat_leader,
                "combat_damage_unit": combat_unit,
                "effect_damage_leader": effect_leader,
                "effect_damage_unit": effect_unit,
                "total_leader_damage": combat_leader + effect_leader,
                "total_unit_damage": combat_unit + effect_unit,
                "total_damage": (
                    combat_leader + combat_unit + effect_leader + effect_unit
                ),
                "leader_healing": leader_healing,
                "unit_healing": unit_healing,
                "total_healing": leader_healing + unit_healing,
                "lifesteal_healing": heal_source("lifesteal"),
                "effect_healing": heal_source("effect"),
                "max_health_sync_healing": heal_source("max_health_sync"),
                "transform_max_health_sync_healing": heal_source(
                    "transform_max_health_sync"
                ),
                "overheal": float(heal["overheal"].sum()),
                "blocked_combat_damage": float(
                    dmg.loc[
                        dmg["event_type"] == "combat_damage_unit",
                        "blocked",
                    ].sum()
                ),
            }
        )

    agg = pd.DataFrame(rows)
    out = base.merge(
        agg,
        on=["game_id", "player_index"],
        how="left",
    )
    for col in metric_columns:
        out[col] = out[col].fillna(0.0)
    return out


def build_deck_summary(game_profile: pd.DataFrame) -> pd.DataFrame:
    if game_profile.empty:
        return pd.DataFrame()

    numeric_metrics = [
        "combat_damage_leader",
        "combat_damage_unit",
        "effect_damage_leader",
        "effect_damage_unit",
        "total_leader_damage",
        "total_unit_damage",
        "total_damage",
        "leader_healing",
        "unit_healing",
        "total_healing",
        "lifesteal_healing",
        "effect_healing",
        "max_health_sync_healing",
        "transform_max_health_sync_healing",
        "overheal",
        "blocked_combat_damage",
    ]

    rows = []
    for deck_id, g in game_profile.groupby("deck_id"):
        row = {
            "deck_id": deck_id,
            "games": int(g["game_id"].nunique()),
            "win_rate": float(g["won"].mean()),
        }
        for metric in numeric_metrics:
            row[f"avg_{metric}"] = float(g[metric].mean())

        requested_heal = (
            g["total_healing"].sum() + g["overheal"].sum()
        )
        row["healing_efficiency"] = (
            float(g["total_healing"].sum() / requested_heal)
            if requested_heal > 0
            else float("nan")
        )

        total_leader = g["total_leader_damage"].sum()
        row["leader_damage_combat_share"] = (
            float(g["combat_damage_leader"].sum() / total_leader)
            if total_leader > 0
            else float("nan")
        )
        row["leader_damage_effect_share"] = (
            float(g["effect_damage_leader"].sum() / total_leader)
            if total_leader > 0
            else float("nan")
        )

        # Offensive leader pressure after own leader healing. This is descriptive,
        # not a literal game-state equation because healing can happen at different times.
        row["avg_net_leader_pressure"] = float(
            (g["total_leader_damage"] - g["leader_healing"]).mean()
        )
        rows.append(row)

    return pd.DataFrame(rows).sort_values("deck_id").reset_index(drop=True)


def build_damage_source_summary(profile_events: pd.DataFrame) -> pd.DataFrame:
    if profile_events.empty:
        return pd.DataFrame()

    dmg = profile_events[profile_events["event_type"].isin(DAMAGE_EVENTS)].copy()
    if dmg.empty:
        return pd.DataFrame()

    card_id = dmg["card_id"].fillna("").astype(str)
    dmg["source_label"] = card_id.where(card_id != "", "(unknown)")

    return (
        dmg.groupby(
            ["deck_id", "source_label", "damage_channel"],
            as_index=False,
        )
        .agg(
            events=("event_type", "size"),
            total_damage=("amount", "sum"),
            games=("game_id", "nunique"),
        )
        .sort_values(
            ["deck_id", "total_damage"],
            ascending=[True, False],
        )
        .reset_index(drop=True)
    )


def build_healing_source_summary(profile_events: pd.DataFrame) -> pd.DataFrame:
    if profile_events.empty:
        return pd.DataFrame()

    heal = profile_events[profile_events["event_type"] == HEAL_EVENT].copy()
    if heal.empty:
        return pd.DataFrame()

    return (
        heal.groupby(
            ["deck_id", "source_type", "target_kind"],
            as_index=False,
        )
        .agg(
            events=("event_type", "size"),
            actual_healing=("amount", "sum"),
            requested_healing=("requested_amount", "sum"),
            overheal=("overheal", "sum"),
            games=("game_id", "nunique"),
        )
        .sort_values(
            ["deck_id", "actual_healing"],
            ascending=[True, False],
        )
        .reset_index(drop=True)
    )


def build_comparison(deck_summary: pd.DataFrame) -> pd.DataFrame:
    if deck_summary.empty or not {"D001", "D002"}.issubset(
        set(deck_summary["deck_id"])
    ):
        return pd.DataFrame()

    d = deck_summary.set_index("deck_id")
    metrics = [
        "avg_combat_damage_leader",
        "avg_effect_damage_leader",
        "avg_total_leader_damage",
        "avg_combat_damage_unit",
        "avg_effect_damage_unit",
        "avg_total_damage",
        "avg_total_healing",
        "avg_leader_healing",
        "avg_unit_healing",
        "avg_lifesteal_healing",
        "avg_effect_healing",
        "avg_max_health_sync_healing",
        "avg_transform_max_health_sync_healing",
        "avg_overheal",
        "healing_efficiency",
        "leader_damage_combat_share",
        "leader_damage_effect_share",
        "avg_net_leader_pressure",
    ]
    return pd.DataFrame(
        [
            {
                "metric": metric,
                "D001": d.loc["D001", metric],
                "D002": d.loc["D002", metric],
                "D001_minus_D002": (
                    d.loc["D001", metric] - d.loc["D002", metric]
                ),
            }
            for metric in metrics
        ]
    )


def analyze_damage_healing(
    summaries: pd.DataFrame,
    events: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    profile_events = build_profile_events(summaries, events)
    game_profile = build_game_profile(summaries, profile_events)
    deck_summary = build_deck_summary(game_profile)
    damage_sources = build_damage_source_summary(profile_events)
    healing_sources = build_healing_source_summary(profile_events)
    comparison = build_comparison(deck_summary)

    return {
        "profile_events": profile_events,
        "game_profile": game_profile,
        "deck_summary": deck_summary,
        "damage_sources": damage_sources,
        "healing_sources": healing_sources,
        "comparison": comparison,
    }


def _fmt(v, digits=3):
    if pd.isna(v):
        return "n/a"
    return f"{float(v):.{digits}f}"


def _pct(v):
    if pd.isna(v):
        return "n/a"
    return f"{float(v) * 100:.2f}%"


def render_report(result: dict[str, pd.DataFrame]) -> str:
    lines = ["=== M3.7.5 Damage / Healing Profile ===", ""]
    deck = result["deck_summary"]
    comparison = result["comparison"]
    damage_sources = result["damage_sources"]
    healing_sources = result["healing_sources"]

    if deck.empty:
        lines.append(
            "No usable damage/heal telemetry found. "
            "Apply M3.7.5 instrumentation and run fresh simulations."
        )
        return "\n".join(lines)

    for _, r in deck.iterrows():
        deck_id = r["deck_id"]
        lines.extend([
            f"Deck: {deck_id}",
            f"  win_rate={_pct(r['win_rate'])}",
            "  damage / game:",
            f"    combat_to_leader={_fmt(r['avg_combat_damage_leader'])}",
            f"    effect_to_leader={_fmt(r['avg_effect_damage_leader'])}",
            f"    total_to_leader={_fmt(r['avg_total_leader_damage'])}",
            f"    combat_to_unit={_fmt(r['avg_combat_damage_unit'])}",
            f"    effect_to_unit={_fmt(r['avg_effect_damage_unit'])}",
            f"    total_damage={_fmt(r['avg_total_damage'])}",
            "  leader damage mix:",
            f"    combat_share={_pct(r['leader_damage_combat_share'])}",
            f"    effect_share={_pct(r['leader_damage_effect_share'])}",
            "  healing / game:",
            f"    total={_fmt(r['avg_total_healing'])}",
            f"    leader={_fmt(r['avg_leader_healing'])}",
            f"    unit={_fmt(r['avg_unit_healing'])}",
            f"    lifesteal={_fmt(r['avg_lifesteal_healing'])}",
            f"    effect={_fmt(r['avg_effect_healing'])}",
            f"    max_health_sync={_fmt(r['avg_max_health_sync_healing'])}",
            f"    transform_max_health_sync={_fmt(r['avg_transform_max_health_sync_healing'])}",
            f"    overheal={_fmt(r['avg_overheal'])}",
            f"    healing_efficiency={_pct(r['healing_efficiency'])}",
            f"  avg_net_leader_pressure={_fmt(r['avg_net_leader_pressure'])}",
            "",
        ])

        if not damage_sources.empty:
            top = damage_sources[
                (damage_sources["deck_id"] == deck_id)
                & damage_sources["damage_channel"].isin(
                    ["combat_leader", "effect_leader"]
                )
            ].head(8)
            lines.append("  top leader-damage sources:")
            if top.empty:
                lines.append("    none")
            else:
                for _, s in top.iterrows():
                    lines.append(
                        f"    {s['source_label']} [{s['damage_channel']}]: "
                        f"damage={_fmt(s['total_damage'], 0)} "
                        f"events={int(s['events'])} games={int(s['games'])}"
                    )
            lines.append("")

        if not healing_sources.empty:
            hs = healing_sources[healing_sources["deck_id"] == deck_id]
            lines.append("  healing sources:")
            if hs.empty:
                lines.append("    none")
            else:
                for _, s in hs.iterrows():
                    lines.append(
                        f"    {s['source_type']} -> {s['target_kind']}: "
                        f"actual={_fmt(s['actual_healing'], 0)} "
                        f"requested={_fmt(s['requested_healing'], 0)} "
                        f"overheal={_fmt(s['overheal'], 0)}"
                    )
            lines.append("")

    if not comparison.empty:
        lines.append("=== Deck Comparison (D001 - D002) ===")
        for _, r in comparison.iterrows():
            if "share" in r["metric"] or "efficiency" in r["metric"]:
                value = _pct(r["D001_minus_D002"])
            else:
                value = _fmt(r["D001_minus_D002"])
            lines.append(f"  {r['metric']}: {value}")

    lines.extend([
        "",
        "Interpretation:",
        "  Leader damage is split into combat and effect channels.",
        "  Heal uses actual restored HP; requested_amount and overheal are kept separately.",
        "  Max-HP synchronized healing is tracked separately from ordinary heal effects.",
        "  avg_net_leader_pressure is descriptive (leader damage dealt minus own leader healing), not a causal game-state metric.",
    ])
    return "\n".join(lines)


def export_analysis(
    result: dict[str, pd.DataFrame],
    output_dir: str | Path,
) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    filenames = {
        "game_profile": "damage_healing_by_game.csv",
        "deck_summary": "damage_healing_deck_summary.csv",
        "damage_sources": "damage_sources.csv",
        "healing_sources": "healing_sources.csv",
        "comparison": "damage_healing_comparison.csv",
    }
    for key, filename in filenames.items():
        result[key].to_csv(out / filename, index=False, encoding="utf-8-sig")

    (out / "damage_healing_report.txt").write_text(
        render_report(result),
        encoding="utf-8",
    )
    return out
