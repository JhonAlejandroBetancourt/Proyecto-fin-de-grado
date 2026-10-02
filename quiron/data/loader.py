"""Carga y preparación de las fuentes de datos de Quirón.

Este módulo centraliza la lectura de los archivos CSV utilizados por la
aplicación. Ningún componente visual debe leer archivos directamente.

Fuentes administradas:
  - cirugia-plastica-01_07_2026.csv: oferta de servicios por sede.
  - osb_tipoprestadores.csv: resumen oficial por naturaleza y prestador.
  - osb_ofertasrv-ips-urgencias.csv: sedes de urgencias georreferenciadas.
  - sedes_geocodificadas.csv: resultado del proceso de geocodificación.

Principios de diseño:
  - Las rutas se resuelven desde la ubicación del paquete, no desde la
    carpeta desde la que se ejecuta Python.
  - Se validan las columnas obligatorias antes de transformar datos.
  - Los identificadores de sede se manejan como texto para conservar su
    consistencia entre archivos.
  - Una ausencia de datos se representa como valor nulo; no se inventan
    coordenadas ni categorías de relleno.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

ARCHIVO_CIRUGIA_PLASTICA = (
    RAW_DIR / "cirugia-plastica-01_07_2026.csv"
)

ARCHIVO_TIPO_PRESTADORES = (
    RAW_DIR / "osb_tipoprestadores.csv"
)

ARCHIVO_URGENCIAS = (
    RAW_DIR / "osb_ofertasrv-ips-urgencias.csv"
)

ARCHIVO_SEDES_GEOCODIFICADAS = (
    PROCESSED_DIR / "sedes_geocodificadas.csv"
)

CODIGOS_QUIRURGICOS = {
    "213",
    "369",
}

COLUMNAS_CIRUGIA_OBLIGATORIAS = {
    "SEDE -NOMBRE",
    "DIRECCION",
    "TELEFONO",
    "CORREO ELECTRÓNICO",
    "NATURALEZA",
    "TIPO DE PRESTADOR",
}

COLUMNAS_GEOCODIFICADAS_OBLIGATORIAS = {
    "sede_id",
    "sede",
    "direccion",
    "direccion_normalizada",
    "latitud",
    "longitud",
    "geocodificado",
}


def _validar_existencia(ruta_archivo):
    """Verifica que un archivo exista antes de intentar leerlo."""

    if not ruta_archivo.exists():
        raise FileNotFoundError(
            "No se encontró el archivo requerido: "
            f"{ruta_archivo}. "
            "Verifica la ruta y el nombre del archivo."
        )


def _validar_columnas(
    tabla,
    columnas_obligatorias,
    nombre_fuente,
):
    """Garantiza que una fuente contenga las columnas requeridas."""

    columnas_faltantes = columnas_obligatorias.difference(
        tabla.columns
    )

    if columnas_faltantes:
        faltantes = ", ".join(
            sorted(columnas_faltantes)
        )

        raise ValueError(
            f"La fuente '{nombre_fuente}' no contiene "
            f"las columnas obligatorias: {faltantes}."
        )


def _sin_saltos(texto):
    """Elimina saltos de línea y espacios repetidos."""

    return " ".join(
        str(texto).split()
    )


def _columnas_de_servicio(columnas):
    """Identifica las columnas cuyo nombre inicia con un código."""

    resultado = []

    for columna in columnas:
        if columna[:1].isdigit():
            resultado.append(columna)

    return resultado


def _normalizar_booleano(valor):
    """Convierte representaciones textuales a booleanos reales."""

    if pd.isna(valor):
        return False

    if isinstance(valor, bool):
        return valor

    texto = str(valor).strip().lower()

    valores_verdaderos = {
        "true",
        "1",
        "si",
        "sí",
        "s",
        "yes",
    }

    valores_falsos = {
        "false",
        "0",
        "no",
        "n",
        "",
    }

    if texto in valores_verdaderos:
        return True

    if texto in valores_falsos:
        return False

    raise ValueError(
        "Valor no reconocido en la columna "
        f"'geocodificado': {valor!r}."
    )


def cargar_cirugia_plastica():
    """Transforma la oferta desde formato ancho a formato largo.

    El resultado contiene una fila por combinación de sede y servicio.
    La columna ``es_quirurgico`` identifica los códigos incluidos en el
    alcance actual del proyecto.
    """

    _validar_existencia(
        ARCHIVO_CIRUGIA_PLASTICA
    )

    crudo = pd.read_csv(
        ARCHIVO_CIRUGIA_PLASTICA,
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
    )

    crudo.columns = [
        _sin_saltos(columna)
        for columna in crudo.columns
    ]

    crudo = crudo.loc[
        :,
        ~crudo.columns.str.contains(
            r"^Unnamed"
        ),
    ]

    _validar_columnas(
        crudo,
        COLUMNAS_CIRUGIA_OBLIGATORIAS,
        ARCHIVO_CIRUGIA_PLASTICA.name,
    )

    crudo = crudo.dropna(
        subset=["SEDE -NOMBRE"]
    ).copy()

    crudo = crudo.reset_index(
        drop=True
    )

    columnas_servicio = _columnas_de_servicio(
        crudo.columns
    )

    if not columnas_servicio:
        raise ValueError(
            "La fuente de cirugía plástica no "
            "contiene columnas de servicio "
            "identificadas por código numérico."
        )

    nombres_base = {
        "SEDE -NOMBRE": "sede",
        "DIRECCION": "direccion",
        "TELEFONO": "telefono",
        "CORREO ELECTRÓNICO": "correo",
        "NATURALEZA": "naturaleza",
        "TIPO DE PRESTADOR": "tipo_prestador",
    }

    base = crudo.rename(
        columns=nombres_base
    )[
        list(nombres_base.values())
    ].copy()

    base["sede_id"] = (
        base.index.astype(str)
    )

    marcas = crudo[
        columnas_servicio
    ].apply(
        lambda columna: (
            columna
            .fillna("")
            .str.strip()
            .str.upper()
            .eq("X")
        )
    )

    marcas.index = base["sede_id"]

    filas = []

    for columna in columnas_servicio:
        codigo, separador, nombre = (
            columna.partition(" - ")
        )

        codigo = codigo.strip()
        nombre_limpio = nombre.strip()

        if separador and nombre_limpio:
            nombre_final = (
                f"{codigo} · {nombre_limpio}"
            )
        else:
            nombre_final = columna.strip()

        sedes_con_servicio = marcas.index[
            marcas[columna]
        ]

        for sede_id in sedes_con_servicio:
            filas.append(
                {
                    "sede_id": sede_id,
                    "codigo_servicio": codigo,
                    "nombre_servicio": nombre_final,
                    "es_quirurgico": (
                        codigo
                        in CODIGOS_QUIRURGICOS
                    ),
                }
            )

    servicios = pd.DataFrame(
        filas
    )

    if servicios.empty:
        raise ValueError(
            "La fuente fue leída, pero no se "
            "encontraron servicios marcados "
            "con 'X'."
        )

    tabla = servicios.merge(
        base,
        on="sede_id",
        how="left",
        validate="many_to_one",
    )

    columnas_orden = [
        "sede_id",
        "sede",
        "direccion",
        "telefono",
        "correo",
        "naturaleza",
        "tipo_prestador",
        "codigo_servicio",
        "nombre_servicio",
        "es_quirurgico",
    ]

    return tabla[
        columnas_orden
    ].reset_index(
        drop=True
    )


def cargar_tipo_prestadores():
    """Carga la tabla oficial de contraste por tipo de prestador."""

    _validar_existencia(
        ARCHIVO_TIPO_PRESTADORES
    )

    tabla = pd.read_csv(
        ARCHIVO_TIPO_PRESTADORES,
        sep=";",
        encoding="latin-1",
        dtype=str,
    )

    tabla.columns = [
        _sin_saltos(columna)
        for columna in tabla.columns
    ]

    columnas_obligatorias = {
        "Naturaleza",
        "Prestador",
        "Cantidad",
        "Porcentaje",
    }

    _validar_columnas(
        tabla,
        columnas_obligatorias,
        ARCHIVO_TIPO_PRESTADORES.name,
    )

    tabla["Cantidad"] = (
        pd.to_numeric(
            tabla["Cantidad"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )

    tabla["Porcentaje"] = pd.to_numeric(
        tabla["Porcentaje"].str.replace(
            ",",
            ".",
            regex=False,
        ),
        errors="coerce",
    )

    return tabla


def cargar_urgencias():
    """Carga las sedes de urgencias y convierte sus coordenadas."""

    _validar_existencia(
        ARCHIVO_URGENCIAS
    )

    tabla = pd.read_csv(
        ARCHIVO_URGENCIAS,
        sep=";",
        encoding="latin-1",
        dtype=str,
    )

    tabla.columns = [
        _sin_saltos(columna)
        for columna in tabla.columns
    ]

    columnas_obligatorias = {
        "sede_nombre",
        "Longitud",
        "Latitud",
    }

    _validar_columnas(
        tabla,
        columnas_obligatorias,
        ARCHIVO_URGENCIAS.name,
    )

    for columna in (
        "Longitud",
        "Latitud",
    ):
        tabla[columna] = pd.to_numeric(
            tabla[columna].str.replace(
                ",",
                ".",
                regex=False,
            ),
            errors="coerce",
        )

    return tabla


def cargar_sedes_geocodificadas():
    """Carga el resultado de la geocodificación.

    Se conservan tanto las sedes geocodificadas como las no resueltas.

    La columna ``coordenada_valida`` identifica cuáles registros pueden
    mostrarse en el mapa. Los registros no válidos permanecen en la tabla
    para facilitar su revisión y mantener la trazabilidad.
    """

    _validar_existencia(
        ARCHIVO_SEDES_GEOCODIFICADAS
    )

    tabla = pd.read_csv(
        ARCHIVO_SEDES_GEOCODIFICADAS,
        encoding="utf-8-sig",
        dtype={
            "sede_id": str,
        },
    )

    _validar_columnas(
        tabla,
        COLUMNAS_GEOCODIFICADAS_OBLIGATORIAS,
        ARCHIVO_SEDES_GEOCODIFICADAS.name,
    )

    if tabla["sede_id"].duplicated().any():
        duplicados = tabla.loc[
            tabla["sede_id"].duplicated(
                keep=False
            ),
            "sede_id",
        ].tolist()

        raise ValueError(
            "El archivo de sedes geocodificadas "
            "contiene identificadores duplicados: "
            f"{duplicados}."
        )

    tabla["sede_id"] = (
        tabla["sede_id"].astype(str)
    )

    tabla["latitud"] = pd.to_numeric(
        tabla["latitud"],
        errors="coerce",
    )

    tabla["longitud"] = pd.to_numeric(
        tabla["longitud"],
        errors="coerce",
    )

    tabla["geocodificado"] = (
        tabla["geocodificado"].apply(
            _normalizar_booleano
        )
    )

    latitud_en_rango = tabla[
        "latitud"
    ].between(
        -90,
        90,
        inclusive="both",
    )

    longitud_en_rango = tabla[
        "longitud"
    ].between(
        -180,
        180,
        inclusive="both",
    )

    coordenadas_presentes = tabla[
        [
            "latitud",
            "longitud",
        ]
    ].notna().all(
        axis=1
    )

    tabla["coordenada_valida"] = (
        tabla["geocodificado"]
        & coordenadas_presentes
        & latitud_en_rango
        & longitud_en_rango
    )

    return tabla


def cargar_oferta_con_coordenadas():
    """Combina la oferta quirúrgica con las coordenadas.

    La unión se realiza por ``sede_id`` y conserva todos los registros
    de oferta, incluso si una sede no pudo geocodificarse.

    Una sede puede aparecer en varias filas cuando registra más de un
    servicio, pero debe existir una sola fila de coordenadas por sede.
    """

    oferta = cargar_cirugia_plastica()
    sedes = cargar_sedes_geocodificadas()

    columnas_para_union = [
        "sede_id",
        "direccion_normalizada",
        "latitud",
        "longitud",
        "geocodificado",
        "coordenada_valida",
    ]

    resultado = oferta.merge(
        sedes[columnas_para_union],
        on="sede_id",
        how="left",
        validate="many_to_one",
    )

    resultado["geocodificado"] = (
        resultado["geocodificado"]
        .fillna(False)
        .astype(bool)
    )

    resultado["coordenada_valida"] = (
        resultado["coordenada_valida"]
        .fillna(False)
        .astype(bool)
    )

    return resultado