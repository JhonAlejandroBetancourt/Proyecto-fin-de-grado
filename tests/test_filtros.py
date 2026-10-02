"""Pruebas unitarias de las reglas de filtrado de Quirón.

Las pruebas utilizan una tabla controlada, pequeña e independiente de los
archivos CSV reales. Esto permite detectar errores en las reglas sin que
el resultado dependa de cambios futuros en las fuentes oficiales.

Aspectos verificados:
  - Exclusión de servicios fuera del alcance quirúrgico.
  - Filtrado individual por servicio, naturaleza y tipo de prestador.
  - Combinación de filtros mediante lógica AND.
  - Búsqueda por sede tolerante a tildes y mayúsculas.
  - Conteo correcto de sedes físicas únicas.
  - Generación de opciones para los controles visuales.
  - Detección de filtros activos.
  - Conservación de la tabla original.
  - Validación de columnas obligatorias.
"""

import pandas as pd
import pytest

from quiron.filtros import (
    _normalizar_texto,
    aplicar_filtros,
    contar_sedes_unicas,
    filtros_activos,
    obtener_opciones_filtros,
)


@pytest.fixture
def tabla_oferta():
    """Construye una muestra controlada de oferta de servicios."""

    return pd.DataFrame(
        [
            {
                "sede_id": "1",
                "sede": "Clínica del Norte",
                "naturaleza": "Privada",
                "tipo_prestador": "IPS",
                "codigo_servicio": "213",
                "nombre_servicio": (
                    "213 · CIRUGÍA PLÁSTICA "
                    "Y ESTÉTICA"
                ),
                "es_quirurgico": True,
            },
            {
                "sede_id": "1",
                "sede": "Clínica del Norte",
                "naturaleza": "Privada",
                "tipo_prestador": "IPS",
                "codigo_servicio": "369",
                "nombre_servicio": (
                    "369 · CIRUGÍA PLÁSTICA "
                    "Y ESTÉTICA"
                ),
                "es_quirurgico": True,
            },
            {
                "sede_id": "2",
                "sede": "Hospital Central",
                "naturaleza": "Pública",
                "tipo_prestador": "IPS",
                "codigo_servicio": "213",
                "nombre_servicio": (
                    "213 · CIRUGÍA PLÁSTICA "
                    "Y ESTÉTICA"
                ),
                "es_quirurgico": True,
            },
            {
                "sede_id": "3",
                "sede": "Centro Médico Ágil",
                "naturaleza": "Privada",
                "tipo_prestador": (
                    "Profesional Independiente"
                ),
                "codigo_servicio": "369",
                "nombre_servicio": (
                    "369 · CIRUGÍA PLÁSTICA "
                    "Y ESTÉTICA"
                ),
                "es_quirurgico": True,
            },
            {
                "sede_id": "4",
                "sede": "Consulta Estética",
                "naturaleza": "Privada",
                "tipo_prestador": (
                    "Profesional Independiente"
                ),
                "codigo_servicio": "356",
                "nombre_servicio": (
                    "356 · OTRAS CONSULTAS"
                ),
                "es_quirurgico": False,
            },
        ]
    )


def test_sin_filtros_conserva_solo_oferta_quirurgica(
    tabla_oferta,
):
    resultado = aplicar_filtros(
        tabla_oferta
    )

    assert len(resultado) == 4
    assert resultado[
        "es_quirurgico"
    ].all()


def test_filtra_por_un_servicio(
    tabla_oferta,
):
    resultado = aplicar_filtros(
        tabla_oferta,
        servicios=["213"],
    )

    assert set(
        resultado["sede_id"]
    ) == {
        "1",
        "2",
    }

    assert set(
        resultado["codigo_servicio"]
    ) == {
        "213",
    }


def test_filtra_por_varios_servicios(
    tabla_oferta,
):
    resultado = aplicar_filtros(
        tabla_oferta,
        servicios=[
            "213",
            "369",
        ],
    )

    assert len(resultado) == 4

    assert set(
        resultado["codigo_servicio"]
    ) == {
        "213",
        "369",
    }


def test_filtra_por_naturaleza(
    tabla_oferta,
):
    resultado = aplicar_filtros(
        tabla_oferta,
        naturalezas=["Pública"],
    )

    assert set(
        resultado["sede_id"]
    ) == {
        "2",
    }

    assert set(
        resultado["naturaleza"]
    ) == {
        "Pública",
    }


def test_filtra_por_tipo_de_prestador(
    tabla_oferta,
):
    resultado = aplicar_filtros(
        tabla_oferta,
        tipos_prestador=[
            "Profesional Independiente"
        ],
    )

    assert set(
        resultado["sede_id"]
    ) == {
        "3",
    }


def test_busqueda_de_sede_ignora_tildes(
    tabla_oferta,
):
    resultado = aplicar_filtros(
        tabla_oferta,
        texto_sede="clinica",
    )

    assert set(
        resultado["sede_id"]
    ) == {
        "1",
    }


