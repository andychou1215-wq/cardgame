from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.playtest.fun_feedback import (
    FunFeedback,
    append_fun_feedback,
    card_exposure,
)


def fun_questionnaire(game, human_player_index: int, output_path: str | Path) -> None:
    if game.winner_index is None:
        return

    game_id = game.telemetry.game_id
    submitted_key = f"fun_feedback_submitted_{game_id}"
    if st.session_state.get(submitted_key, False):
        st.success("這局的好玩度問卷已保存，謝謝你的判斷。")
        return

    human = game.players[human_player_index]
    ai = game.players[1 - human_player_index]
    exposure = card_exposure(game, human_player_index, "U011")

    st.divider()
    st.markdown("## 🎯 局後好玩度問卷")
    st.caption(
        "1 分代表非常差，5 分代表非常好。請依實際遊玩感受評分，不必配合勝負。"
    )
    st.caption(
        f"本局 U011：抽到 {exposure['drawn']} 次、打出 {exposure['played']} 次、"
        f"翻面 {exposure['transformed']} 次。"
    )

    with st.form(f"fun_feedback_form_{game_id}"):
        decision_depth = st.slider("每回合是否有值得思考的選擇？", 1, 5, 3)
        u011_playability = st.slider("U011 的 8 費手感是否合理、不會過度卡手？", 1, 5, 3)
        u011_payoff = st.slider("成功打出 U011 後，回報是否值得等待？", 1, 5, 3)
        shelter_clarity = st.slider("暫時【庇護】是否清楚且有戰術價值？", 1, 5, 3)
        fairness = st.slider("本局勝負是否感覺公平？", 1, 5, 3)
        replay_desire = st.slider("你是否想立刻再玩一局？", 1, 5, 3)
        overall_fun = st.slider("整體好玩程度", 1, 5, 3)
        notes = st.text_area(
            "補充觀察（選填）",
            placeholder="例如：U011 卡手的回合、最有趣或最挫折的決策。",
        )
        submitted = st.form_submit_button(
            "保存這局評分",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    feedback = FunFeedback(
        game_id=game_id,
        human_player_index=human_player_index,
        human_deck=human.deck_id,
        ai_deck=ai.deck_id,
        winner_index=game.winner_index,
        first_player_index=game.first_player_index,
        turn_number=game.turn_number,
        human_won=game.winner_index == human_player_index,
        decision_depth=decision_depth,
        u011_playability=u011_playability,
        u011_payoff=u011_payoff,
        shelter_clarity=shelter_clarity,
        fairness=fairness,
        replay_desire=replay_desire,
        overall_fun=overall_fun,
        u011_drawn=exposure["drawn"],
        u011_played=exposure["played"],
        u011_transformed=exposure["transformed"],
        notes=notes.strip(),
    )
    try:
        saved_path = append_fun_feedback(output_path, feedback)
    except (OSError, ValueError) as exc:
        st.error(f"問卷保存失敗：{exc}")
        return

    st.session_state[submitted_key] = True
    st.success(f"問卷已保存：{saved_path}")

