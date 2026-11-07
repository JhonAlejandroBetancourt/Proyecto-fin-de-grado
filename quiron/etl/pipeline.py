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
import io
from dataclasses import dataclass, field

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
    informe: dict = field(
        default_factory=dict
    )

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
        datos["informe"] = self.informe
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
    columnas_origen,
    traza,
    filas=None,
):
    """Registra tanto los mapeos reales como los campos ignorados."""

    columnas = [
        " ".join(
            str(columna).split()
        )
        for columna in columnas_origen
    ]

    for origen in columnas:
        if origen in MAPEO_COLUMNAS_BASE:
            destino = MAPEO_COLUMNAS_BASE[
                origen
            ]
            transformacion = (
                "Renombrado y normalizado "
                "(sin saltos de línea)"
            )
            estado = "Mapeado"
        elif origen[:1].isdigit():
            destino = (
                "codigo_servicio, nombre_servicio"
            )
            transformacion = (
                "Columna de servicio en formato "
                "ancho; se transforma en filas por "
                "sede y servicio marcado con 'X'."
            )
            estado = "Mapeado"
        elif origen.casefold().startswith(
            "unnamed"
        ):
            destino = "—"
            transformacion = (
                "Columna auxiliar sin encabezado; "
                "se descarta."
            )
            estado = "Ignorado"
        else:
            destino = "Sin mapear"
            transformacion = (
                "Campo de origen no reconocido; "
                "se conserva en el informe y no se "
                "usa en los indicadores."
            )
            estado = "No mapeado"

        traza.mapear(
            campo_origen=origen,
            campo_destino=destino,
            transformacion=transformacion,
            filas=filas,
            estado=estado,
        )

    presentes = set(columnas)
    for campo in MAPEO_COLUMNAS_BASE:
        if campo not in presentes:
            traza.mapear(
                campo_origen="—",
                campo_destino=(
                    MAPEO_COLUMNAS_BASE[campo]
                ),
                transformacion=(
                    "Campo obligatorio ausente en "
                    "el archivo de origen."
                ),
                filas=filas,
                estado="Faltante",
            )

    traza.mapear(
        campo_origen="codigo_servicio",
        campo_destino="es_quirurgico",
        transformacion=(
            "Marca booleana para los códigos "
            f"quirúrgicos {sorted(CODIGOS_QUIRURGICOS)}"
        ),
        filas=filas,
        estado="Derivado",
    )

    traza.mapear(
        campo_origen="índice de fila",
        campo_destino="sede_id",
        transformacion=(
            "Identificador técnico de esta carga; "
            "no se usa para comparar cambios entre "
            "ejecuciones"
        ),
        filas=filas,
        estado="Derivado",
    )

    traza.mapear(
        campo_origen="sedes_geocodificadas.csv",
        campo_destino=(
            "latitud, longitud, coordenada_valida"
        ),
        transformacion=(
            "Coincidencia única por nombre de sede "
            "y dirección normalizados; independiente "
            "del orden de las filas"
        ),
        filas=filas,
        estado="Enriquecido",
    )


