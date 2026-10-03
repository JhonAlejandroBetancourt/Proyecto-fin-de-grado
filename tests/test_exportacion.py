"""Pruebas unitarias de las exportaciones de Quirón.

La suite comprueba:

  - Exclusión de registros fuera del alcance quirúrgico.
  - Eliminación de duplicados por sede y servicio.
  - Conservación de servicios distintos de una misma sede.
  - Conteo de sedes únicas por servicio y naturaleza.
  - Comportamiento con resultados vacíos.
  - Conservación de la tabla original.
  - Generación del CSV sin índice.
  - Conservación de caracteres en español.
  - Inclusión de la marca BOM de UTF-8.
  - Generación determinista de nombres de archivo.
  - Conversión de zonas horarias.
  - Validación de tipos y columnas obligatorias.
"""

from datetime import datetime, timezone
from io import StringIO

import pandas as pd
import pytest

from quiron.exportacion import (
    COLUMNAS_DETALLE,
    convertir_a_csv,
    generar_nombre_archivo,
    preparar_detalle_exportacion,
    preparar_resumen_por_naturaleza,
    preparar_resumen_por_servicio,
)


@pytest.fixture
def tabla_oferta():
    """Construye una muestra con duplicados y servicios distintos."""

    return pd.DataFrame(
        [
            {
                "sede_id": "1",
                "sede": "Clínica del Norte",
                "direccion": "Carrera 10 # 20-30",
                "telefono": "6011111111",
                "correo": "contacto@clinica.co",
                "naturaleza": "Privada",
                "tipo_prestador": "IPS",
                "codigo_servicio": "213",
                "nombre_servicio": (
                    "213 · CIRUGÍA PLÁSTICA "
                    "Y ESTÉTICA"
                ),
                "latitud": 4.6500,
                "longitud": -74.0700,
                "coordenada_valida": True,
                "es_quirurgico": True,
            },
            {
                # Duplicado exacto de sede y servicio.
                "sede_id": "1",
                "sede": "Clínica del Norte",
                "direccion": "Carrera 10 # 20-30",
                "telefono": "6011111111",
                "correo": "contacto@clinica.co",
                "naturaleza": "Privada",
                "tipo_prestador": "IPS",
                "codigo_servicio": "213",
                "nombre_servicio": (
                    "213 · CIRUGÍA PLÁSTICA "
                    "Y ESTÉTICA"
                ),
                "latitud": 4.6500,
                "longitud": -74.0700,
                "coordenada_valida": True,
                "es_quirurgico": True,
            },
            {
                # Misma sede, pero otro servicio.
                "sede_id": "1",
                "sede": "Clínica del Norte",
                "direccion": "Carrera 10 # 20-30",
                "telefono": "6011111111",
                "correo": "contacto@clinica.co",
                "naturaleza": "Privada",
                "tipo_prestador": "IPS",
                "codigo_servicio": "369",
                "nombre_servicio": (
                    "369 · CIRUGÍA PLÁSTICA "
                    "Y ESTÉTICA"
                ),
                "latitud": 4.6500,
                "longitud": -74.0700,
                "coordenada_valida": True,
                "es_quirurgico": True,
            },
            {
                "sede_id": "2",
                "sede": "Hospital Público Ágil",
                "direccion": "Calle 30 # 40-50",
                "telefono": "6012222222",
                "correo": "contacto@hospital.gov.co",
                "naturaleza": "Pública",
                "tipo_prestador": "IPS",
                "codigo_servicio": "213",
                "nombre_servicio": (
                    "213 · CIRUGÍA PLÁSTICA "
                    "Y ESTÉTICA"
                ),
                "latitud": None,
                "longitud": None,
                "coordenada_valida": False,
                "es_quirurgico": True,
            },
            {
                # Registro fuera del alcance quirúrgico.
                "sede_id": "3",
                "sede": "Consulta Estética",
                "direccion": "Calle 50 # 60-70",
                "telefono": "6013333333",
                "correo": "consulta@example.com",
                "naturaleza": "Privada",
                "tipo_prestador": (
                    "Profesional Independiente"
                ),
                "codigo_servicio": "356",
                "nombre_servicio": (
                    "356 · OTRAS CONSULTAS"
                ),
                "latitud": 4.7000,
                "longitud": -74.1000,
                "coordenada_valida": True,
                "es_quirurgico": False,
            },
        ]
    )


def test_detalle_excluye_registros_no_quirurgicos(
    tabla_oferta,
):
    """El detalle solo incluye registros del alcance quirúrgico."""

    detalle = preparar_detalle_exportacion(
        tabla_oferta
    )

    assert detalle[
        "codigo_servicio"
    ].isin(
        [
            "213",
            "369",
        ]
    ).all()

    assert (
        "356"
        not in detalle[
            "codigo_servicio"
        ].tolist()
    )


