"""Callbacks interactivos del dashboard Quirón.

Este módulo conecta los controles de filtrado con:

  - Indicadores.
  - Mapa.
  - Cobertura geográfica.
  - Tablas descriptivas.
  - Descarga de detalle filtrado.
  - Descarga de resumen por servicio.
  - Descarga de resumen por naturaleza.
  - Descarga de metadata y trazabilidad.

La tabla completa se carga una sola vez desde ``server.py``. Cada
callback trabaja sobre copias filtradas y no modifica los datos
originales.
"""

from dash import (
    Input,
    Output,
    State,
    dcc,
)

from quiron.data.metrics import (
    conteo_por_naturaleza,
    conteo_por_servicio,
    resumen_general,
)
from quiron.exportacion import (
    convertir_a_csv,
    generar_nombre_archivo,
    preparar_detalle_exportacion,
    preparar_resumen_por_naturaleza,
    preparar_resumen_por_servicio,
)
from quiron.filtros import (
    aplicar_filtros,
    contar_sedes_unicas,
    filtros_activos,
)
from quiron.metadata import (
    metadata_para_exportacion,
)
from quiron.visualizaciones.mapa import (
    crear_mapa_oferta_quirurgica,
)


TIPO_CONTENIDO_CSV = (
    "text/csv; charset=utf-8"
)


def _formatear_numero(
    valor,
):
    """Formatea un entero utilizando punto como separador de miles."""

    return (
        "{:,}"
        .format(int(valor))
        .replace(",", ".")
    )


def _calcular_cobertura_geografica(
    tabla,
):
    """Calcula cobertura cartográfica sobre sedes únicas.

    Los conteos utilizan ``sede_id`` para evitar que una sede con varios
    servicios se contabilice varias veces.
    """

    total_sedes = contar_sedes_unicas(
        tabla
    )

    sedes_geocodificadas = tabla.loc[
        tabla[
            "coordenada_valida"
        ]
        .fillna(False)
        .astype(bool),
        "sede_id",
    ].nunique()

    sedes_sin_coordenadas = (
        total_sedes
        - sedes_geocodificadas
    )

    porcentaje_cobertura = (
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
        "porcentaje_cobertura": float(
            porcentaje_cobertura
        ),
    }


def _construir_estado_filtros(
    tabla_filtrada,
    total_sedes_fuente,
    servicios,
    naturalezas,
    tipos_prestador,
    texto_sede,
):
    """Genera el mensaje mostrado debajo del panel de filtros."""

    sedes_resultantes = contar_sedes_unicas(
        tabla_filtrada
    )

    hay_filtros = filtros_activos(
        servicios=servicios,
        naturalezas=naturalezas,
        tipos_prestador=tipos_prestador,
        texto_sede=texto_sede,
    )

    if not hay_filtros:
        return (
            "Mostrando toda la oferta "
            "quirúrgica registrada: "
            f"{_formatear_numero(sedes_resultantes)} "
            "sedes."
        )

    if sedes_resultantes == 0:
        return (
            "No se encontraron sedes que cumplan "
            "todos los criterios seleccionados."
        )

    return (
        "Resultado filtrado: "
        f"{_formatear_numero(sedes_resultantes)} "
        "de "
        f"{_formatear_numero(total_sedes_fuente)} "
        "sedes con oferta quirúrgica."
    )


def _datos_tabla(
    tabla,
):
    """Convierte un DataFrame a registros para Dash DataTable."""

    return tabla.to_dict(
        "records"
    )


def _aplicar_filtros_actuales(
    tabla_original,
    servicios,
    naturalezas,
    tipos_prestador,
    texto_sede,
):
    """Aplica los valores actuales de los controles.

    La función concentra esta operación para que las cuatro descargas
    utilicen exactamente las mismas reglas del dashboard.
    """

    return aplicar_filtros(
        tabla_original,
        servicios=servicios,
        naturalezas=naturalezas,
        tipos_prestador=tipos_prestador,
        texto_sede=texto_sede,
    )


def _respuesta_descarga(
    tabla,
    tipo,
):
    """Construye la respuesta esperada por dcc.Download."""

    contenido = convertir_a_csv(
        tabla
    )

    nombre_archivo = generar_nombre_archivo(
        tipo
    )

    return {
        "content": contenido,
        "filename": nombre_archivo,
        "type": TIPO_CONTENIDO_CSV,
        "base64": False,
    }


