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


def test_etl_asocia_coordenadas_si_solo_cambia_la_huella():
    """Cambios de bytes no deben descartar coincidencias seguras."""

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
    fuente = ejecutar_etl()
    assert fuente.tabla is not None

    assert resultado.huella_sha256 != fuente.huella_sha256
    assert resultado.tabla[
        "coordenada_valida"
    ].sum() == fuente.tabla[
        "coordenada_valida"
    ].sum()
    assert any(
        paso.nivel is NivelTraza.ADVERTENCIA
        for paso in resultado.traza.pasos
        if paso.nombre == "Cruce de coordenadas"
    )
    assert "sin ubicación" in next(
        paso.mensaje
        for paso in resultado.traza.pasos
        if paso.nombre == "Cruce de coordenadas"
    )


def test_etl_registra_limpieza_y_metricas_de_cada_etapa():
    """La traza expone todas las etapas y las filas descartadas."""

    contenido = (
        "SEDE -NOMBRE;DIRECCION;TELEFONO;"
        "CORREO ELECTRÓNICO;NATURALEZA;"
        "TIPO DE PRESTADOR;213 - CIRUGÍA PLÁSTICA;"
        "Unnamed: 7\n"
        "  Clínica   Limpia  ; Calle   1 ;123;"
        "prueba@example.com;Privada;IPS;X;\n"
        " ;Calle 2;456;otra@example.com;Privada;IPS;X;\n"
        "Sede sin marca;Calle 3;789;otra@example.com;"
        "Privada;IPS;SI;\n"
    ).encode("utf-8")

    resultado = ejecutar_etl(
        origen=contenido,
        nombre_fuente="limpieza.csv",
    )

    assert resultado.exito is True
    assert resultado.tabla is not None
    assert resultado.tabla["sede"].tolist() == [
        "Clínica Limpia",
    ]

    pasos = {
        paso.nombre: paso
        for paso in resultado.traza.pasos
    }
    assert {
        "Lectura del CSV",
        "Normalización de encabezados",
        "Validación de estructura",
        "Limpieza de registros",
        "Detección de columnas de servicio",
        "Transformación de formato ancho a largo",
        "Lectura de referencia geográfica",
        "Validación de referencia geográfica",
        "Normalización y control de coordenadas",
        "Normalización y depuración de identidades",
        "Cruce de coordenadas",
        "Control de integridad de la oferta",
        "Carga del conjunto transformado",
    }.issubset(pasos)

    limpieza = pasos["Limpieza de registros"]
    assert limpieza.filas_entrada == 3
    assert limpieza.filas_salida == 2
    assert limpieza.filas_eliminadas == 1
    assert pasos["Normalización de encabezados"].columnas_entrada == 8
    assert pasos["Normalización de encabezados"].columnas_salida == 7
    transformacion = pasos[
        "Transformación de formato ancho a largo"
    ]
    assert transformacion.filas_entrada == 2
    assert transformacion.filas_salida == 1
    assert transformacion.filas_eliminadas == 1
    assert transformacion.nivel is NivelTraza.ADVERTENCIA
    assert "SI" in transformacion.detalle


def test_etl_asigna_el_error_a_la_etapa_que_falla():
    """Un esquema inválido identifica la validación que detuvo el ETL."""

    resultado = ejecutar_etl(
        origen=b"columna_a;columna_b\n1;2\n",
        nombre_fuente="esquema-invalido.csv",
    )

    assert resultado.exito is False
    paso_error = next(
        paso
        for paso in resultado.traza.pasos
        if paso.nivel is NivelTraza.ERROR
    )
    assert paso_error.nombre == "Validación de estructura"
    assert paso_error.fase == "Validación"


def test_etl_asigna_errores_de_lectura_a_extraccion():
    """Los errores de sintaxis CSV quedan atribuidos a la lectura."""

    resultado = ejecutar_etl(
        origen=b'"unterminated field\n',
        nombre_fuente="malformado.csv",
    )

    assert resultado.exito is False
    paso_error = next(
        paso
        for paso in resultado.traza.pasos
        if paso.nivel is NivelTraza.ERROR
    )
    assert paso_error.nombre == "Lectura del CSV"
    assert paso_error.fase == "Extracción"


def test_etl_rechaza_encabezados_duplicados():
    """Un duplicado no debe ocultarse por la renominación de pandas."""

    resultado = ejecutar_etl(
        origen=(
            "SEDE -NOMBRE;SEDE -NOMBRE;DIRECCION;TELEFONO;"
            "CORREO ELECTRÓNICO;NATURALEZA;TIPO DE PRESTADOR;"
            "213 - CIRUGÍA PLÁSTICA\n"
            "Clínica;Clínica alterna;Calle 1;123;"
            "prueba@example.com;Privada;IPS;X\n"
        ).encode("utf-8"),
        nombre_fuente="encabezados-duplicados.csv",
    )

    assert resultado.exito is False
    paso_error = next(
        paso
        for paso in resultado.traza.pasos
        if paso.nivel is NivelTraza.ERROR
    )
    assert paso_error.nombre == "Normalización de encabezados"
    assert "duplicados" in paso_error.mensaje


