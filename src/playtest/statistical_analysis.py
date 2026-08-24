from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path
import csv


@dataclass(frozen=True)
class BinomialEstimate:
    wins: int
    games: int
    win_rate: float
    ci_low: float
    ci_high: float


def wilson_interval(wins: int, games: int, z: float = 1.959963984540054) -> BinomialEstimate:
    """Wilson score interval for a binomial proportion."""
    if games <= 0:
        return BinomialEstimate(wins, games, 0.0, 0.0, 0.0)

    p = wins / games
    z2 = z * z
    denominator = 1.0 + z2 / games
    center = (p + z2 / (2.0 * games)) / denominator
    margin = (
        z
        * sqrt((p * (1.0 - p) / games) + z2 / (4.0 * games * games))
        / denominator
    )

    return BinomialEstimate(
        wins=wins,
        games=games,
        win_rate=p,
        ci_low=max(0.0, center - margin),
        ci_high=min(1.0, center + margin),
    )


def load_mirrored_games(path: str | Path) -> list[dict]:
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        row["winner_index"] = _int_or_none(row.get("winner_index"))
        row["mirror_group"] = _int_or_none(row.get("mirror_group"))
        row["game_seed"] = _int_or_none(row.get("game_seed"))
        row["turn_number"] = int(row.get("turn_number") or 0)
        row["actions"] = int(row.get("actions") or 0)

    return rows


def analyze_mirrored_games(rows: list[dict]) -> dict:
    finished = [row for row in rows if row.get("status") == "finished"]

    return {
        "overall": _overall(rows, finished),
        "deck_by_seat": _deck_by_seat(finished),
        "deck_by_pairing": _deck_by_pairing(finished),
        "policy_head_to_head": _policy_head_to_head(finished),
        "deck_overall": _deck_overall(finished),
        "pairing_health": _pairing_health(rows),
    }


def _overall(rows, finished):
    p1_wins = sum(row["winner_index"] == 0 for row in finished)
    estimate = wilson_interval(p1_wins, len(finished))

    return {
        "games": len(rows),
        "finished": len(finished),
        "finish_rate": len(finished) / len(rows) if rows else 0.0,
        "p1_wins": p1_wins,
        "p2_wins": sum(row["winner_index"] == 1 for row in finished),
        "p1_win_rate": estimate.win_rate,
        "p1_ci_low": estimate.ci_low,
        "p1_ci_high": estimate.ci_high,
        "avg_turns": _avg(row["turn_number"] for row in rows),
        "avg_actions": _avg(row["actions"] for row in rows),
        "invalid_legal_action": sum(
            row.get("status") == "invalid_legal_action" for row in rows
        ),
        "stalled": sum(row.get("status") == "stalled" for row in rows),
        "action_limit": sum(row.get("status") == "action_limit" for row in rows),
    }


def _deck_overall(finished):
    decks = sorted(
        {
            deck
            for row in finished
            for deck in (row.get("deck_p1", ""), row.get("deck_p2", ""))
            if deck
        }
    )

    out = []
    for deck in decks:
        games = sum(
            row.get("deck_p1") == deck or row.get("deck_p2") == deck
            for row in finished
        )
        wins = sum(row.get("winning_deck") == deck for row in finished)
        e = wilson_interval(wins, games)

        out.append({
            "deck": deck,
            "wins": wins,
            "games": games,
            "win_rate": e.win_rate,
            "ci_low": e.ci_low,
            "ci_high": e.ci_high,
        })

    return out


def _deck_by_seat(finished):
    decks = sorted(
        {
            deck
            for row in finished
            for deck in (row.get("deck_p1", ""), row.get("deck_p2", ""))
            if deck
        }
    )

    out = []
    for deck in decks:
        for seat in (0, 1):
            key = "deck_p1" if seat == 0 else "deck_p2"
            games_rows = [row for row in finished if row.get(key) == deck]
            games = len(games_rows)
            wins = sum(row["winner_index"] == seat for row in games_rows)
            e = wilson_interval(wins, games)

            out.append({
                "deck": deck,
                "seat": "P1" if seat == 0 else "P2",
                "wins": wins,
                "games": games,
                "win_rate": e.win_rate,
                "ci_low": e.ci_low,
                "ci_high": e.ci_high,
            })

    return out