def registrar_callbacks(
    app,
    tabla_original,
):
    """Registra todos los callbacks interactivos de Quirón.

    Parámetros
    ----------
    app : dash.Dash
        Aplicación donde se registrarán los callbacks.

    tabla_original : pandas.DataFrame
        Resultado completo de
        ``cargar_oferta_con_coordenadas()``.
    """

    resumen_fuente = resumen_general(
        tabla_original
    )

    total_sedes_registradas = (
        resumen_fuente[
            "sedes_totales"
        ]
    )

    total_sedes_oferta = (
        resumen_fuente[
            "sedes_con_oferta_quirurgica"
        ]
    )

    @app.callback(
        Output(
            "kpi-sedes-totales",
            "children",
        ),
        Output(
            "kpi-sedes-oferta",
            "children",
        ),
        Output(
            "kpi-tipos-servicio",
            "children",
        ),
        Output(
            "kpi-sedes-publicas",
            "children",
        ),
        Output(
            "kpi-sedes-privadas",
            "children",
        ),
        Output(
            "mapa-oferta-quirurgica",
            "figure",
        ),
        Output(
            "mapa-sedes-visibles",
            "children",
        ),
        Output(
            (
                "mapa-sedes-"
                "sin-coordenadas"
            ),
            "children",
        ),
        Output(
            "mapa-cobertura",
            "children",
        ),
        Output(
            "tabla-por-servicio",
            "data",
        ),
        Output(
            "tabla-por-naturaleza",
            "data",
        ),
        Output(
            "estado-filtros",
            "children",
        ),
        Input(
            "filtro-servicio",
            "value",
        ),
        Input(
            "filtro-naturaleza",
            "value",
        ),
        Input(
            "filtro-tipo-prestador",
            "value",
        ),
        Input(
            "filtro-texto-sede",
            "value",
        ),
    )
    def actualizar_dashboard(
        servicios,
        naturalezas,
        tipos_prestador,
        texto_sede,
    ):
        """Actualiza el dashboard cuando cambia algún filtro."""

        tabla_filtrada = (
            _aplicar_filtros_actuales(
                tabla_original=(
                    tabla_original
                ),
                servicios=servicios,
                naturalezas=naturalezas,
                tipos_prestador=(
                    tipos_prestador
                ),
                texto_sede=texto_sede,
            )
        )

        resumen_filtrado = resumen_general(
            tabla_filtrada
        )

        tabla_por_servicio = (
            conteo_por_servicio(
                tabla_filtrada
            )
        )

        tabla_por_naturaleza = (
            conteo_por_naturaleza(
                tabla_filtrada
            )
        )

        figura_mapa = (
            crear_mapa_oferta_quirurgica(
                tabla_filtrada
            )
        )

        cobertura = (
            _calcular_cobertura_geografica(
                tabla_filtrada
            )
        )

        estado = (
            _construir_estado_filtros(
                tabla_filtrada=(
                    tabla_filtrada
                ),
                total_sedes_fuente=(
                    total_sedes_oferta
                ),
                servicios=servicios,
                naturalezas=naturalezas,
                tipos_prestador=(
                    tipos_prestador
                ),
                texto_sede=texto_sede,
            )
        )

        return (
            _formatear_numero(
                total_sedes_registradas
            ),
            _formatear_numero(
                resumen_filtrado[
                    "sedes_con_oferta_quirurgica"
                ]
            ),
            _formatear_numero(
                resumen_filtrado[
                    "tipos_de_servicio_quirurgico"
                ]
            ),
            _formatear_numero(
                resumen_filtrado[
                    "sedes_publicas"
                ]
            ),
            _formatear_numero(
                resumen_filtrado[
                    "sedes_privadas"
                ]
            ),
            figura_mapa,
            _formatear_numero(
                cobertura[
                    "sedes_geocodificadas"
                ]
            ),
            _formatear_numero(
                cobertura[
                    "sedes_sin_coordenadas"
                ]
            ),
            (
                f"{cobertura['porcentaje_cobertura']:.1f} %"
            ),
            _datos_tabla(
                tabla_por_servicio
            ),
            _datos_tabla(
                tabla_por_naturaleza
            ),
            estado,
        )

    @app.callback(
        Output(
            "filtro-servicio",
            "value",
        ),
        Output(
            "filtro-naturaleza",
            "value",
        ),
        Output(
            "filtro-tipo-prestador",
            "value",
        ),
        Output(
            "filtro-texto-sede",
            "value",
        ),
        Input(
            "boton-limpiar-filtros",
            "n_clicks",
        ),
        prevent_initial_call=True,
    )
    def limpiar_filtros(
        numero_clics,
    ):
        """Restablece todos los controles."""

        return (
            [],
            [],
            [],
            "",
        )

    @app.callback(
        Output(
            "descarga-detalle",
            "data",
        ),
        Input(
            "boton-descargar-detalle",
            "n_clicks",
        ),
        State(
            "filtro-servicio",
            "value",
        ),
        State(
            "filtro-naturaleza",
            "value",
        ),
        State(
            "filtro-tipo-prestador",
            "value",
        ),
        State(
            "filtro-texto-sede",
            "value",
        ),
        prevent_initial_call=True,
    )
    def descargar_detalle(
        numero_clics,
        servicios,
        naturalezas,
        tipos_prestador,
        texto_sede,
    ):
        """Descarga el detalle correspondiente a los filtros activos."""

        tabla_filtrada = (
            _aplicar_filtros_actuales(
                tabla_original=(
                    tabla_original
                ),
                servicios=servicios,
                naturalezas=naturalezas,
                tipos_prestador=(
                    tipos_prestador
                ),
                texto_sede=texto_sede,
            )
        )

        detalle = (
            preparar_detalle_exportacion(
                tabla_filtrada
            )
        )

        return _respuesta_descarga(
            tabla=detalle,
            tipo="detalle",
        )

    @app.callback(
        Output(
            "descarga-servicio",
            "data",
        ),
        Input(
            "boton-descargar-servicio",
            "n_clicks",
        ),
        State(
            "filtro-servicio",
            "value",
        ),
        State(
            "filtro-naturaleza",
            "value",
        ),
        State(
            "filtro-tipo-prestador",
            "value",
        ),
        State(
            "filtro-texto-sede",
            "value",
        ),
        prevent_initial_call=True,
    )
    def descargar_resumen_servicio(
        numero_clics,
        servicios,
        naturalezas,
        tipos_prestador,
        texto_sede,
    ):
        """Descarga el resumen por servicio de los datos filtrados."""

        tabla_filtrada = (
            _aplicar_filtros_actuales(
                tabla_original=(
                    tabla_original
                ),
                servicios=servicios,
                naturalezas=naturalezas,
                tipos_prestador=(
                    tipos_prestador
                ),
                texto_sede=texto_sede,
            )
        )

        resumen = preparar_resumen_por_servicio(
            tabla_filtrada
        )

        return _respuesta_descarga(
            tabla=resumen,
            tipo="servicio",
        )

    @app.callback(
        Output(
            "descarga-naturaleza",
            "data",
        ),
        Input(
            "boton-descargar-naturaleza",
            "n_clicks",
        ),
        State(
            "filtro-servicio",
            "value",
        ),
        State(
            "filtro-naturaleza",
            "value",
        ),
        State(
            "filtro-tipo-prestador",
            "value",
        ),
        State(
            "filtro-texto-sede",
            "value",
        ),
        prevent_initial_call=True,
    )
    def descargar_resumen_naturaleza(
        numero_clics,
        servicios,
        naturalezas,
        tipos_prestador,
        texto_sede,
    ):
        """Descarga el resumen por naturaleza de los datos filtrados."""

        tabla_filtrada = (
            _aplicar_filtros_actuales(
                tabla_original=(
                    tabla_original
                ),
                servicios=servicios,
                naturalezas=naturalezas,
                tipos_prestador=(
                    tipos_prestador
                ),
                texto_sede=texto_sede,
            )
        )

        resumen = (
            preparar_resumen_por_naturaleza(
                tabla_filtrada
            )
        )

        return _respuesta_descarga(
            tabla=resumen,
            tipo="naturaleza",
        )

    @app.callback(
        Output(
            "descarga-metadata",
            "data",
        ),
        Input(
            "boton-descargar-metadata",
            "n_clicks",
        ),
        State(
            "filtro-servicio",
            "value",
        ),
        State(
            "filtro-naturaleza",
            "value",
        ),
        State(
            "filtro-tipo-prestador",
            "value",
        ),
        State(
            "filtro-texto-sede",
            "value",
        ),
        prevent_initial_call=True,
    )
    def descargar_metadata(
        numero_clics,
        servicios,
        naturalezas,
        tipos_prestador,
        texto_sede,
    ):
        """Descarga la metadata y cobertura del resultado actual."""

        tabla_filtrada = (
            _aplicar_filtros_actuales(
                tabla_original=(
                    tabla_original
                ),
                servicios=servicios,
                naturalezas=naturalezas,
                tipos_prestador=(
                    tipos_prestador
                ),
                texto_sede=texto_sede,
            )
        )

        metadata_exportable = (
            metadata_para_exportacion(
                tabla_filtrada
            )
        )

        return _respuesta_descarga(
            tabla=metadata_exportable,
            tipo="metadata",
        )