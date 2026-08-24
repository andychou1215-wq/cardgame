from types import SimpleNamespace

from src.ai.actions import DECLARE_ATTACK, PLAY_CARD
from src.ai.legal_actions import legal_actions


class Card:
    def __init__(self, card_type="unit", cost=1, card_id="U1", instance_id="i1"):
        self.card_type = card_type
        self.cost = cost
        self.card_id = card_id
        self.instance_id = instance_id


class Data:
    def effects_for(self, card_id, trigger, side):
        return []


def base_game():
    player = SimpleNamespace(
        mana=10,
        hand=[],
        battlefield=[],
    )
    return SimpleNamespace(
        winner_index=None,
        pending_choice=None,
        pending_combat=None,
        priority_window=None,
        active_player_index=0,
        players=[player, SimpleNamespace()],
        data=Data(),
        activated_options=lambda: [],
        legal_attackers=lambda: [],
        legal_attack_targets=lambda: [],
    )


def test_response_not_offered_as_normal_play():
    game = base_game()
    game.players[0].hand = [Card(card_type="response", card_id="R1")]
    actions = legal_actions(game, 0)
    assert not any(a.kind == PLAY_CARD for a in actions)


def test_attackers_come_from_engine_authority():
    game = base_game()
    unit = Card(card_type="unit", instance_id="u1")
    target = SimpleNamespace(key="leader:1")
    game.legal_attackers = lambda: [unit]
    game.legal_attack_targets = lambda: [target]

    actions = legal_actions(game, 0)
    attacks = [a for a in actions if a.kind == DECLARE_ATTACK]
    assert len(attacks) == 1
    assert attacks[0].source_id == "u1"
