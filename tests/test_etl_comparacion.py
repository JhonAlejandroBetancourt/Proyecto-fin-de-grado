"""Pruebas de comparación segura entre cargas de sedes."""

import pandas as pd

from quiron.etl.comparacion import (
    comparar_datasets,
)


def _tabla(
    *,
    sede_id="1",
    sede="Clínica de Prueba",
    direccion="Calle 1",
    telefono="123",
    correo="prueba@example.com",
    servicio="213",
):
    return pd.DataFrame(
        [
            {
                "sede_id": sede_id,
                "sede": sede,
                "direccion": direccion,
                "telefono": telefono,
                "correo": correo,
                "naturaleza": "Privada",
                "tipo_prestador": "IPS",
                "codigo_servicio": servicio,
            },
        ]
    )


def test_comparacion_ignora_orden_e_identificador_de_fila():
    anterior = _tabla()
    nuevo = _tabla(
        sede_id="98",
        sede=" clínica   de prueba ",
    )

    resultado = comparar_datasets(
        anterior,
        nuevo,
    )

    assert resultado["sin_diferencias"] is True
    assert resultado["sin_cambios"] == 1
    assert resultado["actualizadas"] == 0


def test_comparacion_informa_actualizacion_de_direccion():
    anterior = _tabla()
    nuevo = _tabla(
        sede_id="2",
        direccion="Carrera 10",
    )

    resultado = comparar_datasets(
        anterior,
        nuevo,
    )

    assert resultado["sin_diferencias"] is False
    assert resultado["actualizadas"] == 1
    assert resultado["nuevas"] == 0
    assert resultado["retiradas"] == 0
    assert resultado["cambios"] == [
        {
            "sede": "Clínica de Prueba",
            "campo": "Dirección",
            "valor_anterior": "Calle 1",
            "valor_nuevo": "Carrera 10",
        }
    ]


def test_comparacion_separa_sedes_con_mismo_nombre_por_direccion():
    anterior = pd.concat(
        [
            _tabla(
                sede_id="1",
                direccion="Calle 1",
            ),
            _tabla(
                sede_id="2",
                direccion="Calle 2",
            ),
        ],
        ignore_index=True,
    )
    nuevo = pd.concat(
        [
            _tabla(
                sede_id="3",
                direccion="Calle 1",
            ),
            _tabla(
                sede_id="4",
                direccion="Calle 3",
            ),
        ],
        ignore_index=True,
    )

    resultado = comparar_datasets(
        anterior,
        nuevo,
    )

    assert resultado["sin_cambios"] == 1
    assert resultado["nuevas"] == 1
    assert resultado["retiradas"] == 1
    assert resultado["ambiguas"] == 0


def test_comparacion_no_actualiza_identidad_ambigua():
    anterior = pd.concat(
        [
            _tabla(
                sede_id="1",
                telefono="111",
            ),
            _tabla(
                sede_id="2",
                telefono="222",
            ),
        ],
        ignore_index=True,
    )
    nuevo = pd.concat(
        [
            _tabla(
                sede_id="3",
                telefono="333",
            ),
            _tabla(
                sede_id="4",
                telefono="444",
            ),
        ],
        ignore_index=True,
    )

    resultado = comparar_datasets(
        anterior,
        nuevo,
    )

    assert resultado["ambiguas"] == 1
    assert resultado["sin_diferencias"] is False
    assert "ambigua" in resultado["cambios"][0][
        "campo"
    ].lower()
