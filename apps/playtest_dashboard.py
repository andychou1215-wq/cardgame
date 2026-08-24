from pathlib import Path

import pandas as pd
import streamlit as st

from src.playtest.analytics import PlaytestAnalytics, load_playtest_directory
from src.ui.playtest_dashboard import render_cross_game_dashboard
from src.ui.advanced_playtest_panel import render_m2_4_dashboard


st.set_page_config(page_title="Card Game Playtest Dashboard", page_icon="📈", layout="wide")
st.title("📈 卡牌對決 — M2.2 Playtest Dashboard")

ROOT = Path(__file__).resolve().parent
LOCAL_DIR = ROOT / "playtest_data"

source = st.radio("資料來源", ["repo/playtest_data", "上傳 CSV"], horizontal=True)

if source == "repo/playtest_data":
    render_cross_game_dashboard(load_playtest_directory(LOCAL_DIR))
    st.caption(f"讀取資料夾：{LOCAL_DIR}")
else:
    summaries = st.file_uploader(
        "上傳 game_summary CSV（可多選）",
        type="csv",
        accept_multiple_files=True,
        key="summary_uploads",
    )
    events = st.file_uploader(
        "上傳 event_log CSV（可多選）",
        type="csv",
        accept_multiple_files=True,
        key="event_uploads",
    )

    summary_frames = [pd.read_csv(f) for f in summaries]
    event_frames = [pd.read_csv(f) for f in events]
    analytics = PlaytestAnalytics(
        pd.concat(summary_frames, ignore_index=True) if summary_frames else pd.DataFrame(),
        pd.concat(event_frames, ignore_index=True) if event_frames else pd.DataFrame(),
    )
    render_cross_game_dashboard(analytics)

try:
    render_m2_4_dashboard(analytics)
except NameError:
    pass