def test_detalle_elimina_duplicados_de_sede_y_servicio(
    tabla_oferta,
):
    """Una combinación repetida debe aparecer una sola vez."""

    detalle = preparar_detalle_exportacion(
        tabla_oferta
    )

    combinaciones = detalle[
        [
            "sede_id",
            "codigo_servicio",
        ]
    ]

    assert not combinaciones.duplicated().any()

    assert len(
        detalle
    ) == 3


def test_detalle_conserva_servicios_distintos_de_una_sede(
    tabla_oferta,
):
    """Una sede con dos servicios conserva ambas combinaciones."""

    detalle = preparar_detalle_exportacion(
        tabla_oferta
    )

    servicios_sede_uno = set(
        detalle.loc[
            detalle[
                "sede_id"
            ]
            == "1",
            "codigo_servicio",
        ]
    )

    assert servicios_sede_uno == {
        "213",
        "369",
    }


def test_detalle_respeta_orden_de_columnas(
    tabla_oferta,
):
    """Las columnas disponibles siguen el esquema declarado."""

    detalle = preparar_detalle_exportacion(
        tabla_oferta
    )

    esperadas = [
        columna
        for columna in COLUMNAS_DETALLE
        if columna in tabla_oferta.columns
    ]

    assert list(
        detalle.columns
    ) == esperadas


def test_detalle_ordena_por_sede_y_codigo(
    tabla_oferta,
):
    """El resultado debe producir un orden estable."""

    detalle = preparar_detalle_exportacion(
        tabla_oferta
    )

    pares = list(
        detalle[
            [
                "sede",
                "codigo_servicio",
            ]
        ].itertuples(
            index=False,
            name=None,
        )
    )

    assert pares == sorted(
        pares
    )


def test_resumen_servicio_cuenta_sedes_unicas(
    tabla_oferta,
):
    """El duplicado de la sede 1 no aumenta el conteo."""

    resumen = preparar_resumen_por_servicio(
        tabla_oferta
    )

    fila_213 = resumen.loc[
        resumen[
            "codigo_servicio"
        ].astype(str)
        == "213"
    ].iloc[0]

    fila_369 = resumen.loc[
        resumen[
            "codigo_servicio"
        ].astype(str)
        == "369"
    ].iloc[0]

    assert (
        fila_213[
            "sedes"
        ]
        == 2
    )

    assert (
        fila_369[
            "sedes"
        ]
        == 1
    )


def test_resumen_servicio_no_incluye_fuera_de_alcance(
    tabla_oferta,
):
    """Los códigos no quirúrgicos no aparecen en el resumen."""

    resumen = preparar_resumen_por_servicio(
        tabla_oferta
    )

    assert (
        "356"
        not in resumen[
            "codigo_servicio"
        ]
        .astype(str)
        .tolist()
    )


def test_resumen_naturaleza_cuenta_sedes_unicas(
    tabla_oferta,
):
    """Comprueba el conteo por naturaleza jurídica."""

    resumen = preparar_resumen_por_naturaleza(
        tabla_oferta
    )

    conteos = dict(
        zip(
            resumen[
                "naturaleza"
            ],
            resumen[
                "sedes"
            ],
        )
    )

    assert conteos == {
        "Privada": 1,
        "Pública": 1,
    }


def test_exportaciones_vacias_conservan_columnas(
    tabla_oferta,
):
    """Una selección sin oferta debe seguir siendo exportable."""

    tabla_vacia = tabla_oferta.iloc[
        0:0
    ].copy()

    detalle = preparar_detalle_exportacion(
        tabla_vacia
    )

    servicios = preparar_resumen_por_servicio(
        tabla_vacia
    )

    naturalezas = (
        preparar_resumen_por_naturaleza(
            tabla_vacia
        )
    )

    assert detalle.empty

    assert list(
        servicios.columns
    ) == [
        "codigo_servicio",
        "nombre_servicio",
        "sedes",
    ]

    assert list(
        naturalezas.columns
    ) == [
        "naturaleza",
        "sedes",
    ]


def test_preparacion_no_modifica_tabla_original(
    tabla_oferta,
):
    """Las tres preparaciones deben trabajar sobre copias."""

    original = tabla_oferta.copy(
        deep=True
    )

    preparar_detalle_exportacion(
        tabla_oferta
    )

    preparar_resumen_por_servicio(
        tabla_oferta
    )

    preparar_resumen_por_naturaleza(
        tabla_oferta
    )

    pd.testing.assert_frame_equal(
        tabla_oferta,
        original,
    )


