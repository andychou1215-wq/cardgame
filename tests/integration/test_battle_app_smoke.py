from pathlib import Path

from streamlit.testing.v1 import AppTest


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_battle_app_starts_with_repository_data():
    app = AppTest.from_file(str(REPO_ROOT / "apps" / "battle_app.py"))

    app.run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "🃏 卡牌對決 — Streamlit Prototype v5"
    assert len(app.selectbox) == 2
    assert len(app.selectbox[0].options) == 2
    assert app.selectbox[0].options[0].startswith("D001")
    assert app.selectbox[0].options[1].startswith("D002")
