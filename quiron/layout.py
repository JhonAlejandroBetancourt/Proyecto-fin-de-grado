"""Estructura visual principal del dashboard Quirón.

Este módulo define la composición de la interfaz y los identificadores
que utilizarán los callbacks. No lee archivos, no filtra datos y no
calcula indicadores.

Los datos iniciales, las opciones de filtro y la figura del mapa llegan
desde ``server.py``. Las actualizaciones posteriores serán realizadas
por ``callbacks.py``.
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


def _formatear_numero(valor):
    """Formatea números enteros utilizando punto de miles."""

    return (
        "{:,}"
        .format(int(valor))
        .replace(",", ".")
    )


def _encabezado():
    """Construye el encabezado institucional."""

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
                (
                    "Radar de oferta quirúrgica "
                    "de las IPS de Bogotá D.C."
                ),
                className="subtitulo",
            ),
            html.Span(
                (
                    "Fundación Universitaria "
                    "Compensar"
                ),
                className="chip-marca",
            ),
        ],
    )


def _campo_filtro(
    etiqueta,
    control,
    ayuda=None,
):
    """Construye un campo individual del panel de filtros."""

    contenido = [
        html.Label(
            etiqueta,
            className="filtro-etiqueta",
        ),
        control,
    ]

    if ayuda:
        contenido.append(
            html.Small(
                ayuda,
                className="filtro-ayuda",
            )
        )

    return html.Div(
        className="campo-filtro",
        children=contenido,
    )


def _panel_filtros(
    opciones_filtros,
):
    """Construye el panel de exploración interactiva."""

    return html.Section(
        className="panel-filtros",
        **{
            "aria-labelledby": (
                "titulo-filtros"
            ),
        },
        children=[
            html.Div(
                className="encabezado-filtros",
                children=[
                    html.Div(
                        children=[
                            html.H2(
                                "Explorar la oferta",
                                id="titulo-filtros",
                            ),
                            html.P(
                                (
                                    "Combina uno o varios "
                                    "criterios para actualizar "
                                    "los indicadores, el mapa "
                                    "y las tablas."
                                ),
                                className=(
                                    "descripcion-seccion"
                                ),
                            ),
                        ],
                    ),
                    html.Button(
                        "Limpiar filtros",
                        id=(
                            "boton-limpiar-filtros"
                        ),
                        n_clicks=0,
                        type="button",
                        className=(
                            "boton-limpiar-filtros"
                        ),
                    ),
                ],
            ),
            html.Div(
                className="rejilla-filtros",
                children=[
                    _campo_filtro(
                        "Servicio quirúrgico",
                        dcc.Dropdown(
                            id=(
                                "filtro-servicio"
                            ),
                            options=(
                                opciones_filtros[
                                    "servicios"
                                ]
                            ),
                            value=[],
                            multi=True,
                            clearable=True,
                            searchable=True,
                            placeholder=(
                                "Selecciona uno o "
                                "varios servicios"
                            ),
                            className=(
                                "control-filtro"
                            ),
                        ),
                    ),
                    _campo_filtro(
                        "Naturaleza jurídica",
                        dcc.Dropdown(
                            id=(
                                "filtro-naturaleza"
                            ),
                            options=(
                                opciones_filtros[
                                    "naturalezas"
                                ]
                            ),
                            value=[],
                            multi=True,
                            clearable=True,
                            searchable=True,
                            placeholder=(
                                "Selecciona una "
                                "naturaleza"
                            ),
                            className=(
                                "control-filtro"
                            ),
                        ),
                    ),
                    _campo_filtro(
                        "Tipo de prestador",
                        dcc.Dropdown(
                            id=(
                                "filtro-tipo-prestador"
                            ),
                            options=(
                                opciones_filtros[
                                    "tipos_prestador"
                                ]
                            ),
                            value=[],
                            multi=True,
                            clearable=True,
                            searchable=True,
                            placeholder=(
                                "Selecciona un tipo "
                                "de prestador"
                            ),
                            className=(
                                "control-filtro"
                            ),
                        ),
                    ),
                    _campo_filtro(
                        "Buscar sede",
                        dcc.Input(
                            id=(
                                "filtro-texto-sede"
                            ),
                            type="search",
                            value="",
                            debounce=True,
                            placeholder=(
                                "Ej. clínica, hospital "
                                "o IPS"
                            ),
                            autoComplete="off",
                            className=(
                                "entrada-filtro"
                            ),
                        ),
                        ayuda=(
                            "La búsqueda no distingue "
                            "mayúsculas ni tildes."
                        ),
                    ),
                ],
            ),
            html.Div(
                id="estado-filtros",
                className="estado-filtros",
                children=(
                    "Mostrando toda la oferta "
                    "quirúrgica registrada."
                ),
                **{
                    "aria-live": "polite",
                },
            ),
        ],
    )


def _tarjeta_kpi(
    icono,
    valor,
    etiqueta,
    identificador,
):
    """Construye una tarjeta de indicador actualizable."""

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
                _formatear_numero(
                    valor
                ),
                id=identificador,
                className="kpi-valor",
            ),
            html.Span(
                etiqueta,
                className="kpi-etiqueta",
            ),
        ],
    )


def _panel_kpis(
    resumen,
):
    """Agrupa los cinco indicadores principales."""

    return html.Section(
        className="panel-kpis",
        **{
            "aria-label": (
                "Indicadores generales"
            ),
        },
        children=[
            _tarjeta_kpi(
                "🏥",
                resumen[
                    "sedes_totales"
                ],
                (
                    "Sedes registradas "
                    "en la fuente"
                ),
                "kpi-sedes-totales",
            ),
            _tarjeta_kpi(
                "⚕",
                resumen[
                    "sedes_con_oferta_quirurgica"
                ],
                (
                    "Sedes con oferta "
                    "quirúrgica"
                ),
                "kpi-sedes-oferta",
            ),
            _tarjeta_kpi(
                "▤",
                resumen[
                    "tipos_de_servicio_quirurgico"
                ],
                (
                    "Códigos de habilitación "
                    "distintos"
                ),
                "kpi-tipos-servicio",
            ),
            _tarjeta_kpi(
                "🏛",
                resumen[
                    "sedes_publicas"
                ],
                (
                    "Sedes de naturaleza "
                    "pública"
                ),
                "kpi-sedes-publicas",
            ),
            _tarjeta_kpi(
                "▥",
                resumen[
                    "sedes_privadas"
                ],
                (
                    "Sedes de naturaleza "
                    "privada"
                ),
                "kpi-sedes-privadas",
            ),
        ],
    )


def _crear_columnas(
    tabla,
):
    """Convierte las columnas del DataFrame al formato DataTable."""

    columnas = []

    for nombre in tabla.columns:
        etiqueta = (
            nombre
            .replace("_", " ")
            .title()
        )

        columnas.append(
            {
                "name": etiqueta,
                "id": nombre,
            }
        )

    return columnas


def _tabla(
    titulo,
    tabla,
    identificador,
):
    """Construye una tabla actualizable por callback."""

    return html.Article(
        className="tarjeta-tabla",
        children=[
            html.H3(titulo),
            dash_table.DataTable(
                id=identificador,
                data=tabla.to_dict(
                    "records"
                ),
                columns=_crear_columnas(
                    tabla
                ),
                style_as_list_view=True,
                page_action="none",
                style_table={
                    "overflowX": "auto",
                },
                style_header={
                    "backgroundColor": (
                        "#330968"
                    ),
                    "color": "#FFFFFF",
                    "fontWeight": "600",
                    "textAlign": "left",
                    "border": "none",
                },
                style_cell={
                    "padding": "10px 12px",
                    "fontFamily": (
                        "Segoe UI, Arial, "
                        "sans-serif"
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
                    "backgroundColor": (
                        "#FFFFFF"
                    ),
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


def _dato_mapa(
    valor,
    etiqueta,
    identificador,
):
    """Construye un indicador de cobertura geográfica."""

    return html.Div(
        className="dato-mapa",
        children=[
            html.Span(
                str(valor),
                id=identificador,
                className=(
                    "dato-mapa-valor"
                ),
            ),
            html.Span(
                etiqueta,
                className=(
                    "dato-mapa-etiqueta"
                ),
            ),
        ],
    )


def _resumen_cobertura_mapa(
    sedes_geocodificadas,
    sedes_sin_coordenadas,
):
    """Construye el resumen inicial de cobertura del mapa."""

    total = (
        sedes_geocodificadas
        + sedes_sin_coordenadas
    )

    porcentaje = (
        sedes_geocodificadas
        / total
        * 100
    ) if total else 0

    return html.Div(
        className="resumen-mapa",
        children=[
            _dato_mapa(
                sedes_geocodificadas,
                "Sedes visibles",
                "mapa-sedes-visibles",
            ),
            _dato_mapa(
                sedes_sin_coordenadas,
                "Sedes sin coordenadas",
                (
                    "mapa-sedes-"
                    "sin-coordenadas"
                ),
            ),
            _dato_mapa(
                f"{porcentaje:.1f} %",
                "Cobertura geográfica",
                "mapa-cobertura",
            ),
        ],
    )


def _seccion_mapa(
    figura_mapa,
    sedes_geocodificadas,
    sedes_sin_coordenadas,
):
    """Integra la figura cartográfica en la interfaz."""

    return html.Section(
        className="seccion-mapa",
        **{
            "aria-labelledby": (
                "titulo-mapa"
            ),
        },
        children=[
            html.Div(
                className=(
                    "encabezado-seccion"
                ),
                children=[
                    html.Div(
                        children=[
                            html.H2(
                                (
                                    "Distribución "
                                    "geográfica "
                                    "de la oferta"
                                ),
                                id="titulo-mapa",
                            ),
                            html.P(
                                (
                                    "Cada punto representa "
                                    "una sede con oferta "
                                    "quirúrgica y coordenadas "
                                    "verificadas."
                                ),
                                className=(
                                    "descripcion-seccion"
                                ),
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
                        id=(
                            "mapa-oferta-"
                            "quirurgica"
                        ),
                        figure=figura_mapa,
                        config=(
                            CONFIGURACION_GRAFICO
                        ),
                        responsive=True,
                        className=(
                            "mapa-principal"
                        ),
                        style={
                            "width": "100%",
                            "height": "620px",
                        },
                    ),
                ],
            ),
            html.P(
                (
                    "Las sedes sin coordenadas válidas "
                    "se conservan en el conjunto "
                    "analítico, pero no se ubican "
                    "artificialmente en el mapa."
                ),
                className=(
                    "nota-metodologica"
                ),
            ),
        ],
    )


def _seccion_tablas(
    por_servicio,
    por_naturaleza,
):
    """Agrupa las tablas descriptivas actualizables."""

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
                        (
                            "tabla-por-"
                            "servicio"
                        ),
                    ),
                    _tabla(
                        (
                            "Sedes por naturaleza "
                            "jurídica"
                        ),
                        por_naturaleza,
                        (
                            "tabla-por-"
                            "naturaleza"
                        ),
                    ),
                ],
            ),
        ],
    )


def _pie_de_pagina():
    """Construye el pie institucional."""

    return html.Footer(
        className="pie",
        children=(
            "Quirón · Proyecto de grado · "
            "Fundación Universitaria Compensar"
        ),
    )


def build_layout(
    resumen,
    por_servicio,
    por_naturaleza,
    figura_mapa,
    sedes_geocodificadas,
    sedes_sin_coordenadas,
    opciones_filtros,
):
    """Construye la interfaz completa del dashboard."""

    return html.Div(
        className="lienzo",
        children=[
            _encabezado(),
            html.Main(
                children=[
                    _panel_filtros(
                        opciones_filtros
                    ),
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