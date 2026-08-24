from src.core.stack import StackItem


def test_m1_3_positional_constructor_remains_compatible():
    item = StackItem("s", "R1", 1, [], "response_to_response")

    assert item.source_id == "s"
    assert item.card_id == "R1"
    assert item.controller_index == 1
    assert item.trigger == "response_to_response"
    assert item.stack_item_id.startswith("stk-")


def test_m1_4_explicit_stack_item_id_still_supported():
    item = StackItem(
        source_id="s",
        card_id="R1",
        controller_index=1,
        effects=[],
        trigger="priority",
        stack_item_id="stk-explicit",
    )

    assert item.stack_item_id == "stk-explicit"
