from __future__ import annotations

import streamlit as st


def playtest_data_panel(game) -> None:
    recorder = getattr(game, "telemetry", None)
    if recorder is None:
        return

    summary = recorder.summary(game)
    with st.expander("📊 Playtest Data", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Turn", summary.get("turn_number", 0))
        c2.metric("Cards Played", summary["cards_played"])
        c3.metric("Attacks", summary["attacks_declared"])
        c4.metric("Transforms", summary["transforms"])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Units Died", summary["units_died"])
        c2.metric("Healing", summary["healing_done"])
        c3.metric("Combat → Leader", summary["combat_damage_to_leader"])
        c4.metric("Effect Damage", summary["effect_damage"])

        st.caption(
            f"game_id={summary['game_id']} · events={summary['event_count']} · "
            f"state-based passes={summary['state_based_passes']}"
        )

        if recorder.events:
            st.dataframe(recorder.rows(), use_container_width=True, hide_index=True)

        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "下載 event_log.csv",
                recorder.events_csv_text().encode("utf-8-sig"),
                file_name=f"{summary['game_id']}_event_log.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with d2:
            st.download_button(
                "下載 game_summary.csv",
                recorder.summary_csv_text(game).encode("utf-8-sig"),
                file_name=f"{summary['game_id']}_game_summary.csv",
                mime="text/csv",
                use_container_width=True,
            )
