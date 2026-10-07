"""Construcción del mapa interactivo de sedes quirúrgicas.

La función pública de este módulo recibe la tabla unificada generada por
``cargar_oferta_con_coordenadas`` y devuelve una figura de Plotly lista
para utilizarse dentro de un componente ``dcc.Graph`` de Dash.

El mapa se construye con una fila por sede física. Si una sede registra
varios servicios quirúrgicos, los servicios se consolidan en una sola
cadena para evitar dibujar puntos superpuestos en la misma coordenada.

Solo se representan sedes con ``coordenada_valida=True``. Las sedes sin
coordenadas permanecen disponibles en el conjunto analítico, pero no se
ubican artificialmente en el mapa.
"""

from textwrap import wrap

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


COLOR_MORADO_UCOMPENSAR = "#6E48B1"
COLOR_MORADO_PROFUNDO = "#330968"
COLOR_FONDO = "#FFFFFF"
COLOR_TEXTO_SECUNDARIO = "#6B6480"

CENTRO_BOGOTA = {
    "lat": 4.6486,
    "lon": -74.0779,
}

ZOOM_INICIAL = 10
ALTURA_MAPA = 620

ANCHO_LINEA_TOOLTIP = 42
MAXIMO_SERVICIOS_TOOLTIP = 8

COLUMNAS_REQUERIDAS = {
    "sede_id",
    "sede",
    "direccion",
    "naturaleza",
    "tipo_prestador",
    "codigo_servicio",
    "nombre_servicio",
    "latitud",
    "longitud",
    "coordenada_valida",
    "es_quirurgico",
}


def _validar_columnas(
    tabla,
):
    """Verifica que la tabla contenga los campos usados por el mapa."""

    faltantes = COLUMNAS_REQUERIDAS.difference(
        tabla.columns
    )

    if faltantes:
        columnas = ", ".join(
            sorted(
                faltantes
            )
        )

        raise ValueError(
            "No es posible construir el mapa porque "
            f"faltan las columnas: {columnas}."
        )


def _unir_valores_unicos(
    serie,
):
    """Combina valores únicos respetando su orden de aparición."""

    valores = []

    for valor in serie.dropna():
        texto = str(
            valor
        ).strip()

        if texto and texto not in valores:
            valores.append(
                texto
            )

    return " · ".join(
        valores
    )


def _valores_unicos(
    serie,
):
    """Devuelve valores únicos limpios conservando su orden."""

    valores = []

    for valor in serie.dropna():
        texto = str(
            valor
        ).strip()

        if texto and texto not in valores:
            valores.append(
                texto
            )

    return valores


def _envolver_texto_tooltip(
    valor,
    ancho=ANCHO_LINEA_TOOLTIP,
):
    """Divide un valor largo en líneas aptas para el tooltip.

    Plotly interpreta ``<br>`` como salto de línea dentro de
    ``hovertemplate``. La función no modifica el valor analítico
    original; únicamente crea una representación para visualización.
    """

    if pd.isna(
        valor
    ):
        return "No disponible"

    texto = str(
        valor
    ).strip()

    if not texto:
        return "No disponible"

    lineas = wrap(
        texto,
        width=ancho,
        break_long_words=False,
        break_on_hyphens=False,
    )

    return "<br>".join(
        lineas
    )


def _formatear_lista_tooltip(
    valor,
):
    """Formatea una cadena consolidada como lista multilínea."""

    if pd.isna(
        valor
    ):
        return "No disponible"

    texto = str(
        valor
    ).strip()

    if not texto:
        return "No disponible"

    elementos = [
        elemento.strip()
        for elemento in texto.split(" · ")
        if elemento.strip()
    ]

    if not elementos:
        return "No disponible"

    elementos_visibles = elementos[
        :MAXIMO_SERVICIOS_TOOLTIP
    ]

    lineas = []

    for elemento in elementos_visibles:
        elemento_envuelto = (
            _envolver_texto_tooltip(
                elemento
            )
        )

        lineas.append(
            f"• {elemento_envuelto}"
        )

    elementos_ocultos = (
        len(elementos)
        - len(elementos_visibles)
    )

    if elementos_ocultos > 0:
        lineas.append(
            (
                f"• … y {elementos_ocultos} "
                "servicios adicionales"
            )
        )

    return "<br>".join(
        lineas
    )


