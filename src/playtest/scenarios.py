from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ScenarioStep = Callable[[Any], None]
ScenarioAct = Callable[[Any], Any]
ScenarioAssert = Callable[[Any], tuple[bool, str] | bool]


@dataclass(frozen=True)
class Scenario:
    name: str
    arrange: ScenarioStep
    act: ScenarioAct
    verify: ScenarioAssert
    description: str = ""


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    passed: bool
    message: str = ""
    error: str = ""


def run_scenario(game: Any, scenario: Scenario) -> ScenarioResult:
    try:
        scenario.arrange(game)
        scenario.act(game)
        checked = scenario.verify(game)
        if isinstance(checked, tuple):
            passed, message = checked
        else:
            passed, message = bool(checked), ""
        return ScenarioResult(scenario.name, passed, message)
    except Exception as exc:  # scenario runner should report, not hide, failures
        return ScenarioResult(scenario.name, False, error=f"{type(exc).__name__}: {exc}")


def run_scenarios(game_factory: Callable[[], Any], scenarios: list[Scenario]) -> list[ScenarioResult]:
    return [run_scenario(game_factory(), scenario) for scenario in scenarios]
