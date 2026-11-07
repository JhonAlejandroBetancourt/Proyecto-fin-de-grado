"""Pruebas del mapa de oferta quirúrgica."""

from quiron.data.loader import ARCHIVO_CIRUGIA_PLASTICA
from quiron.etl.pipeline import ejecutar_etl
from quiron.visualizaciones.mapa import (
    crear_mapa_oferta_quirurgica,
)


def test_mapa_fuente_original_muestra_sedes_geocodificadas():
    """La fuente incluida debe producir puntos en el mapa."""

    resultado = ejecutar_etl()
    figura = crear_mapa_oferta_quirurgica(
        resultado.tabla
    )

    puntos = sum(
        len(traza.lat)
        for traza in figura.data
    )
    sedes_esperadas = resultado.tabla.loc[
        resultado.tabla["es_quirurgico"]
        & resultado.tabla["coordenada_valida"],
        "sede_id",
    ].nunique()

    assert puntos == sedes_esperadas
    assert puntos > 0
    assert not figura.layout.annotations


def test_mapa_csv_alternativo_explica_por_que_no_hay_coordenadas():
    """Un CSV distinto no debe señalar como defectuoso el archivo geocodificado."""

    contenido = (
        ARCHIVO_CIRUGIA_PLASTICA.read_bytes()
        + b"\n"
    )
    resultado = ejecutar_etl(
        origen=contenido,
        nombre_fuente="alterno.csv",
    )
    figura = crear_mapa_oferta_quirurgica(
        resultado.tabla
    )

    mensaje = figura.layout.annotations[0].text

    assert "CSV distinto a la fuente original" in mensaje
    assert "no reutiliza las coordenadas del proyecto" in mensaje
    assert "si ya está activo, revisa" in mensaje
