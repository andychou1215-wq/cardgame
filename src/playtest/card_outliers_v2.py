from __future__ import annotations

from src.playtest.card_outliers import (
    build_card_outlier_analysis as _legacy_build,
)


def build_card_outlier_analysis_v2(
    *,
    card_telemetry,
    card_efficiency,
    deck_baselines,
    min_acquisitions=10,
    min_uses=5,
):
    """Compatibility wrapper using corrected telemetry semantics.

    M3.5.4's existing analyzer can consume the rebuilt telemetry because
    backward-compatible aliases are emitted. This function documents the new
    naming and provides corrected presentation fields.
    """

    result = _legacy_build(
        card_telemetry=card_telemetry,
        card_efficiency=card_efficiency,
        deck_baselines=deck_baselines,
        min_draws=min_acquisitions,
        min_plays=min_uses,
    )

    for row in result["all_cards"]:
        row["recorded_draw_events"] = row.get("draw_events", 0)
        row["use_events"] = row.get("play_events", 0)
        row["uses_per_recorded_draw"] = row.get(
            "play_given_draw_rate", ""
        )
        row["win_rate_when_used"] = row.get(
            "win_rate_when_played", ""
        )
        row["win_rate_delta_when_used_vs_deck"] = row.get(
            "win_rate_delta_vs_deck", ""
        )

    return result
