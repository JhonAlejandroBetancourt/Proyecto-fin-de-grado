from dash import dash_table, html


def _encabezado():
    encabezado = html.Div(
        className="encabezado",
        children=[
            html.Span("⚕", className="emblema"),
            html.H1("Quirón"),
            html.P(
                "Radar de oferta quirúrgica de las IPS de Bogotá D.C.",
                className="subtitulo",
            ),
            html.Span("Fundación Universitaria Compensar", className="chip-marca"),
        ],
    )
    return encabezado


def _tarjeta_kpi(icono, valor, etiqueta):
    valor_formateado = "{:,}".format(valor).replace(",", ".")
    tarjeta = html.Div(
        className="kpi",
        children=[
            html.Span(icono, className="kpi-icono"),
            html.Span(valor_formateado, className="kpi-valor"),
            html.Span(etiqueta, className="kpi-etiqueta"),
        ],
    )
    return tarjeta


def _panel_kpis(resumen):
    panel = html.Div(
        className="panel-kpis",
        children=[
            _tarjeta_kpi("🏥", resumen["sedes_totales"], "Sedes registradas en la fuente"),
            _tarjeta_kpi("⚕️", resumen["sedes_con_oferta_quirurgica"], "Sedes con oferta quirúrgica"),
            _tarjeta_kpi("🧾", resumen["tipos_de_servicio_quirurgico"], "Códigos de habilitación distintos"),
            _tarjeta_kpi("🏛️", resumen["sedes_publicas"], "Sedes de naturaleza pública"),
            _tarjeta_kpi("🏢", resumen["sedes_privadas"], "Sedes de naturaleza privada"),
        ],
    )
    return panel


def _tabla(titulo, df):
    columnas = []
    for nombre_columna in df.columns:
        etiqueta = nombre_columna.replace("_", " ").title()
        columnas.append({"name": etiqueta, "id": nombre_columna})

    tabla_html = html.Div(
        className="tarjeta-tabla",
        children=[
            html.H3(titulo),
            dash_table.DataTable(
                data=df.to_dict("records"),
                columns=columnas,
                style_as_list_view=True,
                style_header={
                    "backgroundColor": "#330968",
                    "color": "white",
                    "fontWeight": "600",
                    "textAlign": "left",
                },
                style_cell={
                    "padding": "10px 12px",
                    "fontFamily": "Segoe UI, Arial, sans-serif",
                    "fontSize": "14px",
                    "textAlign": "left",
                },
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "#F5F3FA"},
                ],
            ),
        ],
    )
    return tabla_html


def _pie_de_pagina():
    pie = html.Footer(
        "Quirón · Proyecto de grado, Fundación Universitaria Compensar",
        className="pie",
    )
    return pie


def build_layout(resumen, por_servicio, por_naturaleza):
    layout = html.Div(
        className="lienzo",
        children=[
            _encabezado(),
            _panel_kpis(resumen),
            html.Div(
                className="fila-tablas",
                children=[
                    _tabla("Sedes por código de habilitación", por_servicio),
                    _tabla("Sedes por naturaleza jurídica", por_naturaleza),
                ],
            ),
            _pie_de_pagina(),
        ],
    )
    return layout