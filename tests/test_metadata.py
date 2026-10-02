"""Pruebas unitarias de metadata y trazabilidad de Quirón.

Esta suite valida:

  - La fecha de corte declarada.
  - Los campos obligatorios de trazabilidad.
  - La independencia de las copias de metadata.
  - Los conteos de registros y sedes únicas.
  - La cobertura de geocodificación.
  - Los códigos quirúrgicos presentes.
  - La validación del archivo fuente.
  - El formato preparado para exportación.
"""

from datetime import date

import pandas as pd
import pytest

from quiron.metadata import (
    ARCHIVO_PRINCIPAL,
    CODIGOS_QUIRURGICOS_ANALIZADOS,
    FECHA_CORTE,
    METADATA_BASE,
    _serializar_valor,
    metadata_para_exportacion,
    obtener_metadata,
)


@pytest.fixture
def tabla_oferta():
    """Construye una muestra controlada para las pruebas."""

    return pd.DataFrame(
        [
            {
                "sede_id": "1",
                "codigo_servicio": "213",
                "es_quirurgico": True,
                "coordenada_valida": True,
            },
            {
                "sede_id": "1",
                "codigo_servicio": "369",
                "es_quirurgico": True,
                "coordenada_valida": True,
            },
            {
                "sede_id": "2",
                "codigo_servicio": "213",
                "es_quirurgico": True,
                "coordenada_valida": False,
            },
            {
                "sede_id": "3",
                "codigo_servicio": "356",
                "es_quirurgico": False,
                "coordenada_valida": False,
            },
        ]
    )


def test_fecha_corte_declarada_explicita():
    """Comprueba la fecha de corte declarada en el módulo."""

    assert FECHA_CORTE == date(
        2026,
        7,
        1,
    )

    assert (
        METADATA_BASE[
            "fecha_corte"
        ]
        == "2026-07-01"
    )

    assert (
        METADATA_BASE[
            "fecha_corte_legible"
        ]
        == "01/07/2026"
    )


def test_metadata_base_contiene_campos_obligatorios():
    """Comprueba la presencia de los campos metodológicos."""

    campos_obligatorios = {
        "proyecto",
        "entidad_publicadora",
        "portal_publicacion",
        "conjunto_datos",
        "url_fuente",
        "archivo_principal",
        "archivo_geocodificado",
        "fecha_corte",
        "fecha_corte_legible",
        "cobertura_geografica",
        "unidad_analisis",
        "codigos_quirurgicos",
        "advertencia_interpretacion",
        "advertencia_geocodificacion",
    }

    assert campos_obligatorios.issubset(
        METADATA_BASE
    )


def test_metadata_base_documenta_archivo_principal():
    """Comprueba que el archivo principal esté documentado."""

    assert (
        METADATA_BASE[
            "archivo_principal"
        ]
        == ARCHIVO_PRINCIPAL
    )


def test_metadata_base_documenta_codigos_analizados():
    """Comprueba los códigos incluidos en el alcance."""

    assert (
        METADATA_BASE[
            "codigos_quirurgicos"
        ]
        == list(
            CODIGOS_QUIRURGICOS_ANALIZADOS
        )
    )


def test_obtener_metadata_sin_tabla_no_agrega_cobertura():
    """Sin tabla no deben inventarse estadísticas de cobertura."""

    metadata = obtener_metadata()

    assert (
        "cobertura_datos"
        not in metadata
    )


def test_obtener_metadata_devuelve_copia_independiente():
    """Modificar un resultado no debe alterar la metadata original."""

    primera_copia = obtener_metadata()

    primera_copia[
        "codigos_quirurgicos"
    ].append(
        "999"
    )

    segunda_copia = obtener_metadata()

    assert (
        "999"
        not in segunda_copia[
            "codigos_quirurgicos"
        ]
    )

    assert (
        "999"
        not in METADATA_BASE[
            "codigos_quirurgicos"
        ]
    )


def test_calcula_total_de_registros(
    tabla_oferta,
):
    """Comprueba los conteos de registros generales y quirúrgicos."""

    cobertura = obtener_metadata(
        tabla_oferta
    )[
        "cobertura_datos"
    ]

    assert (
        cobertura[
            "total_registros"
        ]
        == 4
    )

    assert (
        cobertura[
            "registros_quirurgicos"
        ]
        == 3
    )


def test_cuenta_sedes_quirurgicas_unicas(
    tabla_oferta,
):
    """Una sede con dos servicios debe contarse una sola vez."""

    cobertura = obtener_metadata(
        tabla_oferta
    )[
        "cobertura_datos"
    ]

    assert (
        cobertura[
            "sedes_quirurgicas"
        ]
        == 2
    )


