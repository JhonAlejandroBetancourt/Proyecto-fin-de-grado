from pathlib import Path

import dash

from quiron.layout import build_layout

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


def create_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        title="Quirón · Oferta Quirúrgica Bogotá",
        assets_folder=str(ASSETS_DIR),
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
            {"name": "theme-color", "content": "#330968"},
        ],
    )
    app.layout = build_layout()
    return app