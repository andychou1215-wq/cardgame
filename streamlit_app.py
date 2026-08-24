"""Deprecated compatibility launcher.

Use: py -m streamlit run apps/battle_app.py
"""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).parent / "apps/battle_app.py"), run_name="__main__")
