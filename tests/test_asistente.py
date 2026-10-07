"""Pruebas del intérprete seguro de comandos de voz."""

import json
from io import BytesIO
from urllib.error import HTTPError, URLError

import pandas as pd
import pytest

from quiron.asistente import (
    ErrorAsistente,
    buscar_sede_mencionada,
    buscar_sede_unica,
    interpretar_solicitud,
    solicita_descarga_detalle,
    validar_comando,
)


@pytest.fixture
def opciones_filtros():
    return {
        "servicios": [
            {
                "label": "CIRUGÍA PLÁSTICA Y ESTÉTICA",
                "value": "369",
            },
        ],
        "naturalezas": [
            {
                "label": "Pública",
                "value": "Pública",
            },
            {
                "label": "Privada",
                "value": "Privada",
            },
        ],
        "tipos_prestador": [
            {
                "label": "IPS",
                "value": "IPS",
            },
        ],
    }


def _comando_base():
    return {
        "understood": True,
        "clear_filters": False,
        "change_services": False,
        "services": [],
        "change_nature": True,
        "nature": ["publica"],
        "change_providers": False,
        "providers": [],
        "change_name_search": False,
        "name_search": "",
        "focus_sede": "",
        "download_detail": False,
    }


def test_validar_comando_usa_valores_de_filtro_canonicos(
    opciones_filtros,
):
    comando = validar_comando(
        _comando_base(),
        opciones_filtros,
    )

    assert comando["nature"] == ["Pública"]
    assert comando["change_nature"] is True


def test_etiqueta_duplicada_selecciona_todos_los_codigos(
    opciones_filtros,
):
    opciones_filtros["servicios"].append(
        {
            "label": "CIRUGÍA PLÁSTICA Y ESTÉTICA",
            "value": "213",
        }
    )
    comando = _comando_base()
    comando["change_services"] = True
    comando["services"] = [
        "CIRUGÍA PLÁSTICA Y ESTÉTICA",
    ]

    resultado = validar_comando(
        comando,
        opciones_filtros,
    )

    assert resultado["services"] == ["369", "213"]


def test_validar_comando_rechaza_opciones_inventadas(
    opciones_filtros,
):
    comando = _comando_base()
    comando["nature"] = ["No existe"]

    with pytest.raises(
        ErrorAsistente,
        match="No reconocí una opción válida",
    ):
        validar_comando(
            comando,
            opciones_filtros,
        )


def test_solicitud_sin_api_key_muestra_como_configurarla(
    monkeypatch,
    opciones_filtros,
):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(
        "quiron.asistente.load_dotenv",
        lambda: None,
    )

    with pytest.raises(
        ErrorAsistente,
        match="GEMINI_API_KEY",
    ):
        interpretar_solicitud(
            "filtra las sedes públicas",
            opciones_filtros,
        )


def test_interpretar_solicitud_valida_respuesta_de_gemini_simulada(
    monkeypatch,
    opciones_filtros,
):
    solicitudes = []

    def responder_con_gemini(solicitud, timeout):
        solicitudes.append(
            json.loads(solicitud.data.decode("utf-8"))
        )
        return BytesIO(
            json.dumps(respuesta_gemini).encode("utf-8")
        )

    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(
        "quiron.asistente.load_dotenv",
        lambda: None,
    )
    respuesta_gemini = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(_comando_base()),
                        },
                    ],
                },
            },
        ],
    }
    monkeypatch.setattr(
        "quiron.asistente.urlopen",
        responder_con_gemini,
    )

    comando = interpretar_solicitud(
        "filtra las sedes públicas",
        opciones_filtros,
    )

    assert comando["nature"] == ["Pública"]
    assert comando["change_nature"] is True
    assert solicitudes[0]["generationConfig"]["thinkingConfig"] == {
        "thinkingLevel": "LOW",
    }


def test_interpretar_solicitud_informa_cuota_y_tiempo_de_renovacion(
    monkeypatch,
    opciones_filtros,
):
    respuesta_error = json.dumps(
        {
            "error": {
                "message": (
                    "Quota exceeded. Please retry in 20h5m46s."
                ),
            },
        }
    ).encode("utf-8")

    def responder_con_cuota_agotada(solicitud, timeout):
        raise HTTPError(
            solicitud.full_url,
            429,
            "Too Many Requests",
            {},
            BytesIO(respuesta_error),
        )

    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(
        "quiron.asistente.load_dotenv",
        lambda: None,
    )
    monkeypatch.setattr(
        "quiron.asistente.urlopen",
        responder_con_cuota_agotada,
    )

    with pytest.raises(
        ErrorAsistente,
        match="20h5m46s",
    ):
        interpretar_solicitud(
            "filtra las sedes públicas",
            opciones_filtros,
        )


