from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def test_streamlit_app_runs():
    assert APP_PATH.is_file(), f"Streamlit app not found: {APP_PATH}"

    app = AppTest.from_file(str(APP_PATH))
    app.run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "🌊 HydroLens"