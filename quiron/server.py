"""Inicialización de la aplicación Dash Quirón.

Este módulo coordina las capas del proyecto:

  1. Carga la oferta y las coordenadas procesadas.
  2. Calcula los indicadores y tablas iniciales.
  3. Construye el mapa inicial.
  4. Genera las opciones disponibles para los filtros.
  5. Calcula la metadata y la trazabilidad.
  6. Compone la interfaz principal.
  7. Registra los callbacks interactivos y de descarga.

La aplicación carga los datos una sola vez durante el arranque.

Los callbacks reutilizan la tabla en memoria y no vuelven a leer los
archivos CSV en cada interacción del usuario.
"""

from pathlib import Path

import dash

from quiron.callbacks import (
    registrar_callbacks,
)
from quiron.data.loader import (
    cargar_oferta_con_coordenadas,
)
from quiron.data.metrics import (
    conteo_por_naturaleza,
    conteo_por_servicio,
    resumen_general,
)
from quiron.filtros import (
    obtener_opciones_filtros,
)
from quiron.layout import (
    build_layout,
)
from quiron.metadata import (
    obtener_metadata,
)
from quiron.visualizaciones.mapa import (
    crear_mapa_oferta_quirurgica,
)


BASE_DIR = Path(
    __file__
).resolve().parent

ASSETS_DIR = (
    BASE_DIR
    / "assets"
)


def _calcular_cobertura_geografica(
    tabla,
):
    """Calcula la cobertura sobre sedes quirúrgicas únicas.

    Una sede puede aparecer en más de una fila debido a que puede
    registrar varios servicios.

    Por este motivo, los conteos se realizan con ``sede_id`` únicos y no
    con el número de filas.
    """

    oferta_quirurgica = tabla.loc[
        tabla[
            "es_quirurgico"
        ]
        .fillna(False)
        .astype(bool)
    ].copy()

    total_sedes = (
        oferta_quirurgica[
            "sede_id"
        ]
        .nunique()
    )

    sedes_geocodificadas = (
        oferta_quirurgica.loc[
            oferta_quirurgica[
                "coordenada_valida"
            ]
            .fillna(False)
            .astype(bool),
            "sede_id",
        ]
        .nunique()
    )

    sedes_sin_coordenadas = (
        total_sedes
        - sedes_geocodificadas
    )

    porcentaje_geocodificacion = (
        sedes_geocodificadas
        / total_sedes
        * 100
    ) if total_sedes else 0.0

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
        "porcentaje_geocodificacion": round(
            porcentaje_geocodificacion,
            1,
        ),
    }


def _construir_datos_iniciales(
    tabla,
):
    """Prepara los datos utilizados al crear la interfaz.

    Todos los componentes iniciales se construyen a partir de la misma
    tabla cargada para evitar diferencias entre indicadores, filtros,
    mapa, metadata y exportaciones.
    """

    resumen = resumen_general(
        tabla
    )

    por_servicio = conteo_por_servicio(
        tabla
    )

    por_naturaleza = conteo_por_naturaleza(
        tabla
    )

    figura_mapa = (
        crear_mapa_oferta_quirurgica(
            tabla
        )
    )

    cobertura = (
        _calcular_cobertura_geografica(
            tabla
        )
    )

    opciones_filtros = (
        obtener_opciones_filtros(
            tabla
        )
    )

    metadata = obtener_metadata(
        tabla=tabla
    )

    return {
        "resumen": resumen,
        "por_servicio": por_servicio,
        "por_naturaleza": (
            por_naturaleza
        ),
        "figura_mapa": figura_mapa,
        "cobertura": cobertura,
        "opciones_filtros": (
            opciones_filtros
        ),
        "metadata": metadata,
    }


def _crear_aplicacion_dash():
    """Crea la instancia base de Dash."""

    return dash.Dash(
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
                    "de la oferta registrada de "
                    "servicios quirúrgicos de las "
                    "IPS de Bogotá D.C."
                ),
            },
            {
                "name": "theme-color",
                "content": "#330968",
            },
        ],
    )


def create_app():
    """Crea, configura y devuelve la aplicación completa."""

    tabla = (
        cargar_oferta_con_coordenadas()
    )

    datos_iniciales = (
        _construir_datos_iniciales(
            tabla
        )
    )

    app = _crear_aplicacion_dash()

    cobertura = datos_iniciales[
        "cobertura"
    ]

    app.layout = build_layout(
        resumen=datos_iniciales[
            "resumen"
        ],
        por_servicio=datos_iniciales[
            "por_servicio"
        ],
        por_naturaleza=datos_iniciales[
            "por_naturaleza"
        ],
        figura_mapa=datos_iniciales[
            "figura_mapa"
        ],
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
        opciones_filtros=datos_iniciales[
            "opciones_filtros"
        ],
        metadata=datos_iniciales[
            "metadata"
        ],
    )

    registrar_callbacks(
        app=app,
        tabla_original=tabla,
    )

    return app