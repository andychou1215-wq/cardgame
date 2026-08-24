from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StateBasedResult:
    changed: bool = False
    deaths: bool = False
    transforms: bool = False
    winner_changed: bool = False

    @property
    def stable(self) -> bool:
        return not self.changed


class StateBasedCheck:
    """Single authoritative state-based checkpoint.

    Order:
    1. simultaneous lethal-unit collection
    2. transform checks (AP -> NAP)
    3. winner check

    A pass stops after deaths/transforms mutate state, allowing their triggers
    to resolve before another state-based pass.
    """

    def run_once(self, game) -> StateBasedResult:
        if game._handle_deaths():
            return StateBasedResult(changed=True, deaths=True)

        if game.check_transforms():
            return StateBasedResult(changed=True, transforms=True)

        before = game.winner_index
        game._check_winner()
        winner_changed = game.winner_index != before
        return StateBasedResult(
            changed=winner_changed,
            winner_changed=winner_changed,
        )
