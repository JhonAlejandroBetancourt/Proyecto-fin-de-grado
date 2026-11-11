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
from time import perf_counter

import pandas as pd

from quiron.data.loader import (
    ARCHIVO_CIRUGIA_PLASTICA,
    CODIGOS_QUIRURGICOS,
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
):
    """Documenta el mapeo de campos origen → destino en la traza."""

    filas = len(tabla)

    traza.mapear(
        campo_origen="Encabezados del CSV",
        campo_destino="Encabezados normalizados",
        transformacion=(
            "Eliminación de saltos de línea y compactación "
            "de espacios; descarte de columnas Unnamed"
        ),
        filas=filas,
    )

    traza.mapear(
        campo_origen="Campos de texto del CSV",
        campo_destino="Campos de texto limpios",
        transformacion=(
            "Recorte de espacios y normalización de saltos "
            "de línea; se descartan filas sin nombre de sede"
        ),
        filas=filas,
    )

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

    traza.mapear(
        campo_origen="sedes_geocodificadas.csv",
        campo_destino=(
            "latitud, longitud, coordenada_valida"
        ),
        transformacion=(
            "Validación de coordenadas y cruce por coincidencia "
            "única de nombre y dirección normalizados; las claves "
            "vacías o ambiguas no reciben coordenadas"
        ),
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
    nombre = nombre_fuente or "archivo cargado"
    etapa_actual = {
        "fase": "Extracción",
        "nombre": "Lectura de la fuente",
    }
    error_reportado = False

    def observar_etapa(evento):
        nonlocal error_reportado
        etapa_actual["fase"] = evento.get(
            "fase",
            etapa_actual["fase"],
        )
        etapa_actual["nombre"] = evento.get(
            "nombre",
            etapa_actual["nombre"],
        )
        if evento.get("estado") == "en_progreso":
            return

        nivel = NivelTraza(
            evento.get(
                "nivel",
                NivelTraza.INFO.value,
            )
        )
        if nivel is NivelTraza.ERROR:
            error_reportado = True
        traza.registrar(
            nombre=etapa_actual["nombre"],
            fase=etapa_actual["fase"],
            mensaje=evento.get(
                "mensaje",
                "Etapa completada sin mensaje.",
            ),
            nivel=nivel,
            filas=evento.get("filas_salida"),
            filas_entrada=evento.get("filas_entrada"),
            filas_salida=evento.get("filas_salida"),
            filas_eliminadas=evento.get("filas_eliminadas"),
            columnas_entrada=evento.get("columnas_entrada"),
            columnas_salida=evento.get("columnas_salida"),
            detalle=evento.get("detalle"),
            duracion_ms=evento.get("duracion_ms"),
        )

    try:
        etapa_actual.update(
            fase="Extracción",
            nombre="Lectura de la fuente",
        )
        inicio_lectura = perf_counter()
        contenido, nombre = _normalizar_a_bytes(origen)
        if nombre_fuente:
            nombre = nombre_fuente
        traza.registrar(
            nombre="Lectura del contenido",
            fase="Extracción",
            mensaje=(
                f"Se recibieron {len(contenido)} bytes desde "
                f"'{nombre}'."
            ),
            nivel=NivelTraza.EXITO,
            detalle="La fuente se procesa en memoria; no se guarda en disco.",
            duracion_ms=(
                (perf_counter() - inicio_lectura)
                * 1000.0
            ),
        )

        etapa_actual.update(
            fase="Control",
            nombre="Huella e identificación de fuente",
        )
        inicio_huella = perf_counter()
        huella = _calcular_huella(contenido)
        huella_incluida = _calcular_huella(
            ARCHIVO_CIRUGIA_PLASTICA.read_bytes()
        )
        misma_fuente_binaria = huella == huella_incluida
        traza.registrar(
            nombre="Huella e identificación de fuente",
            fase="Control",
            mensaje=(
                "La fuente coincide byte a byte con la incluida."
                if misma_fuente_binaria
                else (
                    "La fuente difiere de la incluida; la asociación "
                    "geográfica dependerá de coincidencias únicas."
                )
            ),
            nivel=(
                NivelTraza.EXITO
                if misma_fuente_binaria
                else NivelTraza.INFO
            ),
            detalle=f"SHA-256: {huella}",
            duracion_ms=(
                (perf_counter() - inicio_huella)
                * 1000.0
            ),
        )

        tabla = cargar_oferta_con_coordenadas(
            origen=contenido,
            nombre_fuente=nombre,
            observador=observar_etapa,
        )

        etapa_actual.update(
            fase="Transformación",
            nombre="Trazabilidad de mapeo",
        )
        inicio_mapeo = perf_counter()
        _registrar_mapeo_campos(
            tabla,
            traza,
        )
        traza.registrar(
            nombre="Trazabilidad de mapeo",
            fase="Transformación",
            mensaje=(
                f"Se documentaron {len(traza.mapeos)} relaciones "
                "entre campos de origen y resultado."
            ),
            nivel=NivelTraza.EXITO,
            filas_entrada=len(tabla),
            filas_salida=len(tabla),
            detalle=(
                "Incluye limpieza, renombrado, normalización, "
                "transformación de servicios y enriquecimiento "
                "geográfico."
            ),
            duracion_ms=(
                (perf_counter() - inicio_mapeo)
                * 1000.0
            ),
        )

        quirurgicas = tabla.loc[
            tabla["es_quirurgico"]
            .fillna(False)
            .astype(bool)
        ]
        sedes_quirurgicas = quirurgicas[
            "sede_id"
        ].nunique()
        coordenadas_validas = int(
            quirurgicas[
                "coordenada_valida"
            ].fillna(False).astype(bool).sum()
        )

        etapa_actual.update(
            fase="Carga",
            nombre="Carga del conjunto transformado",
        )
        inicio_carga = perf_counter()
        traza.registrar(
            nombre="Carga del conjunto transformado",
            fase="Carga",
            mensaje=(
                f"Dataset listo: {len(tabla)} registros, "
                f"{tabla['sede_id'].nunique()} sedes y "
                f"{sedes_quirurgicas} sedes con oferta quirúrgica."
            ),
            nivel=NivelTraza.EXITO,
            filas=len(tabla),
            filas_entrada=len(tabla),
            filas_salida=len(tabla),
            detalle=(
                f"{coordenadas_validas} registros quirúrgicos con "
                "coordenadas válidas. El DataFrame queda disponible "
                "para la aplicación."
            ),
            duracion_ms=(
                (perf_counter() - inicio_carga)
                * 1000.0
            ),
        )

        return ResultadoETL(
            tabla=tabla,
            traza=traza,
            huella_sha256=huella,
            nombre_fuente=nombre,
            exito=True,
        )

    except Exception as error:  # noqa: BLE001
        if not error_reportado:
            traza.registrar(
                nombre=etapa_actual["nombre"],
                fase=etapa_actual["fase"],
                mensaje=str(error),
                nivel=NivelTraza.ERROR,
            )

        return ResultadoETL(
            tabla=None,
            traza=traza,
            huella_sha256=huella,
            nombre_fuente=nombre,
            exito=False,
        )
