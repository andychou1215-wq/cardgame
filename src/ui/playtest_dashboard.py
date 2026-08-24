from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.playtest.analytics import PlaytestAnalytics, load_playtest_directory


def render_cross_game_dashboard(analytics: PlaytestAnalytics) -> None:
    st.subheader("📈 Cross-Game Playtest Dashboard")
    overview = analytics.overview()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Games", int(overview["games"]))
    c2.metric("Avg Turns", f'{overview["avg_turns"]:.2f}')
    c3.metric("P1 Win Rate", f'{overview["p1_win_rate"]:.1%}')
    c4.metric("First Player Win Rate", f'{overview["first_player_win_rate"]:.1%}')

    if analytics.summaries.empty:
        st.info("尚未找到 game_summary CSV。")
        return

    st.markdown("#### Deck Results")
    deck = analytics.deck_results()
    if not deck.empty:
        display = deck.copy()
        display["win_rate"] = display["win_rate"].map(lambda x: f"{x:.1%}")
        display["avg_turns"] = display["avg_turns"].map(lambda x: f"{x:.2f}")
        st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("#### Game Length")
    turns = pd.to_numeric(analytics.summaries["turn_number"], errors="coerce").dropna()
    if not turns.empty:
        st.bar_chart(turns.value_counts().sort_index())

    st.markdown("#### Card Usage")
    cards = analytics.card_usage()
    if not cards.empty:
        st.dataframe(cards, use_container_width=True, hide_index=True)

    st.markdown("#### Event Distribution")
    dist = analytics.event_distribution()
    if not dist.empty:
        st.bar_chart(dist.set_index("event_type")["count"])


def render_repo_playtest_dashboard(repo_root: str | Path) -> None:
    repo_root = Path(repo_root)
    render_cross_game_dashboard(load_playtest_directory(repo_root / "playtest_data"))
