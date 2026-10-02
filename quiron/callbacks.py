"""Callbacks interactivos del dashboard Quirón.

Este módulo conecta los controles de filtrado con los indicadores, el
mapa y las tablas descriptivas.

Responsabilidades:
  - Aplicar los filtros seleccionados por el usuario.
  - Recalcular los indicadores de la oferta filtrada.
  - Reconstruir el mapa con las sedes resultantes.
  - Actualizar la cobertura geográfica.
  - Actualizar las tablas por servicio y naturaleza jurídica.
  - Restablecer los controles mediante el botón "Limpiar filtros".

Este módulo no lee archivos directamente. La tabla completa se carga una
sola vez en ``server.py`` y se entrega a ``registrar_callbacks``.
"""

from dash import Input, Output

from quiron.data.metrics import (
    conteo_por_naturaleza,
    conteo_por_servicio,
    resumen_general,
)
from quiron.filtros import (
    aplicar_filtros,
    contar_sedes_unicas,
    filtros_activos,
)
from quiron.visualizaciones.mapa import (
    crear_mapa_oferta_quirurgica,
)


def _formatear_numero(valor):
    """Formatea un número entero utilizando punto como separador."""

    return (
        "{:,}"
        .format(int(valor))
        .replace(",", ".")
    )


def _calcular_cobertura_geografica(tabla):
    """Calcula la cobertura cartográfica de una tabla filtrada.

    Los conteos se realizan con identificadores de sede únicos. Esto
    evita contar dos veces una sede que registre varios servicios.
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
    ) if total_sedes else 0

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
    """Genera el mensaje descriptivo mostrado debajo de los filtros."""

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


def _datos_tabla(tabla):
    """Convierte una tabla de pandas a registros para DataTable."""

    return tabla.to_dict(
        "records"
    )


def registrar_callbacks(
    app,
    tabla_original,
):
    """Registra los callbacks interactivos de Quirón.

    Parámetros
    ----------
    app : dash.Dash
        Aplicación Dash donde se registrarán los callbacks.

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
        """Actualiza los resultados cuando cambia un filtro."""

        tabla_filtrada = aplicar_filtros(
            tabla_original,
            servicios=servicios,
            naturalezas=naturalezas,
            tipos_prestador=(
                tipos_prestador
            ),
            texto_sede=texto_sede,
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
        """Restablece todos los controles a su estado inicial."""

        if not numero_clics:
            return (
                [],
                [],
                [],
                "",
            )

        return (
            [],
            [],
            [],
            "",
        )