def test_busqueda_de_sede_ignora_mayusculas(
    tabla_oferta,
):
    resultado = aplicar_filtros(
        tabla_oferta,
        texto_sede="HOSPITAL CENTRAL",
    )

    assert set(
        resultado["sede_id"]
    ) == {
        "2",
    }


def test_busqueda_de_sede_ignora_espacios_repetidos(
    tabla_oferta,
):
    resultado = aplicar_filtros(
        tabla_oferta,
        texto_sede=(
            "  centro   medico  "
        ),
    )

    assert set(
        resultado["sede_id"]
    ) == {
        "3",
    }


def test_combina_filtros_con_logica_and(
    tabla_oferta,
):
    resultado = aplicar_filtros(
        tabla_oferta,
        servicios=["369"],
        naturalezas=["Privada"],
        tipos_prestador=["IPS"],
    )

    assert len(resultado) == 1

    assert resultado.iloc[0][
        "sede_id"
    ] == "1"

    assert resultado.iloc[0][
        "codigo_servicio"
    ] == "369"


def test_combinacion_sin_coincidencias_devuelve_tabla_vacia(
    tabla_oferta,
):
    resultado = aplicar_filtros(
        tabla_oferta,
        servicios=["369"],
        naturalezas=["Pública"],
    )

    assert resultado.empty

    assert list(
        resultado.columns
    ) == list(
        tabla_oferta.columns
    )


def test_cuenta_sedes_unicas_y_no_filas(
    tabla_oferta,
):
    resultado = aplicar_filtros(
        tabla_oferta
    )

    assert len(resultado) == 4

    assert contar_sedes_unicas(
        resultado
    ) == 3


def test_genera_opciones_de_servicio_sin_duplicados(
    tabla_oferta,
):
    opciones = obtener_opciones_filtros(
        tabla_oferta
    )

    valores = [
        opcion["value"]
        for opcion
        in opciones["servicios"]
    ]

    assert valores == [
        "213",
        "369",
    ]


def test_no_incluye_servicios_fuera_del_alcance_en_opciones(
    tabla_oferta,
):
    opciones = obtener_opciones_filtros(
        tabla_oferta
    )

    valores = {
        opcion["value"]
        for opcion
        in opciones["servicios"]
    }

    assert "356" not in valores


def test_genera_opciones_de_naturaleza(
    tabla_oferta,
):
    opciones = obtener_opciones_filtros(
        tabla_oferta
    )

    valores = {
        opcion["value"]
        for opcion
        in opciones["naturalezas"]
    }

    assert valores == {
        "Privada",
        "Pública",
    }


def test_genera_opciones_de_tipo_de_prestador(
    tabla_oferta,
):
    opciones = obtener_opciones_filtros(
        tabla_oferta
    )

    valores = {
        opcion["value"]
        for opcion
        in opciones[
            "tipos_prestador"
        ]
    }

    assert valores == {
        "IPS",
        "Profesional Independiente",
    }


@pytest.mark.parametrize(
    "argumentos, esperado",
    [
        (
            {},
            False,
        ),
        (
            {
                "servicios": [
                    "213"
                ],
            },
            True,
        ),
        (
            {
                "naturalezas": [
                    "Privada"
                ],
            },
            True,
        ),
        (
            {
                "tipos_prestador": [
                    "IPS"
                ],
            },
            True,
        ),
        (
            {
                "texto_sede": "norte",
            },
            True,
        ),
        (
            {
                "texto_sede": "   ",
            },
            False,
        ),
        (
            {
                "servicios": [],
                "naturalezas": [],
                "tipos_prestador": [],
                "texto_sede": None,
            },
            False,
        ),
    ],
)
def test_detecta_filtros_activos(
    argumentos,
    esperado,
):
    assert filtros_activos(
        **argumentos
    ) is esperado


def test_no_modifica_la_tabla_original(
    tabla_oferta,
):
    copia_original = tabla_oferta.copy(
        deep=True
    )

    aplicar_filtros(
        tabla_oferta,
        servicios=["213"],
        naturalezas=["Privada"],
    )

    pd.testing.assert_frame_equal(
        tabla_oferta,
        copia_original,
    )


def test_valida_columnas_obligatorias(
    tabla_oferta,
):
    tabla_incompleta = tabla_oferta.drop(
        columns=[
            "tipo_prestador"
        ]
    )

    with pytest.raises(
        ValueError,
        match="tipo_prestador",
    ):
        aplicar_filtros(
            tabla_incompleta
        )


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        (
            "  CLÍNICA   ÁGIL ",
            "clinica agil",
        ),
        (
            "PÚBLICA",
            "publica",
        ),
        (
            "Bogotá D. C.",
            "bogota d. c.",
        ),
        (
            None,
            "",
        ),
        (
            "",
            "",
        ),
        (
            "   ",
            "",
        ),
    ],
)
def test_normalizacion_de_texto(
    entrada,
    esperado,
):
    assert _normalizar_texto(
        entrada
    ) == esperado
