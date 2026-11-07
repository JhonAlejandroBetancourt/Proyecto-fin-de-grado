"""Integración del panel de carga ETL mediante el endpoint de Dash."""

import base64

import pytest

from quiron.server import create_app


@pytest.fixture(scope="module")
def dash_app():
    """Construye la aplicación completa con sus callbacks registrados."""

    return create_app()


def _callback_response(
    app,
    filename,
    csv_content,
    previous_trace=None,
    previous_dataset=None,
):
    """Envía una carga como lo haría el componente dcc.Upload."""

    callback_key = next(
        key
        for key, callback in app.callback_map.items()
        if any(
            entrada["id"] == "etl-carga-csv"
            and entrada["property"] == "contents"
            for entrada in callback["inputs"]
        )
    )
    outputs = app.callback_map[callback_key]["output"]
    output_specs = [
        {
            "id": output.component_id,
            "property": output.component_property,
        }
        for output in outputs
    ]
    contents = (
        "data:text/csv;base64,"
        + base64.b64encode(csv_content).decode("ascii")
    )

    response = app.server.test_client().post(
        "/_dash-update-component",
        json={
            "output": callback_key,
            "outputs": output_specs,
            "changedPropIds": [
                "etl-carga-csv.contents",
            ],
            "inputs": [
                {
                    "id": "etl-carga-csv",
                    "property": "contents",
                    "value": contents,
                },
            ],
            "state": [
                {
                    "id": "etl-carga-csv",
                    "property": "filename",
                    "value": filename,
                },
                {
                    "id": "etl-traza",
                    "property": "data",
                    "value": previous_trace,
                },
                {
                    "id": "etl-dataset-activo",
                    "property": "data",
                    "value": previous_dataset,
                },
            ],
        },
    )

    assert response.status_code == 200
    return response.get_json()["response"]


def _text_from_component(value):
    """Extrae texto recursivamente de un componente serializado por Dash."""

    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(
            _text_from_component(item)
            for item in value
        )
    if isinstance(value, dict):
        return " ".join(
            _text_from_component(item)
            for item in value.values()
        )
    return ""


def test_upload_valido_y_esquema_invalido_conservan_estado_etl(
    dash_app,
):
    """La carga válida activa el dataset y la inválida conserva el anterior."""

    csv_valido = (
        "SEDE -NOMBRE;DIRECCION;TELEFONO;"
        "CORREO ELECTRÓNICO;NATURALEZA;"
        "TIPO DE PRESTADOR;"
        "213 - CIRUGÍA PLÁSTICA\n"
        "Clínica de Prueba;Calle 1;123;"
        "prueba@example.com;Privada;IPS;X\n"
    ).encode("utf-8")

    respuesta_valida = _callback_response(
        dash_app,
        "oferta-valida.csv",
        csv_valido,
    )

    dataset_activo = respuesta_valida[
        "etl-dataset-activo"
    ]["data"]
    traza_valida = respuesta_valida[
        "etl-traza"
    ]["data"]
    mapeos = respuesta_valida[
        "etl-tabla-mapeo"
    ]["data"]
    historial_valido = respuesta_valida[
        "etl-tabla-historico"
    ]["data"]

    assert len(dataset_activo) == 1
    assert dataset_activo[0]["sede"] == "Clínica de Prueba"
    assert len(mapeos) > 0
    assert any(
        mapeo["campo_destino"] == "sede"
        for mapeo in mapeos
    )
    sedes_sin_coordenadas = respuesta_valida[
        "etl-tabla-sedes-no-mapeadas"
    ]["data"]
    assert len(sedes_sin_coordenadas) == 1
    assert "coincidencia única" in (
        sedes_sin_coordenadas[0][
            "motivo_geocodificacion"
        ]
    )
    assert historial_valido
    assert all(
        paso["ejecucion"] == 1
        for paso in historial_valido
    )
    assert respuesta_valida[
        "etl-panel-errores"
    ]["className"] == "etl-errores etl-oculto"

    respuesta_invalida = _callback_response(
        dash_app,
        "esquema-invalido.csv",
        b"columna_a;columna_b\n1;2\n",
        previous_trace=traza_valida,
        previous_dataset=dataset_activo,
    )

    assert "etl-dataset-activo" not in respuesta_invalida
    assert dataset_activo[0]["sede"] == "Clínica de Prueba"
    assert respuesta_invalida[
        "etl-panel-errores"
    ]["className"] == "etl-errores"
    texto_errores = _text_from_component(
        respuesta_invalida["etl-panel-errores"]["children"]
    )
    assert "obligatorias" in texto_errores

    traza_invalida = respuesta_invalida[
        "etl-traza"
    ]["data"]
    mapeos_invalidos = respuesta_invalida[
        "etl-tabla-mapeo"
    ]["data"]
    historial_invalido = respuesta_invalida[
        "etl-tabla-historico"
    ]["data"]

    assert traza_invalida["errores"]
    assert any(
        mapeo["estado"] == "Faltante"
        for mapeo in mapeos_invalidos
    )
    assert any(
        mapeo["estado"] == "No mapeado"
        for mapeo in mapeos_invalidos
    )
    assert traza_invalida["numero_ejecucion"] == 2
    assert len(historial_invalido) > len(historial_valido)
    assert {paso["ejecucion"] for paso in historial_invalido} == {
        1,
        2,
    }


