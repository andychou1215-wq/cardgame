from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src/playtest/mirrored_baseline.py"


def main():
    if not TARGET.exists():
        raise SystemExit("src/playtest/mirrored_baseline.py not found")

    text = TARGET.read_text(encoding="utf-8")

    old = '''def _rate_by_value(rows, value_getter, denominator_getter, label):
    values = sorted(
        set(value_getter(row) for row in rows if value_getter(row))
    )
    out = []

    for value in values:
        wins = sum(value_getter(row) == value for row in rows)
        denominator = denominator_getter(value)
        out.append({
            label: value,
            "wins": wins,
            "opportunities": denominator,
            "win_rate": wins / denominator if denominator else 0.0,
        })

    return out
'''

    new = '''def _rate_by_value(
    rows,
    value_getter,
    denominator_getter,
    label,
    participant_values=None,
):
    if participant_values is None:
        values = sorted(
            set(value_getter(row) for row in rows if value_getter(row))
        )
    else:
        values = sorted(set(v for v in participant_values if v))

    out = []

    for value in values:
        wins = sum(value_getter(row) == value for row in rows)
        denominator = denominator_getter(value)
        out.append({
            label: value,
            "wins": wins,
            "opportunities": denominator,
            "win_rate": wins / denominator if denominator else 0.0,
        })

    return out
'''

    if old not in text and "participant_values=None" not in text:
        raise SystemExit("Could not find _rate_by_value() anchor")

    if old in text:
        text = text.replace(old, new, 1)

    old_deck = '''    deck_rows = _rate_by_value(
        finished,
        value_getter=lambda r: r.winning_deck,
        denominator_getter=lambda deck: sum(
            1 for r in finished if r.deck_p1 == deck or r.deck_p2 == deck
        ),
        label="deck",
    )
'''

    new_deck = '''    deck_rows = _rate_by_value(
        finished,
        value_getter=lambda r: r.winning_deck,
        denominator_getter=lambda deck: sum(
            1 for r in finished if r.deck_p1 == deck or r.deck_p2 == deck
        ),
        label="deck",
        participant_values=[
            value
            for r in finished
            for value in (r.deck_p1, r.deck_p2)
        ],
    )
'''

    old_policy = '''    policy_rows = _rate_by_value(
        finished,
        value_getter=lambda r: r.winning_bot,
        denominator_getter=lambda bot: sum(
            int(r.bot_p1 == bot) + int(r.bot_p2 == bot)
            for r in finished
        ),
        label="policy",
    )
'''

    new_policy = '''    policy_rows = _rate_by_value(
        finished,
        value_getter=lambda r: r.winning_bot,
        denominator_getter=lambda bot: sum(
            int(r.bot_p1 == bot) + int(r.bot_p2 == bot)
            for r in finished
        ),
        label="policy",
        participant_values=[
            value
            for r in finished
            for value in (r.bot_p1, r.bot_p2)
        ],
    )
'''

    if old_deck in text:
        text = text.replace(old_deck, new_deck, 1)
    elif "participant_values=[" not in text:
        raise SystemExit("Could not find deck summary anchor")

    if old_policy in text:
        text = text.replace(old_policy, new_policy, 1)
    elif text.count("participant_values=[") < 2:
        raise SystemExit("Could not find policy summary anchor")

    TARGET.write_text(text, encoding="utf-8")

    verify = TARGET.read_text(encoding="utf-8")
    checks = [
        "participant_values=None",
        "for value in (r.deck_p1, r.deck_p2)",
        "for value in (r.bot_p1, r.bot_p2)",
    ]
    missing = [x for x in checks if x not in verify]
    if missing:
        raise SystemExit("Hotfix verification failed: " + ", ".join(missing))

    print("M3.5.1 summary hotfix applied.")
    print("Run:")
    print("  py -m pytest -q")
    print("  py tools/run_mirrored_baseline.py --mirror-groups-per-pairing 10 --seed 42")


if __name__ == "__main__":
    main()