def test_calcula_cobertura_geografica(
    tabla_oferta,
):
    """Comprueba sedes visibles, faltantes y porcentaje."""

    cobertura = obtener_metadata(
        tabla_oferta
    )[
        "cobertura_datos"
    ]

    assert (
        cobertura[
            "sedes_geocodificadas"
        ]
        == 1
    )

    assert (
        cobertura[
            "sedes_sin_coordenadas"
        ]
        == 1
    )

    assert (
        cobertura[
            "porcentaje_geocodificacion"
        ]
        == 50.0
    )


def test_informa_codigos_quirurgicos_presentes(
    tabla_oferta,
):
    """Incluye únicamente códigos pertenecientes a la oferta quirúrgica."""

    cobertura = obtener_metadata(
        tabla_oferta
    )[
        "cobertura_datos"
    ]

    assert (
        cobertura[
            "codigos_quirurgicos_presentes"
        ]
        == [
            "213",
            "369",
        ]
    )

    assert (
        "356"
        not in cobertura[
            "codigos_quirurgicos_presentes"
        ]
    )


def test_tabla_sin_sedes_quirurgicas_no_divide_por_cero(
    tabla_oferta,
):
    """Una tabla sin oferta quirúrgica produce cobertura cero."""

    tabla_sin_oferta = tabla_oferta.assign(
        es_quirurgico=False
    )

    cobertura = obtener_metadata(
        tabla_sin_oferta
    )[
        "cobertura_datos"
    ]

    assert (
        cobertura[
            "sedes_quirurgicas"
        ]
        == 0
    )

    assert (
        cobertura[
            "porcentaje_geocodificacion"
        ]
        == 0.0
    )


def test_rechaza_objeto_que_no_es_dataframe():
    """La cobertura solo puede calcularse desde un DataFrame."""

    with pytest.raises(
        TypeError,
        match="pandas.DataFrame",
    ):
        obtener_metadata(
            tabla=[]
        )


def test_rechaza_tabla_con_columnas_faltantes(
    tabla_oferta,
):
    """Comprueba la validación de columnas obligatorias."""

    tabla_incompleta = tabla_oferta.drop(
        columns=[
            "coordenada_valida"
        ]
    )

    with pytest.raises(
        ValueError,
        match="coordenada_valida",
    ):
        obtener_metadata(
            tabla_incompleta
        )


def test_valida_archivo_documentado(
    tabla_oferta,
    tmp_path,
):
    """Comprueba el nombre y tamaño del archivo fuente."""

    ruta_archivo = (
        tmp_path
        / ARCHIVO_PRINCIPAL
    )

    ruta_archivo.write_text(
        "contenido de prueba",
        encoding="utf-8",
    )

    metadata = obtener_metadata(
        tabla_oferta,
        ruta_archivo,
    )

    assert (
        metadata[
            "archivo_fuente"
        ][
            "nombre"
        ]
        == ARCHIVO_PRINCIPAL
    )

    assert (
        metadata[
            "archivo_fuente"
        ][
            "tamano_bytes"
        ]
        > 0
    )


def test_rechaza_archivo_inexistente(
    tabla_oferta,
    tmp_path,
):
    """Comprueba el error cuando el archivo no existe."""

    ruta_inexistente = (
        tmp_path
        / ARCHIVO_PRINCIPAL
    )

    with pytest.raises(
        FileNotFoundError,
        match="No se encontró",
    ):
        obtener_metadata(
            tabla_oferta,
            ruta_inexistente,
        )


def test_rechaza_nombre_de_archivo_distinto(
    tabla_oferta,
    tmp_path,
):
    """Comprueba que no se acepte otro archivo silenciosamente."""

    ruta_distinta = (
        tmp_path
        / "archivo-distinto.csv"
    )

    ruta_distinta.write_text(
        "contenido",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="no coincide",
    ):
        obtener_metadata(
            tabla_oferta,
            ruta_distinta,
        )


def test_metadata_para_exportacion_aplana_diccionarios(
    tabla_oferta,
):
    """Comprueba la estructura tabular preparada para CSV."""

    exportacion = metadata_para_exportacion(
        tabla_oferta
    )

    assert list(
        exportacion.columns
    ) == [
        "campo",
        "valor",
    ]

    campos = set(
        exportacion[
            "campo"
        ]
    )

    assert (
        "cobertura_datos_sedes_quirurgicas"
        in campos
    )

    assert (
        "cobertura_datos_porcentaje_geocodificacion"
        in campos
    )


@pytest.mark.parametrize(
    "valor, esperado",
    [
        (
            [
                "213",
                "369",
            ],
            "213; 369",
        ),
        (
            (
                "a",
                "b",
            ),
            "a; b",
        ),
        (
            None,
            "",
        ),
        (
            50.0,
            "50.0",
        ),
        (
            "Bogotá D.C.",
            "Bogotá D.C.",
        ),
    ],
)
def test_serializa_valores(
    valor,
    esperado,
):
    """Comprueba la serialización utilizada en la exportación."""

    assert (
        _serializar_valor(
            valor
        )
        == esperado
    )