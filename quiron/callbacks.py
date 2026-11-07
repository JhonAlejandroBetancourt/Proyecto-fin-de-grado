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

import base64
import io
import json
import uuid

import pandas as pd

from dash import (
    Input,
    Output,
    State,
    dcc,
    html,
    no_update,
)

from quiron.etl import (
    NivelTraza,
    TrazaETL,
    ejecutar_etl,
)
from quiron.etl.comparacion import (
    comparar_datasets,
)
from quiron.layout import (
    resumen_etl_component,
)
from quiron.asistente import (
    ErrorAsistente,
    buscar_sede_mencionada,
    buscar_sede_unica,
    interpretar_solicitud,
    solicita_descarga_detalle,
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
    obtener_opciones_filtros,
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

TAMANO_MAXIMO_CSV_ETL = (
    10 * 1024 * 1024
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


def _tarjeta_error(
    titulo,
    mensaje,
):
    """Construye una tarjeta visual para un error del ETL."""

    return html.Div(
        className="etl-error",
        children=[
            html.Strong(
                f"{titulo}: "
            ),
            html.Span(mensaje),
        ],
    )


def _traza_error_carga(
    nombre_fuente,
    mensaje,
):
    """Construye una traza completa para errores previos al ETL."""

    traza = TrazaETL()
    traza.registrar_error(
        "Carga",
        mensaje,
    )
    datos = traza.como_dict()
    datos.update(
        {
            "huella_sha256": None,
            "nombre_fuente": (
                nombre_fuente
                or "archivo cargado"
            ),
            "exito": False,
        }
    )
    return datos


def _combinar_historial_etl(
    traza_actual,
    traza_anterior,
):
    """Acumula las ejecuciones en la sesión del navegador."""

    traza_anterior = traza_anterior or {}
    historial = traza_anterior.get(
        "historial",
        traza_anterior.get("pasos", []),
    )
    historial = list(historial or [])
    numero_ejecucion = int(
        traza_anterior.get(
            "numero_ejecucion",
            1 if historial else 0,
        )
    ) + 1

    pasos_actuales = list(
        traza_actual.get("pasos", [])
    )

    if not pasos_actuales:
        for error in traza_actual.get(
            "errores",
            [],
        ):
            pasos_actuales.append(
                {
                    "orden": (
                        len(pasos_actuales) + 1
                    ),
                    "nombre": error.get(
                        "paso",
                        "Error",
                    ),
                    "nivel": NivelTraza.ERROR.value,
                    "mensaje": error.get(
                        "mensaje",
                        "Error no especificado.",
                    ),
                    "marca_tiempo": error.get(
                        "marca_tiempo",
                        "",
                    ),
                    "duracion_ms": 0.0,
                    "filas": None,
                }
            )

    historial.extend(
        {
            **paso,
            "ejecucion": numero_ejecucion,
        }
        for paso in pasos_actuales
    )
    traza_actual["historial"] = historial[-500:]
    traza_actual["numero_ejecucion"] = (
        numero_ejecucion
    )
    return traza_actual


def _tabla_activa(
    dataset_activo,
    tabla_original,
):
    """Devuelve el conjunto de datos vigente.

    Si el usuario cargó un CSV válido, el store ``etl-dataset-activo``
    contiene la tabla serializada; en caso contrario se usa la tabla base
    cargada al arrancar la aplicación. Así, cualquier fallo en la carga
    conserva el conjunto de datos incluido sin interrumpir el dashboard.
    """

    if not dataset_activo:
        return tabla_original

    try:
        tabla = pd.DataFrame(
            dataset_activo
        )
    except (ValueError, TypeError):
        return tabla_original

    if tabla.empty:
        return tabla_original

    for columna in (
        "es_quirurgico",
        "coordenada_valida",
        "geocodificado",
    ):
        if columna in tabla.columns:
            tabla[columna] = (
                tabla[columna]
                .fillna(False)
                .astype(bool)
            )

    return tabla


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

    @app.callback(
        Output(
            "vista-dashboard",
            "className",
        ),
        Output(
            "vista-etl",
            "className",
        ),
        Output(
            "nav-dashboard",
            "className",
        ),
        Output(
            "nav-etl",
            "className",
        ),
        Input(
            "url",
            "pathname",
        ),
    )
    def navegar_pagina(pathname):
        """Alterna entre el dashboard y la página independiente del ETL."""

        if pathname == "/etl":
            return (
                "pagina pagina-oculta",
                "pagina",
                "enlace-nav",
                "enlace-nav enlace-nav-activo",
            )
        return (
            "pagina",
            "pagina pagina-oculta",
            "enlace-nav enlace-nav-activo",
            "enlace-nav",
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
        Input(
            "etl-dataset-activo",
            "data",
        ),
    )
    def actualizar_dashboard(
        servicios,
        naturalezas,
        tipos_prestador,
        texto_sede,
        dataset_activo,
    ):
        """Actualiza el dashboard cuando cambia un filtro o el dataset."""

        tabla_base = _tabla_activa(
            dataset_activo,
            tabla_original,
        )

        resumen_base = resumen_general(
            tabla_base
        )

        total_sedes_registradas_actual = (
            resumen_base["sedes_totales"]
        )

        total_sedes_oferta_actual = (
            resumen_base[
                "sedes_con_oferta_quirurgica"
            ]
        )

        tabla_filtrada = (
            _aplicar_filtros_actuales(
                tabla_original=(
                    tabla_base
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
                    total_sedes_oferta_actual
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
                total_sedes_registradas_actual
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
            "etl-dataset-activo",
            "data",
        ),
        Output(
            "etl-traza",
            "data",
        ),
        Output(
            "etl-tabla-historico",
            "data",
        ),
        Output(
            "etl-tabla-mapeo",
            "data",
        ),
        Output(
            "etl-panel-errores",
            "children",
        ),
        Output(
            "etl-panel-errores",
            "className",
        ),
        Output(
            "etl-estado",
            "children",
        ),
        Output(
            "etl-resumen",
            "children",
        ),
        Output(
            "etl-tabla-sedes-no-mapeadas",
            "data",
        ),
        Output(
            "etl-tabla-cambios",
            "data",
        ),
        Output(
            "filtro-servicio",
            "options",
        ),
        Output(
            "filtro-naturaleza",
            "options",
        ),
        Output(
            "filtro-tipo-prestador",
            "options",
        ),
        Output(
            "filtro-servicio",
            "value",
            allow_duplicate=True,
        ),
        Output(
            "filtro-naturaleza",
            "value",
            allow_duplicate=True,
        ),
        Output(
            "filtro-tipo-prestador",
            "value",
            allow_duplicate=True,
        ),
        Output(
            "filtro-texto-sede",
            "value",
            allow_duplicate=True,
        ),
        Input(
            "etl-carga-csv",
            "contents",
        ),
        State(
            "etl-carga-csv",
            "filename",
        ),
        State(
            "etl-traza",
            "data",
        ),
        State(
            "etl-dataset-activo",
            "data",
        ),
        prevent_initial_call=True,
    )
    def cargar_csv_etl(
        contenido,
        nombre_archivo,
        traza_anterior,
        dataset_anterior,
    ):
        """Ejecuta el ETL con el CSV cargado y actualiza la observabilidad.

        Si el ETL es válido, escribe la tabla en ``etl-dataset-activo``,
        lo que desencadena la actualización en vivo de los indicadores,
        el mapa y las tablas. Si falla, conserva el dataset vigente y
        muestra los errores sin interrumpir el dashboard.
        """

        if not contenido:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        if (
            not nombre_archivo
            or not nombre_archivo.lower().endswith(
                ".csv"
            )
        ):
            error = (
                "Selecciona un archivo con "
                "extensión .csv."
            )
            traza_error = _traza_error_carga(
                nombre_archivo,
                error,
            )
            traza_error = _combinar_historial_etl(
                traza_error,
                traza_anterior,
            )
            return (
                no_update,
                traza_error,
                [],
                [],
                [_tarjeta_error("Carga", error)],
                "etl-errores",
                (
                    "Tipo de archivo no válido. "
                    "Se mantiene el conjunto de "
                    "datos vigente."
                ),
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        if len(contenido) > (
            (TAMANO_MAXIMO_CSV_ETL * 4 // 3)
            + 8192
        ):
            error = (
                "El archivo supera el límite "
                "de 10 MB."
            )
            traza_error = _traza_error_carga(
                nombre_archivo,
                error,
            )
            traza_error = _combinar_historial_etl(
                traza_error,
                traza_anterior,
            )
            return (
                no_update,
                traza_error,
                [],
                [],
                [_tarjeta_error("Carga", error)],
                "etl-errores",
                (
                    "El archivo es demasiado "
                    "grande. Se mantiene el "
                    "conjunto de datos vigente."
                ),
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        try:
            _, cadena_contenido = (
                contenido.split(",", 1)
            )
            datos = base64.b64decode(
                cadena_contenido,
                validate=True,
            )
        except (ValueError, TypeError):
            error = (
                "No fue posible decodificar "
                "el archivo cargado."
            )
            traza_error = _traza_error_carga(
                nombre_archivo,
                error,
            )
            traza_error = _combinar_historial_etl(
                traza_error,
                traza_anterior,
            )
            errores = [
                _tarjeta_error(
                    "Carga",
                    error,
                )
            ]

            return (
                no_update,
                traza_error,
                [],
                [],
                errores,
                "etl-errores",
                (
                    "No se pudo leer el archivo "
                    "cargado. Se mantiene el "
                    "conjunto de datos vigente."
                ),
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        if len(datos) > TAMANO_MAXIMO_CSV_ETL:
            error = (
                "El archivo supera el límite "
                "de 10 MB."
            )
            traza_error = _traza_error_carga(
                nombre_archivo,
                error,
            )
            traza_error = _combinar_historial_etl(
                traza_error,
                traza_anterior,
            )
            return (
                no_update,
                traza_error,
                [],
                [],
                [_tarjeta_error("Carga", error)],
                "etl-errores",
                (
                    "El archivo es demasiado "
                    "grande. Se mantiene el "
                    "conjunto de datos vigente."
                ),
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        resultado = ejecutar_etl(
            origen=datos,
            nombre_fuente=(
                nombre_archivo
                or "archivo cargado"
            ),
        )

        traza_dict = (
            resultado.como_dict_traza()
        )
        traza_dict = _combinar_historial_etl(
            traza_dict,
            traza_anterior,
        )

        historico = traza_dict["historial"]
        mapeo = traza_dict["mapeos"]

        if not resultado.exito:
            errores = [
                _tarjeta_error(
                    error["paso"],
                    error["mensaje"],
                )
                for error in traza_dict[
                    "errores"
                ]
            ]

            estado = (
                "El ETL de "
                f"'{resultado.nombre_fuente}' "
                "falló. Se mantiene el conjunto "
                "de datos vigente."
            )

            return (
                no_update,
                traza_dict,
                historico,
                mapeo,
                errores,
                "etl-errores",
                estado,
                resumen_etl_component(
                    traza_dict.get(
                        "informe",
                        {},
                    )
                ),
                traza_dict.get(
                    "informe",
                    {},
                ).get(
                    "sedes_no_mapeadas",
                    [],
                ),
                [],
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        comparacion = comparar_datasets(
            _tabla_activa(
                dataset_anterior,
                tabla_original,
            ),
            resultado.tabla,
        )
        cambios_visibles = list(
            comparacion["cambios"]
        )
        cambios_visibles.extend(
            {
                "sede": duplicado.get(
                    "sede",
                    "",
                ),
                "campo": (
                    "Duplicado exacto omitido"
                ),
                "valor_anterior": "—",
                "valor_nuevo": (
                    "Se conservó una copia"
                ),
            }
            for duplicado in traza_dict[
                "informe"
            ].get(
                "duplicados",
                [],
            )
        )
        traza_dict["cambios"] = (
            cambios_visibles
        )
        traza_dict["informe"][
            "comparacion"
        ] = {
            clave: valor
            for clave, valor in comparacion.items()
            if clave != "cambios"
        }

        opciones = obtener_opciones_filtros(
            resultado.tabla
        )

        resumen_etl = resumen_etl_component(
            traza_dict["informe"],
            comparacion,
        )

        if comparacion["ambiguas"]:
            errores = [
                _tarjeta_error(
                    "Comparación ambigua",
                    (
                        f"Se encontraron "
                        f"{comparacion['ambiguas']} "
                        "identidades repetidas con "
                        "valores distintos. No se "
                        "actualizó el conjunto activo."
                    ),
                )
            ]
            return (
                no_update,
                traza_dict,
                historico,
                mapeo,
                errores,
                "etl-errores",
                (
                    "La carga pasó el ETL, pero no se "
                    "aplicó porque la identidad de una "
                    "o más sedes es ambigua."
                ),
                resumen_etl,
                traza_dict["informe"].get(
                    "sedes_no_mapeadas",
                    [],
                ),
                cambios_visibles,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        if comparacion["sin_diferencias"]:
            return (
                no_update,
                traza_dict,
                historico,
                mapeo,
                [],
                "etl-errores etl-oculto",
                (
                    "No se detectaron cambios en los datos; "
                    "el conjunto activo se conserva sin "
                    "volver a cargarlo. "
                    f"Huella SHA-256: "
                    f"{resultado.huella_sha256[:12]}…"
                ),
                resumen_etl,
                traza_dict["informe"].get(
                    "sedes_no_mapeadas",
                    [],
                ),
                cambios_visibles,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        estado = (
            "Se aplicó la carga de "
            f"'{resultado.nombre_fuente}': "
            f"{comparacion['actualizadas']} actualizadas, "
            f"{comparacion['nuevas']} nuevas y "
            f"{comparacion['retiradas']} retiradas; "
            f"{comparacion['sin_cambios']} sin cambios. "
            f"Huella SHA-256: "
            f"{resultado.huella_sha256[:12]}…"
        )

        return (
            resultado.tabla.to_dict(
                "records"
            ),
            traza_dict,
            historico,
            mapeo,
            [],
            "etl-errores etl-oculto",
            estado,
            resumen_etl,
            traza_dict["informe"].get(
                "sedes_no_mapeadas",
                [],
            ),
            cambios_visibles,
            opciones["servicios"],
            opciones["naturalezas"],
            opciones["tipos_prestador"],
            [],
            [],
            [],
            "",
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
        State(
            "etl-dataset-activo",
            "data",
        ),
        prevent_initial_call=True,
    )
    def descargar_detalle(
        numero_clics,
        servicios,
        naturalezas,
        tipos_prestador,
        texto_sede,
        dataset_activo,
    ):
        """Descarga el detalle correspondiente a los filtros activos."""

        tabla_filtrada = (
            _aplicar_filtros_actuales(
                tabla_original=(
                    _tabla_activa(
                        dataset_activo,
                        tabla_original,
                    )
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
        State(
            "etl-dataset-activo",
            "data",
        ),
        State(
            "etl-traza",
            "data",
        ),
        prevent_initial_call=True,
    )
    def descargar_resumen_servicio(
        numero_clics,
        servicios,
        naturalezas,
        tipos_prestador,
        texto_sede,
        dataset_activo,
        traza_etl,
    ):
        """Descarga el resumen por servicio de los datos filtrados."""

        tabla_filtrada = (
            _aplicar_filtros_actuales(
                tabla_original=(
                    _tabla_activa(
                        dataset_activo,
                        tabla_original,
                    )
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
        State(
            "etl-dataset-activo",
            "data",
        ),
        prevent_initial_call=True,
    )
    def descargar_resumen_naturaleza(
        numero_clics,
        servicios,
        naturalezas,
        tipos_prestador,
        texto_sede,
        dataset_activo,
    ):
        """Descarga el resumen por naturaleza de los datos filtrados."""

        tabla_filtrada = (
            _aplicar_filtros_actuales(
                tabla_original=(
                    _tabla_activa(
                        dataset_activo,
                        tabla_original,
                    )
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
        State(
            "etl-dataset-activo",
            "data",
        ),
        State(
            "etl-traza",
            "data",
        ),
        prevent_initial_call=True,
    )
    def descargar_metadata(
        numero_clics,
        servicios,
        naturalezas,
        tipos_prestador,
        texto_sede,
        dataset_activo,
        traza_etl,
    ):
        """Descarga la metadata y cobertura del resultado actual."""

        tabla_filtrada = (
            _aplicar_filtros_actuales(
                tabla_original=(
                    _tabla_activa(
                        dataset_activo,
                        tabla_original,
                    )
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
        if traza_etl:
            filas_etl = pd.DataFrame(
                [
                    {
                        "campo": (
                            "etl_nombre_fuente"
                        ),
                        "valor": traza_etl.get(
                            "nombre_fuente",
                            "",
                        ),
                    },
                    {
                        "campo": (
                            "etl_huella_sha256"
                        ),
                        "valor": traza_etl.get(
                            "huella_sha256",
                            "",
                        )
                        or "",
                    },
                ]
            )
            metadata_exportable = pd.concat(
                [
                    metadata_exportable,
                    filas_etl,
                ],
                ignore_index=True,
            )

        return _respuesta_descarga(
            tabla=metadata_exportable,
            tipo="metadata",
        )

    @app.callback(
        Output(
            "filtro-servicio",
            "value",
            allow_duplicate=True,
        ),
        Output(
            "filtro-naturaleza",
            "value",
            allow_duplicate=True,
        ),
        Output(
            "filtro-tipo-prestador",
            "value",
            allow_duplicate=True,
        ),
        Output(
            "filtro-texto-sede",
            "value",
            allow_duplicate=True,
        ),
        Output(
            "asistente-estado",
            "children",
        ),
        Output(
            "asistente-respuesta",
            "children",
        ),
        Output(
            "mapa-enfoque-pendiente",
            "children",
        ),
        Output(
            "descarga-detalle",
            "data",
            allow_duplicate=True,
        ),
        Input(
            "asistente-enviar",
            "n_clicks",
        ),
        State(
            "asistente-solicitud",
            "value",
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
        State(
            "etl-dataset-activo",
            "data",
        ),
        prevent_initial_call=True,
    )
    def ejecutar_asistente(
        numero_clics,
        solicitud,
        servicios_actuales,
        naturalezas_actuales,
        tipos_actuales,
        texto_actual,
        dataset_activo,
    ):
        """Interpreta una solicitud y aplica únicamente acciones permitidas."""

        tabla_base = _tabla_activa(
            dataset_activo,
            tabla_original,
        )
        opciones_asistente_actuales = (
            obtener_opciones_filtros(
                tabla_base
            )
        )

        try:
            sede_mencionada = buscar_sede_mencionada(
                tabla_base,
                solicitud,
            )
            descarga_detalle = solicita_descarga_detalle(
                solicitud
            )
            if sede_mencionada is not None or descarga_detalle:
                comando = {
                    "understood": True,
                    "clear_filters": False,
                    "change_services": False,
                    "services": [],
                    "change_nature": False,
                    "nature": [],
                    "change_providers": False,
                    "providers": [],
                    "change_name_search": False,
                    "name_search": "",
                    "focus_sede": (
                        str(sede_mencionada["sede"])
                        if sede_mencionada is not None
                        else ""
                    ),
                    "download_detail": descarga_detalle,
                }
            else:
                comando = interpretar_solicitud(
                    solicitud,
                    opciones_asistente_actuales,
                )
        except ErrorAsistente as error:
            mensaje = str(error)
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                mensaje,
                mensaje,
                "",
                no_update,
            )
        if not comando["understood"]:
            mensaje = (
                "No entendí la solicitud. Prueba, por ejemplo: "
                "«filtra las sedes públicas» o "
                "«ubica Clínica del Norte en el mapa»."
            )
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                mensaje,
                mensaje,
                "",
                no_update,
            )

        if comando["clear_filters"]:
            nuevos_servicios = []
            nuevas_naturalezas = []
            nuevos_tipos = []
            nuevo_texto = ""
        else:
            nuevos_servicios = (
                comando["services"]
                if comando["change_services"]
                else servicios_actuales or []
            )
            nuevas_naturalezas = (
                comando["nature"]
                if comando["change_nature"]
                else naturalezas_actuales or []
            )
            nuevos_tipos = (
                comando["providers"]
                if comando["change_providers"]
                else tipos_actuales or []
            )
            nuevo_texto = (
                comando["name_search"]
                if comando["change_name_search"]
                else texto_actual or ""
            )

        sede_enfocada = None
        consulta_sede = comando["focus_sede"]
        if consulta_sede:
            sede_enfocada, error_busqueda = buscar_sede_unica(
                tabla_base,
                consulta_sede,
            )
            if error_busqueda:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    error_busqueda,
                    error_busqueda,
                    "",
                    no_update,
                )

            coincidencias_filtradas = aplicar_filtros(
                tabla_base,
                servicios=nuevos_servicios,
                naturalezas=nuevas_naturalezas,
                tipos_prestador=nuevos_tipos,
                texto_sede=nuevo_texto,
            )
            if not coincidencias_filtradas[
                "sede_id"
            ].astype(str).eq(
                str(sede_enfocada["sede_id"])
            ).any():
                mensaje = (
                    f"Encontré «{sede_enfocada['sede']}», pero no aparece "
                    "con los filtros actuales. Ajusta los filtros o pide "
                    "limpiarlos y vuelve a intentarlo."
                )
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    mensaje,
                    mensaje,
                    "",
                    no_update,
                )

            nuevo_texto = str(
                sede_enfocada["sede"]
            )

        if comando["download_detail"]:
            respuesta = (
                "De acuerdo, descargué el detalle filtrado."
            )
        elif comando["clear_filters"]:
            respuesta = "De acuerdo, limpié todos los filtros."
        elif sede_enfocada is not None:
            respuesta = (
                f"De acuerdo, encontré {sede_enfocada['sede']}. "
                "La filtré y acerqué el mapa."
            )
        elif comando["change_name_search"]:
            respuesta = (
                "De acuerdo, actualicé la búsqueda de sedes."
                if nuevo_texto
                else "De acuerdo, quité el filtro de búsqueda de sedes."
            )
        elif any(
            (
                comando["change_services"],
                comando["change_nature"],
                comando["change_providers"],
            )
        ):
            respuesta = "De acuerdo, apliqué los filtros solicitados."
        else:
            respuesta = (
                "Entendí la solicitud, pero no detecté un cambio "
                "que pueda aplicar."
            )

        enfoque = ""
        if sede_enfocada is not None:
            enfoque = json.dumps(
                {
                    "id": uuid.uuid4().hex,
                    "lat": float(
                        sede_enfocada["latitud"]
                    ),
                    "lon": float(
                        sede_enfocada["longitud"]
                    ),
                    "zoom": 15,
                }
            )

        descarga = no_update
        if comando["download_detail"]:
            tabla_filtrada = _aplicar_filtros_actuales(
                tabla_original=tabla_base,
                servicios=nuevos_servicios,
                naturalezas=nuevas_naturalezas,
                tipos_prestador=nuevos_tipos,
                texto_sede=nuevo_texto,
            )
            descarga = _respuesta_descarga(
                tabla=preparar_detalle_exportacion(
                    tabla_filtrada
                ),
                tipo="detalle",
            )

        return (
            nuevos_servicios,
            nuevas_naturalezas,
            nuevos_tipos,
            nuevo_texto,
            "Solicitud aplicada.",
            respuesta,
            enfoque,
            descarga,
        )