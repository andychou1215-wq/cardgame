from pathlib import Path

from src.core.events import TriggerEvent, TriggerQueue
from src.playtest.core_scenario_catalog import CORE_SCENARIOS
from src.playtest.telemetry import PlaytestRecorder


def test_trigger_queue_fifo_and_snapshot():
    q = TriggerQueue()
    q.push(TriggerEvent("on_leave", "a", "U001", "front", 0))
    q.push(TriggerEvent("on_flip", "b", "U002", "back", 1))
    assert q.pop().source_id == "a"
    event = q.pop()
    assert event.source_id == "b"
    assert event.side == "back"


def test_exactly_ten_core_scenarios():
    assert len(CORE_SCENARIOS) == 10
    assert CORE_SCENARIOS[0].scenario_id == "S001"
    assert CORE_SCENARIOS[-1].scenario_id == "S010"


def test_recorder_exports_csv(tmp_path: Path):
    r = PlaytestRecorder(seed=42, game_id="g")
    r.record("card_played", turn=1, active_player=0, player_index=0, card_id="U001")
    r.record("heal", turn=1, active_player=0, player_index=0, amount=2)
    event_path = r.export_csv(tmp_path / "event_log.csv")
    summary_path = r.export_summary_csv(tmp_path / "game_summary.csv")
    assert event_path.exists()
    assert summary_path.exists()
    assert "card_played" in event_path.read_text(encoding="utf-8-sig")
    assert "healing_done" in summary_path.read_text(encoding="utf-8-sig")
