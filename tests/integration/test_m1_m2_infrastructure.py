from pathlib import Path

from src.core.events import TriggerEvent, TriggerQueue
from src.playtest.scenarios import Scenario, run_scenario
from src.playtest.telemetry import PlaytestRecorder


def test_trigger_queue_is_fifo():
    queue = TriggerQueue()
    queue.push(TriggerEvent("on_leave", "a", "U001", "front", 0))
    queue.push(TriggerEvent("on_leave", "b", "U002", "front", 1))

    assert queue.pop().source_id == "a"
    assert queue.pop().source_id == "b"
    assert not queue


def test_trigger_event_keeps_source_side_snapshot():
    queue = TriggerQueue()
    queue.push(TriggerEvent("on_flip", "x", "U009", "back", 0))

    event = queue.pop()
    assert event.card_id == "U009"
    assert event.side == "back"


def test_playtest_recorder_summary_and_export(tmp_path: Path):
    recorder = PlaytestRecorder(seed=42, game_id="test-game")
    recorder.record("card_played", turn=1, active_player=0, player_index=0, card_id="U001")
    recorder.record("draw", turn=1, active_player=0, player_index=0, amount=2)
    recorder.record("heal", turn=1, active_player=0, player_index=0, amount=3)
    recorder.record("combat_damage_leader", turn=1, active_player=0, player_index=0, amount=4)
    recorder.record("transform", turn=1, active_player=0, player_index=0, card_id="U001")

    summary = recorder.summary()
    assert summary["cards_played"] == 1
    assert summary["cards_drawn"] == 2
    assert summary["healing_done"] == 3
    assert summary["combat_damage_to_leader"] == 4
    assert summary["transforms"] == 1

    json_path = recorder.export_json(tmp_path / "game.json")
    csv_path = recorder.export_csv(tmp_path / "events.csv")
    assert json_path.exists()
    assert csv_path.exists()


def test_scenario_runner_reports_pass():
    game = {"value": 0}
    scenario = Scenario(
        "increment",
        arrange=lambda g: g.update(value=1),
        act=lambda g: g.update(value=g["value"] + 1),
        verify=lambda g: (g["value"] == 2, "value should become 2"),
    )

    result = run_scenario(game, scenario)
    assert result.passed
    assert result.error == ""
