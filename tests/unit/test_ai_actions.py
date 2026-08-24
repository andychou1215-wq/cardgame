from src.ai.actions import END_TURN, GameAction

def test_action_key_stable():
    assert GameAction(END_TURN,0).key == GameAction(END_TURN,0).key
