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


def test_mapa_fuente_con_huella_diferente_conserva_las_coordenadas():
    """Un cambio de bytes no debe dejar vacío el mapa."""

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

    puntos = sum(
        len(traza.lat)
        for traza in figura.data
    )
    sedes_geocodificadas = (
        ejecutar_etl()
        .tabla.drop_duplicates(
            subset=["sede_id"]
        )["coordenada_valida"]
        .sum()
    )

    assert puntos == sedes_geocodificadas
    assert puntos > 0
    assert not figura.layout.annotations


def test_mapa_sin_coincidencias_explica_el_motivo():
    """Un CSV con sedes nuevas explica el criterio de asociación segura."""

    contenido = (
        "SEDE -NOMBRE;DIRECCION;TELEFONO;"
        "CORREO ELECTRÓNICO;NATURALEZA;"
        "TIPO DE PRESTADOR;"
        "213 - CIRUGÍA PLÁSTICA\n"
        "Clínica Nueva;Dirección nueva;123;"
        "nueva@example.com;Privada;IPS;X\n"
    ).encode("utf-8")
    resultado = ejecutar_etl(
        origen=contenido,
        nombre_fuente="sedes-nuevas.csv",
    )
    figura = crear_mapa_oferta_quirurgica(
        resultado.tabla
    )

    mensaje = figura.layout.annotations[0].text

    assert "coinciden de forma única" in mensaje
    assert "Verifica esos campos" in mensaje
    assert "coincidencias ambiguas no se muestran" in mensaje
