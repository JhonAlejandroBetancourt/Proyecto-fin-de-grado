"""Estructura visual principal del dashboard Quirón.

Este módulo define únicamente la composición de la interfaz. No lee
archivos, no calcula indicadores y no construye figuras de Plotly.

Los datos, indicadores y visualizaciones se reciben como argumentos
desde server.py. Esta separación evita mezclar presentación, acceso a
datos y lógica analítica.
"""

from dash import dash_table, dcc, html


CONFIGURACION_GRAFICO = {
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": True,
    "modeBarButtonsToRemove": [
        "lasso2d",
        "select2d",
    ],
}


def _encabezado():
    """Construye el encabezado institucional del dashboard."""

    return html.Header(
        className="encabezado",
        children=[
            html.Span(
                "⚕",
                className="emblema",
                **{
                    "aria-hidden": "true",
                },
            ),
            html.H1("Quirón"),
            html.P(
                "Radar de oferta quirúrgica de las IPS de Bogotá D.C.",
                className="subtitulo",
            ),
            html.Span(
                "Fundación Universitaria Compensar",
                className="chip-marca",
            ),
        ],
    )


def _tarjeta_kpi(
    icono,
    valor,
    etiqueta,
):
    """Construye una tarjeta de indicador."""

    valor_formateado = (
        "{:,}"
        .format(valor)
        .replace(",", ".")
    )

    return html.Article(
        className="kpi",
        children=[
            html.Span(
                icono,
                className="kpi-icono",
                **{
                    "aria-hidden": "true",
                },
            ),
            html.Span(
                valor_formateado,
                className="kpi-valor",
            ),
            html.Span(
                etiqueta,
                className="kpi-etiqueta",
            ),
        ],
    )


def _panel_kpis(resumen):
    """Agrupa los indicadores principales."""

    return html.Section(
        className="panel-kpis",
        **{
            "aria-label": "Indicadores generales",
        },
        children=[
            _tarjeta_kpi(
                "🏥",
                resumen["sedes_totales"],
                "Sedes registradas en la fuente",
            ),
            _tarjeta_kpi(
                "⚕",
                resumen["sedes_con_oferta_quirurgica"],
                "Sedes con oferta quirúrgica",
            ),
            _tarjeta_kpi(
                "▤",
                resumen["tipos_de_servicio_quirurgico"],
                "Códigos de habilitación distintos",
            ),
            _tarjeta_kpi(
                "🏛",
                resumen["sedes_publicas"],
                "Sedes de naturaleza pública",
            ),
            _tarjeta_kpi(
                "▥",
                resumen["sedes_privadas"],
                "Sedes de naturaleza privada",
            ),
        ],
    )


def _tabla(
    titulo,
    tabla,
):
    """Construye una tabla visual de resultados."""

    columnas = []

    for nombre_columna in tabla.columns:
        etiqueta = (
            nombre_columna
            .replace("_", " ")
            .title()
        )

        columnas.append(
            {
                "name": etiqueta,
                "id": nombre_columna,
            }
        )

    return html.Article(
        className="tarjeta-tabla",
        children=[
            html.H3(titulo),
            dash_table.DataTable(
                data=tabla.to_dict(
                    "records"
                ),
                columns=columnas,
                style_as_list_view=True,
                page_action="none",
                style_table={
                    "overflowX": "auto",
                },
                style_header={
                    "backgroundColor": "#330968",
                    "color": "#FFFFFF",
                    "fontWeight": "600",
                    "textAlign": "left",
                    "border": "none",
                },
                style_cell={
                    "padding": "10px 12px",
                    "fontFamily": (
                        "Segoe UI, Arial, sans-serif"
                    ),
                    "fontSize": "14px",
                    "textAlign": "left",
                    "whiteSpace": "normal",
                    "height": "auto",
                    "border": "none",
                    "borderBottom": (
                        "1px solid #E4DEF2"
                    ),
                },
                style_data={
                    "backgroundColor": "#FFFFFF",
                    "color": "#231942",
                },
                style_data_conditional=[
                    {
                        "if": {
                            "row_index": "odd",
                        },
                        "backgroundColor": (
                            "#F5F3FA"
                        ),
                    },
                ],
            ),
        ],
    )


