"""Pruebas unitarias de la capa de observabilidad y pipeline ETL.

Esta suite valida:

  - El registro de pasos, mapeos y errores en ``TrazaETL``.
  - La serialización de la traza a estructuras simples.
  - La ejecución correcta del ETL con el archivo incluido.
  - La ejecución del ETL con una fuente en memoria (bytes).
  - El manejo de errores sin interrumpir el flujo.
  - La reproducibilidad de la huella SHA-256.
"""

import hashlib

import pandas as pd
import pytest

from quiron.data.loader import (
    ARCHIVO_CIRUGIA_PLASTICA,
    cargar_cirugia_plastica,
)
from quiron.etl import (
    NivelTraza,
    ResultadoETL,
    TrazaETL,
    ejecutar_etl,
)


def test_traza_registra_pasos_en_orden():
    """Comprueba que los pasos se numeren y acumulen en orden."""

    traza = TrazaETL()

    traza.registrar(
        "Paso uno",
        "mensaje uno",
    )
    traza.registrar(
        "Paso dos",
        "mensaje dos",
        nivel=NivelTraza.EXITO,
    )

    assert len(traza.pasos) == 2
    assert traza.pasos[0].orden == 1
    assert traza.pasos[1].orden == 2
    assert (
        traza.pasos[1].nivel
        is NivelTraza.EXITO
    )


def test_traza_acumula_errores():
    """Comprueba que un paso de error se refleje en la lista de errores."""

    traza = TrazaETL()

    assert traza.tiene_errores is False

    traza.registrar_error(
        "Validación",
        "columna faltante",
    )

    assert traza.tiene_errores is True
    assert len(traza.errores) == 1
    assert (
        traza.errores[0]["paso"]
        == "Validación"
    )


def test_traza_registra_mapeo_campos():
    """Comprueba el registro de mapeos origen → destino."""

    traza = TrazaETL()

    traza.mapear(
        "SEDE -NOMBRE",
        "sede",
        "renombrado",
        filas=10,
    )

    assert len(traza.mapeos) == 1
    mapeo = traza.mapeos[0].como_dict()
    assert mapeo["campo_origen"] == "SEDE -NOMBRE"
    assert mapeo["campo_destino"] == "sede"
    assert mapeo["filas"] == 10


def test_traza_como_dict_es_serializable():
    """Comprueba que la traza se serialice a estructuras simples."""

    traza = TrazaETL()
    traza.registrar("Inicio", "ok")
    traza.mapear("a", "b", "t")

    datos = traza.como_dict()

    assert set(datos) >= {
        "pasos",
        "mapeos",
        "errores",
        "tiene_errores",
        "duracion_total_ms",
    }
    assert isinstance(datos["pasos"], list)
    assert isinstance(datos["mapeos"], list)


def test_ejecutar_etl_con_archivo_incluido():
    """El ETL debe completarse con el archivo del proyecto."""

    resultado = ejecutar_etl()

    assert isinstance(resultado, ResultadoETL)
    assert resultado.exito is True
    assert resultado.tabla is not None
    assert len(resultado.tabla) > 0
    assert resultado.huella_sha256 is not None
    assert len(resultado.huella_sha256) == 64
    assert resultado.traza.tiene_errores is False
    assert len(resultado.traza.mapeos) > 0


def test_ejecutar_etl_huella_reproducible():
    """La huella del ETL debe coincidir con la del contenido del archivo."""

    esperada = hashlib.sha256(
        ARCHIVO_CIRUGIA_PLASTICA.read_bytes()
    ).hexdigest()

    resultado = ejecutar_etl()

    assert resultado.huella_sha256 == esperada


def test_etl_no_reutiliza_coordenadas_para_csv_diferente():
    """Un CSV alterno no debe heredar coordenadas por índice de fila."""

    contenido = (
        ARCHIVO_CIRUGIA_PLASTICA.read_bytes()
        + b"\n"
    )

    resultado = ejecutar_etl(
        origen=contenido,
        nombre_fuente="alterno.csv",
    )

    assert resultado.exito is True
    assert resultado.tabla is not None
    assert resultado.tabla[
        "coordenada_valida"
    ].eq(False).all()
    assert resultado.tabla[
        "latitud"
    ].isna().all()
    assert any(
        paso.nivel is NivelTraza.ADVERTENCIA
        for paso in resultado.traza.pasos
    )


def test_ejecutar_etl_con_bytes_en_memoria():
    """El ETL debe procesar una fuente cargada en memoria."""

    contenido = (
        ARCHIVO_CIRUGIA_PLASTICA.read_bytes()
    )

    resultado = ejecutar_etl(
        origen=contenido,
        nombre_fuente="cargado.csv",
    )

    assert resultado.exito is True
    assert resultado.nombre_fuente == "cargado.csv"
    assert resultado.tabla is not None
    assert len(resultado.tabla) > 0


def test_ejecutar_etl_fuente_invalida_no_rompe():
    """Una fuente inválida se reporta sin lanzar excepción."""

    resultado = ejecutar_etl(
        origen=b"columna_a;columna_b\n1;2\n",
        nombre_fuente="malo.csv",
    )

    assert resultado.exito is False
    assert resultado.tabla is None
    assert resultado.huella_sha256 == hashlib.sha256(
        b"columna_a;columna_b\n1;2\n"
    ).hexdigest()
    assert resultado.traza.tiene_errores is True


def test_loader_sin_argumentos_sigue_funcionando():
    """La llamada histórica sin argumentos no debe cambiar."""

    tabla = cargar_cirugia_plastica()

    assert isinstance(tabla, pd.DataFrame)
    assert "sede_id" in tabla.columns
    assert "es_quirurgico" in tabla.columns


def test_loader_acepta_bytes():
    """El loader debe aceptar una fuente en bytes equivalente al archivo."""

    contenido = (
        ARCHIVO_CIRUGIA_PLASTICA.read_bytes()
    )

    desde_archivo = cargar_cirugia_plastica()
    desde_bytes = cargar_cirugia_plastica(
        origen=contenido
    )

    assert len(desde_archivo) == len(desde_bytes)
    assert list(desde_archivo.columns) == list(
        desde_bytes.columns
    )


def test_resultado_como_dict_traza_incluye_metadatos():
    """La traza serializada debe incluir huella, fuente y éxito."""

    resultado = ejecutar_etl(
        nombre_fuente="incluido.csv",
    )

    datos = resultado.como_dict_traza()

    assert datos["exito"] is True
    assert datos["nombre_fuente"] == "incluido.csv"
    assert len(datos["huella_sha256"]) == 64
    assert "pasos" in datos
    assert "mapeos" in datos


def test_tabla_activa_usa_store_cuando_hay_datos():
    """La resolución del dataset activo debe preferir el store cargado."""

    from quiron.callbacks import _tabla_activa

    base = cargar_cirugia_plastica()

    resultado = ejecutar_etl()
    registros = resultado.tabla.to_dict(
        "records"
    )

    activa = _tabla_activa(
        registros,
        base,
    )

    assert len(activa) == len(
        resultado.tabla
    )
    assert activa["es_quirurgico"].dtype == bool


def test_tabla_activa_fallback_sin_store():
    """Sin store, la resolución debe devolver la tabla base."""

    from quiron.callbacks import _tabla_activa

    base = cargar_cirugia_plastica()

    activa = _tabla_activa(None, base)

    assert activa is base

    activa_vacia = _tabla_activa([], base)

    assert activa_vacia is base
