"""Deprecated compatibility launcher.

Use: py -m streamlit run apps/playtest_dashboard.py
"""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).parent / "apps/playtest_dashboard.py"), run_name="__main__")
