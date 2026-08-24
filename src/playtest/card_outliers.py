from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import csv
import math


def load_csv(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_card_outlier_analysis(
    *,
    card_telemetry: list[dict],
    card_efficiency: list[dict],
    deck_baselines: dict[str, float],
    min_draws: int = 10,
    min_plays: int = 5,
) -> dict:
    """Compare card performance against its own deck baseline.

    This is intentionally diagnostic, not causal. A high card delta can be
    caused by selection effects, game-state timing, deck strength, or actual
    card power.
    """

    membership = _build_membership(card_efficiency)
    telemetry_by_card = {
        row.get("card_id", "").strip(): row
        for row in card_telemetry
        if row.get("card_id", "").strip()
    }

    rows = []

    for card_id, memberships in sorted(membership.items()):
        t = telemetry_by_card.get(card_id, {})
        draw_events = _int(t.get("draw_events"), 0)
        play_events = _int(t.get("play_events"), 0)
        response_events = _int(t.get("response_events"), 0)
        transform_events = _int(t.get("transform_events"), 0)
        effect_damage_events = _int(t.get("effect_damage_events"), 0)
        heal_events = _int(t.get("heal_events"), 0)
        games_played = _int(t.get("games_played"), 0)

        win_rate_when_played = _float_or_none(
            t.get("win_rate_when_played")
        )
        play_given_draw = _float_or_none(
            t.get("play_given_draw_rate")
        )
        avg_play_turn = _float_or_none(t.get("avg_play_turn"))

        for m in memberships:
            deck_id = m["deck_id"]
            baseline = deck_baselines.get(deck_id)

            delta = None
            if (
                win_rate_when_played is not None
                and baseline is not None
            ):
                delta = win_rate_when_played - baseline

            usage_confidence = _volume_weight(
                draws=draw_events,
                plays=play_events,
                min_draws=min_draws,
                min_plays=min_plays,
            )

            # Outlier score is not a "power score". It rewards:
            # - sufficient volume
            # - high absolute deviation from deck baseline
            # - actual play rate after draw
            #
            # Sign is preserved:
            # positive = above deck baseline
            # negative = below deck baseline
            if delta is None:
                outlier_score = None
            else:
                usage = (
                    play_given_draw
                    if play_given_draw is not None
                    else 0.0
                )
                outlier_score = (
                    delta
                    * usage_confidence
                    * (0.5 + 0.5 * usage)
                )

            rows.append({
                "deck_id": deck_id,
                "card_id": card_id,
                "name": m.get("name", ""),
                "type": m.get("type", ""),
                "cost": _int(m.get("cost"), 0),
                "quantity": _int(m.get("quantity"), 0),
                "front_stats_per_mana": m.get(
                    "front_stats_per_mana", ""
                ),
                "keywords": m.get("keywords", ""),
                "operations": m.get("operations", ""),
                "triggers": m.get("triggers", ""),
                "draw_events": draw_events,
                "play_events": play_events,
                "play_given_draw_rate": (
                    round(play_given_draw, 4)
                    if play_given_draw is not None
                    else ""
                ),
                "avg_play_turn": (
                    round(avg_play_turn, 3)
                    if avg_play_turn is not None
                    else ""
                ),
                "games_played": games_played,
                "win_rate_when_played": (
                    round(win_rate_when_played, 4)
                    if win_rate_when_played is not None
                    else ""
                ),
                "deck_baseline_win_rate": (
                    round(baseline, 4)
                    if baseline is not None
                    else ""
                ),
                "win_rate_delta_vs_deck": (
                    round(delta, 4)
                    if delta is not None
                    else ""
                ),
                "usage_confidence": round(
                    usage_confidence, 4
                ),
                "outlier_score": (
                    round(outlier_score, 6)
                    if outlier_score is not None
                    else ""
                ),
                "response_events": response_events,
                "transform_events": transform_events,
                "effect_damage_events": effect_damage_events,
                "heal_events": heal_events,
            })

    diagnostics = {
        "all_cards": rows,
        "positive_outliers": _positive_outliers(
            rows, min_plays=min_plays
        ),
        "negative_outliers": _negative_outliers(
            rows, min_plays=min_plays
        ),
        "high_draw_low_play": _high_draw_low_play(
            rows, min_draws=min_draws
        ),
        "high_usage": _high_usage(
            rows, min_draws=min_draws
        ),
        "response_frequency": _frequency_rank(
            rows, "response_events"
        ),
        "transform_frequency": _frequency_rank(
            rows, "transform_events"
        ),
        "effect_damage_frequency": _frequency_rank(
            rows, "effect_damage_events"
        ),
        "heal_frequency": _frequency_rank(
            rows, "heal_events"
        ),
    }

    return diagnostics


def load_deck_baselines(
    deck_overall_path: str | Path,
) -> dict[str, float]:
    rows = load_csv(deck_overall_path)
    out = {}
    for row in rows:
        deck = row.get("deck", "").strip()
        wr = _float_or_none(row.get("win_rate"))
        if deck and wr is not None:
            out[deck] = wr
    return out


def render_outlier_report(
    analysis: dict,
    deck_baselines: dict[str, float],
) -> str:
    lines = [
        "# M3.5.4 Card Performance / Outlier Diagnostics",
        "",
        "## Deck baselines",
        "",
        "| Deck | Baseline Win Rate |",
        "|---|---:|",
    ]

    for deck, wr in sorted(deck_baselines.items()):
        lines.append(f"| {deck} | {wr:.1%} |")

    lines += [
        "",
        "## Positive outliers vs own deck baseline",
        "",
        "| Deck | Card | Play | Draw | Play/Draw | WR Played | Deck WR | Delta | Score |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in analysis["positive_outliers"][:20]:
        lines.append(_card_row(row))

    lines += [
        "",
        "## Negative outliers vs own deck baseline",
        "",
        "| Deck | Card | Play | Draw | Play/Draw | WR Played | Deck WR | Delta | Score |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in analysis["negative_outliers"][:20]:
        lines.append(_card_row(row))

    lines += [
        "",
        "## High draw / low play",
        "",
        "| Deck | Card | Draw | Play | Play/Draw | Avg Play Turn |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in analysis["high_draw_low_play"][:20]:
        lines.append(
            f"| {row['deck_id']} | {row['card_id']} {row['name']} | "
            f"{row['draw_events']} | {row['play_events']} | "
            f"{_pct(row['play_given_draw_rate'])} | "
            f"{row['avg_play_turn']} |"
        )

    lines += [
        "",
        "## High-frequency Response cards",
        "",
        "| Deck | Card | Response Events | Play Events | WR Played | Delta vs Deck |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in analysis["response_frequency"][:15]:
        lines.append(_frequency_row(row, "response_events"))

    lines += [
        "",
        "## High-frequency Transform cards",
        "",
        "| Deck | Card | Transform Events | Play Events | WR Played | Delta vs Deck |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in analysis["transform_frequency"][:15]:
        lines.append(_frequency_row(row, "transform_events"))

    lines += [
        "",
        "## Reading this report",
        "",
        "- `win_rate_delta_vs_deck` is the card's win-when-played rate minus its own deck baseline.",
        "- A positive delta does not prove the card causes wins; strong cards may be played only when already ahead.",
        "- A negative delta can reflect late-game desperation plays rather than a weak card.",
        "- `outlier_score` combines delta, usage volume, and play-after-draw rate. It is a triage score, not a balance value.",
        "- Review positive and negative outliers together with cost, keywords, operations, and average play turn.",
        "- High draw / low play cards are especially useful for spotting cards that are too expensive, too conditional, or poorly valued by the current bot.",
        "",
    ]

    return "\n".join(lines)


def save_analysis_outputs(
    output_dir: str | Path,
    analysis: dict,
    deck_baselines: dict[str, float],
) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {}

    for name, rows in analysis.items():
        path = output_dir / f"{name}.csv"
        save_csv(path, rows)
        outputs[name] = path

    report = output_dir / "REPORT.md"
    report.write_text(
        render_outlier_report(analysis, deck_baselines),
        encoding="utf-8",
    )
    outputs["report"] = report

    return outputs


def save_csv(path: str | Path, rows: list[dict]) -> Path:
    path = Path(path)
    if not rows:
        path.write_text("", encoding="utf-8")
        return path

    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    return path


def _build_membership(card_efficiency):
    out = defaultdict(list)
    for row in card_efficiency:
        card_id = row.get("card_id", "").strip()
        if card_id:
            out[card_id].append(row)
    return out


def _volume_weight(
    *,
    draws: int,
    plays: int,
    min_draws: int,
    min_plays: int,
) -> float:
    draw_weight = min(
        1.0,
        draws / max(1, min_draws),
    )
    play_weight = min(
        1.0,
        plays / max(1, min_plays),
    )
    return math.sqrt(draw_weight * play_weight)


def _positive_outliers(rows, min_plays):
    filtered = [
        r
        for r in rows
        if _int(r.get("play_events"), 0) >= min_plays
        and _float_or_none(r.get("outlier_score")) is not None
        and _float_or_none(r.get("outlier_score")) > 0
    ]
    return sorted(
        filtered,
        key=lambda r: _float_or_none(r["outlier_score"]) or 0,
        reverse=True,
    )


def _negative_outliers(rows, min_plays):
    filtered = [
        r
        for r in rows
        if _int(r.get("play_events"), 0) >= min_plays
        and _float_or_none(r.get("outlier_score")) is not None
        and _float_or_none(r.get("outlier_score")) < 0
    ]
    return sorted(
        filtered,
        key=lambda r: _float_or_none(r["outlier_score"]) or 0,
    )


def _high_draw_low_play(rows, min_draws):
    filtered = [
        r
        for r in rows
        if _int(r.get("draw_events"), 0) >= min_draws
        and _float_or_none(r.get("play_given_draw_rate")) is not None
    ]
    return sorted(
        filtered,
        key=lambda r: (
            _float_or_none(r["play_given_draw_rate"]) or 0,
            -_int(r["draw_events"], 0),
        ),
    )


def _high_usage(rows, min_draws):
    filtered = [
        r
        for r in rows
        if _int(r.get("draw_events"), 0) >= min_draws
        and _float_or_none(r.get("play_given_draw_rate")) is not None
    ]
    return sorted(
        filtered,
        key=lambda r: (
            _float_or_none(r["play_given_draw_rate"]) or 0,
            _int(r["play_events"], 0),
        ),
        reverse=True,
    )


def _frequency_rank(rows, field):
    return sorted(
        [r for r in rows if _int(r.get(field), 0) > 0],
        key=lambda r: _int(r.get(field), 0),
        reverse=True,
    )


def _card_row(row):
    return (
        f"| {row['deck_id']} | {row['card_id']} {row['name']} | "
        f"{row['play_events']} | {row['draw_events']} | "
        f"{_pct(row['play_given_draw_rate'])} | "
        f"{_pct(row['win_rate_when_played'])} | "
        f"{_pct(row['deck_baseline_win_rate'])} | "
        f"{_pct(row['win_rate_delta_vs_deck'], signed=True)} | "
        f"{row['outlier_score']} |"
    )


def _frequency_row(row, field):
    return (
        f"| {row['deck_id']} | {row['card_id']} {row['name']} | "
        f"{row[field]} | {row['play_events']} | "
        f"{_pct(row['win_rate_when_played'])} | "
        f"{_pct(row['win_rate_delta_vs_deck'], signed=True)} |"
    )


def _pct(value, signed=False):
    x = _float_or_none(value)
    if x is None:
        return ""
    if signed:
        return f"{x:+.1%}"
    return f"{x:.1%}"


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
