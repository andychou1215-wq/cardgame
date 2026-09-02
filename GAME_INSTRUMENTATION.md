# M3.7.5 Core Telemetry Instrumentation

The current recorder already summarizes these event names:

- `heal`
- `combat_damage_leader`
- `combat_damage_unit`
- `effect_damage`

But current `Game.resolve_combat()` / `_resolve_effect()` do not consistently
record them. Apply the following instrumentation before running M3.7.5.

## 1. Combat damage to leader

In `resolve_combat()`, after calculating `amount` and applying leader damage:

```python
self.telemetry.record(
    "combat_damage_leader",
    turn=self.turn_number,
    active_player=self.active_player_index,
    player_index=attacker.owner_index,
    card_id=attacker.card_id,
    source_id=attacker.instance_id,
    target=defender,
    amount=amount,
    metadata={"source_type": "combat"},
)
```

If your UnitInstance does not expose `owner_index`, use the attacking player's
known index from the combat state instead.

## 2. Combat damage between units

After simultaneous damage calculation, emit TWO events: active attack and
counterattack.

```python
self.telemetry.record(
    "combat_damage_unit",
    turn=self.turn_number,
    active_player=self.active_player_index,
    player_index=attacker.owner_index,
    card_id=attacker.card_id,
    source_id=attacker.instance_id,
    target=TargetRef("unit", target.owner_index, target.instance_id),
    amount=dealt_to_target,
    metadata={
        "source_type": "combat",
        "role": "active_attack",
        "blocked": blocked_by_target,
        "raw_amount": attacker_raw,
    },
)

self.telemetry.record(
    "combat_damage_unit",
    turn=self.turn_number,
    active_player=self.active_player_index,
    player_index=target.owner_index,
    card_id=target.card_id,
    source_id=target.instance_id,
    target=TargetRef("unit", attacker.owner_index, attacker.instance_id),
    amount=dealt_to_attacker,
    metadata={
        "source_type": "combat",
        "role": "counterattack",
        "blocked": blocked_by_attacker,
        "raw_amount": defender_raw,
    },
)
```

Zero actual damage may still be recorded when useful for block analysis. If you
prefer smaller logs, record only when amount > 0 or blocked > 0.

## 3. Lifesteal healing

Change `_apply_lifesteal()` so it records actual healing, requested healing,
and overheal.

Immediately after:

```python
healed = attacker.heal(damage_dealt)
```

record:

```python
owner_index = attacker.owner_index

self.telemetry.record(
    "heal",
    turn=self.turn_number,
    active_player=self.active_player_index,
    player_index=owner_index,
    card_id=attacker.card_id,
    source_id=attacker.instance_id,
    target=TargetRef("unit", owner_index, attacker.instance_id),
    amount=healed,
    metadata={
        "source_type": "lifesteal",
        "requested_amount": damage_dealt,
        "overheal": max(0, damage_dealt - healed),
    },
)
```

Record the event even when actual heal is 0 if you want overheal diagnostics.

## 4. Effect healing

Inside `_resolve_effect()`, `effect.operation == "heal"` already computes
`healed`.

After that computation, add:

```python
self.telemetry.record(
    "heal",
    turn=self.turn_number,
    active_player=self.active_player_index,
    player_index=queued.source_player_index,
    card_id=getattr(source, "card_id", ""),
    source_id=queued.source_id,
    target=ref,
    amount=healed,
    metadata={
        "source_type": "effect",
        "effect_id": effect.effect_id,
        "requested_amount": effect.value,
        "overheal": max(0, effect.value - healed),
    },
)
```

This attributes healing to the deck/card that caused it, while target fields
identify who actually received the healing.

## 5. Effect damage

For leader damage, calculate ACTUAL damage instead of blindly using
`effect.value` in telemetry:

```python
if ref.kind == "leader":
    p = self.players[ref.player_index]
    before = p.leader_health
    p.leader_health = max(0, p.leader_health - effect.value)
    dealt = before - p.leader_health
else:
    target = self.find_unit(ref.instance_id)
    dealt = target.take_damage(effect.value) if target else 0
```

Then record:

```python
self.telemetry.record(
    "effect_damage",
    turn=self.turn_number,
    active_player=self.active_player_index,
    player_index=queued.source_player_index,
    card_id=getattr(source, "card_id", ""),
    source_id=queued.source_id,
    target=ref,
    amount=dealt,
    metadata={
        "source_type": "effect",
        "effect_id": effect.effect_id,
        "requested_amount": effect.value,
    },
)
```

## 6. Max-health synchronized healing from effects

The current rule correctly calls `increase_max_health()` /
`add_timed_max_health()` and receives `healed_with_max_hp`.

When `kind == "max_health" and effect.value > 0`, add:

```python
self.telemetry.record(
    "heal",
    turn=self.turn_number,
    active_player=self.active_player_index,
    player_index=queued.source_player_index,
    card_id=getattr(source, "card_id", ""),
    source_id=queued.source_id,
    target=ref,
    amount=healed_with_max_hp,
    metadata={
        "source_type": "max_health_sync",
        "effect_id": effect.effect_id,
        "requested_amount": healed_with_max_hp,
        "overheal": 0,
        "max_health_increase": effect.value,
    },
)
```

This keeps synchronized healing separate from ordinary healing.

## 7. Transform max-health synchronized healing

In `_transform()`, the engine already calculates `max_increase` and synchronizes
current health.

When `max_increase > 0`, add:

```python
sync_heal = unit.current_health - before_health

self.telemetry.record(
    "heal",
    turn=self.turn_number,
    active_player=self.active_player_index,
    player_index=owner_index,
    card_id=unit.card_id,
    source_id=unit.instance_id,
    target=TargetRef("unit", owner_index, unit.instance_id),
    amount=sync_heal,
    metadata={
        "source_type": "transform_max_health_sync",
        "requested_amount": sync_heal,
        "overheal": 0,
        "max_health_increase": max_increase,
    },
)
```

## Smoke-test telemetry

After instrumentation:

```powershell
py -m pytest -q

py tools/run_simulation.py `
  --games 10 `
  --seed 37501 `
  --deck1 D001 `
  --deck2 D002 `
  --rules-version "v0.1.1-M3.7.5"
```

Check:

```powershell
Import-Csv playtest_data/raw/event_log.csv |
  Where-Object {
    $_.event_type -in @(
      "combat_damage_leader",
      "combat_damage_unit",
      "effect_damage",
      "heal"
    )
  } |
  Select-Object -Last 20
```

Do not run the full 5,000-game batch until these events are present.