def test_interpretar_solicitud_informa_si_gemini_supera_el_tiempo_de_espera(
    monkeypatch,
    opciones_filtros,
):
    def agotar_tiempo_espera(solicitud, timeout):
        raise URLError(
            TimeoutError("timed out")
        )

    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(
        "quiron.asistente.load_dotenv",
        lambda: None,
    )
    monkeypatch.setattr(
        "quiron.asistente.urlopen",
        agotar_tiempo_espera,
    )

    with pytest.raises(
        ErrorAsistente,
        match="tardó más de 30 segundos",
    ):
        interpretar_solicitud(
            "filtra las sedes públicas",
            opciones_filtros,
        )


def test_validar_comando_rechaza_instrucciones_incompletas(
    opciones_filtros,
):
    comando = _comando_base()
    del comando["understood"]

    with pytest.raises(
        ErrorAsistente,
        match="incompleta",
    ):
        validar_comando(
            comando,
            opciones_filtros,
        )


def test_validar_comando_rechaza_limpiar_y_enfocar_a_la_vez(
    opciones_filtros,
):
    comando = _comando_base()
    comando["clear_filters"] = True
    comando["focus_sede"] = "Clínica del Norte"

    with pytest.raises(
        ErrorAsistente,
        match="acciones incompatibles",
    ):
        validar_comando(
            comando,
            opciones_filtros,
        )


def test_validar_comando_permite_descargar_con_cambio_de_filtros(
    opciones_filtros,
):
    comando = _comando_base()
    comando["download_detail"] = True
    comando["change_nature"] = True

    resultado = validar_comando(
        comando,
        opciones_filtros,
    )

    assert resultado["download_detail"] is True


@pytest.mark.parametrize(
    "solicitud",
    [
        "Descarga el detalle filtrado",
        "Descargar el detalle filtrado, por favor",
        "Exporta el detalle",
        "Descarga los resultados",
    ],
)
def test_solicita_descarga_detalle_detecta_ordenes_directas(
    solicitud,
):
    assert solicita_descarga_detalle(solicitud) is True


def test_solicita_descarga_detalle_no_se_activa_por_mencion():
    assert solicita_descarga_detalle(
        "¿Dónde puedo descargar el detalle?"
    ) is False


@pytest.fixture
def tabla_sedes():
    return pd.DataFrame(
        [
            {
                "sede_id": "1",
                "sede": "Clínica del Norte",
                "coordenada_valida": True,
                "latitud": 4.7,
                "longitud": -74.0,
            },
            {
                "sede_id": "1",
                "sede": "Clínica del Norte",
                "coordenada_valida": True,
                "latitud": 4.7,
                "longitud": -74.0,
            },
            {
                "sede_id": "2",
                "sede": "Clínica del Norte Sede 2",
                "coordenada_valida": True,
                "latitud": 4.8,
                "longitud": -74.1,
            },
            {
                "sede_id": "3",
                "sede": "Hospital Central",
                "coordenada_valida": False,
                "latitud": None,
                "longitud": None,
            },
        ]
    )


def test_buscar_sede_usa_nombre_sin_tildes_y_una_fila_por_sede(
    tabla_sedes,
):
    sede, error = buscar_sede_unica(
        tabla_sedes,
        "clinica del norte",
    )

    assert error is None
    assert sede["sede_id"] == "1"
    assert sede["latitud"] == 4.7


def test_buscar_sede_rechaza_nombres_ambiguos(
    tabla_sedes,
):
    sede, error = buscar_sede_unica(
        tabla_sedes,
        "Norte",
    )

    assert sede is None
    assert "varias sedes" in error


def test_buscar_sede_rechaza_sedes_sin_coordenadas(
    tabla_sedes,
):
    sede, error = buscar_sede_unica(
        tabla_sedes,
        "Hospital Central",
    )

    assert sede is None
    assert "No encontré" in error


def test_buscar_sede_mencionada_resuelve_orden_de_mapa_localmente(
    tabla_sedes,
):
    tabla_sedes.loc[
        tabla_sedes["sede_id"].eq("1"),
        "sede",
    ] = "Unidad de Servicios de Salud Simón Bolívar"
    tabla_sedes.loc[
        tabla_sedes["sede_id"].eq("2"),
        "sede",
    ] = "Clínica Simón Bolívar Sede 2"

    sede = buscar_sede_mencionada(
        tabla_sedes,
        (
            "Muéstrame la unidad de servicios de salud "
            "Simon Bolivar en el mapa."
        ),
    )

    assert sede is not None
    assert sede["sede_id"] == "1"


def test_buscar_sede_mencionada_no_interpreta_menciones_sin_intencion_de_mapa(
    tabla_sedes,
):
    sede = buscar_sede_mencionada(
        tabla_sedes,
        "La Clínica del Norte ofrece cirugía.",
    )

    assert sede is None
