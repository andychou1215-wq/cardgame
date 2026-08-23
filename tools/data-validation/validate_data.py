import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CARDS_FILE = ROOT / "data" / "cards" / "cards.csv"
EFFECTS_FILE = ROOT / "data" / "cards" / "effects.csv"


def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def validate_card_ids():
    cards = load_csv(CARDS_FILE)
    effects = load_csv(EFFECTS_FILE)

    # cards.csv 中所有合法 card id
    valid_card_ids = {row["id"].strip() for row in cards}

    errors = []

    for line_number, effect in enumerate(effects, start=2):
        effect_id = effect["effect_id"].strip()
        card_id = effect["card_id"].strip()

        if not card_id:
            errors.append(
                f"[effects.csv:{line_number}] "
                f"{effect_id}: card_id 不可為空"
            )
            continue

        if card_id not in valid_card_ids:
            errors.append(
                f"[effects.csv:{line_number}] "
                f"{effect_id}: 找不到 card_id '{card_id}'"
            )

    return errors


def main():
    errors = []

    errors.extend(validate_card_ids())

    if errors:
        print("Data validation failed:\n")

        for error in errors:
            print(f"  ERROR: {error}")

        print(f"\n共發現 {len(errors)} 個錯誤。")
        sys.exit(1)

    print("Data validation passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()