def _resumen_cobertura_mapa(
    sedes_geocodificadas,
    sedes_sin_coordenadas,
):
    """Presenta la cobertura alcanzada por la geocodificación."""

    total = (
        sedes_geocodificadas
        + sedes_sin_coordenadas
    )

    if total:
        porcentaje = (
            sedes_geocodificadas
            / total
            * 100
        )
    else:
        porcentaje = 0

    return html.Div(
        className="resumen-mapa",
        children=[
            html.Div(
                className="dato-mapa",
                children=[
                    html.Span(
                        str(
                            sedes_geocodificadas
                        ),
                        className="dato-mapa-valor",
                    ),
                    html.Span(
                        "Sedes visibles",
                        className="dato-mapa-etiqueta",
                    ),
                ],
            ),
            html.Div(
                className="dato-mapa",
                children=[
                    html.Span(
                        str(
                            sedes_sin_coordenadas
                        ),
                        className="dato-mapa-valor",
                    ),
                    html.Span(
                        "Sedes sin coordenadas",
                        className="dato-mapa-etiqueta",
                    ),
                ],
            ),
            html.Div(
                className="dato-mapa",
                children=[
                    html.Span(
                        f"{porcentaje:.1f} %",
                        className="dato-mapa-valor",
                    ),
                    html.Span(
                        "Cobertura geográfica",
                        className="dato-mapa-etiqueta",
                    ),
                ],
            ),
        ],
    )


def _seccion_mapa(
    figura_mapa,
    sedes_geocodificadas,
    sedes_sin_coordenadas,
):
    """Integra la figura de Plotly dentro del dashboard."""

    return html.Section(
        className="seccion-mapa",
        **{
            "aria-labelledby": "titulo-mapa",
        },
        children=[
            html.Div(
                className="encabezado-seccion",
                children=[
                    html.Div(
                        children=[
                            html.H2(
                                "Distribución geográfica de la oferta",
                                id="titulo-mapa",
                            ),
                            html.P(
                                (
                                    "Cada punto representa una sede con "
                                    "oferta quirúrgica y coordenadas "
                                    "verificadas."
                                ),
                                className="descripcion-seccion",
                            ),
                        ],
                    ),
                    _resumen_cobertura_mapa(
                        sedes_geocodificadas,
                        sedes_sin_coordenadas,
                    ),
                ],
            ),
            dcc.Loading(
                type="circle",
                color="#6E48B1",
                children=[
                    dcc.Graph(
                        id="mapa-oferta-quirurgica",
                        figure=figura_mapa,
                        config=CONFIGURACION_GRAFICO,
                        responsive=True,
                        className="mapa-principal",
                        style={
                            "width": "100%",
                            "height": "620px",
                        },
                    ),
                ],
            ),
            html.P(
                (
                    "Las sedes sin coordenadas válidas se conservan "
                    "en el conjunto analítico, pero no se ubican "
                    "artificialmente en el mapa."
                ),
                className="nota-metodologica",
            ),
        ],
    )


def _seccion_tablas(
    por_servicio,
    por_naturaleza,
):
    """Agrupa las tablas descriptivas del dashboard."""

    return html.Section(
        className="seccion-tablas",
        **{
            "aria-label": (
                "Tablas descriptivas"
            ),
        },
        children=[
            html.Div(
                className="fila-tablas",
                children=[
                    _tabla(
                        (
                            "Sedes por código "
                            "de habilitación"
                        ),
                        por_servicio,
                    ),
                    _tabla(
                        (
                            "Sedes por naturaleza "
                            "jurídica"
                        ),
                        por_naturaleza,
                    ),
                ],
            ),
        ],
    )


def _pie_de_pagina():
    """Construye el pie institucional."""

    return html.Footer(
        className="pie",
        children=[
            html.Span(
                (
                    "Quirón · Proyecto de grado · "
                    "Fundación Universitaria Compensar"
                )
            ),
        ],
    )


def build_layout(
    resumen,
    por_servicio,
    por_naturaleza,
    figura_mapa,
    sedes_geocodificadas,
    sedes_sin_coordenadas,
):
    """Construye la interfaz completa del dashboard."""

    return html.Div(
        className="lienzo",
        children=[
            _encabezado(),
            html.Main(
                children=[
                    _panel_kpis(
                        resumen
                    ),
                    _seccion_mapa(
                        figura_mapa,
                        sedes_geocodificadas,
                        sedes_sin_coordenadas,
                    ),
                    _seccion_tablas(
                        por_servicio,
                        por_naturaleza,
                    ),
                ],
            ),
            _pie_de_pagina(),
        ],
    )