def _columnas_origen(contenido):
    """Lee los encabezados sin cargar de nuevo el conjunto completo."""

    tabla = pd.read_csv(
        io.BytesIO(contenido),
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
        nrows=0,
    )
    return [
        " ".join(
            str(columna).split()
        )
        for columna in tabla.columns
    ]


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
    columnas_origen = None
    informe = {
        "campos_no_mapeados": [],
        "campos_faltantes": [],
        "sedes_no_mapeadas": [],
        "duplicados": [],
        "duplicados_exactos": 0,
        "identidades_repetidas": 0,
    }

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

        columnas_origen = _columnas_origen(
            contenido
        )

        huella_incluida = _calcular_huella(
            ARCHIVO_CIRUGIA_PLASTICA.read_bytes()
        )
        misma_fuente_binaria = (
            huella == huella_incluida
        )

        tabla = cargar_oferta_con_coordenadas(
            origen=contenido,
            nombre_fuente=nombre,
        )
        _registrar_mapeo_campos(
            columnas_origen,
            traza,
            filas=len(tabla),
        )

        informe["campos_no_mapeados"] = [
            mapeo.como_dict()
            for mapeo in traza.mapeos
            if mapeo.estado == "No mapeado"
        ]
        informe["campos_faltantes"] = [
            mapeo.como_dict()
            for mapeo in traza.mapeos
            if mapeo.estado == "Faltante"
        ]
        informe["duplicados_exactos"] = int(
            tabla.attrs.get(
                "duplicados_exactos",
                0,
            )
        )
        informe["duplicados"] = list(
            tabla.attrs.get(
                "duplicados_exactos_registros",
                [],
            )
        )
        informe["identidades_repetidas"] = int(
            tabla.attrs.get(
                "identidades_repetidas",
                0,
            )
        )
        informe["sedes_no_mapeadas"] = (
            tabla.loc[
                tabla["es_quirurgico"]
                .fillna(False)
                .astype(bool)
                & ~tabla[
                    "coordenada_valida"
                ].fillna(False).astype(bool),
                [
                    "sede_id",
                    "sede",
                    "direccion",
                    "motivo_geocodificacion",
                ],
            ]
            .drop_duplicates(
                subset=["sede_id"]
            )
            .fillna("")
            .to_dict("records")
        )

        sedes_quirurgicas = tabla.loc[
            tabla["es_quirurgico"]
            .fillna(False)
            .astype(bool)
        ].drop_duplicates(
            subset=["sede_id"]
        )
        sedes_asociadas = int(
            sedes_quirurgicas[
                "direccion_normalizada"
            ].notna().sum()
        )
        sedes_totales = len(sedes_quirurgicas)
        sedes_con_coordenadas = int(
            sedes_quirurgicas[
                "coordenada_valida"
            ].fillna(False).astype(bool).sum()
        )
        informe["resumen"] = {
            "registros": int(len(tabla)),
            "sedes_quirurgicas": int(
                sedes_totales
            ),
            "sedes_con_coordenadas": (
                sedes_con_coordenadas
            ),
            "sedes_sin_coordenadas": int(
                len(
                    informe[
                        "sedes_no_mapeadas"
                    ]
                )
            ),
            "campos_mapeados": sum(
                mapeo.estado in (
                    "Mapeado",
                    "Derivado",
                    "Enriquecido",
                )
                for mapeo in traza.mapeos
            ),
            "campos_no_mapeados": len(
                informe["campos_no_mapeados"]
            ),
        }

        if informe["duplicados_exactos"]:
            traza.registrar(
                "Deduplicación",
                (
                    f"Se omitieron "
                    f"{informe['duplicados_exactos']} "
                    "filas idénticas repetidas del "
                    "archivo."
                ),
                nivel=NivelTraza.ADVERTENCIA,
                filas=(
                    informe["duplicados_exactos"]
                ),
            )
        if informe["identidades_repetidas"]:
            traza.registrar(
                "Identidades repetidas",
                (
                    f"Se detectaron "
                    f"{informe['identidades_repetidas']} "
                    "filas con nombre y dirección "
                    "repetidos; se revisará si sus "
                    "datos coinciden antes de "
                    "actualizar."
                ),
                nivel=NivelTraza.ADVERTENCIA,
                filas=(
                    informe["identidades_repetidas"]
                ),
            )

        if misma_fuente_binaria:
            mensaje_geocodificacion = (
                f"Se asociaron {sedes_asociadas} de "
                f"{sedes_totales} sedes quirúrgicas por "
                "coincidencia única de nombre y dirección; "
                f"{sedes_con_coordenadas} tienen "
                "coordenadas válidas."
            )
            nivel_geocodificacion = NivelTraza.EXITO
        else:
            sedes_sin_coincidencia = (
                sedes_totales - sedes_asociadas
            )
            if sedes_sin_coincidencia:
                mensaje_geocodificacion = (
                    "La huella del archivo difiere de la "
                    "fuente original. Se asociaron "
                    f"{sedes_asociadas} de {sedes_totales} "
                    "sedes quirúrgicas solo mediante "
                    "coincidencia única de nombre y "
                    "dirección; "
                    f"{sedes_sin_coincidencia} sin "
                    "coincidencia segura; "
                    f"{sedes_con_coordenadas} tienen "
                    "coordenadas válidas."
                )
                nivel_geocodificacion = (
                    NivelTraza.ADVERTENCIA
                )
            else:
                mensaje_geocodificacion = (
                    "Aunque la huella del archivo difiere, "
                    "se asociaron todas las sedes quirúrgicas "
                    "mediante coincidencia única de nombre y "
                    "dirección; "
                    f"{sedes_con_coordenadas} tienen "
                    "coordenadas válidas."
                )
                nivel_geocodificacion = NivelTraza.EXITO

        traza.registrar(
            "Geocodificación",
            mensaje_geocodificacion,
            nivel=nivel_geocodificacion,
            filas=sedes_asociadas,
        )

        traza.registrar(
            "Transformación",
            "Transformación de formato ancho a "
            "largo completada.",
            nivel=NivelTraza.EXITO,
            filas=len(tabla),
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
            informe=informe,
        )

    except Exception as error:  # noqa: BLE001
        if columnas_origen is not None and not traza.mapeos:
            _registrar_mapeo_campos(
                columnas_origen,
                traza,
            )
            informe["campos_no_mapeados"] = [
                mapeo.como_dict()
                for mapeo in traza.mapeos
                if mapeo.estado == "No mapeado"
            ]
            informe["campos_faltantes"] = [
                mapeo.como_dict()
                for mapeo in traza.mapeos
                if mapeo.estado == "Faltante"
            ]
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
            informe=informe,
        )
