"""Metadata y trazabilidad de las fuentes utilizadas por Quirón.

Este módulo centraliza la información metodológica que debe mostrarse en
el dashboard y acompañar las exportaciones. No modifica los archivos ni
los registros analíticos.

La fecha de corte se declara explícitamente. No se utiliza la fecha de
modificación del archivo porque esa marca pertenece al sistema de
archivos y no demuestra el periodo de referencia de la fuente.
"""

from copy import deepcopy
from datetime import date
from pathlib import Path

import pandas as pd


NOMBRE_PROYECTO = (
    "Dashboard para el análisis de la oferta registrada de servicios "
    "quirúrgicos de las IPS de Bogotá D.C."
)

ENTIDAD_PUBLICADORA = (
    "Secretaría Distrital de Salud de Bogotá"
)

PORTAL_PUBLICACION = (
    "Datos Abiertos Bogotá"
)

NOMBRE_CONJUNTO_DATOS = (
    "IPS habilitadas con oferta de servicios quirúrgicos "
    "de cirugía estética"
)

URL_FUENTE = (
    "https://datosabiertos.bogota.gov.co/dataset/"
    "ips-servicios-cirugia-estetica"
)

ARCHIVO_PRINCIPAL = (
    "cirugia-plastica-01_07_2026.csv"
)

ARCHIVO_GEOCODIFICADO = (
    "sedes_geocodificadas.csv"
)

# Fecha declarada por el corte utilizado en el proyecto.
#
# IMPORTANTE:
# Esta fecha se estableció con base en el nombre del archivo utilizado.
# Debe verificarse contra la documentación del recurso oficial antes de
# la entrega académica definitiva.
#
# Si la entidad publica un archivo posterior, esta constante debe
# actualizarse únicamente después de verificar la fecha de corte del
# nuevo recurso.
FECHA_CORTE = date(
    2026,
    7,
    1,
)

COBERTURA_GEOGRAFICA = (
    "Bogotá D.C."
)

UNIDAD_ANALISIS = (
    "Sede y servicio registrado"
)

CODIGOS_QUIRURGICOS_ANALIZADOS = (
    "213",
    "369",
)

ADVERTENCIA_INTERPRETACION = (
    "Los resultados describen oferta registrada en la fuente utilizada. "
    "No representan disponibilidad en tiempo real, capacidad efectiva de "
    "atención, número de procedimientos, tiempos de espera, demanda, "
    "resultados clínicos ni calidad del servicio."
)

ADVERTENCIA_GEOCODIFICACION = (
    "La ubicación cartográfica proviene de un proceso de normalización y "
    "geocodificación de direcciones. Las sedes sin coordenadas válidas se "
    "conservan en el conjunto analítico, pero no se muestran en el mapa."
)

METADATA_BASE = {
    "proyecto": (
        NOMBRE_PROYECTO
    ),
    "entidad_publicadora": (
        ENTIDAD_PUBLICADORA
    ),
    "portal_publicacion": (
        PORTAL_PUBLICACION
    ),
    "conjunto_datos": (
        NOMBRE_CONJUNTO_DATOS
    ),
    "url_fuente": (
        URL_FUENTE
    ),
    "archivo_principal": (
        ARCHIVO_PRINCIPAL
    ),
    "archivo_geocodificado": (
        ARCHIVO_GEOCODIFICADO
    ),
    "fecha_corte": (
        FECHA_CORTE.isoformat()
    ),
    "fecha_corte_legible": (
        FECHA_CORTE.strftime(
            "%d/%m/%Y"
        )
    ),
    "cobertura_geografica": (
        COBERTURA_GEOGRAFICA
    ),
    "unidad_analisis": (
        UNIDAD_ANALISIS
    ),
    "codigos_quirurgicos": list(
        CODIGOS_QUIRURGICOS_ANALIZADOS
    ),
    "advertencia_interpretacion": (
        ADVERTENCIA_INTERPRETACION
    ),
    "advertencia_geocodificacion": (
        ADVERTENCIA_GEOCODIFICACION
    ),
}

COLUMNAS_REQUERIDAS = {
    "sede_id",
    "codigo_servicio",
    "es_quirurgico",
    "coordenada_valida",
}


