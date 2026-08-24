from __future__ import annotations

from src.ai.heuristic_bot import HeuristicBot
from src.ai.random_bot import RandomBot


def make_bot(kind: str, player_index: int, seed: int | None = None):
    normalized = kind.strip().lower()
    if normalized in {"random", "r"}:
        return RandomBot(player_index, seed=seed)
    if normalized in {"heuristic", "h"}:
        return HeuristicBot(player_index, seed=seed)
    raise ValueError(f"Unknown bot kind: {kind}")
