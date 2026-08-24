import streamlit as st
from src.playtest.advanced_analytics import matchup_matrix, card_performance
from src.playtest.version_compare import version_summary, balance_report_csv

def render_m2_4_dashboard(analytics) -> None:
    st.subheader("M2.4 Balance Comparison")

    versions = version_summary(analytics.summaries)
    if not versions.empty:
        display = versions.copy()
        display["p1_win_rate"] = display["p1_win_rate"].map(lambda x: f"{x:.1%}")
        display["first_player_win_rate"] = display["first_player_win_rate"].map(lambda x: f"{x:.1%}")
        st.dataframe(display, use_container_width=True, hide_index=True)

    matchups = matchup_matrix(analytics.summaries)
    cards = card_performance(analytics.events, analytics.summaries)
    report = balance_report_csv(analytics.summaries, matchups, cards)

    st.download_button(
        "下載 Balance Report",
        report.encode("utf-8-sig"),
        file_name="balance_report.csv",
        mime="text/csv",
        use_container_width=True,
    )