def _validar_tabla(tabla):
    """Valida la estructura necesaria para calcular cobertura."""

    if not isinstance(
        tabla,
        pd.DataFrame,
    ):
        raise TypeError(
            "La metadata dinámica requiere una "
            "instancia de pandas.DataFrame."
        )

    columnas_faltantes = (
        COLUMNAS_REQUERIDAS.difference(
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
            "No es posible calcular la metadata "
            "porque faltan las columnas: "
            f"{nombres}."
        )


def _validar_archivo_fuente(
    ruta_archivo,
):
    """Valida que la ruta corresponda al archivo esperado."""

    ruta = Path(
        ruta_archivo
    )

    if not ruta.exists():
        raise FileNotFoundError(
            "No se encontró el archivo fuente "
            f"requerido: {ruta}."
        )

    if not ruta.is_file():
        raise ValueError(
            "La ruta indicada no corresponde "
            f"a un archivo: {ruta}."
        )

    if ruta.name != ARCHIVO_PRINCIPAL:
        raise ValueError(
            "El archivo recibido no coincide "
            "con el recurso documentado. "
            f"Esperado: {ARCHIVO_PRINCIPAL}. "
            f"Recibido: {ruta.name}."
        )

    return ruta


def _calcular_cobertura(
    tabla,
):
    """Calcula conteos trazables sobre sedes únicas.

    El total de registros corresponde al número de filas de la tabla.

    Los conteos de sedes se realizan con ``sede_id`` únicos para evitar
    contar varias veces una sede que registre más de un servicio.
    """

    _validar_tabla(
        tabla
    )

    oferta_quirurgica = tabla.loc[
        tabla[
            "es_quirurgico"
        ]
        .fillna(False)
        .astype(bool)
    ].copy()

    total_registros = int(
        len(tabla)
    )

    registros_quirurgicos = int(
        len(oferta_quirurgica)
    )

    sedes_quirurgicas = int(
        oferta_quirurgica[
            "sede_id"
        ].nunique()
    )

    sedes_geocodificadas = int(
        oferta_quirurgica.loc[
            oferta_quirurgica[
                "coordenada_valida"
            ]
            .fillna(False)
            .astype(bool),
            "sede_id",
        ].nunique()
    )

    sedes_sin_coordenadas = (
        sedes_quirurgicas
        - sedes_geocodificadas
    )

    porcentaje_geocodificacion = (
        sedes_geocodificadas
        / sedes_quirurgicas
        * 100
    ) if sedes_quirurgicas else 0.0

    codigos_presentes = sorted(
        oferta_quirurgica[
            "codigo_servicio"
        ]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[
            lambda serie: serie.ne("")
        ]
        .unique()
        .tolist()
    )

    return {
        "total_registros": (
            total_registros
        ),
        "registros_quirurgicos": (
            registros_quirurgicos
        ),
        "sedes_quirurgicas": (
            sedes_quirurgicas
        ),
        "sedes_geocodificadas": (
            sedes_geocodificadas
        ),
        "sedes_sin_coordenadas": int(
            sedes_sin_coordenadas
        ),
        "porcentaje_geocodificacion": round(
            porcentaje_geocodificacion,
            1,
        ),
        "codigos_quirurgicos_presentes": (
            codigos_presentes
        ),
    }


def obtener_metadata(
    tabla=None,
    ruta_archivo=None,
):
    """Devuelve una copia independiente de la metadata.

    Parámetros
    ----------
    tabla : pandas.DataFrame, opcional
        Tabla resultante de
        ``cargar_oferta_con_coordenadas``.

        Cuando se proporciona, se añaden conteos y cobertura calculados
        desde los datos realmente cargados.

    ruta_archivo : str o pathlib.Path, opcional
        Ruta del CSV principal.

        Cuando se proporciona, se valida su existencia y su nombre, y se
        añade su tamaño en bytes.

        La fecha de modificación del archivo no se utiliza como fecha de
        corte porque no representa necesariamente la fecha de referencia
        de la fuente oficial.

    Retorna
    -------
    dict
        Copia independiente de la metadata estática y dinámica.
    """

    metadata = deepcopy(
        METADATA_BASE
    )

    if tabla is not None:
        metadata[
            "cobertura_datos"
        ] = _calcular_cobertura(
            tabla
        )

    if ruta_archivo is not None:
        ruta = _validar_archivo_fuente(
            ruta_archivo
        )

        metadata[
            "archivo_fuente"
        ] = {
            "nombre": (
                ruta.name
            ),
            "tamano_bytes": int(
                ruta.stat().st_size
            ),
        }

    return metadata


def metadata_para_exportacion(
    tabla,
    ruta_archivo=None,
):
    """Convierte la metadata a pares clave-valor para CSV.

    Las listas se serializan como texto separado por punto y coma.

    Los diccionarios internos, por ejemplo ``cobertura_datos``, se
    aplanan usando el nombre del bloque como prefijo.
    """

    metadata = obtener_metadata(
        tabla=tabla,
        ruta_archivo=ruta_archivo,
    )

    filas = []

    for clave, valor in metadata.items():
        if isinstance(
            valor,
            dict,
        ):
            for subclave, subvalor in valor.items():
                filas.append(
                    {
                        "campo": (
                            f"{clave}_{subclave}"
                        ),
                        "valor": _serializar_valor(
                            subvalor
                        ),
                    }
                )
        else:
            filas.append(
                {
                    "campo": clave,
                    "valor": _serializar_valor(
                        valor
                    ),
                }
            )

    return pd.DataFrame(
        filas,
        columns=[
            "campo",
            "valor",
        ],
    )


def _serializar_valor(
    valor,
):
    """Serializa valores simples y colecciones."""

    if isinstance(
        valor,
        (
            list,
            tuple,
            set,
        ),
    ):
        return "; ".join(
            str(elemento)
            for elemento in valor
        )

    if valor is None:
        return ""

    return str(
        valor
    )