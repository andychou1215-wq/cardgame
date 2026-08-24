from pathlib import Path

from src.playtest.card_deck_diagnostics import build_telemetry_diagnostics


def test_missing_event_log_is_reported_unavailable():
    result = build_telemetry_diagnostics(None, None, {})
    assert result["available"] is False
    assert result["card_metrics"] == []
