from __future__ import annotations

import html
import streamlit as st

from src.cards.models import CardInstance, UnitInstance
from src.core.game import Game, PlayerState


CARD_CSS = """
<style>
.card-box {border:1px solid #555; border-radius:12px; padding:10px; min-height:150px; margin-bottom:8px;}
.card-name {font-weight:700; font-size:1.05rem;}
.card-meta {opacity:.75; font-size:.86rem;}
.stat-line {font-weight:650; margin-top:7px;}
.board-label {font-weight:700; margin:8px 0 4px;}
</style>
"""


def inject_css() -> None:
    st.markdown(CARD_CSS, unsafe_allow_html=True)


def card_html(card: CardInstance, *, hide_details: bool = False) -> str:
    if hide_details:
        return '<div class="card-box"><div class="card-name">🂠 手牌</div><div class="card-meta">Hidden</div></div>'
    d = card.definition
    details = f"{html.escape(d.card_type)} · {d.cost} Mana"
    stats = ""
    text = d.effect_text
    if isinstance(card, UnitInstance):
        stats = f'<div class="stat-line">⚔ {card.attack} &nbsp; ♥ {card.current_health}/{card.max_health}</div>'
        kw = " · ".join(card.keywords)
        if kw:
            text = f"{kw}<br>{text}"
    return (
        '<div class="card-box">'
        f'<div class="card-name">{html.escape(card.card_id)} · {html.escape(card.name)}</div>'
        f'<div class="card-meta">{html.escape(details)}</div>{stats}'
        f'<div>{html.escape(text) if "<br>" not in text else text}</div>'
        '</div>'
    )


def player_header(player: PlayerState, *, opponent: bool = False) -> None:
    title = "對手" if opponent else "目前玩家"
    st.markdown(f"### {title} — {player.name}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Leader", player.leader.name)
    c2.metric("HP", f"{player.leader_health}/{player.leader.max_health}")
    c3.metric("Mana", f"{player.mana}/{player.max_mana}")
    c4.metric("Deck / Hand", f"{len(player.deck)} / {len(player.hand)}")


def battlefield(player: PlayerState, prefix: str) -> None:
    st.markdown('<div class="board-label">戰場</div>', unsafe_allow_html=True)
    slots = max(5, len(player.battlefield))
    cols = st.columns(slots)
    for i, col in enumerate(cols):
        with col:
            if i < len(player.battlefield):
                st.markdown(card_html(player.battlefield[i]), unsafe_allow_html=True)
            else:
                st.markdown('<div class="card-box"><div class="card-meta">Empty</div></div>', unsafe_allow_html=True)


def hand(game: Game) -> None:
    player = game.active_player
    st.markdown("### 手牌")
    if not player.hand:
        st.info("目前沒有手牌。")
        return
    cols = st.columns(min(5, len(player.hand)))
    for idx, card in enumerate(player.hand):
        col = cols[idx % len(cols)]
        with col:
            st.markdown(card_html(card), unsafe_allow_html=True)
            disabled = card.card_type != "unit" or card.cost > player.mana
            if st.button("出牌", key=f"play_{card.instance_id}", disabled=disabled, use_container_width=True):
                ok, message = game.play_card(idx)
                st.session_state["flash"] = ("success" if ok else "error", message)
                st.rerun()


def sidebar(game: Game) -> None:
    with st.sidebar:
        st.header("Game Log")
        st.caption(f"Round {game.turn_number} · {game.active_player.name} 回合")
        st.divider()
        for line in reversed(game.log_entries[-30:]):
            st.write(line)
