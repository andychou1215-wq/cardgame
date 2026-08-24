from types import SimpleNamespace
from src.playtest.persistence import PlaytestStore

class R:
    def summary(self,g): return {"game_id":"g1","seed":42,"winner_index":0,"turn_number":8,"deck_id_p1":"D1","deck_id_p2":"D2"}
    def rows(self): return [{"game_id":"g1","seq":1,"event_type":"card_played","turn":1,"active_player":0,"player_index":0,"card_id":"U1","source_id":"x","target_kind":"","target_player_index":"","target_instance_id":"","amount":"","metadata":"{}"}]

def test_store(tmp_path):
    s=PlaytestStore(tmp_path/"playtest_data")
    out=s.save_game(R(),SimpleNamespace())
    assert (tmp_path/"playtest_data/summaries/game_summary.csv").exists()
    assert (tmp_path/f"playtest_data/replays/{out['game_id']}.json").exists()
