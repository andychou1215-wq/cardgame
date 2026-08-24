import pandas as pd

def version_summary(summaries: pd.DataFrame) -> pd.DataFrame:
    cols = ["version", "games", "avg_turns", "p1_win_rate", "first_player_win_rate"]
    if summaries.empty:
        return pd.DataFrame(columns=cols)

    s = summaries.copy()
    source = "rules_version" if "rules_version" in s.columns else (
        "commit_hash" if "commit_hash" in s.columns else None
    )
    s["version"] = (
        s[source].fillna("").replace("", "unknown") if source else "unknown"
    )

    rows = []
    for version, g in s.groupby("version"):
        winner = pd.to_numeric(g["winner_index"], errors="coerce")
        turns = pd.to_numeric(g["turn_number"], errors="coerce")
        fp_rate = 0.0
        if "first_player_index" in g.columns:
            first = pd.to_numeric(g["first_player_index"], errors="coerce")
            valid = winner.notna() & first.notna()
            if valid.any():
                fp_rate = float((winner[valid] == first[valid]).mean())
        rows.append({
            "version": version,
            "games": len(g),
            "avg_turns": float(turns.mean()) if turns.notna().any() else 0.0,
            "p1_win_rate": float((winner == 0).mean()),
            "first_player_win_rate": fp_rate,
        })
    return pd.DataFrame(rows, columns=cols)

def balance_report_csv(summaries, matchup, card_perf) -> str:
    return "\n".join([
        "# VERSION SUMMARY\n" + version_summary(summaries).to_csv(index=False),
        "# MATCHUPS\n" + matchup.to_csv(index=False),
        "# CARD PERFORMANCE\n" + card_perf.to_csv(index=False),
    ])
