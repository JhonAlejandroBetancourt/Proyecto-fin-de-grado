"""Lectura de las fuentes crudas publicadas por la Secretaría de Salud.

Cada archivo llega con su propia idiosincrasia de codificación y formato
(la Secretaría publica unos en UTF-8 con BOM y otros en Latin-1, cosas de
exportar desde Excel en distintos equipos), así que este módulo se encarga
de domesticarlos antes de que el resto de la aplicación los toque.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent / "raw"

ARCHIVO_CIRUGIA_PLASTICA = RAW_DIR / "cirugia-plastica-01_07_2026.csv"
ARCHIVO_TIPO_PRESTADORES = RAW_DIR / "osb_tipoprestadores.csv"
ARCHIVO_URGENCIAS = RAW_DIR / "osb_ofertasrv-ips-urgencias.csv"

# Códigos de habilitación REPS que sí corresponden a un procedimiento
# quirúrgico. Las columnas 356 y 397 son consulta/medicina estética y
# quedan fuera del alcance del proyecto, pero se conservan en el dataset
# para poder explicar por qué una sede aparece sin ser "quirúrgica".
CODIGOS_QUIRURGICOS = {"213", "369"}


def _sin_saltos(texto: str) -> str:
    return " ".join(texto.split())


def _columnas_de_servicio(columnas) -> list[str]:
    return [c for c in columnas if c[:1].isdigit()]


def cargar_cirugia_plastica() -> pd.DataFrame:
    """Devuelve una tabla larga: una fila por cada (sede, servicio) marcado
    con "X" en el archivo original, que venía en formato ancho.
    """
    crudo = pd.read_csv(ARCHIVO_CIRUGIA_PLASTICA, sep=";", encoding="utf-8-sig")
    crudo.columns = [_sin_saltos(c) for c in crudo.columns]
    crudo = crudo.loc[:, ~crudo.columns.str.contains(r"^Unnamed")]
    crudo = crudo.dropna(subset=["SEDE -NOMBRE"])

    columnas_servicio = _columnas_de_servicio(crudo.columns)

    fijas = {
        "SEDE -NOMBRE": "sede",
        "DIRECCION": "direccion",
        "TELEFONO": "telefono",
        "CORREO ELECTRÓNICO": "correo",
        "NATURALEZA": "naturaleza",
        "TIPO DE PRESTADOR": "tipo_prestador",
    }
    base = crudo.rename(columns=fijas)[list(fijas.values())].copy()
    base["sede_id"] = base.index.astype(str)

    marcadas = crudo[columnas_servicio].notna()
    marcadas.index = base["sede_id"]

    filas = []
    for columna in columnas_servicio:
        codigo, _, nombre = columna.partition(" - ")
        codigo = codigo.strip()
        # Dos códigos REPS distintos (213 y 369) comparten la misma
        # descripción textual en el archivo fuente. Se antepone el código
        # para no perder esa distinción al momento de agrupar resultados.
        nombre = f"{codigo} · {nombre.strip()}" if nombre.strip() else columna
        sedes_con_servicio = marcadas.index[marcadas[columna]]
        for sede_id in sedes_con_servicio:
            filas.append(
                {
                    "sede_id": sede_id,
                    "codigo_servicio": codigo,
                    "nombre_servicio": nombre,
                    "es_quirurgico": codigo in CODIGOS_QUIRURGICOS,
                }
            )

    servicios = pd.DataFrame(filas)
    tabla = servicios.merge(base, on="sede_id", how="left")
    columnas_orden = [
        "sede_id", "sede", "direccion", "telefono", "correo",
        "naturaleza", "tipo_prestador",
        "codigo_servicio", "nombre_servicio", "es_quirurgico",
    ]
    return tabla[columnas_orden].reset_index(drop=True)


def cargar_tipo_prestadores() -> pd.DataFrame:
    """Tabla oficial de referencia (Naturaleza x Tipo de prestador), útil
    para contrastar nuestras cifras contra el universo total de la ciudad.
    """
    tabla = pd.read_csv(ARCHIVO_TIPO_PRESTADORES, sep=";", encoding="latin-1")
    tabla["Porcentaje"] = (
        tabla["Porcentaje"].astype(str).str.replace(",", ".").astype(float)
    )
    tabla["Cantidad"] = pd.to_numeric(tabla["Cantidad"], errors="coerce").fillna(0).astype(int)
    return tabla


def cargar_urgencias() -> pd.DataFrame:
    """Sedes con servicio de urgencias habilitado, ya georreferenciadas.
    No entra en el conteo de oferta quirúrgica, pero servirá más adelante
    para enriquecer el mapa con puntos de referencia.
    """
    tabla = pd.read_csv(ARCHIVO_URGENCIAS, sep=";", encoding="latin-1")
    for columna in ("Longitud", "Latitud"):
        tabla[columna] = (
            tabla[columna].astype(str).str.replace(",", ".").astype(float)
        )
    return tabla