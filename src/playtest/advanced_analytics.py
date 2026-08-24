import pandas as pd

def matchup_matrix(summaries: pd.DataFrame) -> pd.DataFrame:
    cols = ["deck","opponent","games","wins","win_rate"]
    if summaries.empty: return pd.DataFrame(columns=cols)
    rows=[]
    for _, g in summaries.iterrows():
        try: winner=int(g["winner_index"])
        except Exception: winner=None
        d1=str(g.get("deck_id_p1","") or "")
        d2=str(g.get("deck_id_p2","") or "")
        if d1 and d2 and d1!="nan" and d2!="nan":
            rows += [
                {"deck":d1,"opponent":d2,"win":int(winner==0)},
                {"deck":d2,"opponent":d1,"win":int(winner==1)},
            ]
    if not rows: return pd.DataFrame(columns=cols)
    df=pd.DataFrame(rows)
    out=df.groupby(["deck","opponent"]).agg(games=("win","size"),wins=("win","sum")).reset_index()
    out["win_rate"]=out["wins"]/out["games"]
    return out[cols]

def matchup_pivot(summaries: pd.DataFrame) -> pd.DataFrame:
    flat=matchup_matrix(summaries)
    return pd.DataFrame() if flat.empty else flat.pivot(index="deck", columns="opponent", values="win_rate")

def card_performance(events: pd.DataFrame, summaries: pd.DataFrame) -> pd.DataFrame:
    cols=["card_id","games_drawn","games_played","draw_events","play_events","response_events","transform_events","win_rate_when_played","play_given_draw_rate"]
    if events.empty or "card_id" not in events.columns: return pd.DataFrame(columns=cols)
    winners={}
    if not summaries.empty and {"game_id","winner_index"}.issubset(summaries.columns):
        for _,r in summaries.iterrows():
            try:winners[str(r["game_id"])]=int(r["winner_index"])
            except Exception:pass
    e=events.copy(); e["card_id"]=e["card_id"].fillna("").astype(str); e=e[e["card_id"]!=""]
    rows=[]
    for cid,g in e.groupby("card_id"):
        dr=g[g["event_type"].isin(["draw_card","card_drawn"])]
        pl=g[g["event_type"]=="card_played"]
        rp=g[g["event_type"]=="response_played"]
        tr=g[g["event_type"]=="transform"]
        dg=set(dr["game_id"].astype(str)); pg=set(pl["game_id"].astype(str))
        wins=[]
        for _,ev in pl.drop_duplicates("game_id").iterrows():
            try:
                if str(ev["game_id"]) in winners: wins.append(int(winners[str(ev["game_id"])]==int(ev["player_index"])))
            except Exception: pass
        rows.append({
            "card_id":cid,"games_drawn":len(dg),"games_played":len(pg),
            "draw_events":len(dr),"play_events":len(pl),"response_events":len(rp),"transform_events":len(tr),
            "win_rate_when_played":sum(wins)/len(wins) if wins else None,
            "play_given_draw_rate":len(pg & dg)/len(dg) if dg else None,
        })
    return pd.DataFrame(rows, columns=cols).sort_values(["games_played","play_events"], ascending=False)