def test_csv_incluye_bom_utf8(
    tabla_oferta,
):
    """El contenido comienza con la marca BOM de UTF-8."""

    detalle = preparar_detalle_exportacion(
        tabla_oferta
    )

    contenido = convertir_a_csv(
        detalle
    )

    assert contenido.startswith(
        "\ufeff"
    )


def test_csv_no_exporta_indice(
    tabla_oferta,
):
    """El CSV no debe incorporar la columna índice de pandas."""

    detalle = preparar_detalle_exportacion(
        tabla_oferta
    )

    contenido = convertir_a_csv(
        detalle
    )

    primera_linea = (
        contenido
        .lstrip("\ufeff")
        .splitlines()[0]
    )

    assert primera_linea.startswith(
        "sede_id,"
    )

    assert not primera_linea.startswith(
        ","
    )


def test_csv_conserva_caracteres_en_espanol(
    tabla_oferta,
):
    """Tildes, eñes y otros caracteres se conservan."""

    detalle = preparar_detalle_exportacion(
        tabla_oferta
    )

    contenido = convertir_a_csv(
        detalle
    )

    assert (
        "Clínica del Norte"
        in contenido
    )

    assert (
        "Hospital Público Ágil"
        in contenido
    )

    assert (
        "CIRUGÍA PLÁSTICA"
        in contenido
    )


def test_csv_puede_leerse_nuevamente(
    tabla_oferta,
):
    """El CSV generado debe ser recuperable como DataFrame."""

    detalle = preparar_detalle_exportacion(
        tabla_oferta
    )

    contenido = convertir_a_csv(
        detalle
    )

    recuperado = pd.read_csv(
        StringIO(
            contenido.lstrip(
                "\ufeff"
            )
        ),
        dtype={
            "sede_id": str,
            "codigo_servicio": str,
        },
    )

    assert len(
        recuperado
    ) == len(
        detalle
    )

    assert set(
        recuperado[
            "codigo_servicio"
        ]
    ) == {
        "213",
        "369",
    }


@pytest.mark.parametrize(
    "tipo, nombre_base",
    [
        (
            "detalle",
            (
                "quiron_detalle_"
                "oferta_quirurgica"
            ),
        ),
        (
            "servicio",
            (
                "quiron_resumen_"
                "por_servicio"
            ),
        ),
        (
            "naturaleza",
            (
                "quiron_resumen_"
                "por_naturaleza"
            ),
        ),
        (
            "metadata",
            (
                "quiron_metadata_"
                "trazabilidad"
            ),
        ),
    ],
)
def test_genera_nombres_deterministas(
    tipo,
    nombre_base,
):
    """Un momento fijo produce un nombre predecible."""

    momento = datetime(
        2026,
        10,
        2,
        15,
        30,
        45,
    )

    nombre = generar_nombre_archivo(
        tipo,
        momento=momento,
    )

    assert nombre == (
        f"{nombre_base}_"
        "20261002_153045.csv"
    )


def test_nombre_convierte_hora_utc_a_colombia():
    """Un datetime consciente se convierte a America/Bogota."""

    momento_utc = datetime(
        2026,
        10,
        2,
        20,
        30,
        0,
        tzinfo=timezone.utc,
    )

    nombre = generar_nombre_archivo(
        "detalle",
        momento=momento_utc,
    )

    assert nombre.endswith(
        "20261002_153000.csv"
    )


def test_rechaza_tipo_de_exportacion_desconocido():
    """Solo se permiten los cuatro tipos documentados."""

    with pytest.raises(
        ValueError,
        match="Tipo de exportación no válido",
    ):
        generar_nombre_archivo(
            "desconocido"
        )


def test_rechaza_objeto_que_no_es_dataframe():
    """La preparación requiere un DataFrame."""

    with pytest.raises(
        TypeError,
        match="pandas.DataFrame",
    ):
        preparar_detalle_exportacion(
            []
        )


def test_rechaza_tabla_con_columnas_faltantes(
    tabla_oferta,
):
    """Comprueba la validación del esquema mínimo."""

    tabla_incompleta = tabla_oferta.drop(
        columns=[
            "nombre_servicio"
        ]
    )

    with pytest.raises(
        ValueError,
        match="nombre_servicio",
    ):
        preparar_resumen_por_servicio(
            tabla_incompleta
        )


def test_convertir_csv_rechaza_objeto_invalido():
    """La serialización CSV también valida el tipo recibido."""

    with pytest.raises(
        TypeError,
        match="pandas.DataFrame",
    ):
        convertir_a_csv(
            {
                "sede": [
                    "Clínica"
                ]
            }
        )