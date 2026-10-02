"""Inicialización de la aplicación Dash Quirón.

Este módulo coordina las capas del proyecto:
  1. Carga la oferta y las coordenadas procesadas.
  2. Calcula los indicadores y tablas descriptivas.
  3. Construye el mapa de sedes con coordenadas válidas.
  4. Entrega todos los componentes al layout principal.

La lectura de archivos permanece en ``quiron.data.loader``; los cálculos,
en ``quiron.data.metrics``; la visualización cartográfica, en
``quiron.visualizaciones.mapa``; y la composición HTML, en
``quiron.layout``.
"""

from pathlib import Path

import dash

from quiron.data.loader import cargar_oferta_con_coordenadas
from quiron.data.metrics import (
    conteo_por_naturaleza,
    conteo_por_servicio,
    resumen_general,
)
from quiron.layout import build_layout
from quiron.visualizaciones.mapa import crear_mapa_oferta_quirurgica

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


def _calcular_cobertura_geografica(tabla):
    """Calcula la cobertura del mapa sobre sedes quirúrgicas únicas.

    Una sede puede aparecer varias veces en la tabla porque puede ofrecer
    más de un servicio. Por esa razón, los conteos se realizan con
    ``sede_id`` únicos y no con el número total de filas.
    """

    oferta_quirurgica = tabla.loc[
        tabla["es_quirurgico"].fillna(False)
    ].copy()

    total_sedes = oferta_quirurgica[
        "sede_id"
    ].nunique()

    sedes_geocodificadas = oferta_quirurgica.loc[
        oferta_quirurgica[
            "coordenada_valida"
        ].fillna(False),
        "sede_id",
    ].nunique()

    sedes_sin_coordenadas = (
        total_sedes
        - sedes_geocodificadas
    )

    return {
        "total_sedes": int(
            total_sedes
        ),
        "sedes_geocodificadas": int(
            sedes_geocodificadas
        ),
        "sedes_sin_coordenadas": int(
            sedes_sin_coordenadas
        ),
    }


def create_app():
    """Crea y configura la aplicación Dash completa."""

    tabla = cargar_oferta_con_coordenadas()

    resumen = resumen_general(
        tabla
    )

    por_servicio = conteo_por_servicio(
        tabla
    )

    por_naturaleza = conteo_por_naturaleza(
        tabla
    )

    figura_mapa = crear_mapa_oferta_quirurgica(
        tabla
    )

    cobertura = _calcular_cobertura_geografica(
        tabla
    )

    app = dash.Dash(
        __name__,
        title=(
            "Quirón · Oferta Quirúrgica "
            "de Bogotá D.C."
        ),
        assets_folder=str(
            ASSETS_DIR
        ),
        assets_url_path="assets",
        suppress_callback_exceptions=False,
        update_title=(
            "Actualizando Quirón..."
        ),
        meta_tags=[
            {
                "name": "viewport",
                "content": (
                    "width=device-width, "
                    "initial-scale=1"
                ),
            },
            {
                "name": "description",
                "content": (
                    "Dashboard para el análisis "
                    "de la oferta de servicios "
                    "quirúrgicos de las IPS de "
                    "Bogotá D.C."
                ),
            },
            {
                "name": "theme-color",
                "content": "#330968",
            },
        ],
    )

    app.layout = build_layout(
        resumen=resumen,
        por_servicio=por_servicio,
        por_naturaleza=por_naturaleza,
        figura_mapa=figura_mapa,
        sedes_geocodificadas=(
            cobertura[
                "sedes_geocodificadas"
            ]
        ),
        sedes_sin_coordenadas=(
            cobertura[
                "sedes_sin_coordenadas"
            ]
        ),
    )

    return app