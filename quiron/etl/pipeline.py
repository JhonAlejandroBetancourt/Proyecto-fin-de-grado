"""Orquestación instrumentada del ETL de Quirón.

Este módulo ejecuta el proceso ETL de la oferta quirúrgica emitiendo una
``TrazaETL`` con el histórico de pasos, la traza de mapeo de campos, los
errores y la huella SHA-256 del contenido procesado.

El objetivo es que la interfaz pueda mostrar, de forma transparente, cómo
se construyó el conjunto de datos a partir de un CSV, ya sea el archivo
incluido en el proyecto o uno cargado por la persona usuaria.

Cuando una fuente cargada falla la validación, ``ejecutar_etl`` NO lanza
la excepción hacia arriba: la captura, la registra en la traza y devuelve
un ``ResultadoETL`` sin tabla. Así el dashboard puede conservar el
conjunto de datos vigente y mostrar los errores sin interrumpirse.
"""

import hashlib
from dataclasses import dataclass

import pandas as pd

from quiron.data.loader import (
    ARCHIVO_CIRUGIA_PLASTICA,
    CODIGOS_QUIRURGICOS,
    cargar_cirugia_plastica,
    cargar_oferta_con_coordenadas,
)
from quiron.etl.observabilidad import (
    NivelTraza,
    TrazaETL,
)


MAPEO_COLUMNAS_BASE = {
    "SEDE -NOMBRE": "sede",
    "DIRECCION": "direccion",
    "TELEFONO": "telefono",
    "CORREO ELECTRÓNICO": "correo",
    "NATURALEZA": "naturaleza",
    "TIPO DE PRESTADOR": "tipo_prestador",
}


@dataclass
class ResultadoETL:
    """Resultado de una ejecución instrumentada del ETL."""

    tabla: pd.DataFrame | None
    traza: TrazaETL
    huella_sha256: str | None
    nombre_fuente: str
    exito: bool

    def como_dict_traza(self):
        """Devuelve la traza serializada junto con metadatos de la fuente."""

        datos = self.traza.como_dict()
        datos["huella_sha256"] = (
            self.huella_sha256
        )
        datos["nombre_fuente"] = (
            self.nombre_fuente
        )
        datos["exito"] = self.exito
        return datos


def _calcular_huella(contenido):
    """Calcula la huella SHA-256 del contenido en bytes."""

    return hashlib.sha256(
        contenido
    ).hexdigest()


def _normalizar_a_bytes(
    origen,
):
    """Obtiene el contenido en bytes de la fuente para el ETL.

    Devuelve una tupla ``(bytes, nombre)``. Cuando ``origen`` es ``None``
    se lee el archivo incluido en el proyecto.
    """

    from pathlib import Path

    from quiron.data.loader import (
        ARCHIVO_CIRUGIA_PLASTICA,
    )

    if origen is None:
        contenido = (
            ARCHIVO_CIRUGIA_PLASTICA.read_bytes()
        )
        return (
            contenido,
            ARCHIVO_CIRUGIA_PLASTICA.name,
        )

    if isinstance(origen, bytes):
        return (origen, "archivo cargado")

    if isinstance(origen, (str, Path)):
        ruta = Path(origen)
        return (
            ruta.read_bytes(),
            ruta.name,
        )

    # Objeto tipo archivo (por ejemplo io.BytesIO).
    contenido = origen.read()
    if isinstance(contenido, str):
        contenido = contenido.encode(
            "utf-8"
        )
    return (contenido, "archivo cargado")


def _registrar_mapeo_campos(
    tabla,
    traza,
    incluir_geocodificacion,
):
    """Documenta el mapeo de campos origen → destino en la traza."""

    filas = len(tabla)

    for origen, destino in (
        MAPEO_COLUMNAS_BASE.items()
    ):
        traza.mapear(
            campo_origen=origen,
            campo_destino=destino,
            transformacion=(
                "Renombrado y normalizado "
                "(sin saltos de línea)"
            ),
            filas=filas,
        )

    traza.mapear(
        campo_origen=(
            "Columnas '<código> - <nombre>'"
        ),
        campo_destino=(
            "codigo_servicio, nombre_servicio"
        ),
        transformacion=(
            "Transformación de formato ancho a "
            "largo: una fila por sede y servicio "
            "marcado con 'X'"
        ),
        filas=filas,
    )

    traza.mapear(
        campo_origen="codigo_servicio",
        campo_destino="es_quirurgico",
        transformacion=(
            "Marca booleana para los códigos "
            f"quirúrgicos {sorted(CODIGOS_QUIRURGICOS)}"
        ),
        filas=filas,
    )

    traza.mapear(
        campo_origen="índice de fila",
        campo_destino="sede_id",
        transformacion=(
            "Identificador de sede derivado del "
            "orden de filas del origen"
        ),
        filas=filas,
    )

    if incluir_geocodificacion:
        transformacion_coordenadas = (
            "Unión segura por sede_id; el "
            "contenido coincide con el CSV "
            "geocodificado"
        )
    else:
        transformacion_coordenadas = (
            "No se reutilizan coordenadas: "
            "sede_id depende del orden de filas "
            "y el CSV cargado es diferente"
        )

    traza.mapear(
        campo_origen="sedes_geocodificadas.csv",
        campo_destino=(
            "latitud, longitud, coordenada_valida"
        ),
        transformacion=transformacion_coordenadas,
        filas=filas,
    )


