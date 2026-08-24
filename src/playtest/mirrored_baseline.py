from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import csv
import random

from src.ai.policies import make_bot
from src.playtest.simulation import run_bot_game


@dataclass
class MirroredGameResult:
    pairing: str
    mirror_group: int
    mirror_side: str
    game_seed: int
    bot_p1: str
    bot_p2: str
    deck_p1: str
    deck_p2: str
    winner_index: int | None
    winning_bot: str
    winning_deck: str
    turn_number: int
    actions: int
    status: str
    reason: str = ""


def run_mirrored_pairing(
    game_factory,
    *,
    bot_p1: str,
    bot_p2: str,
    deck_a: str,
    deck_b: str,
    mirror_groups: int,
    seed: int,
    max_actions: int = 1000,
    persist_callback=None,
):
    """Run paired-seat games using the same game seed for each mirror pair.

    For every mirror group:
      A: deck_a=P1, deck_b=P2
      B: deck_b=P1, deck_a=P2

    Bot policy seats are kept fixed for the pairing. This isolates deck/seat
    effects while still allowing policy-vs-policy comparison.
    """

    rng = random.Random(seed)
    results = []

    for group in range(1, mirror_groups + 1):
        game_seed = rng.randrange(0, 2**31)

        # Use deterministic paired bot seeds too. P1 policy receives the same
        # policy seed across the two mirror games, same for P2.
        bot1_seed = rng.randrange(0, 2**31)
        bot2_seed = rng.randrange(0, 2**31)

        mirrors = [
            ("A", deck_a, deck_b),
            ("B", deck_b, deck_a),
        ]

        for mirror_side, deck_p1, deck_p2 in mirrors:
            game = game_factory(deck_p1, deck_p2, game_seed)
            _auto_start(game)

            result = run_bot_game(
                game,
                bot0=make_bot(bot_p1, 0, bot1_seed),
                bot1=make_bot(bot_p2, 1, bot2_seed),
                max_actions=max_actions,
            )

            if result.winner_index == 0:
                winning_bot = bot_p1
                winning_deck = deck_p1
            elif result.winner_index == 1:
                winning_bot = bot_p2
                winning_deck = deck_p2
            else:
                winning_bot = ""
                winning_deck = ""

            row = MirroredGameResult(
                pairing=f"{bot_p1}_vs_{bot_p2}",
                mirror_group=group,
                mirror_side=mirror_side,
                game_seed=game_seed,
                bot_p1=bot_p1,
                bot_p2=bot_p2,
                deck_p1=deck_p1,
                deck_p2=deck_p2,
                winner_index=result.winner_index,
                winning_bot=winning_bot,
                winning_deck=winning_deck,
                turn_number=result.turn_number,
                actions=result.actions,
                status=result.status,
                reason=result.reason,
            )
            results.append(row)

            if persist_callback is not None and game.winner_index is not None:
                persist_callback(game)

    return results


def run_standard_mirrored_baseline(
    game_factory,
    *,
    deck_a: str,
    deck_b: str,
    mirror_groups_per_pairing: int = 50,
    seed: int = 42,
    max_actions: int = 1000,
    persist_callback=None,
):
    """Run all standard M3.5 policy pairings with mirrored deck seats."""

    pairings = [
        ("random", "random"),
        ("heuristic", "random"),
        ("random", "heuristic"),
        ("heuristic", "heuristic"),
    ]

    results = []

    for index, (bot_p1, bot_p2) in enumerate(pairings):
        results.extend(
            run_mirrored_pairing(
                game_factory,
                bot_p1=bot_p1,
                bot_p2=bot_p2,
                deck_a=deck_a,
                deck_b=deck_b,
                mirror_groups=mirror_groups_per_pairing,
                seed=seed + index * 100003,
                max_actions=max_actions,
                persist_callback=persist_callback,
            )
        )

    return results


def summarize_mirrored_baseline(results):
    """Return pairing, seat, deck, and policy summaries."""

    finished = [r for r in results if r.status == "finished"]
    total = len(results)

    summary = {
        "games": total,
        "finished": len(finished),
        "finish_rate": len(finished) / total if total else 0.0,
        "p1_wins": sum(r.winner_index == 0 for r in finished),
        "p2_wins": sum(r.winner_index == 1 for r in finished),
        "p1_win_rate": (
            sum(r.winner_index == 0 for r in finished) / len(finished)
            if finished else 0.0
        ),
        "avg_turns": (
            sum(r.turn_number for r in results) / total
            if total else 0.0
        ),
        "avg_actions": (
            sum(r.actions for r in results) / total
            if total else 0.0
        ),
        "stalled": sum(r.status == "stalled" for r in results),
        "invalid_legal_action": sum(
            r.status == "invalid_legal_action" for r in results
        ),
        "action_limit": sum(r.status == "action_limit" for r in results),
    }

    deck_rows = _rate_by_value(
        finished,
        value_getter=lambda r: r.winning_deck,
        denominator_getter=lambda deck: sum(
            1 for r in finished if r.deck_p1 == deck or r.deck_p2 == deck
        ),
        label="deck",
        participant_values=[
            value
            for r in finished
            for value in (r.deck_p1, r.deck_p2)
        ],
    )

    policy_rows = _rate_by_value(
        finished,
        value_getter=lambda r: r.winning_bot,
        denominator_getter=lambda bot: sum(
            int(r.bot_p1 == bot) + int(r.bot_p2 == bot)
            for r in finished
        ),
        label="policy",
        participant_values=[
            value
            for r in finished
            for value in (r.bot_p1, r.bot_p2)
        ],
    )

    pairing_rows = []
    pairings = sorted(set(r.pairing for r in results))
    for pairing in pairings:
        rows = [r for r in results if r.pairing == pairing]
        done = [r for r in rows if r.status == "finished"]
        pairing_rows.append({
            "pairing": pairing,
            "games": len(rows),
            "finished": len(done),
            "p1_win_rate": (
                sum(r.winner_index == 0 for r in done) / len(done)
                if done else 0.0
            ),
            "avg_turns": (
                sum(r.turn_number for r in rows) / len(rows)
                if rows else 0.0
            ),
            "avg_actions": (
                sum(r.actions for r in rows) / len(rows)
                if rows else 0.0
            ),
            "invalid_legal_action": sum(
                r.status == "invalid_legal_action" for r in rows
            ),
            "stalled": sum(r.status == "stalled" for r in rows),
            "action_limit": sum(r.status == "action_limit" for r in rows),
        })

    return {
        "overall": summary,
        "decks": deck_rows,
        "policies": policy_rows,
        "pairings": pairing_rows,
    }


def _rate_by_value(
    rows,
    value_getter,
    denominator_getter,
    label,
    participant_values=None,
):
    if participant_values is None:
        values = sorted(
            set(value_getter(row) for row in rows if value_getter(row))
        )
    else:
        values = sorted(set(v for v in participant_values if v))

    out = []

    for value in values:
        wins = sum(value_getter(row) == value for row in rows)
        denominator = denominator_getter(value)
        out.append({
            label: value,
            "wins": wins,
            "opportunities": denominator,
            "win_rate": wins / denominator if denominator else 0.0,
        })

    return out


def save_rows(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = [
        asdict(row) if hasattr(row, "__dataclass_fields__") else dict(row)
        for row in rows
    ]

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
