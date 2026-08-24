RESPONSE_TRIGGER_ORDER = (
    "response_to_response",
    "before_combat_damage",
    "ally_becomes_attack_target",
    "priority",
)

def response_triggers_for_window(reason: str) -> tuple[str, ...]:
    if reason == "attack_declared":
        return RESPONSE_TRIGGER_ORDER
    return ("response_to_response", "priority")
