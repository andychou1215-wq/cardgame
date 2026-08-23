from __future__ import annotations

from pathlib import Path
import streamlit as st

from src.core.game import Game
from src.deck.loader import DataError, GameData
from src.ui.components import battlefield, hand, inject_css, player_header, sidebar


st.set_page_config(page_title="卡牌對決 Streamlit Prototype", page_icon="🃏", layout="wide")
inject_css()

REPO_ROOT = Path(__file__).resolve().parent


@st.cache_resource
def load_data() -> GameData:
    return GameData(REPO_ROOT)


def reset_game(deck1: str, deck2: str) -> None:
    st.session_state.game = Game(load_data(), deck1, deck2)
    st.session_state.pop("flash", None)


st.title("🃏 卡牌對決 — Streamlit Prototype")
st.caption("MVP：載入測試牌組、洗牌、起手、Mana、Unit 出牌、Hot-seat End Turn。")

try:
    data = load_data()
except DataError as exc:
    st.error("無法載入 repo 資料。")
    st.code(str(exc))
    st.info("請把此 Prototype 的檔案放在 cardgame repo 根目錄，確保 data/cards、data/decks、data/factions 存在。")
    st.stop()

available = data.available_decks()
if len(available) < 2:
    st.error("至少需要兩副 decks.csv 牌組才能開始。")
    st.stop()

deck_ids = [d.deck_id for d in available]
deck_label = {d.deck_id: f"{d.deck_id} — {d.name}" for d in available}

with st.expander("新對局設定", expanded="game" not in st.session_state):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        d1 = st.selectbox("Player 1 Deck", deck_ids, index=0, format_func=lambda x: deck_label[x])
    with c2:
        default2 = 1 if len(deck_ids) > 1 else 0
        d2 = st.selectbox("Player 2 Deck", deck_ids, index=default2, format_func=lambda x: deck_label[x])
    with c3:
        st.write("")
        st.write("")
        if st.button("開始 / 重開", type="primary", use_container_width=True):
            reset_game(d1, d2)
            st.rerun()

if "game" not in st.session_state:
    reset_game(deck_ids[0], deck_ids[1])

game: Game = st.session_state.game
sidebar(game)

flash = st.session_state.pop("flash", None)
if flash:
    kind, message = flash
    getattr(st, kind)(message)

# Opponent hand intentionally hidden in hot-seat mode.
player_header(game.inactive_player, opponent=True)
battlefield(game.inactive_player, "opponent")
st.caption(f"對手手牌：{len(game.inactive_player.hand)} 張（Hot-seat 模式隱藏內容）")

st.divider()

player_header(game.active_player)
battlefield(game.active_player, "active")
hand(game)

st.divider()
left, right = st.columns([4, 1])
with left:
    st.info("目前 MVP 僅允許 Unit 出牌；Spell / Artifact / Response、攻擊、翻面與 effects.csv 結算會在下一階段加入。")
with right:
    if st.button("結束回合 ➜", type="primary", use_container_width=True):
        game.end_turn()
        st.rerun()
