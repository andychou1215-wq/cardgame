from __future__ import annotations

import html
import streamlit as st

from src.cards.models import CardInstance, UnitInstance
from src.core.game import Game, PlayerState
from src.effects.models import TargetRef


CARD_CSS = """
<style>
.card-box {border:1px solid #555; border-radius:12px; padding:10px; min-height:155px; margin-bottom:8px;}
.card-name {font-weight:700; font-size:1.05rem;}
.card-meta {opacity:.75; font-size:.86rem;}
.stat-line {font-weight:650; margin-top:7px;}
.board-label {font-weight:700; margin:8px 0 4px;}
.back-side {border-style:dashed;}
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
    klass = "card-box"
    if isinstance(card, UnitInstance):
        klass += " back-side" if card.current_side == "back" else ""
        stats = f'<div class="stat-line">⚔ {card.attack} &nbsp; ♥ {card.current_health}/{card.max_health} · {card.current_side}</div>'
        kw = " · ".join(card.keywords)
        side_text = card.side_definition.effect_text
        pieces = [p for p in [kw, side_text, text] if p]
        text = "<br>".join(html.escape(p) for p in pieces)
    else:
        text = html.escape(text)
    return (
        f'<div class="{klass}">'
        f'<div class="card-name">{html.escape(card.card_id)} · {html.escape(card.name)}</div>'
        f'<div class="card-meta">{details}</div>{stats}'
        f'<div>{text}</div>'
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


def battlefield(player: PlayerState, prefix: str, game: Game | None = None) -> None:
    st.markdown('<div class="board-label">戰場</div>', unsafe_allow_html=True)
    slots = max(5, len(player.battlefield))
    cols = st.columns(slots)
    for i, col in enumerate(cols):
        with col:
            if i < len(player.battlefield):
                unit = player.battlefield[i]
                st.markdown(card_html(unit), unsafe_allow_html=True)
                if game is not None and player is game.active_player and unit.can_attack(game.turn_number):
                    st.caption("✓ 可攻擊")
            else:
                st.markdown('<div class="card-box"><div class="card-meta">Empty</div></div>', unsafe_allow_html=True)


def _target_label(game: Game, ref: TargetRef) -> str:
    return game.describe_target(ref)


def hand(game: Game) -> None:
    player = game.active_player
    st.markdown("### 手牌")
    if not player.hand:
        st.info("目前沒有手牌。")
        return
    cols = st.columns(min(5, len(player.hand)))
    for idx, card in enumerate(list(player.hand)):
        col = cols[idx % len(cols)]
        with col:
            st.markdown(card_html(card), unsafe_allow_html=True)
            if card.card_type == "response":
                st.caption("Response：只能在攻擊回應視窗使用")
                continue
            targets = game.legal_play_targets(idx)
            selected = None
            if targets:
                selected = st.selectbox(
                    "目標",
                    targets,
                    format_func=lambda r: _target_label(game, r),
                    key=f"play_target_{card.instance_id}",
                )
            disabled = card.cost > player.mana or (card.card_type == "unit" and len(player.battlefield) >= 5)
            if st.button("出牌", key=f"play_{card.instance_id}", disabled=disabled, use_container_width=True):
                ok, message = game.play_card(idx, selected)
                st.session_state["flash"] = ("success" if ok else "error", message)
                st.rerun()


def combat_controls(game: Game) -> None:
    st.markdown("### ⚔ Combat")
    attackers = game.legal_attackers()
    if not attackers:
        st.caption("目前沒有可攻擊的單位。")
        return
    attacker = st.selectbox(
        "攻擊者",
        attackers,
        format_func=lambda u: f"{u.card_id} {u.name} · {u.attack} ATK",
        key="combat_attacker",
    )
    targets = game.legal_attack_targets()
    target = st.selectbox("攻擊目標", targets, format_func=lambda r: _target_label(game, r), key="combat_target")
    if st.button("宣告攻擊", type="primary", use_container_width=True):
        ok, message = game.declare_attack(attacker.instance_id, target)
        st.session_state["flash"] = ("success" if ok else "error", message)
        st.rerun()


def activated_controls(game: Game) -> None:
    options = game.activated_options()
    st.markdown("### ✦ Activated Abilities")
    if not options:
        st.caption("目前沒有可啟動的能力。")
        return
    for card, effect in options:
        with st.expander(f"{card.card_id} {card.name} — {effect.effect_text}"):
            st.caption(f"額外魔力：{effect.mana_cost} · {effect.usage_limit_type or '無次數限制'}")
            targets = game.legal_activation_targets(card, effect)
            selected = None
            if targets:
                selected = st.selectbox(
                    "目標",
                    targets,
                    format_func=lambda r: _target_label(game, r),
                    key=f"activate_target_{card.instance_id}_{effect.effect_id}",
                )
            if st.button("啟動", key=f"activate_{card.instance_id}_{effect.effect_id}"):
                ok, message = game.activate(card.instance_id, effect.effect_id, selected)
                st.session_state["flash"] = ("success" if ok else "error", message)
                st.rerun()


def artifact_row(game: Game, player: PlayerState | None = None) -> None:
    player = player or game.active_player
    if not player.artifacts:
        return
    st.markdown("### Artifacts")
    cols = st.columns(min(4, len(player.artifacts)))
    for i, card in enumerate(player.artifacts):
        with cols[i % len(cols)]:
            st.markdown(card_html(card), unsafe_allow_html=True)


def pending_effect_choice(game: Game) -> None:
    pending = game.pending_choice
    if pending is None:
        return
    st.warning(f"效果等待選擇：{pending.prompt}")
    selected = st.selectbox(
        "合法目標",
        pending.candidates,
        format_func=lambda r: _target_label(game, r),
        key=f"pending_effect_{pending.queued.effect.effect_id}",
    )
    if st.button("確認效果目標", type="primary"):
        ok, message = game.resolve_pending_choice(selected)
        st.session_state["flash"] = ("success" if ok else "error", message)
        st.rerun()


def response_window(game: Game) -> None:
    combat = game.pending_combat
    if combat is None:
        return

    attacker = game.find_unit(combat.attacker_id)
    st.warning(
        f"Response / Priority Window："
        f"{attacker.card_id if attacker else '?'} 攻擊 "
        f"{game.describe_target(combat.defender)}"
    )

    window = getattr(game, "priority_window", None)
    if window is None:
        st.error("Priority Window 尚未初始化。")
        return

    if window.is_open:
        pidx = window.current_player_index
        player = game.players[pidx]
        st.info(
            f"目前 Priority：{player.name} · "
            f"Stack {window.stack_size} · "
            f"連續 Pass {window.consecutive_passes}/2"
        )

        responses = game.available_responses(pidx)
        if responses:
            st.write(f"{player.name} 可以使用：")
            cols = st.columns(min(3, len(responses)))
            for n, (hand_idx, card, effect) in enumerate(responses):
                with cols[n % len(cols)]:
                    st.markdown(card_html(card), unsafe_allow_html=True)
                    if st.button(
                        "加入 Response Stack",
                        key=f"response_{pidx}_{card.instance_id}",
                    ):
                        ok, message = game.play_response(hand_idx, pidx)
                        st.session_state["flash"] = ("success" if ok else "error", message)
                        st.rerun()
        else:
            st.caption(f"{player.name} 目前沒有合法 Response。")

        if st.button(
            f"{player.name} — Pass Priority",
            type="primary",
            use_container_width=True,
        ):
            ok, message = game.pass_priority()
            st.session_state["flash"] = ("success" if ok else "error", message)
            st.rerun()
        return

    st.success("雙方已連續 Pass；Response Stack 已結算。")
    if st.button("進入戰鬥結算", type="primary", use_container_width=True):
        ok, message = game.resolve_combat()
        st.session_state["flash"] = ("success" if ok else "error", message)
        st.rerun()

def sidebar(game: Game) -> None:
    with st.sidebar:
        st.header("Game Log")
        st.caption(f"Round {game.turn_number} · {game.active_player.name} 回合")
        st.divider()
        for line in reversed(game.log_entries[-40:]):
            st.write(line)


def mulligan_panel(game: Game, *, hot_seat: bool = True) -> None:
    """Hot-seat Mulligan: each player may replace any number of opening cards once."""
    pidx = game.mulligan_player_index
    player = game.players[pidx]
    st.info(
        f"Mulligan — {player.name}: 可選擇任意張起手牌退回牌組，洗牌後抽回等量。每位玩家僅一次。"
    )
    if hot_seat:
        st.caption("Hot-seat：請只讓目前玩家查看此區域，完成後將裝置交給下一位玩家。")
    else:
        st.caption("AI 會自動保留起手牌；你確認 Mulligan 後將立即開始對局。")
    choices = st.multiselect(
        "選擇要更換的卡（可不選，直接保留全部）",
        options=player.hand,
        format_func=lambda c: f"{c.card_id} {c.name} · {c.card_type} · Cost {c.cost}",
        key=f"mulligan_choices_{pidx}",
    )
    cols = st.columns(min(5, max(1, len(player.hand))))
    for i, card in enumerate(player.hand):
        with cols[i % len(cols)]:
            st.markdown(card_html(card), unsafe_allow_html=True)
    if st.button(
        f"確認 {player.name} Mulligan（更換 {len(choices)} 張）",
        type="primary",
        use_container_width=True,
        key=f"confirm_mulligan_{pidx}",
    ):
        ok, message = game.mulligan_hand([c.instance_id for c in choices])
        st.session_state["flash"] = ("success" if ok else "error", message)
        st.rerun()
