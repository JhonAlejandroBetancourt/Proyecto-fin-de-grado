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


def _validar_columnas(tabla):
    """Verifica que la tabla contenga los campos usados por el mapa."""

    faltantes = COLUMNAS_REQUERIDAS.difference(
        tabla.columns
    )

    if faltantes:
        columnas = ", ".join(
            sorted(faltantes)
        )

        raise ValueError(
            "No es posible construir el mapa porque "
            f"faltan las columnas: {columnas}."
        )


def _unir_valores_unicos(serie):
    """Combina valores únicos respetando su orden de aparición."""

    valores = []

    for valor in serie.dropna():
        texto = str(valor).strip()

        if texto and texto not in valores:
            valores.append(texto)

    return " · ".join(valores)


def _preparar_sedes_para_mapa(tabla):
    """Consolida la oferta a una sola fila por sede georreferenciada.

    Una sede puede registrar varios servicios quirúrgicos. En lugar de
    dibujar varios puntos exactamente en las mismas coordenadas, esta
    función agrupa los códigos y nombres de servicio en una sola fila.
    """

    _validar_columnas(tabla)

    coordenadas_validas = (
        tabla["coordenada_valida"]
        .fillna(False)
        .astype(bool)
    )

    servicios_quirurgicos = (
        tabla["es_quirurgico"]
        .fillna(False)
        .astype(bool)
    )

    registros_validos = tabla.loc[
        coordenadas_validas
        & servicios_quirurgicos
        & tabla["latitud"].notna()
        & tabla["longitud"].notna()
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


def crear_mapa_oferta_quirurgica(tabla):
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
        hover_name="sede",
        custom_data=[
            "direccion",
            "naturaleza",
            "tipo_prestador",
            "codigos_servicio",
            "servicios",
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
        marker={
            "size": 11,
            "opacity": 0.82,
        },
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Dirección: %{customdata[0]}<br>"
            "Naturaleza jurídica: %{customdata[1]}<br>"
            "Tipo de prestador: %{customdata[2]}<br>"
            "Códigos de servicio: %{customdata[3]}<br>"
            "Servicios: %{customdata[4]}"
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
            "font": {
                "family": (
                    "Segoe UI, Arial, sans-serif"
                ),
                "size": 13,
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