def _preparar_sedes_para_mapa(
    tabla,
):
    """Consolida la oferta a una fila por sede georreferenciada.

    Una sede puede registrar varios servicios quirúrgicos. En lugar de
    dibujar varios puntos exactamente en las mismas coordenadas, esta
    función agrupa los códigos y nombres de servicio en una sola fila.

    Se crean columnas adicionales terminadas en ``_tooltip``. Estas
    columnas se utilizan únicamente para presentar información dentro
    del recuadro del mapa y no sustituyen los valores originales.
    """

    _validar_columnas(
        tabla
    )

    coordenadas_validas = (
        tabla[
            "coordenada_valida"
        ]
        .fillna(False)
        .astype(bool)
    )

    servicios_quirurgicos = (
        tabla[
            "es_quirurgico"
        ]
        .fillna(False)
        .astype(bool)
    )

    registros_validos = tabla.loc[
        coordenadas_validas
        & servicios_quirurgicos
        & tabla[
            "latitud"
        ].notna()
        & tabla[
            "longitud"
        ].notna()
    ].copy()

    if registros_validos.empty:
        return pd.DataFrame(
            columns=[
                "sede_id",
                "sede",
                "direccion",
                "naturaleza",
                "tipo_prestador",
                "servicios",
                "codigos_servicio",
                "latitud",
                "longitud",
                "sede_tooltip",
                "direccion_tooltip",
                "naturaleza_tooltip",
                "tipo_prestador_tooltip",
                "codigos_tooltip",
                "servicios_tooltip",
            ]
        )

    sedes = (
        registros_validos
        .groupby(
            "sede_id",
            as_index=False,
        )
        .agg(
            sede=(
                "sede",
                "first",
            ),
            direccion=(
                "direccion",
                "first",
            ),
            naturaleza=(
                "naturaleza",
                "first",
            ),
            tipo_prestador=(
                "tipo_prestador",
                "first",
            ),
            servicios=(
                "nombre_servicio",
                _unir_valores_unicos,
            ),
            codigos_servicio=(
                "codigo_servicio",
                _unir_valores_unicos,
            ),
            latitud=(
                "latitud",
                "first",
            ),
            longitud=(
                "longitud",
                "first",
            ),
        )
        .sort_values(
            "sede",
            kind="stable",
        )
        .reset_index(
            drop=True
        )
    )

    sedes[
        "sede_tooltip"
    ] = sedes[
        "sede"
    ].apply(
        _envolver_texto_tooltip
    )

    sedes[
        "direccion_tooltip"
    ] = sedes[
        "direccion"
    ].apply(
        _envolver_texto_tooltip
    )

    sedes[
        "naturaleza_tooltip"
    ] = sedes[
        "naturaleza"
    ].apply(
        _envolver_texto_tooltip
    )

    sedes[
        "tipo_prestador_tooltip"
    ] = sedes[
        "tipo_prestador"
    ].apply(
        _envolver_texto_tooltip
    )

    sedes[
        "codigos_tooltip"
    ] = sedes[
        "codigos_servicio"
    ].apply(
        _formatear_lista_tooltip
    )

    sedes[
        "servicios_tooltip"
    ] = sedes[
        "servicios"
    ].apply(
        _formatear_lista_tooltip
    )

    return sedes


def _crear_mapa_sin_datos():
    """Crea una figura informativa cuando no existen puntos válidos."""

    figura = go.Figure()

    figura.add_annotation(
        text=(
            "No hay sedes con coordenadas válidas para mostrar. "
            "Revisa el archivo sedes_geocodificadas.csv."
        ),
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        align="center",
        font={
            "family": (
                "Segoe UI, Arial, sans-serif"
            ),
            "size": 16,
            "color": (
                COLOR_TEXTO_SECUNDARIO
            ),
        },
    )

    figura.update_layout(
        height=ALTURA_MAPA,
        paper_bgcolor=COLOR_FONDO,
        plot_bgcolor=COLOR_FONDO,
        margin={
            "l": 0,
            "r": 0,
            "t": 20,
            "b": 0,
        },
        xaxis={
            "visible": False,
        },
        yaxis={
            "visible": False,
        },
    )

    return figura


def crear_mapa_oferta_quirurgica(
    tabla,
):
    """Crea el mapa interactivo de sedes con oferta quirúrgica.

    Parámetros
    ----------
    tabla : pandas.DataFrame
        Resultado de ``cargar_oferta_con_coordenadas``.

    Retorna
    -------
    plotly.graph_objects.Figure
        Figura lista para asignar a ``dcc.Graph(figure=...)``.
    """

    sedes = _preparar_sedes_para_mapa(
        tabla
    )

    if sedes.empty:
        return _crear_mapa_sin_datos()

    figura = px.scatter_map(
        sedes,
        lat="latitud",
        lon="longitud",
        custom_data=[
            "sede_tooltip",
            "direccion_tooltip",
            "naturaleza_tooltip",
            "tipo_prestador_tooltip",
            "codigos_tooltip",
            "servicios_tooltip",
        ],
        center=CENTRO_BOGOTA,
        zoom=ZOOM_INICIAL,
        height=ALTURA_MAPA,
        map_style="carto-positron",
        color_discrete_sequence=[
            COLOR_MORADO_UCOMPENSAR
        ],
    )

    figura.update_traces(
        mode="markers",
        marker={
            "size": 11,
            "opacity": 0.82,
        },
        hovertemplate=(
            "<b>%{customdata[0]}</b><br><br>"
            "<b>Dirección:</b><br>"
            "%{customdata[1]}<br><br>"
            "<b>Naturaleza jurídica:</b><br>"
            "%{customdata[2]}<br><br>"
            "<b>Tipo de prestador:</b><br>"
            "%{customdata[3]}<br><br>"
            "<b>Códigos de servicio:</b><br>"
            "%{customdata[4]}<br><br>"
            "<b>Servicios:</b><br>"
            "%{customdata[5]}"
            "<extra></extra>"
        ),
    )

    figura.update_layout(
        paper_bgcolor=COLOR_FONDO,
        plot_bgcolor=COLOR_FONDO,
        font={
            "family": (
                "Segoe UI, Arial, sans-serif"
            ),
            "color": (
                COLOR_MORADO_PROFUNDO
            ),
        },
        margin={
            "l": 0,
            "r": 0,
            "t": 10,
            "b": 0,
        },
        showlegend=False,
        hoverlabel={
            "bgcolor": (
                COLOR_FONDO
            ),
            "bordercolor": (
                COLOR_MORADO_UCOMPENSAR
            ),
            "align": "left",
            "font": {
                "family": (
                    "Segoe UI, Arial, sans-serif"
                ),
                "size": 12,
                "color": (
                    COLOR_MORADO_PROFUNDO
                ),
            },
        },
        uirevision=(
            "mapa-oferta-quirurgica"
        ),
    )

    return figura