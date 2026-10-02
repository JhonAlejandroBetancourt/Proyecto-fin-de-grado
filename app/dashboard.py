"""
dashboard.py
------------------------------------------------------------------------------
Punto de entrada de la capa de PRESENTACIÓN. Ensambla layout + callbacks +
conexión a la base de datos, y expone `main()` para levantar el servidor Dash.

CORRECCIÓN (rama feature/branding-ucompensar-ui):
  Dash resuelve `assets_folder` de forma relativa al directorio del MÓDULO
  donde se instancia `Dash(__name__)`. Como este archivo vive en `app/`, sin
  especificar `assets_folder` explícitamente Dash buscaba `app/assets/`
  (inexistente) en lugar de `<raíz-del-proyecto>/assets/`, por lo que el CSS
  nunca se servía y la app se veía como texto plano. Se corrige apuntando
  `assets_folder` a la ruta absoluta de la carpeta `assets/` en la raíz.

Uso:
    python main.py app
    # o directamente:
    python -m app.dashboard
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import dash
import yaml

from app.layout import construir_layout
from app.queries import obtener_filtros_disponibles
from app.callbacks import registrar_callbacks

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"


def _cargar_config() -> dict:
    with open(ROOT / "config" / "config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def crear_app() -> dash.Dash:
    config = _cargar_config()
    db_path = str(ROOT / config["rutas"]["db_path"])

    conn = sqlite3.connect(db_path)
    try:
        opciones_filtros = obtener_filtros_disponibles(conn)
    finally:
        conn.close()

    fecha_corte_actual = opciones_filtros["cortes"][0] if opciones_filtros["cortes"] else "N/D"

    app = dash.Dash(
        __name__,
        title=config["app"]["titulo"],
        suppress_callback_exceptions=True,
        assets_folder=str(ASSETS_DIR),      # <- corrección: ruta absoluta a la raíz
        assets_url_path="/assets",
        update_title="Cargando...",
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
            {"name": "description", "content": "Dashboard de oferta de servicios quirúrgicos de las IPS de Bogotá D.C. — UCompensar"},
            {"name": "theme-color", "content": "#330968"},
        ],
    )
    app.layout = construir_layout(opciones_filtros, config["app"]["titulo"], fecha_corte_actual)
    registrar_callbacks(app, db_path)
    return app


def main():
    config = _cargar_config()
    app = crear_app()
    app.run(
        debug=config["app"].get("debug", False),
        port=config["app"].get("puerto", 8050),
        host="0.0.0.0",
    )


if __name__ == "__main__":
    main()