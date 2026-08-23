from __future__ import annotations

from pathlib import Path
import streamlit as st

from src.core.game import Game
from src.deck.loader import DataError, GameData
from src.ui.components import (
    activated_controls,
    artifact_row,
    battlefield,
    combat_controls,
    hand,
    inject_css,
    pending_effect_choice,
    player_header,
    response_window,
    sidebar,
)


st.set_page_config(page_title="卡牌對決 Streamlit Prototype", page_icon="🃏", layout="wide")
inject_css()
REPO_ROOT = Path(__file__).resolve().parent


@st.cache_resource
def load_data() -> GameData:
    return GameData(REPO_ROOT)


def reset_game(deck1: str, deck2: str) -> None:
    st.session_state.game = Game(load_data(), deck1, deck2)
    st.session_state.pop("flash", None)


st.title("🃏 卡牌對決 — Streamlit Prototype v2")
st.caption("Combat + Transform + effects.csv Resolver：攻擊、Response Window、翻面、Spell/Artifact、Triggered/Activated effects。")

try:
    data = load_data()
except DataError as exc:
    st.error("無法載入 repo 資料。")
    st.code(str(exc))
    st.info("請把 Prototype 檔案放在 cardgame repo 根目錄，確保 data/cards、data/decks、data/factions 存在。")
    st.stop()

available = data.available_decks()
if len(available) < 2:
    st.error("至少需要兩副 decks.csv 牌組才能開始。")
    st.stop()

deck_ids = [d.deck_id for d in available]
deck_label = {d.deck_id: f"{d.deck_id} — {d.name} v{d.version}" for d in available}

with st.expander("新對局設定", expanded="game" not in st.session_state):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        d1 = st.selectbox("Player 1 Deck", deck_ids, index=0, format_func=lambda x: deck_label[x])
    with c2:
        d2 = st.selectbox("Player 2 Deck", deck_ids, index=1 if len(deck_ids) > 1 else 0, format_func=lambda x: deck_label[x])
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

if game.winner_index is not None:
    st.success(f"🏆 {game.players[game.winner_index].name} 獲勝！")

# Opponent view.
player_header(game.inactive_player, opponent=True)
battlefield(game.inactive_player, "opponent", game)
st.caption(f"對手手牌：{len(game.inactive_player.hand)} 張（Hot-seat 模式隱藏內容）")

st.divider()
player_header(game.active_player)
battlefield(game.active_player, "active", game)
artifact_row(game)

# Blocking resolution windows always take priority over new actions.
if game.pending_choice:
    pending_effect_choice(game)
elif game.pending_combat:
    response_window(game)
elif game.winner_index is None:
    hand(game)
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        combat_controls(game)
    with c2:
        activated_controls(game)
    st.divider()
    if st.button("結束回合 ➜", type="primary", use_container_width=True):
        ok, message = game.end_turn()
        if not ok:
            st.session_state["flash"] = ("error", message)
        st.rerun()

with st.expander("Prototype 規則假設 / 已知限制"):
    st.markdown(
        """
- 依 repo 規則：單位每回合最多攻擊 1 次，剛進場不能攻擊；Prototype 將 `迅擊` 視為可忽略進場限制。
- repo 尚未明確定義「單位攻擊單位」的傷害方向；v2 暫採 **雙方同時以攻擊力互相造成傷害**，方便 Playtest，之後可在 Combat 模組替換。
- `庇護` 目前能被 effect filter 辨識與賦予，但其完整戰鬥規則尚未在此版推定實作。
- Artifact durability 尚未消耗；目前先支援 Artifact 進場與 activated effect。
- `until_turn_end`、`until_attack_end`、`until_opponent_turn_end` 已支援效果到期。
        """
    )
