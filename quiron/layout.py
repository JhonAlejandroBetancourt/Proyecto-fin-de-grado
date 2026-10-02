from dash import html


def _encabezado() -> html.Div:
    return html.Div(
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


def _hoja_de_ruta() -> html.Div:
    pendientes = [
        "Conexión a la fuente de datos y primeras cifras",
        "Mapa georreferenciado de sedes",
        "Filtros por localidad, servicio y naturaleza jurídica",
    ]
    return html.Div(
        className="tarjeta-ruta",
        children=[
            html.H3("En construcción"),
            html.P("Esta entrega deja lista la base del proyecto: estructura, estilos e identidad."),
            html.Ul([html.Li(item) for item in pendientes]),
        ],
    )


def build_layout() -> html.Div:
    return html.Div(
        className="lienzo",
        children=[
            _encabezado(),
            _hoja_de_ruta(),
            html.Footer("Quirón · Proyecto académico, Fundación Universitaria Compensar", className="pie"),
        ],
    )