def ejecutar_etl(
    origen=None,
    nombre_fuente=None,
):
    """Ejecuta el ETL de la oferta quirúrgica de forma instrumentada.

    Parámetros
    ----------
    origen : ruta, buffer o ``bytes``, opcional
        Fuente de datos. ``None`` usa el archivo incluido en el proyecto.

    nombre_fuente : str, opcional
        Nombre descriptivo de la fuente para la traza y los errores.

    Retorna
    -------
    ResultadoETL
        Contiene la tabla resultante (o ``None`` si falló), la traza
        completa, la huella SHA-256 del contenido y el estado de éxito.
    """

    traza = TrazaETL()

    traza.registrar(
        "Inicio",
        "Inicio del proceso ETL de la oferta "
        "quirúrgica.",
        nivel=NivelTraza.INFO,
    )

    huella = None
    nombre = (
        nombre_fuente
        or "archivo cargado"
    )

    try:
        contenido, nombre = _normalizar_a_bytes(
            origen,
        )

        if nombre_fuente:
            nombre = nombre_fuente

        huella = _calcular_huella(contenido)

        traza.registrar(
            "Extracción",
            "Lectura del contenido de "
            f"'{nombre}' ({len(contenido)} bytes). "
            f"Huella SHA-256: {huella[:12]}…",
            nivel=NivelTraza.INFO,
        )

        huella_incluida = _calcular_huella(
            ARCHIVO_CIRUGIA_PLASTICA.read_bytes()
        )
        incluir_geocodificacion = (
            huella == huella_incluida
        )

        if incluir_geocodificacion:
            tabla = cargar_oferta_con_coordenadas(
                origen=contenido,
                nombre_fuente=nombre,
            )
        else:
            tabla = cargar_cirugia_plastica(
                origen=contenido,
                nombre_fuente=nombre,
            )
            tabla["direccion_normalizada"] = [
                None
            ] * len(tabla)
            tabla["latitud"] = [None] * len(tabla)
            tabla["longitud"] = [None] * len(tabla)
            tabla["geocodificado"] = False
            tabla["coordenada_valida"] = False

            traza.registrar(
                "Geocodificación",
                "No se reutilizaron coordenadas del "
                "CSV del proyecto porque el archivo "
                "cargado tiene una huella diferente; "
                "los identificadores dependen del "
                "orden de filas.",
                nivel=NivelTraza.ADVERTENCIA,
                filas=len(tabla),
            )

        traza.registrar(
            "Transformación",
            "Transformación de formato ancho a "
            "largo completada.",
            nivel=NivelTraza.EXITO,
            filas=len(tabla),
        )

        _registrar_mapeo_campos(
            tabla,
            traza,
            incluir_geocodificacion,
        )

        quirurgicas = tabla[
            tabla["es_quirurgico"]
        ]
        sedes_quirurgicas = quirurgicas[
            "sede_id"
        ].nunique()

        traza.registrar(
            "Carga",
            "Conjunto de datos listo: "
            f"{len(tabla)} registros, "
            f"{sedes_quirurgicas} sedes con oferta "
            "quirúrgica.",
            nivel=NivelTraza.EXITO,
            filas=len(tabla),
        )

        return ResultadoETL(
            tabla=tabla,
            traza=traza,
            huella_sha256=huella,
            nombre_fuente=nombre,
            exito=True,
        )

    except Exception as error:  # noqa: BLE001
        traza.registrar_error(
            "Validación",
            "El ETL no pudo completarse: "
            f"{error}",
        )

        return ResultadoETL(
            tabla=None,
            traza=traza,
            huella_sha256=huella,
            nombre_fuente=nombre,
            exito=False,
        )
