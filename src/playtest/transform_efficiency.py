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
    try:
        parsed = json.loads(str(value))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _attach_deck(events: pd.DataFrame, summaries: pd.DataFrame) -> pd.DataFrame:
    _require_columns(events, ["game_id", "player_index"], "events")
    _require_columns(
        summaries,
        ["game_id", "deck_id_p1", "deck_id_p2", "winner_index"],
        "summaries",
    )

    mapping = summaries[
        ["game_id", "deck_id_p1", "deck_id_p2", "winner_index"]
    ].drop_duplicates("game_id")

    out = events.merge(mapping, on="game_id", how="left")
    out = out[out["player_index"].notna()].copy()
    out["player_index"] = out["player_index"].astype(int)
    out["deck_id"] = out.apply(
        lambda r: r["deck_id_p1"] if r["player_index"] == 0 else r["deck_id_p2"],
        axis=1,
    )
    out["won"] = out["winner_index"] == out["player_index"]
    return out


def build_transform_events(
    summaries: pd.DataFrame,
    events: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    _require_columns(
        events,
        ["game_id", "event_type", "turn", "player_index", "card_id", "source_id", "metadata"],
        "events",
    )

    plays = events[events["event_type"] == "card_played"].copy()
    transforms = events[events["event_type"] == "transform"].copy()

    # on_flip trigger is authoritative evidence that the transform trigger entered
    # the trigger queue. It is not itself an arbitrary "value score".
    triggers = events[events["event_type"] == "trigger"].copy()
    if not triggers.empty:
        triggers["metadata_obj"] = triggers["metadata"].apply(_parse_metadata)
        triggers = triggers[
            triggers["metadata_obj"].apply(lambda x: x.get("trigger") == "on_flip")
        ].copy()

    return (
        _attach_deck(plays, summaries),
        _attach_deck(transforms, summaries),
        _attach_deck(triggers, summaries) if not triggers.empty else triggers,
    )


def build_deck_baseline(summaries: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        summaries,
        ["game_id", "deck_id_p1", "deck_id_p2", "winner_index"],
        "summaries",
    )

    rows = []
    for _, r in summaries.iterrows():
        winner = r["winner_index"]
        for pidx, col in [(0, "deck_id_p1"), (1, "deck_id_p2")]:
            rows.append(
                {
                    "game_id": r["game_id"],
                    "deck_id": r[col],
                    "player_index": pidx,
                    "won": winner == pidx,
                }
            )
    df = pd.DataFrame(rows)
    return (
        df.groupby("deck_id", as_index=False)
        .agg(
            games=("game_id", "nunique"),
            deck_win_rate=("won", "mean"),
        )
        .sort_values("deck_id")
        .reset_index(drop=True)
    )


def build_transform_card_summary(
    summaries: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    plays, transforms, flip_triggers = build_transform_events(summaries, events)

    # Count unique instances so one malformed duplicate telemetry row cannot inflate
    # transform rate.
    unit_plays = (
        plays[plays["source_id"].astype(str) != ""]
        .groupby(["deck_id", "card_id"], as_index=False)
        .agg(
            played_instances=("source_id", "nunique"),
            games_played=("game_id", "nunique"),
        )
    )

    if transforms.empty:
        transforms_agg = pd.DataFrame(
            columns=[
                "deck_id", "card_id", "transformed_instances",
                "games_transformed", "avg_transform_turn",
                "wins_when_transformed", "transform_game_win_rate",
            ]
        )
    else:
        transforms_agg = (
            transforms.groupby(["deck_id", "card_id"], as_index=False)
            .agg(
                transformed_instances=("source_id", "nunique"),
                games_transformed=("game_id", "nunique"),
                avg_transform_turn=("turn", "mean"),
                wins_when_transformed=("won", "sum"),
                transform_game_win_rate=("won", "mean"),
            )
        )

    result = unit_plays.merge(
        transforms_agg,
        on=["deck_id", "card_id"],
        how="left",
    )

    for col in [
        "transformed_instances",
        "games_transformed",
        "wins_when_transformed",
    ]:
        result[col] = result[col].fillna(0).astype(int)

    result["transform_rate_per_play"] = (
        result["transformed_instances"] / result["played_instances"]
    )

    if flip_triggers.empty:
        result["on_flip_trigger_count"] = 0
        result["on_flip_trigger_per_transform"] = float("nan")
    else:
        trig = (
            flip_triggers.groupby(["deck_id", "card_id"], as_index=False)
            .size()
            .rename(columns={"size": "on_flip_trigger_count"})
        )
        result = result.merge(trig, on=["deck_id", "card_id"], how="left")
        result["on_flip_trigger_count"] = result["on_flip_trigger_count"].fillna(0).astype(int)
        denom = result["transformed_instances"].where(result["transformed_instances"] > 0)
        result["on_flip_trigger_per_transform"] = result["on_flip_trigger_count"] / denom

    baseline = build_deck_baseline(summaries)
    result = result.merge(baseline[["deck_id", "deck_win_rate"]], on="deck_id", how="left")
    result["win_rate_delta_when_transformed"] = (
        result["transform_game_win_rate"] - result["deck_win_rate"]
    )

    return result.sort_values(
        ["deck_id", "transform_rate_per_play", "played_instances"],
        ascending=[True, False, False],
    ).reset_index(drop=True)


def build_transform_deck_summary(
    card_summary: pd.DataFrame,
    summaries: pd.DataFrame,
) -> pd.DataFrame:
    baseline = build_deck_baseline(summaries)
    if card_summary.empty:
        return baseline

    rows = []
    for deck_id, g in card_summary.groupby("deck_id"):
        plays = g["played_instances"].sum()
        transforms = g["transformed_instances"].sum()
        transformed_cards = g[g["transformed_instances"] > 0]

        weighted_turn = float("nan")
        if transforms > 0:
            valid = transformed_cards["avg_transform_turn"].notna()
            if valid.any():
                weighted_turn = float(
                    (
                        transformed_cards.loc[valid, "avg_transform_turn"]
                        * transformed_cards.loc[valid, "transformed_instances"]
                    ).sum()
                    / transformed_cards.loc[valid, "transformed_instances"].sum()
                )

        # Use unique game/deck data to avoid card-level double counting for win rate.
        rows.append(
            {
                "deck_id": deck_id,
                "played_instances": int(plays),
                "transformed_instances": int(transforms),
                "overall_transform_rate_per_play": (
                    float(transforms / plays) if plays else float("nan")
                ),
                "avg_transform_turn_weighted": weighted_turn,
                "transforming_card_types": int(
                    transformed_cards["card_id"].nunique()
                ),
                "on_flip_trigger_count": int(g["on_flip_trigger_count"].sum()),
            }
        )

    out = pd.DataFrame(rows)
    return (
        out.merge(baseline, on="deck_id", how="left")
        .sort_values("deck_id")
        .reset_index(drop=True)
    )


def build_transform_game_summary(
    summaries: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    _, transforms, _ = build_transform_events(summaries, events)
    baseline_rows = []
    for _, r in summaries.iterrows():
        for pidx, col in [(0, "deck_id_p1"), (1, "deck_id_p2")]:
            baseline_rows.append(
                {
                    "game_id": r["game_id"],
                    "player_index": pidx,
                    "deck_id": r[col],
                    "won": r["winner_index"] == pidx,
                }
            )
    game_players = pd.DataFrame(baseline_rows)

    if transforms.empty:
        game_players["transform_count"] = 0
    else:
        counts = (
            transforms.groupby(
                ["game_id", "player_index", "deck_id"],
                as_index=False,
            )
            .agg(
                transform_count=("source_id", "nunique"),
                first_transform_turn=("turn", "min"),
            )
        )
        game_players = game_players.merge(
            counts,
            on=["game_id", "player_index", "deck_id"],
            how="left",
        )
        game_players["transform_count"] = game_players["transform_count"].fillna(0).astype(int)

    game_players["transformed_any"] = game_players["transform_count"] > 0
    return game_players


def build_transform_outcome_summary(game_summary: pd.DataFrame) -> pd.DataFrame:
    if game_summary.empty:
        return pd.DataFrame()

    return (
        game_summary.groupby(["deck_id", "transformed_any"], as_index=False)
        .agg(
            games=("game_id", "nunique"),
            win_rate=("won", "mean"),
            avg_transform_count=("transform_count", "mean"),
        )
        .sort_values(["deck_id", "transformed_any"])
        .reset_index(drop=True)
    )


def build_deck_comparison(deck_summary: pd.DataFrame) -> pd.DataFrame:
    if deck_summary.empty or not {"D001", "D002"}.issubset(set(deck_summary["deck_id"])):
        return pd.DataFrame()

    d = deck_summary.set_index("deck_id")
    metrics = [
        "overall_transform_rate_per_play",
        "avg_transform_turn_weighted",
        "on_flip_trigger_count",
    ]
    return pd.DataFrame(
        [
            {
                "metric": m,
                "D001": d.loc["D001", m],
                "D002": d.loc["D002", m],
                "D001_minus_D002": d.loc["D001", m] - d.loc["D002", m],
            }
            for m in metrics
        ]
    )


def analyze_transform_efficiency(
    summaries: pd.DataFrame,
    events: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    card_summary = build_transform_card_summary(summaries, events)
    deck_summary = build_transform_deck_summary(card_summary, summaries)
    game_summary = build_transform_game_summary(summaries, events)
    outcome_summary = build_transform_outcome_summary(game_summary)
    comparison = build_deck_comparison(deck_summary)
    return {
        "card_summary": card_summary,
        "deck_summary": deck_summary,
        "game_summary": game_summary,
        "outcome_summary": outcome_summary,
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
    lines = ["=== M3.7.4 Transform Efficiency ===", ""]
    deck = result["deck_summary"]
    cards = result["card_summary"]
    outcomes = result["outcome_summary"]
    comparison = result["comparison"]

    for _, r in deck.iterrows():
        deck_id = r["deck_id"]
        lines.extend([
            f"Deck: {deck_id}",
            f"  played_instances={int(r['played_instances'])}",
            f"  transformed_instances={int(r['transformed_instances'])}",
            f"  transform_rate_per_play={_pct(r['overall_transform_rate_per_play'])}",
            f"  avg_transform_turn={_fmt(r['avg_transform_turn_weighted'])}",
            f"  transforming_card_types={int(r['transforming_card_types'])}",
            f"  on_flip_trigger_count={int(r['on_flip_trigger_count'])}",
            f"  deck_win_rate={_pct(r['deck_win_rate'])}",
            "",
        ])

        deck_cards = cards[
            (cards["deck_id"] == deck_id)
            & (cards["transformed_instances"] > 0)
        ].sort_values(
            ["transform_rate_per_play", "transformed_instances"],
            ascending=False,
        )
        lines.append("  transform cards:")
        if deck_cards.empty:
            lines.append("    none")
        else:
            for _, c in deck_cards.iterrows():
                lines.append(
                    f"    {c['card_id']}: "
                    f"plays={int(c['played_instances'])} "
                    f"transforms={int(c['transformed_instances'])} "
                    f"rate={_pct(c['transform_rate_per_play'])} "
                    f"avg_turn={_fmt(c['avg_transform_turn'])} "
                    f"WR_when_transformed={_pct(c['transform_game_win_rate'])} "
                    f"delta_vs_deck={_pct(c['win_rate_delta_when_transformed'])} "
                    f"flip_triggers={int(c['on_flip_trigger_count'])}"
                )
        lines.append("")

    if not outcomes.empty:
        lines.append("=== Transform / Outcome ===")
        for _, r in outcomes.iterrows():
            state = "transformed" if bool(r["transformed_any"]) else "not_transformed"
            lines.append(
                f"  {r['deck_id']} {state}: "
                f"games={int(r['games'])} WR={_pct(r['win_rate'])} "
                f"avg_transforms={_fmt(r['avg_transform_count'])}"
            )
        lines.append("")

    if not comparison.empty:
        lines.append("=== Deck Comparison (D001 - D002) ===")
        for _, r in comparison.iterrows():
            value = r["D001_minus_D002"]
            if "rate" in r["metric"]:
                shown = _pct(value)
            else:
                shown = _fmt(value)
            lines.append(f"  {r['metric']}: {shown}")

    lines.extend([
        "",
        "Interpretation note:",
        "  transform_rate_per_play = unique transformed instances / unique played instances.",
        "  WR_when_transformed is associative, not causal: stronger games may simply survive long enough to transform.",
        "  on_flip_trigger_count verifies that Transform effects entered the trigger pipeline; it is not an arbitrary value score.",
    ])
    return "\n".join(lines)


def export_analysis(result: dict[str, pd.DataFrame], output_dir: str | Path) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    filenames = {
        "card_summary": "transform_by_card.csv",
        "deck_summary": "transform_deck_summary.csv",
        "game_summary": "transform_by_game.csv",
        "outcome_summary": "transform_outcome_summary.csv",
        "comparison": "transform_comparison.csv",
    }
    for key, filename in filenames.items():
        result[key].to_csv(out / filename, index=False, encoding="utf-8-sig")

    (out / "transform_report.txt").write_text(
        render_report(result),
        encoding="utf-8",
    )
    return out
