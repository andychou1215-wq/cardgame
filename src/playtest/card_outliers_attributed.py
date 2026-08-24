from __future__ import annotations

from collections import defaultdict
import math


def build_attributed_outliers(
    *,
    deck_card_telemetry: list[dict],
    card_efficiency: list[dict],
    deck_baselines: dict[str, float],
    min_draws: int = 10,
    min_uses: int = 5,
) -> dict:
    efficiency = {
        (str(row.get("deck_id", "")).strip(), str(row.get("card_id", "")).strip()): row
        for row in card_efficiency
        if row.get("deck_id") and row.get("card_id")
    }

    rows = []

    for telemetry in deck_card_telemetry:
        deck_id = str(telemetry.get("deck_id", "")).strip()
        card_id = str(telemetry.get("card_id", "")).strip()
        if not deck_id or not card_id:
            continue

        static = efficiency.get((deck_id, card_id), {})
        baseline = deck_baselines.get(deck_id)

        draws = _int(telemetry.get("recorded_draw_events"), 0)
        uses = _int(telemetry.get("use_events"), 0)
        use_ratio = _float_or_none(
            telemetry.get("uses_per_recorded_draw")
        )
        win_rate = _float_or_none(
            telemetry.get("win_rate_when_used")
        )

        delta = (
            win_rate - baseline
            if win_rate is not None and baseline is not None
            else None
        )

        confidence = math.sqrt(
            min(1.0, draws / max(1, min_draws))
            * min(1.0, uses / max(1, min_uses))
        )

        # Ratio may exceed 1 because draw telemetry is incomplete.
        # Cap only the weighting contribution, not the reported metric.
        bounded_usage_weight = (
            min(1.0, max(0.0, use_ratio))
            if use_ratio is not None else 0.0
        )

        score = (
            delta
            * confidence
            * (0.5 + 0.5 * bounded_usage_weight)
            if delta is not None
            else None
        )

        rows.append({
            "deck_id": deck_id,
            "card_id": card_id,
            "name": static.get("name", ""),
            "type": static.get("type", ""),
            "cost": static.get("cost", ""),
            "quantity": static.get("quantity", ""),
            "keywords": static.get("keywords", ""),
            "operations": static.get("operations", ""),
            "triggers": static.get("triggers", ""),
            "recorded_draw_events": draws,
            "normal_play_events": _int(
                telemetry.get("normal_play_events"), 0
            ),
            "response_play_events": _int(
                telemetry.get("response_play_events"), 0
            ),
            "use_events": uses,
            "uses_per_recorded_draw": (
                round(use_ratio, 4)
                if use_ratio is not None else ""
            ),
            "avg_use_turn": telemetry.get("avg_use_turn", ""),
            "games_used": telemetry.get("games_used", ""),
            "win_rate_when_used": (
                round(win_rate, 4)
                if win_rate is not None else ""
            ),
            "deck_baseline_win_rate": (
                round(baseline, 4)
                if baseline is not None else ""
            ),
            "win_rate_delta_vs_deck": (
                round(delta, 4)
                if delta is not None else ""
            ),
            "usage_confidence": round(confidence, 4),
            "outlier_score": (
                round(score, 6)
                if score is not None else ""
            ),
            "attribution_method": telemetry.get(
                "attribution_method", ""
            ),
        })

    positive = sorted(
        [
            row for row in rows
            if _int(row["use_events"], 0) >= min_uses
            and _float_or_none(row["outlier_score"]) is not None
            and _float_or_none(row["outlier_score"]) > 0
        ],
        key=lambda row: _float_or_none(row["outlier_score"]) or 0,
        reverse=True,
    )

    negative = sorted(
        [
            row for row in rows
            if _int(row["use_events"], 0) >= min_uses
            and _float_or_none(row["outlier_score"]) is not None
            and _float_or_none(row["outlier_score"]) < 0
        ],
        key=lambda row: _float_or_none(row["outlier_score"]) or 0,
    )

    return {
        "all_cards": rows,
        "positive_outliers": positive,
        "negative_outliers": negative,
    }


def _int(value, default=0):
    try:
        if value in ("", None):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _float_or_none(value):
    try:
        if value in ("", None):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
