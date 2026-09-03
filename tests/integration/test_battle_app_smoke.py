from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.playtest.simulation import decision_player_index


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_battle_app_starts_with_repository_data():
    app = AppTest.from_file(str(REPO_ROOT / "apps" / "battle_app.py"))

    app.run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "🃏 卡牌對決 — Streamlit Prototype v6"
    assert len(app.radio) == 1
    assert app.radio[0].options == ["雙人 Hot-seat", "玩家 vs Heuristic AI"]
    assert len(app.selectbox) == 2
    assert len(app.selectbox[0].options) == 2
    assert app.selectbox[0].options[0].startswith("D001")
    assert app.selectbox[0].options[1].startswith("D002")


def test_battle_app_ai_mode_mulligan_yields_to_player_and_shows_questionnaire():
    app = AppTest.from_file(str(REPO_ROOT / "apps" / "battle_app.py"))
    app.run(timeout=10)

    app.radio[0].set_value(app.radio[0].options[1]).run(timeout=10)
    assert [box.label for box in app.selectbox[:2]] == ["玩家牌組", "AI 牌組"]

    next(button for button in app.button if button.label == "開始 / 重開").click().run(
        timeout=10
    )
    next(button for button in app.button if button.key == "confirm_mulligan_0").click().run(
        timeout=10
    )

    game = app.session_state["game"]
    assert not app.exception
    assert game.game_started
    assert game.mulligan_done == [True, True]
    assert [player.name for player in game.players] == ["玩家", "Heuristic AI"]
    assert decision_player_index(game) == 0

    game.winner_index = 0
    app.run(timeout=10)

    assert not app.exception
    assert len(app.slider) == 7
    assert app.text_area[0].label == "補充觀察（選填）"