def test_etl_reporta_salida_vacia_si_no_hay_marcas_reconocidas():
    """El ETL explica por qué no pudo crear registros de servicio."""

    resultado = ejecutar_etl(
        origen=(
            "SEDE -NOMBRE;DIRECCION;TELEFONO;"
            "CORREO ELECTRÓNICO;NATURALEZA;"
            "TIPO DE PRESTADOR;213 - CIRUGÍA PLÁSTICA\n"
            "Clínica sin marca;Calle 1;123;"
            "prueba@example.com;Privada;IPS;SI\n"
        ).encode("utf-8"),
        nombre_fuente="sin-marcas.csv",
    )

    assert resultado.exito is False
    transformacion = next(
        paso
        for paso in resultado.traza.pasos
        if paso.nombre == "Transformación de formato ancho a largo"
    )
    assert transformacion.filas_salida == 0
    assert transformacion.nivel is NivelTraza.ADVERTENCIA
    paso_error = next(
        paso
        for paso in resultado.traza.pasos
        if paso.nivel is NivelTraza.ERROR
    )
    assert paso_error.nombre == "Control de integridad de la oferta"
    assert "no produjo registros de servicio" in paso_error.mensaje


def test_etl_asocia_coordenadas_independientemente_del_orden():
    """Una fuente reordenada conserva solo las coordenadas por identidad."""

    fuente_original = pd.read_csv(
        ARCHIVO_CIRUGIA_PLASTICA,
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
    )
    contenido_reordenado = fuente_original.iloc[
        ::-1
    ].to_csv(
        sep=";",
        index=False,
        lineterminator="\n",
    ).encode("utf-8")

    original = ejecutar_etl()
    reordenado = ejecutar_etl(
        origen=contenido_reordenado,
        nombre_fuente="reordenado.csv",
    )

    assert original.tabla is not None
    assert reordenado.tabla is not None

    columnas = [
        "sede",
        "direccion",
        "latitud",
        "longitud",
    ]

    coordenadas_originales = (
        original.tabla.loc[
            original.tabla["coordenada_valida"],
            columnas,
        ]
        .drop_duplicates(
            subset=["sede", "direccion"]
        )
        .set_index(
            ["sede", "direccion"]
        )
        .sort_index()
    )
    coordenadas_reordenadas = (
        reordenado.tabla.loc[
            reordenado.tabla["coordenada_valida"],
            columnas,
        ]
        .drop_duplicates(
            subset=["sede", "direccion"]
        )
        .set_index(
            ["sede", "direccion"]
        )
        .sort_index()
    )

    pd.testing.assert_frame_equal(
        coordenadas_reordenadas,
        coordenadas_originales,
    )


def test_etl_no_asocia_identidades_ambiguas():
    """Una sede duplicada por nombre y dirección no hereda coordenadas."""

    from quiron.data.loader import (
        ARCHIVO_SEDES_GEOCODIFICADAS,
    )

    fuente = pd.read_csv(
        ARCHIVO_CIRUGIA_PLASTICA,
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
    )
    sedes_geocodificadas = pd.read_csv(
        ARCHIVO_SEDES_GEOCODIFICADAS,
        dtype=str,
        encoding="utf-8-sig",
    )
    identidades_validas = set(
        zip(
            sedes_geocodificadas.loc[
                sedes_geocodificadas[
                    "geocodificado"
                ].eq("True"),
                "sede",
            ],
            sedes_geocodificadas.loc[
                sedes_geocodificadas[
                    "geocodificado"
                ].eq("True"),
                "direccion",
            ],
        )
    )
    indice = next(
        indice
        for indice, fila in fuente.iterrows()
        if (
            fila["SEDE -NOMBRE"],
            fila["DIRECCION"],
        ) in identidades_validas
    )
    fila_duplicada = fuente.loc[
        [indice]
    ]
    fuente_ambigua = pd.concat(
        [
            fuente,
            fila_duplicada,
        ],
        ignore_index=True,
    )

    resultado = ejecutar_etl(
        origen=fuente_ambigua.to_csv(
            sep=";",
            index=False,
            lineterminator="\n",
        ).encode("utf-8"),
        nombre_fuente="identidad-ambigua.csv",
    )

    assert resultado.tabla is not None
    nombre = fila_duplicada.iloc[0][
        "SEDE -NOMBRE"
    ]
    direccion = fila_duplicada.iloc[0][
        "DIRECCION"
    ]
    registros_ambiguos = resultado.tabla.loc[
        resultado.tabla["sede"].eq(nombre)
        & resultado.tabla["direccion"].eq(direccion)
    ]

    assert not registros_ambiguos[
        "coordenada_valida"
    ].any()


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
