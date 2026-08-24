from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import csv
import random

from src.ai.policies import make_bot
from src.playtest.simulation import run_bot_game


@dataclass
class BaselineGameResult:
    pairing: str
    game_number: int
    seed: int
    bot_p1: str
    bot_p2: str
    winner_index: int | None
    turn_number: int
    actions: int
    status: str
    reason: str = ""


def run_pairing(
    game_factory,
    *,
    bot_p1: str,
    bot_p2: str,
    games: int,
    seed: int,
    max_actions: int = 1000,
    persist_callback=None,
):
    rng = random.Random(seed)
    out = []

    for game_number in range(1, games + 1):
        game_seed = rng.randrange(0, 2**31)
        bot1_seed = rng.randrange(0, 2**31)
        bot2_seed = rng.randrange(0, 2**31)

        game = game_factory(game_seed)
        _auto_start(game)

        result = run_bot_game(
            game,
            bot0=make_bot(bot_p1, 0, bot1_seed),
            bot1=make_bot(bot_p2, 1, bot2_seed),
            max_actions=max_actions,
        )

        row = BaselineGameResult(
            pairing=f"{bot_p1}_vs_{bot_p2}",
            game_number=game_number,
            seed=game_seed,
            bot_p1=bot_p1,
            bot_p2=bot_p2,
            winner_index=result.winner_index,
            turn_number=result.turn_number,
            actions=result.actions,
            status=result.status,
            reason=result.reason,
        )
        out.append(row)

        if persist_callback is not None and game.winner_index is not None:
            persist_callback(game)

    return out


def run_standard_baseline(
    game_factory,
    *,
    games_per_pairing: int = 100,
    seed: int = 42,
    max_actions: int = 1000,
    persist_callback=None,
):
    pairings = [
        ("random", "random"),
        ("heuristic", "random"),
        ("random", "heuristic"),
        ("heuristic", "heuristic"),
    ]

    results = []
    for index, (p1, p2) in enumerate(pairings):
        results.extend(
            run_pairing(
                game_factory,
                bot_p1=p1,
                bot_p2=p2,
                games=games_per_pairing,
                seed=seed + index * 100003,
                max_actions=max_actions,
                persist_callback=persist_callback,
            )
        )
    return results


def summarize_baseline(results):
    grouped = {}
    for row in results:
        bucket = grouped.setdefault(
            row.pairing,
            {
                "pairing": row.pairing,
                "games": 0,
                "finished": 0,
                "p1_wins": 0,
                "p2_wins": 0,
                "turns": 0,
                "actions": 0,
                "stalled": 0,
                "invalid_legal_action": 0,
                "action_limit": 0,
            },
        )

        bucket["games"] += 1
        bucket["turns"] += row.turn_number
        bucket["actions"] += row.actions

        if row.status == "finished":
            bucket["finished"] += 1
            if row.winner_index == 0:
                bucket["p1_wins"] += 1
            elif row.winner_index == 1:
                bucket["p2_wins"] += 1
        elif row.status in bucket:
            bucket[row.status] += 1

    summaries = []
    for bucket in grouped.values():
        games = bucket["games"]
        finished = bucket["finished"]
        summaries.append({
            **bucket,
            "finish_rate": finished / games if games else 0.0,
            "p1_win_rate": bucket["p1_wins"] / finished if finished else 0.0,
            "p2_win_rate": bucket["p2_wins"] / finished if finished else 0.0,
            "avg_turns": bucket["turns"] / games if games else 0.0,
            "avg_actions": bucket["actions"] / games if games else 0.0,
        })

    return summaries


def save_rows(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(r) if hasattr(r, "__dataclass_fields__") else dict(r) for r in rows]
    if not payload:
        return path
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(payload[0].keys()))
        writer.writeheader()
        writer.writerows(payload)
    return path


def _auto_start(game):
    fn = getattr(game, "mulligan_hand", None)
    if not callable(fn):
        return
    guard = 0
    while not getattr(game, "game_started", True) and guard < 4:
        fn([])
        guard += 1