def _deck_by_pairing(finished):
    decks = sorted(
        {
            deck
            for row in finished
            for deck in (row.get("deck_p1", ""), row.get("deck_p2", ""))
            if deck
        }
    )
    pairings = sorted({row.get("pairing", "") for row in finished if row.get("pairing")})

    out = []
    for pairing in pairings:
        pairing_rows = [row for row in finished if row.get("pairing") == pairing]
        for deck in decks:
            games = sum(
                row.get("deck_p1") == deck or row.get("deck_p2") == deck
                for row in pairing_rows
            )
            wins = sum(row.get("winning_deck") == deck for row in pairing_rows)
            e = wilson_interval(wins, games)

            out.append({
                "pairing": pairing,
                "deck": deck,
                "wins": wins,
                "games": games,
                "win_rate": e.win_rate,
                "ci_low": e.ci_low,
                "ci_high": e.ci_high,
            })

    return out


def _policy_head_to_head(finished):
    # Same-policy games contain no information about H vs R policy strength.
    cross = [
        row
        for row in finished
        if row.get("bot_p1") != row.get("bot_p2")
        and {row.get("bot_p1"), row.get("bot_p2")} == {"heuristic", "random"}
    ]

    heuristic_wins = sum(row.get("winning_bot") == "heuristic" for row in cross)
    random_wins = sum(row.get("winning_bot") == "random" for row in cross)
    heuristic_est = wilson_interval(heuristic_wins, len(cross))

    seat_rows = []
    for heuristic_seat in (0, 1):
        if heuristic_seat == 0:
            subset = [
                row for row in cross
                if row.get("bot_p1") == "heuristic"
            ]
        else:
            subset = [
                row for row in cross
                if row.get("bot_p2") == "heuristic"
            ]

        wins = sum(row.get("winning_bot") == "heuristic" for row in subset)
        e = wilson_interval(wins, len(subset))
        seat_rows.append({
            "heuristic_seat": "P1" if heuristic_seat == 0 else "P2",
            "heuristic_wins": wins,
            "games": len(subset),
            "heuristic_win_rate": e.win_rate,
            "ci_low": e.ci_low,
            "ci_high": e.ci_high,
        })

    deck_rows = []
    decks = sorted(
        {
            deck
            for row in cross
            for deck in (row.get("deck_p1", ""), row.get("deck_p2", ""))
            if deck
        }
    )
    for deck in decks:
        subset = []
        for row in cross:
            heuristic_deck = (
                row.get("deck_p1")
                if row.get("bot_p1") == "heuristic"
                else row.get("deck_p2")
            )
            if heuristic_deck == deck:
                subset.append(row)

        wins = sum(row.get("winning_bot") == "heuristic" for row in subset)
        e = wilson_interval(wins, len(subset))
        deck_rows.append({
            "heuristic_deck": deck,
            "heuristic_wins": wins,
            "games": len(subset),
            "heuristic_win_rate": e.win_rate,
            "ci_low": e.ci_low,
            "ci_high": e.ci_high,
        })

    return {
        "overall": {
            "games": len(cross),
            "heuristic_wins": heuristic_wins,
            "random_wins": random_wins,
            "heuristic_win_rate": heuristic_est.win_rate,
            "ci_low": heuristic_est.ci_low,
            "ci_high": heuristic_est.ci_high,
        },
        "by_seat": seat_rows,
        "by_deck": deck_rows,
    }


def _pairing_health(rows):
    out = []
    for pairing in sorted({row.get("pairing", "") for row in rows if row.get("pairing")}):
        subset = [row for row in rows if row.get("pairing") == pairing]
        finished = [row for row in subset if row.get("status") == "finished"]
        p1_wins = sum(row["winner_index"] == 0 for row in finished)
        e = wilson_interval(p1_wins, len(finished))

        out.append({
            "pairing": pairing,
            "games": len(subset),
            "finished": len(finished),
            "p1_win_rate": e.win_rate,
            "p1_ci_low": e.ci_low,
            "p1_ci_high": e.ci_high,
            "avg_turns": _avg(row["turn_number"] for row in subset),
            "avg_actions": _avg(row["actions"] for row in subset),
            "invalid_legal_action": sum(
                row.get("status") == "invalid_legal_action" for row in subset
            ),
            "stalled": sum(row.get("status") == "stalled" for row in subset),
            "action_limit": sum(row.get("status") == "action_limit" for row in subset),
        })

    return out