def test_upload_identico_no_reemplaza_y_cambio_de_direccion_actualiza(
    dash_app,
):
    csv_original = (
        "SEDE -NOMBRE;DIRECCION;TELEFONO;"
        "CORREO ELECTRÓNICO;NATURALEZA;"
        "TIPO DE PRESTADOR;"
        "213 - CIRUGÍA PLÁSTICA\n"
        "Clínica de Prueba;Calle 1;123;"
        "prueba@example.com;Privada;IPS;X\n"
    ).encode("utf-8")

    primera_respuesta = _callback_response(
        dash_app,
        "oferta.csv",
        csv_original,
    )
    dataset = primera_respuesta[
        "etl-dataset-activo"
    ]["data"]
    traza = primera_respuesta[
        "etl-traza"
    ]["data"]

    respuesta_igual = _callback_response(
        dash_app,
        "oferta-igual.csv",
        csv_original,
        previous_trace=traza,
        previous_dataset=dataset,
    )

    assert "etl-dataset-activo" not in respuesta_igual
    assert "No se detectaron cambios" in (
        respuesta_igual["etl-estado"]["children"]
    )
    assert respuesta_igual[
        "etl-tabla-cambios"
    ]["data"] == []

    csv_actualizado = csv_original.replace(
        b"Calle 1",
        b"Carrera 10",
    )
    respuesta_actualizada = _callback_response(
        dash_app,
        "oferta-actualizada.csv",
        csv_actualizado,
        previous_trace=respuesta_igual[
            "etl-traza"
        ]["data"],
        previous_dataset=dataset,
    )

    dataset_actualizado = respuesta_actualizada[
        "etl-dataset-activo"
    ]["data"]
    assert dataset_actualizado[0][
        "direccion"
    ] == "Carrera 10"
    assert respuesta_actualizada[
        "etl-tabla-cambios"
    ]["data"] == [
        {
            "sede": "Clínica de Prueba",
            "campo": "Dirección",
            "valor_anterior": "Calle 1",
            "valor_nuevo": "Carrera 10",
        }
    ]


def test_navegacion_muestra_el_dashboard_o_la_pagina_etl(
    dash_app,
):
    callback_key = next(
        key
        for key, callback in dash_app.callback_map.items()
        if any(
            entrada["id"] == "url"
            and entrada["property"] == "pathname"
            for entrada in callback["inputs"]
        )
    )
    outputs = dash_app.callback_map[
        callback_key
    ]["output"]
    response = dash_app.server.test_client().post(
        "/_dash-update-component",
        json={
            "output": callback_key,
            "outputs": [
                {
                    "id": output.component_id,
                    "property": output.component_property,
                }
                for output in outputs
            ],
            "changedPropIds": ["url.pathname"],
            "inputs": [
                {
                    "id": "url",
                    "property": "pathname",
                    "value": "/etl",
                },
            ],
            "state": [],
        },
    )

    assert response.status_code == 200
    contenido = response.get_json()["response"]
    assert contenido["vista-dashboard"]["className"] == (
        "pagina pagina-oculta"
    )
    assert contenido["vista-etl"]["className"] == "pagina"
    assert contenido["nav-etl"]["className"].endswith(
        "enlace-nav-activo"
    )
