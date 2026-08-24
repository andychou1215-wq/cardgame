from pathlib import Path

from src.core.game import Game
from src.deck.loader import GameData
from src.effects.models import TargetRef


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig")


def make_repo(root: Path) -> None:
    write(root / "data/cards/cards.csv", """id,name,type,cost,faction_id,effect_text,rarity,transform_condition_type,transform_condition_target,transform_condition_value,transform_condition_text,durability
U001,Tester,unit,1,F001,,R,attack_count,self,1,attack once,
U002,Dummy,unit,1,F002,,R,total_damage_taken,self,1,take damage,
S001,Bolt,spell,1,F001,deal 2,R,,,,,
""")
    write(root / "data/cards/unit_sides.csv", """card_id,side,attack,max_health,keywords,effect_text
U001,front,2,3,,
U001,back,2,3,,flip +1 attack
U002,front,1,2,,
U002,back,1,2,,
""")
    write(root / "data/cards/effects.csv", """effect_id,card_id,side,sequence,activation_type,trigger,condition,target,target_count,target_filter,target_required,operation,value,parameter,duration,mana_cost,usage_limit_type,usage_limit_count,optional,failure_behavior,effect_text
E001,U001,back,1,triggered,on_flip,,self,1,,false,modify_attack,1,,permanent,0,,,false,continue,+1 attack
E002,S001,none,1,played,on_play,,opponent_unit,1,zone:battlefield;controller:opponent;type:unit,true,damage,2,,instant,0,,,false,continue,deal 2
""")
    write(root / "data/decks/decks.csv", """deck_id,name,faction_id,leader_id,deck_type,version,description
D001,A,F001,L001,test,0.1,
D002,B,F002,L002,test,0.1,
""")
    write(root / "data/decks/deck_cards.csv", """deck_id,card_id,quantity
D001,U001,5
D001,S001,5
D002,U002,10
""")
    write(root / "data/factions/leader.csv", """leader_id,name,faction_id,hp
L001,L1,F001,25
L002,L2,F002,25
""")


def test_combat_transform_and_effect(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=1)
    game.mulligan_hand([])
    game.mulligan_hand([])
    game.active_player_index = 0

    # Put deterministic units directly on board to isolate the engine mechanics.
    p1 = game.players[0]
    p2 = game.players[1]
    attacker = next(c for c in data.build_deck("D001") if c.card_id == "U001")
    defender = next(c for c in data.build_deck("D002") if c.card_id == "U002")
    attacker.owner_index = 0
    defender.owner_index = 1
    attacker.entered_turn = 0
    defender.entered_turn = 0
    p1.battlefield = [attacker]
    p2.battlefield = [defender]

    ok, _ = game.declare_attack(attacker.instance_id, TargetRef("unit", 1, defender.instance_id))
    assert ok
    ok, _ = game.resolve_combat()
    assert ok
    assert attacker.attacks_made == 1
    assert attacker.current_side == "back"
    assert attacker.attack == 3  # back base 2 + on_flip permanent +1
    assert defender not in p2.battlefield


def test_spell_effect_targeting(tmp_path: Path):
    make_repo(tmp_path)
    data = GameData(tmp_path)
    game = Game(data, "D001", "D002", seed=2)
    game.mulligan_hand([])
    game.mulligan_hand([])
    game.active_player_index = 0
    p1, p2 = game.players
    target = next(c for c in data.build_deck("D002") if c.card_id == "U002")
    target.owner_index = 1
    target.entered_turn = 0
    p2.battlefield = [target]

    # Force a Bolt into hand and enough mana.
    spell = next(c for c in data.build_deck("D001") if c.card_id == "S001")
    p1.hand = [spell]
    p1.mana = 10
    ref = TargetRef("unit", 1, target.instance_id)
    ok, _ = game.play_card(0, ref)
    assert ok
    assert target not in p2.battlefield
    assert spell in p1.graveyard