def save_csv(path: str | Path, rows: list[dict]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return path

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return path


def render_markdown_report(analysis: dict) -> str:
    overall = analysis["overall"]
    h2h = analysis["policy_head_to_head"]["overall"]

    lines = [
        "# M3.5.2 Statistical Analysis",
        "",
        "## Engine / simulation health",
        "",
        f"- Games: {overall['games']}",
        f"- Finished: {overall['finished']} ({overall['finish_rate']:.1%})",
        f"- Invalid legal action: {overall['invalid_legal_action']}",
        f"- Stalled: {overall['stalled']}",
        f"- Action limit: {overall['action_limit']}",
        f"- Average turns: {overall['avg_turns']:.2f}",
        f"- Average actions: {overall['avg_actions']:.2f}",
        "",
        "## Seat signal",
        "",
        (
            f"- P1 win rate: {overall['p1_win_rate']:.1%} "
            f"(95% CI {overall['p1_ci_low']:.1%}–{overall['p1_ci_high']:.1%})"
        ),
        "",
        "## Deck overall",
        "",
        "| Deck | Wins | Games | Win Rate | 95% CI |",
        "|---|---:|---:|---:|---:|",
    ]

    for row in analysis["deck_overall"]:
        lines.append(
            f"| {row['deck']} | {row['wins']} | {row['games']} | "
            f"{row['win_rate']:.1%} | {row['ci_low']:.1%}–{row['ci_high']:.1%} |"
        )

    lines += [
        "",
        "## Deck × Seat",
        "",
        "| Deck | Seat | Wins | Games | Win Rate | 95% CI |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for row in analysis["deck_by_seat"]:
        lines.append(
            f"| {row['deck']} | {row['seat']} | {row['wins']} | {row['games']} | "
            f"{row['win_rate']:.1%} | {row['ci_low']:.1%}–{row['ci_high']:.1%} |"
        )

    lines += [
        "",
        "## Heuristic vs Random — head-to-head only",
        "",
        (
            f"- Heuristic win rate: {h2h['heuristic_win_rate']:.1%} "
            f"({h2h['heuristic_wins']}/{h2h['games']}, "
            f"95% CI {h2h['ci_low']:.1%}–{h2h['ci_high']:.1%})"
        ),
        "",
        "### By Heuristic seat",
        "",
        "| Heuristic Seat | Wins | Games | Win Rate | 95% CI |",
        "|---|---:|---:|---:|---:|",
    ]

    for row in analysis["policy_head_to_head"]["by_seat"]:
        lines.append(
            f"| {row['heuristic_seat']} | {row['heuristic_wins']} | {row['games']} | "
            f"{row['heuristic_win_rate']:.1%} | {row['ci_low']:.1%}–{row['ci_high']:.1%} |"
        )

    lines += [
        "",
        "### By deck controlled by Heuristic",
        "",
        "| Heuristic Deck | Wins | Games | Win Rate | 95% CI |",
        "|---|---:|---:|---:|---:|",
    ]

    for row in analysis["policy_head_to_head"]["by_deck"]:
        lines.append(
            f"| {row['heuristic_deck']} | {row['heuristic_wins']} | {row['games']} | "
            f"{row['heuristic_win_rate']:.1%} | {row['ci_low']:.1%}–{row['ci_high']:.1%} |"
        )

    lines += [
        "",
        "## Interpretation guidance",
        "",
        "- Seat balance: treat P1 rate as a seat signal only after deck mirroring.",
        "- Deck strength: compare both overall deck rate and Deck × Seat rows.",
        "- Policy strength: use cross-policy H-vs-R only; exclude R-vs-R and H-vs-H.",
        "- Confidence intervals describe sampling uncertainty, not all sources of bias.",
        "- Do not rebalance individual cards from one aggregate result; use card-level telemetry next.",
        "",
    ]

    return "\n".join(lines)


def _avg(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _int_or_none(value):
    if value in (None, ""):
        return None
    return int(value)
