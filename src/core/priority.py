from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PriorityWindow:
    first_player_index: int
    reason: str = ""
    trigger_target: Any | None = None
    current_player_index: int = field(init=False)
    consecutive_passes: int = 0
    is_open: bool = True
    stack: list[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.current_player_index = self.first_player_index

    @property
    def stack_size(self) -> int:
        return len(self.stack)

    def add_response(self, player_index: int, item: Any) -> None:
        self._require_open()
        self._require_priority(player_index)
        self.stack.append(item)
        self.consecutive_passes = 0
        self.current_player_index = 1 - player_index

    def pass_priority(self, player_index: int) -> bool:
        self._require_open()
        self._require_priority(player_index)
        self.consecutive_passes += 1
        if self.consecutive_passes >= 2:
            self.is_open = False
            return True
        self.current_player_index = 1 - player_index
        return False

    def pop_stack(self) -> Any:
        if not self.stack:
            raise IndexError("priority stack is empty")
        return self.stack.pop()

    def drain_lifo(self) -> list[Any]:
        result = []
        while self.stack:
            result.append(self.pop_stack())
        return result

    def _require_open(self) -> None:
        if not self.is_open:
            raise ValueError("priority window is already closed")

    def _require_priority(self, player_index: int) -> None:
        if player_index != self.current_player_index:
            raise ValueError(
                f"player {player_index} does not currently have priority "
                f"(expected {self.current_player_index})"
            )
