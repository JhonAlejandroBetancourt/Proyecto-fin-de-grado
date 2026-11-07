"""Compara sedes entre dos ejecuciones del ETL."""

from collections import Counter, defaultdict
import unicodedata

import pandas as pd


CAMPOS_COMPARABLES = {
    "direccion": "Dirección",
    "telefono": "Teléfono",
    "correo": "Correo electrónico",
    "naturaleza": "Naturaleza",
    "tipo_prestador": "Tipo de prestador",
    "servicios": "Servicios habilitados",
}


def _normalizar(valor):
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize(
        "NFKC",
        str(valor),
    )
    return " ".join(
        texto.casefold().split()
    )


def _registros_sede(tabla):
    registros = []
    columnas = (
        "sede",
        "direccion",
        "telefono",
        "correo",
        "naturaleza",
        "tipo_prestador",
    )

    for _, grupo in tabla.groupby(
        "sede_id",
        sort=False,
        dropna=False,
    ):
        primero = grupo.iloc[0]
        registro = {
            columna: (
                ""
                if pd.isna(primero.get(columna))
                else str(primero.get(columna))
            )
            for columna in columnas
        }
        registro["_nombre"] = _normalizar(
            registro["sede"]
        )
        registro["_direccion"] = _normalizar(
            registro["direccion"]
        )
        registro["_servicios"] = tuple(
            sorted(
                {
                    _normalizar(codigo)
                    for codigo in grupo[
                        "codigo_servicio"
                    ].dropna()
                }
            )
        )
        registro["_comparables"] = {
            **{
                campo: _normalizar(
                    registro[campo]
                )
                for campo in columnas
                if campo != "sede"
            },
            "servicios": registro[
                "_servicios"
            ],
        }
        registros.append(registro)

    return registros


def _indexar_sedes(tabla_anterior, tabla_nueva):
    anteriores = _registros_sede(
        tabla_anterior
    )
    nuevas = _registros_sede(
        tabla_nueva
    )
    frecuencias = {
        "anterior": Counter(
            registro["_nombre"]
            for registro in anteriores
            if registro["_nombre"]
        ),
        "nuevo": Counter(
            registro["_nombre"]
            for registro in nuevas
            if registro["_nombre"]
        ),
    }

    def clave(registro):
        nombre = registro["_nombre"]
        if (
            nombre
            and frecuencias["anterior"][nombre] == 1
            and frecuencias["nuevo"][nombre] == 1
        ):
            return ("nombre", nombre)
        return (
            "nombre-direccion",
            nombre,
            registro["_direccion"],
        )

    def agrupar(registros):
        resultado = defaultdict(list)
        for registro in registros:
            resultado[clave(registro)].append(
                registro
            )
        return resultado

    return agrupar(anteriores), agrupar(nuevas)


def comparar_datasets(tabla_anterior, tabla_nueva):
    """Compara instantáneas y solo actualiza cuando detecta cambios.

    El nombre identifica una sede únicamente cuando aparece una sola vez
    en ambos conjuntos. Si no, se usa nombre y dirección para evitar
    fusionar sedes distintas por una coincidencia ambigua.
    """

    anteriores, nuevas = _indexar_sedes(
        tabla_anterior,
        tabla_nueva,
    )
    sin_cambios = 0
    actualizadas = 0
    nuevas_sedes = 0
    retiradas = 0
    ambiguas = 0
    cambios = []

    for clave in anteriores.keys() | nuevas.keys():
        sedes_anteriores = anteriores.get(
            clave,
            [],
        )
        sedes_nuevas = nuevas.get(
            clave,
            [],
        )

        if not sedes_anteriores:
            nuevas_sedes += len(sedes_nuevas)
            continue
        if not sedes_nuevas:
            retiradas += len(sedes_anteriores)
            continue

        anterior = sedes_anteriores[0]
        nuevo = sedes_nuevas[0]
        if (
            len(sedes_anteriores) > 1
            or len(sedes_nuevas) > 1
        ):
            comparables_anteriores = {
                tuple(sorted(registro["_comparables"].items()))
                for registro in sedes_anteriores
            }
            comparables_nuevos = {
                tuple(sorted(registro["_comparables"].items()))
                for registro in sedes_nuevas
            }
            if (
                len(comparables_anteriores) != 1
                or len(comparables_nuevos) != 1
            ):
                ambiguas += 1
                cambios.append(
                    {
                        "sede": nuevo["sede"]
                        or anterior["sede"],
                        "campo": (
                            "Identidad ambigua; "
                            "no se actualizó"
                        ),
                        "valor_anterior": (
                            f"{len(sedes_anteriores)} "
                            "registros"
                        ),
                        "valor_nuevo": (
                            f"{len(sedes_nuevas)} "
                            "registros"
                        ),
                    }
                )
                continue
            anterior = sedes_anteriores[0]
            nuevo = sedes_nuevas[0]

        campos_modificados = []
        for campo, etiqueta in CAMPOS_COMPARABLES.items():
            valor_anterior = anterior[
                "_comparables"
            ][campo]
            valor_nuevo = nuevo[
                "_comparables"
            ][campo]
            if valor_anterior == valor_nuevo:
                continue

            campos_modificados.append(etiqueta)
            cambios.append(
                {
                    "sede": nuevo["sede"],
                    "campo": etiqueta,
                    "valor_anterior": (
                        ", ".join(valor_anterior)
                        if campo == "servicios"
                        else anterior.get(
                            campo,
                            "",
                        )
                    ),
                    "valor_nuevo": (
                        ", ".join(valor_nuevo)
                        if campo == "servicios"
                        else nuevo.get(
                            campo,
                            "",
                        )
                    ),
                }
            )

        if campos_modificados:
            actualizadas += 1
        else:
            sin_cambios += 1

    return {
        "sin_cambios": sin_cambios,
        "actualizadas": actualizadas,
        "nuevas": nuevas_sedes,
        "retiradas": retiradas,
        "ambiguas": ambiguas,
        "cambios": cambios,
        "sin_diferencias": not any(
            (
                actualizadas,
                nuevas_sedes,
                retiradas,
                ambiguas,
            )
        ),
    }
