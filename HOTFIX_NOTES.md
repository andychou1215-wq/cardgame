# M1.1 + M2.1 Hotfix

Fixes the five failures reported after applying the cumulative pack.

## 1. Scenario constructor compatibility

Old test code uses:

```python
Scenario(
    "increment",
    arrange=...,
    act=...,
    verify=...,
)
```

The M1.1 version inserted `scenario_id` before `name`, breaking that API.

`Scenario` is now backward compatible:

```python
Scenario(
    name,
    arrange,
    act,
    verify,
    description="",
    scenario_id="",
)
```

New scenarios can still use `scenario_id="S001"`.

## 2. S004 Block test

The failing assertion read `attacker.attack` after combat resolution.
The attacker had changed attack after combat (for example through Transform/state changes),
so the test compared damage against a post-combat value.

The test now snapshots:

```python
attack_before_combat = attacker.attack
```

and calculates Block from that value.

## 3. U007 fixture assumption

`tests.test_engine_v2.make_repo()` does not guarantee `U007` exists.

S008, S009, and the State-Based Check test now use cards guaranteed by the fixture:

- D001 / U001
- D002 / U002

The scenarios only need disposable Unit instances; they do not require U007 specifically.

## Expected result

Run:

```powershell
py -m pytest -q
```

The five failures reported should be resolved.
