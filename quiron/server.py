from pathlib import Path

import dash

from quiron.data.loader import cargar_cirugia_plastica
from quiron.data.metrics import conteo_por_naturaleza, conteo_por_servicio, resumen_general
from quiron.layout import build_layout

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


def create_app():
    tabla = cargar_cirugia_plastica()

    resumen = resumen_general(tabla)
    por_servicio = conteo_por_servicio(tabla)
    por_naturaleza = conteo_por_naturaleza(tabla)

    app = dash.Dash(
        __name__,
        title="Quirón · Oferta Quirúrgica Bogotá",
        assets_folder=str(ASSETS_DIR),
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
            {"name": "theme-color", "content": "#330968"},
        ],
    )
    app.layout = build_layout(resumen, por_servicio, por_naturaleza)
    return app