# Repository Structure

```text
cardgame/
├─ apps/                 # Streamlit entry points
├─ archive/              # historical patches / deprecated designs
├─ assets/               # art / UI / audio assets
├─ data/                 # cards / effects / decks / factions / keywords / balance
├─ docs/                 # design + architecture + playtest documentation
├─ playtest_data/        # generated playtest outputs
├─ src/                  # game engine source
├─ tests/                # regression, scenario and future categorized tests
├─ tools/                # long-lived developer tools only
├─ CHANGELOG.md
├─ LICENSE
├─ README.md
└─ requirements.txt
```

## Source boundaries

- `src/core/`: game orchestration, events, priority, state-based checks
- `src/combat/`: combat, damage and legal targeting
- `src/cards/`: definitions / instances / transforms
- `src/effects/`: effect models and resolver
- `src/deck/`: data loading / validation
- `src/playtest/`: telemetry, scenarios and analytics
- `src/ai/`: bots / policies
- `src/ui/`: reusable Streamlit UI components

## Tests

The repository currently has historical `test_engine_v2.py` through `v5.py`.
Do **not** move them blindly because newer tests import helper fixtures from those modules.

Migration should happen in a separate commit:

1. extract `make_repo`, `start_game`, `make_keyword_unit` into `tests/conftest.py`
   or `tests/fixtures/`;
2. update imports;
3. run the full suite;
4. then split tests into `unit/`, `integration/`, and `scenarios/`.
