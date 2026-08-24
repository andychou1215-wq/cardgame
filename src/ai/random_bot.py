import random
from src.ai.legal_actions import legal_actions
from src.ai.executor import execute_action

class RandomBot:
    def __init__(self, player_index, seed=None):
        self.player_index = player_index
        self.rng = random.Random(seed)

    def choose_action(self, game):
        actions = legal_actions(game, self.player_index)
        return None if not actions else self.rng.choice(actions)

    def act(self, game):
        action = self.choose_action(game)
        return (None, None) if action is None else (action, execute_action(game, action))
