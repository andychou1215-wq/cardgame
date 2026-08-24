from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class PlaytestAnalytics:
    summaries: pd.DataFrame
    events: pd.DataFrame

    def overview(self) -> dict[str, float | int]:
        if self.summaries.empty:
            return {
                "games": 0,
                "avg_turns": 0.0,
                "p1_win_rate": 0.0,
                "p2_win_rate": 0.0,
                "first_player_win_rate": 0.0,
            }

        s = self.summaries.copy()
        winner = pd.to_numeric(s["winner_index"], errors="coerce")
        turns = pd.to_numeric(s["turn_number"], errors="coerce")

        result = {
            "games": int(len(s)),
            "avg_turns": float(turns.mean()) if turns.notna().any() else 0.0,
            "p1_win_rate": float((winner == 0).mean()),
            "p2_win_rate": float((winner == 1).mean()),
            "first_player_win_rate": 0.0,
        }

        if "first_player_index" in s.columns:
            first = pd.to_numeric(s["first_player_index"], errors="coerce")
            valid = winner.notna() & first.notna()
            if valid.any():
                result["first_player_win_rate"] = float(
                    (winner[valid] == first[valid]).mean()
                )
        return result

    def deck_results(self) -> pd.DataFrame:
        if self.summaries.empty:
            return pd.DataFrame(columns=["deck_id", "games", "wins", "win_rate", "avg_turns"])

        rows = []
        for _, game in self.summaries.iterrows():
            winner = _to_int(game.get("winner_index"))
            turns = _to_float(game.get("turn_number"))
            for player_index, col in ((0, "deck_id_p1"), (1, "deck_id_p2")):
                deck = str(game.get(col, "") or "")
                if not deck or deck == "nan":
                    continue
                rows.append({
                    "deck_id": deck,
                    "win": 1 if winner == player_index else 0,
                    "turns": turns,
                })

        if not rows:
            return pd.DataFrame(columns=["deck_id", "games", "wins", "win_rate", "avg_turns"])

        df = pd.DataFrame(rows)
        out = (
            df.groupby("deck_id", dropna=False)
            .agg(games=("win", "size"), wins=("win", "sum"), avg_turns=("turns", "mean"))
            .reset_index()
        )
        out["win_rate"] = out["wins"] / out["games"]
        return out[["deck_id", "games", "wins", "win_rate", "avg_turns"]].sort_values(
            ["win_rate", "games"], ascending=[False, False]
        )

    def card_usage(self) -> pd.DataFrame:
        if self.events.empty or "card_id" not in self.events.columns:
            return pd.DataFrame(columns=["card_id", "plays", "responses", "transforms", "deaths"])

        e = self.events.copy()
        e["card_id"] = e["card_id"].fillna("").astype(str)
        e = e[e["card_id"] != ""]
        rows = []
        for card_id, group in e.groupby("card_id"):
            counts = group["event_type"].value_counts()
            rows.append({
                "card_id": card_id,
                "plays": int(counts.get("card_played", 0)),
                "responses": int(counts.get("response_played", 0)),
                "transforms": int(counts.get("transform", 0)),
                "deaths": int(counts.get("unit_died", 0)),
            })
        if not rows:
            return pd.DataFrame(columns=["card_id", "plays", "responses", "transforms", "deaths"])
        return pd.DataFrame(rows).sort_values(
            ["plays", "responses", "transforms"], ascending=False
        )

    def event_distribution(self) -> pd.DataFrame:
        if self.events.empty or "event_type" not in self.events.columns:
            return pd.DataFrame(columns=["event_type", "count"])
        return (
            self.events["event_type"]
            .value_counts()
            .rename_axis("event_type")
            .reset_index(name="count")
        )


def _to_int(value):
    try:
        if value != value:
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_float(value):
    try:
        if value != value:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _concat_csv(paths: Iterable[str | Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        p = Path(path)
        if p.exists() and p.stat().st_size:
            frames.append(pd.read_csv(p))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_analytics(summary_paths, event_paths) -> PlaytestAnalytics:
    return PlaytestAnalytics(
        summaries=_concat_csv(summary_paths),
        events=_concat_csv(event_paths),
    )


def load_playtest_directory(directory: str | Path) -> PlaytestAnalytics:
    directory = Path(directory)
    if not directory.exists():
        return PlaytestAnalytics(pd.DataFrame(), pd.DataFrame())

    return load_analytics(
        sorted(directory.glob("*game_summary*.csv")),
        sorted(directory.glob("*event_log*.csv")),
    )
