"""Preparación de datos exportables del dashboard Quirón.

Las funciones de este módulo reciben una tabla ya filtrada y producen
copias aptas para descarga.

El módulo no escribe archivos en disco, no modifica el DataFrame recibido
y no vuelve a aplicar filtros. Los callbacks serán responsables de
entregar los archivos preparados al navegador.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd


ZONA_HORARIA_COLOMBIA = ZoneInfo(
    "America/Bogota"
)

COLUMNAS_DETALLE = [
    "sede_id",
    "sede",
    "direccion",
    "telefono",
    "correo",
    "naturaleza",
    "tipo_prestador",
    "codigo_servicio",
    "nombre_servicio",
    "latitud",
    "longitud",
    "coordenada_valida",
]

COLUMNAS_MINIMAS = {
    "sede_id",
    "sede",
    "naturaleza",
    "tipo_prestador",
    "codigo_servicio",
    "nombre_servicio",
    "es_quirurgico",
}


def _validar_tabla(
    tabla,
):
    """Valida que la tabla pueda utilizarse para exportación."""

    if not isinstance(
        tabla,
        pd.DataFrame,
    ):
        raise TypeError(
            "La exportación requiere una "
            "instancia de pandas.DataFrame."
        )

    columnas_faltantes = (
        COLUMNAS_MINIMAS.difference(
            tabla.columns
        )
    )

    if columnas_faltantes:
        nombres = ", ".join(
            sorted(
                columnas_faltantes
            )
        )

        raise ValueError(
            "No es posible preparar la exportación "
            "porque faltan las columnas: "
            f"{nombres}."
        )


def _oferta_quirurgica(
    tabla,
):
    """Obtiene una copia restringida a la oferta quirúrgica."""

    _validar_tabla(
        tabla
    )

    return tabla.loc[
        tabla[
            "es_quirurgico"
        ]
        .fillna(False)
        .astype(bool)
    ].copy()


def preparar_detalle_exportacion(
    tabla,
):
    """Prepara el detalle de sedes y servicios para exportación.

    El resultado contiene una fila por combinación única de sede y
    servicio quirúrgico.

    Si la tabla contiene accidentalmente registros duplicados para la
    misma combinación ``sede_id`` y ``codigo_servicio``, se conserva la
    primera aparición sin modificar la tabla recibida.
    """

    oferta = _oferta_quirurgica(
        tabla
    )

    columnas_disponibles = [
        columna
        for columna in COLUMNAS_DETALLE
        if columna in oferta.columns
    ]

    detalle = oferta[
        columnas_disponibles
    ].copy()

    detalle[
        "sede_id"
    ] = detalle[
        "sede_id"
    ].astype(str)

    detalle[
        "codigo_servicio"
    ] = detalle[
        "codigo_servicio"
    ].astype(str)

    detalle = detalle.drop_duplicates(
        subset=[
            "sede_id",
            "codigo_servicio",
        ],
        keep="first",
    )

    detalle = detalle.sort_values(
        by=[
            "sede",
            "codigo_servicio",
        ],
        kind="stable",
        na_position="last",
    )

    return detalle.reset_index(
        drop=True
    )


def preparar_resumen_por_servicio(
    tabla,
):
    """Cuenta sedes únicas por código y nombre de servicio."""

    oferta = _oferta_quirurgica(
        tabla
    )

    if oferta.empty:
        return pd.DataFrame(
            columns=[
                "codigo_servicio",
                "nombre_servicio",
                "sedes",
            ]
        )

    resumen = (
        oferta
        .groupby(
            [
                "codigo_servicio",
                "nombre_servicio",
            ],
            dropna=False,
            as_index=False,
        )[
            "sede_id"
        ]
        .nunique()
        .rename(
            columns={
                "sede_id": "sedes",
            }
        )
    )

    resumen = resumen.sort_values(
        by=[
            "sedes",
            "codigo_servicio",
        ],
        ascending=[
            False,
            True,
        ],
        kind="stable",
    )

    return resumen.reset_index(
        drop=True
    )


def preparar_resumen_por_naturaleza(
    tabla,
):
    """Cuenta sedes únicas por naturaleza jurídica."""

    oferta = _oferta_quirurgica(
        tabla
    )

    if oferta.empty:
        return pd.DataFrame(
            columns=[
                "naturaleza",
                "sedes",
            ]
        )

    resumen = (
        oferta
        .groupby(
            "naturaleza",
            dropna=False,
            as_index=False,
        )[
            "sede_id"
        ]
        .nunique()
        .rename(
            columns={
                "sede_id": "sedes",
            }
        )
    )

    resumen = resumen.sort_values(
        by=[
            "sedes",
            "naturaleza",
        ],
        ascending=[
            False,
            True,
        ],
        kind="stable",
        na_position="last",
    )

    return resumen.reset_index(
        drop=True
    )


def convertir_a_csv(
    tabla,
):
    """Convierte un DataFrame en contenido CSV descargable.

    El resultado:

      - No contiene la columna índice de pandas.
      - Usa salto de línea uniforme.
      - Representa los valores faltantes con una cadena vacía.
      - Incluye la marca BOM de UTF-8 para facilitar la apertura del
        archivo en aplicaciones que la utilizan para reconocer texto
        con caracteres como tildes y la letra ñ.
    """

    if not isinstance(
        tabla,
        pd.DataFrame,
    ):
        raise TypeError(
            "La conversión a CSV requiere "
            "un pandas.DataFrame."
        )

    contenido = tabla.to_csv(
        index=False,
        encoding="utf-8-sig",
        lineterminator="\n",
        na_rep="",
    )

    return (
        "\ufeff"
        + contenido.lstrip(
            "\ufeff"
        )
    )


def generar_nombre_archivo(
    tipo,
    momento=None,
):
    """Genera un nombre identificable para cada descarga.

    Parámetros
    ----------
    tipo : str
        Uno de los siguientes valores:

        - ``detalle``
        - ``servicio``
        - ``naturaleza``
        - ``metadata``

    momento : datetime, opcional
        Fecha y hora utilizadas en el nombre. Este parámetro permite
        realizar pruebas deterministas.

        Si no se proporciona, se usa la fecha y hora actual de Colombia.

    Retorna
    -------
    str
        Nombre CSV con el patrón:

        ``quiron_tipo_YYYYMMDD_HHMMSS.csv``
    """

    tipos_validos = {
        "detalle": (
            "detalle_oferta_quirurgica"
        ),
        "servicio": (
            "resumen_por_servicio"
        ),
        "naturaleza": (
            "resumen_por_naturaleza"
        ),
        "metadata": (
            "metadata_trazabilidad"
        ),
    }

    if tipo not in tipos_validos:
        permitidos = ", ".join(
            sorted(
                tipos_validos
            )
        )

        raise ValueError(
            "Tipo de exportación no válido: "
            f"{tipo!r}. "
            f"Permitidos: {permitidos}."
        )

    instante = (
        momento
        or datetime.now(
            ZONA_HORARIA_COLOMBIA
        )
    )

    if instante.tzinfo is None:
        instante = instante.replace(
            tzinfo=(
                ZONA_HORARIA_COLOMBIA
            )
        )
    else:
        instante = instante.astimezone(
            ZONA_HORARIA_COLOMBIA
        )

    marca_temporal = instante.strftime(
        "%Y%m%d_%H%M%S"
    )

    nombre_base = tipos_validos[
        tipo
    ]

    return (
        f"quiron_{nombre_base}_"
        f"{marca_temporal}.csv"
    )