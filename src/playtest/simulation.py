from dataclasses import dataclass, asdict
from pathlib import Path
import csv, random

from src.ai.legal_actions import legal_actions
from src.ai.executor import execute_action
from src.ai.random_bot import RandomBot


@dataclass
class SimulationResult:
    simulation_id: int
    game_id: str
    winner_index: int | None
    turn_number: int
    actions: int
    status: str
    reason: str = ""


def decision_player_index(game):
    # PendingChoice belongs to the queued effect's source player.
    pending = getattr(game, "pending_choice", None)
    if pending is not None:
        queued = getattr(pending, "queued", None)
        owner = getattr(queued, "source_player_index", None)
        if owner in (0, 1):
            return owner

    window = getattr(game, "priority_window", None)
    if window is not None and getattr(window, "is_open", False):
        return window.current_player_index

    return game.active_player_index


def describe_decision_state(game, actor):
    pending = getattr(game, "pending_choice", None)
    combat = getattr(game, "pending_combat", None)
    window = getattr(game, "priority_window", None)

    if pending is not None:
        queued = getattr(pending, "queued", None)
        effect = getattr(queued, "effect", None)
        return (
            "pending_choice"
            f"; actor={actor}"
            f"; source_player={getattr(queued, 'source_player_index', None)}"
            f"; effect_id={getattr(effect, 'effect_id', '')}"
            f"; candidates={len(getattr(pending, 'candidates', []) or [])}"
        )

    if combat is not None:
        return (
            "combat"
            f"; actor={actor}"
            f"; priority_open={bool(window and getattr(window, 'is_open', False))}"
            f"; priority_player={getattr(window, 'current_player_index', None) if window else None}"
        )

    player = game.players[actor]
    return (
        "main_phase"
        f"; actor={actor}"
        f"; hand={len(player.hand)}"
        f"; battlefield={len(player.battlefield)}"
        f"; mana={player.mana}"
    )


def run_bot_game(game, bot0=None, bot1=None, max_actions=1000):
    bots = [bot0 or RandomBot(0), bot1 or RandomBot(1)]
    actions_taken = 0
    stalled = 0

    while game.winner_index is None and actions_taken < max_actions:
        actor = decision_player_index(game)
        actions = legal_actions(game, actor)

        if not actions:
            stalled += 1
            if stalled >= 3:
                return SimulationResult(
                    0,
                    getattr(game.telemetry, "game_id", ""),
                    game.winner_index,
                    game.turn_number,
                    actions_taken,
                    "stalled",
                    "no legal actions; " + describe_decision_state(game, actor),
                )
            continue

        stalled = 0
        action = bots[actor].rng.choice(actions)
        result = execute_action(game, action)
        actions_taken += 1

        if not result.ok:
            return SimulationResult(
                0,
                getattr(game.telemetry, "game_id", ""),
                game.winner_index,
                game.turn_number,
                actions_taken,
                "invalid_legal_action",
                f"{action.kind}: {result.message}; "
                + describe_decision_state(game, actor),
            )

    if game.winner_index is not None:
        return SimulationResult(
            0,
            getattr(game.telemetry, "game_id", ""),
            game.winner_index,
            game.turn_number,
            actions_taken,
            "finished",
        )

    return SimulationResult(
        0,
        getattr(game.telemetry, "game_id", ""),
        None,
        game.turn_number,
        actions_taken,
        "action_limit",
        f"max_actions={max_actions}; "
        + describe_decision_state(game, decision_player_index(game)),
    )


def run_batch(
    game_factory,
    games,
    seed=1,
    max_actions=1000,
    store=None,
    rules_version="",
    commit_hash="",
):
    rng = random.Random(seed)
    results = []

    for sid in range(1, games + 1):
        game = game_factory(rng.randrange(0, 2**31))
        _auto_start(game)

        result = run_bot_game(
            game,
            RandomBot(0, rng.randrange(0, 2**31)),
            RandomBot(1, rng.randrange(0, 2**31)),
            max_actions=max_actions,
        )
        result.simulation_id = sid
        results.append(result)

        if store is not None and game.winner_index is not None:
            store.save_game(
                game.telemetry,
                game,
                rules_version=rules_version,
                commit_hash=commit_hash,
            )

    return results


def save_simulation_results(path, results):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(r) for r in results]

    if rows:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    return path


def _auto_start(game):
    fn = getattr(game, "mulligan_hand", None)
    if not callable(fn):
        return

    guard = 0
    while not getattr(game, "game_started", True) and guard < 4:
        fn([])
        guard += 1
