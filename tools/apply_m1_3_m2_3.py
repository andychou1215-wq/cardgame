from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/"src/core/game.py"

def fail(msg):
    print("[ERROR]",msg); sys.exit(1)

def main():
    if not GAME.exists(): fail("src/core/game.py not found")
    text=GAME.read_text(encoding="utf-8")

    if "from src.core.stack import StackItem, validate_target_ref" not in text:
        anchor="from src.core.priority import PriorityWindow\n"
        if anchor not in text: fail("M1.2 PriorityWindow import not found")
        text=text.replace(anchor, anchor+"from src.core.stack import StackItem, validate_target_ref\nfrom src.core.response_rules import response_triggers_for_window\n",1)

    # Generic response trigger discovery
    start=text.find("    def available_responses(")
    end=text.find("    def play_response(",start)
    if start<0 or end<0: fail("response methods not found")
    if "response_triggers_for_window" not in text[start:end]:
        method="""    def available_responses(self, player_index: int | None = None):
        combat=self.pending_combat
        window=self.priority_window
        if combat is None or window is None or not window.is_open:
            return []
        if player_index is None:
            player_index=window.current_player_index
        if player_index != window.current_player_index:
            return []
        player=self.players[player_index]
        result=[]
        seen=set()
        for idx,card in enumerate(player.hand):
            if player.mana < card.cost:
                continue
            for trigger in response_triggers_for_window(window.reason):
                effects=self.data.response_effects_for(card.card_id, trigger)
                if not effects:
                    continue
                if trigger=="ally_becomes_attack_target":
                    if not (combat.defender.kind=="unit" and combat.defender.player_index==player_index):
                        continue
                for effect in effects:
                    key=(idx,getattr(effect,"effect_id",id(effect)))
                    if key not in seen:
                        seen.add(key); result.append((idx,card,effect))
        return result

"""
        text=text[:start]+method+text[end:]

    # StackItem
    old="""        bundle = [
            QueuedEffect(effect, card.instance_id, player_index, trigger_target=combat.defender)
            for effect in effects
        ]
        window.add_response(player_index, bundle)
"""
    new="""        trigger = getattr(effects[0], "trigger", "priority") if effects else "priority"
        stack_item = StackItem(
            source_id=card.instance_id,
            card_id=card.card_id,
            controller_index=player_index,
            effects=list(effects),
            trigger=trigger,
            trigger_target=combat.defender,
        )
        window.add_response(player_index, stack_item)
"""
    if old in text: text=text.replace(old,new,1)

    # Fizzle-aware resolver
    start=text.find("    def _resolve_response_stack(self) -> None:")
    end=text.find("    def priority_player_index(",start)
    if start<0 or end<0: fail("stack resolver not found")
    resolver="""    def _resolve_response_stack(self) -> None:
        window=self.priority_window
        if window is None:
            return
        for item in window.drain_lifo():
            validation=validate_target_ref(self,item.trigger_target)
            if not validation.valid:
                item.mark_fizzled(validation.reason)
                self.log(f"Response {item.card_id} 結算失敗（fizzle）：{validation.reason}。")
                if hasattr(self,"telemetry"):
                    self.telemetry.record("response_fizzled",turn=self.turn_number,active_player=self.active_player_index,player_index=item.controller_index,card_id=item.card_id,source_id=item.source_id,target=item.trigger_target,metadata={"reason":validation.reason,"trigger":item.trigger})
                continue
            for effect in item.effects:
                self.effect_queue.append(QueuedEffect(effect,item.source_id,item.controller_index,trigger_target=item.trigger_target))
            self.process_effect_queue()
            item.mark_resolved()
            if hasattr(self,"telemetry"):
                self.telemetry.record("response_resolved",turn=self.turn_number,active_player=self.active_player_index,player_index=item.controller_index,card_id=item.card_id,source_id=item.source_id,target=item.trigger_target,metadata={"trigger":item.trigger})
            if self.winner_index is not None:
                break
        if hasattr(self,"_run_state_based_check") and self.winner_index is None:
            self._run_state_based_check()

"""
    text=text[:start]+resolver+text[end:]

    # card_drawn telemetry if deckout helper exists
    old_draw="""            player.hand.append(player.deck.pop())
            drawn += 1
"""
    if '"card_drawn"' not in text and old_draw in text:
        new_draw="""            drawn_card = player.deck.pop()
            player.hand.append(drawn_card)
            drawn += 1
            if hasattr(self, "telemetry"):
                self.telemetry.record(
                    "card_drawn",
                    turn=self.turn_number,
                    active_player=self.active_player_index,
                    player_index=player_index,
                    card_id=drawn_card.card_id,
                    source_id=drawn_card.instance_id,
                    amount=1,
                    metadata={"reason": reason},
                )
"""
        text=text.replace(old_draw,new_draw,1)

    GAME.write_text(text,encoding="utf-8")
    print("M1.3 + M2.3 core patch applied.")
    print("Run: py -m pytest -q")

if __name__=="__main__":
    main()
