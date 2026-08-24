import pandas as pd
from src.playtest.advanced_analytics import matchup_matrix, card_performance

def test_matchup_matrix():
    s=pd.DataFrame([
        {"game_id":"g1","winner_index":0,"deck_id_p1":"A","deck_id_p2":"B"},
        {"game_id":"g2","winner_index":1,"deck_id_p1":"A","deck_id_p2":"B"},
    ])
    r=matchup_matrix(s).set_index(["deck","opponent"])
    assert r.loc[("A","B"),"wins"]==1
    assert r.loc[("B","A"),"wins"]==1

def test_card_performance():
    s=pd.DataFrame([{"game_id":"g1","winner_index":0},{"game_id":"g2","winner_index":1}])
    e=pd.DataFrame([
        {"game_id":"g1","event_type":"card_played","card_id":"U1","player_index":0},
        {"game_id":"g2","event_type":"card_played","card_id":"U1","player_index":0},
    ])
    r=card_performance(e,s).set_index("card_id")
    assert r.loc["U1","win_rate_when_played"]==0.5
