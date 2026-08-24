from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ScenarioStep = Callable[[Any], None]
ScenarioAct = Callable[[Any], Any]
ScenarioAssert = Callable[[Any], tuple[bool, str] | bool]


@dataclass(frozen=True)
class Scenario:
    # Keep `name` first for backward compatibility with the original M1/M2 tests:
    # Scenario("increment", arrange=..., act=..., verify=...)
    name: str
    arrange: ScenarioStep
    act: ScenarioAct
    verify: ScenarioAssert
    description: str = ""
    scenario_id: str = ""

    @property
    def id(self) -> str:
        return self.scenario_id or self.name


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
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
        return ScenarioResult(
            scenario_id=scenario.id,
            name=scenario.name,
            passed=passed,
            message=message,
        )
    except Exception as exc:
        return ScenarioResult(
            scenario_id=scenario.id,
            name=scenario.name,
            passed=False,
            error=f"{type(exc).__name__}: {exc}",
        )


def run_scenarios(game_factory: Callable[[], Any], scenarios: list[Scenario]) -> list[ScenarioResult]:
    return [run_scenario(game_factory(), scenario) for scenario in scenarios]
