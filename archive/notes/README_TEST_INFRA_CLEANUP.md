# Test Infrastructure Cleanup

Scope: infrastructure-only cleanup. No game-rule behavior is intentionally changed.

## Changes

1. `tests/conftest.py`
   - Shared `sample_cards`
   - Shared `sample_deck_cards`
   - Shared `mana_curve_runtime_data`
   - Fixtures use the real repository schema (`cards.id`, `deck_cards.quantity`).

2. `src/playtest/schema.py`
   - Centralizes `cards.id -> card_id` normalization.
   - Validates current `deck_cards` contract (`deck_id`, `card_id`, `quantity`).
   - Intentionally does not carry the deprecated `count` alias.

3. `tests/balance/test_mana_curve.py`
   - Reduces five local-fixture tests to four contract/metric tests.
   - Schema acceptance is folded into `test_curve_contract_and_math` rather than duplicated.
   - Marks the module as `balance`.

4. `pytest.ini`
   - Registers `balance`, `smoke`, and `integration` markers.
   - Does not enable `--strict-markers` yet, so existing tests are not broken by migration.

## Integrate

Copy the files into the repository, then follow `MANA_CURVE_INTEGRATION.txt` for the two calls that must be added to `src/playtest/mana_curve.py`.

## Validate

```powershell
py -m pytest tests/balance/test_mana_curve.py -q
py -m pytest -q
```

Expected local M3.7.1 balance count after this cleanup: 4 tests instead of 5.
The full-suite count should therefore normally be one lower than before, assuming no other tests changed.

## Marker usage

```powershell
# Balance only
py -m pytest -m balance -q

# Skip integration tests during fast iteration
py -m pytest -m "not integration" -q

# Full pre-commit suite
py -m pytest -q
```

## Future M3.7 rule

For each new balance analyzer, prefer:

- 1 contract/math test
- 1 runtime telemetry test (only if applicable)
- shared fixtures from `tests/conftest.py`
- shared schema normalization from `src/playtest/schema.py`

Do not put 5,000-game simulations inside pytest. Those remain playtest/balance-pipeline runs.
