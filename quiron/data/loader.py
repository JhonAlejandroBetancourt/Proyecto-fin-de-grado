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

import re
import unicodedata
from pathlib import Path
from time import perf_counter

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


def _ejecutar_etapa(
    observador,
    fase,
    nombre,
    operacion,
    mensaje,
    metricas=None,
):
    """Ejecuta una operación y emite su resultado o su error medido."""

    if observador is None:
        return operacion()

    inicio = perf_counter()
    observador(
        {
            "fase": fase,
            "nombre": nombre,
            "estado": "en_progreso",
        }
    )

    try:
        resultado = operacion()
        detalles = (
            metricas(resultado)
            if metricas
            else {}
        )
        mensaje_final = (
            mensaje(resultado)
            if callable(mensaje)
            else mensaje
        )
    except Exception as error:
        observador(
            {
                "fase": fase,
                "nombre": nombre,
                "estado": "error",
                "nivel": "error",
                "mensaje": str(error),
                "duracion_ms": (
                    (perf_counter() - inicio)
                    * 1000.0
                ),
            }
        )
        raise

    observador(
        {
            "fase": fase,
            "nombre": nombre,
            "estado": "completado",
            "nivel": detalles.pop(
                "nivel",
                "exito",
            ),
            "mensaje": mensaje_final,
            "duracion_ms": (
                (perf_counter() - inicio)
                * 1000.0
            ),
            **detalles,
        }
    )
    return resultado


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


def _normalizar_clave_sede(valor):
    """Normaliza nombre o dirección sin eliminar diferencias de identidad."""

    if pd.isna(valor):
        return ""

    texto = unicodedata.normalize(
        "NFKC",
        str(valor),
    )
    return " ".join(
        texto.casefold().split()
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


def _resolver_origen_cirugia(
    origen,
    nombre_fuente,
):
    """Normaliza la fuente de datos para ``cargar_cirugia_plastica``.

    Devuelve una tupla ``(fuente, nombre)`` donde ``fuente`` es un objeto
    apto para ``pandas.read_csv`` y ``nombre`` es la etiqueta usada en los
    mensajes de error.
    """

    import io

    if origen is None:
        _validar_existencia(
            ARCHIVO_CIRUGIA_PLASTICA
        )

        return (
            ARCHIVO_CIRUGIA_PLASTICA,
            ARCHIVO_CIRUGIA_PLASTICA.name,
        )

    if isinstance(origen, bytes):
        return (
            io.BytesIO(origen),
            nombre_fuente
            or "archivo cargado",
        )

    if isinstance(
        origen,
        (str, Path),
    ):
        ruta = Path(origen)

        _validar_existencia(ruta)

        return (
            ruta,
            nombre_fuente or ruta.name,
        )

    return (
        origen,
        nombre_fuente
        or "archivo cargado",
    )


def cargar_cirugia_plastica(
    origen=None,
    nombre_fuente=None,
    observador=None,
):
    """Transforma la oferta desde formato ancho a formato largo.

    El resultado contiene una fila por combinación de sede y servicio.
    La columna ``es_quirurgico`` identifica los códigos incluidos en el
    alcance actual del proyecto.

    Parámetros
    ----------
    origen : ruta, buffer o ``bytes``, opcional
        Fuente de datos alternativa. Cuando es ``None`` se utiliza el
        archivo incluido en el proyecto, de modo que la llamada sin
        argumentos mantiene exactamente el comportamiento histórico.

        Se admite una ruta (``str`` o ``Path``), un objeto de archivo en
        memoria (por ejemplo ``io.BytesIO``) o el contenido en ``bytes``,
        lo que permite procesar un CSV cargado por el usuario sin
        escribirlo en disco.

    nombre_fuente : str, opcional
        Nombre descriptivo de la fuente, usado solo en los mensajes de
        error. Si no se indica, se deduce del origen.

    observador : callable, opcional
        Recibe eventos con fase, paso, estado, duración y métricas de
        entrada/salida para la traza visible del ETL.
    """

    fuente, nombre = _resolver_origen_cirugia(
        origen,
        nombre_fuente,
    )

    crudo = _ejecutar_etapa(
        observador,
        "Extracción",
        "Lectura del CSV",
        lambda: pd.read_csv(
            fuente,
            sep=";",
            encoding="utf-8-sig",
            dtype=str,
        ),
        lambda tabla: (
            f"CSV leído con separador ';' y UTF-8. "
            f"{len(tabla)} filas y {len(tabla.columns)} "
            "columnas recibidas."
        ),
        lambda tabla: {
            "filas_salida": len(tabla),
            "columnas_salida": len(tabla.columns),
        },
    )

    columnas_originales = len(crudo.columns)

    def normalizar_encabezados():
        tabla = crudo.copy()
        tabla.columns = [
            _sin_saltos(columna)
            for columna in tabla.columns
        ]
        tabla = tabla.loc[
            :,
            ~tabla.columns.str.contains(
                r"^Unnamed"
            ),
        ]
        encabezados = set(tabla.columns)
        columnas_mangladas = [
            re.sub(r"\.\d+$", "", columna)
            for columna in tabla.columns
            if re.fullmatch(r".+\.\d+", columna)
            and re.sub(r"\.\d+$", "", columna)
            in encabezados
        ]
        duplicadas = list(
            dict.fromkeys(
                [
                    *tabla.columns[
                        tabla.columns.duplicated()
                    ].tolist(),
                    *columnas_mangladas,
                ]
            )
        )
        if duplicadas:
            raise ValueError(
                "La normalización produjo encabezados "
                "duplicados: "
                f"{', '.join(duplicadas)}."
            )
        return tabla

    crudo = _ejecutar_etapa(
        observador,
        "Transformación",
        "Normalización de encabezados",
        normalizar_encabezados,
        lambda tabla: (
            f"Se normalizaron espacios y saltos de línea; "
            f"se descartaron {columnas_originales - len(tabla.columns)} "
            "columnas auxiliares sin nombre."
        ),
        lambda tabla: {
            "filas_entrada": len(tabla),
            "filas_salida": len(tabla),
            "columnas_entrada": columnas_originales,
            "columnas_salida": len(tabla.columns),
        },
    )

    crudo = _ejecutar_etapa(
        observador,
        "Validación",
        "Validación de estructura",
        lambda: (
            _validar_columnas(
                crudo,
                COLUMNAS_CIRUGIA_OBLIGATORIAS,
                nombre,
            )
            or crudo
        ),
        lambda tabla: (
            f"Están presentes las "
            f"{len(COLUMNAS_CIRUGIA_OBLIGATORIAS)} "
            "columnas obligatorias."
        ),
        lambda tabla: {
            "filas_entrada": len(tabla),
            "filas_salida": len(tabla),
            "columnas_entrada": len(tabla.columns),
            "columnas_salida": len(tabla.columns),
        },
    )

    filas_sin_limpiar = len(crudo)

    def limpiar_registros():
        tabla = crudo.copy()
        tabla = tabla.apply(
            lambda columna: columna.map(
                lambda valor: (
                    _sin_saltos(valor)
                    if isinstance(valor, str)
                    else valor
                )
            )
        )
        nombre_sede = tabla["SEDE -NOMBRE"]
        filas_con_sede = (
            nombre_sede.notna()
            & nombre_sede.str.strip().ne("")
        )
        tabla = tabla.loc[filas_con_sede].copy()
        tabla = tabla.reset_index(drop=True)
        return tabla

    crudo = _ejecutar_etapa(
        observador,
        "Limpieza",
        "Limpieza de registros",
        limpiar_registros,
        lambda tabla: (
            f"Se recortaron y compactaron espacios y saltos de línea "
            f"en los campos de texto. Se descartaron "
            f"{filas_sin_limpiar - len(tabla)} filas sin nombre de sede."
        ),
        lambda tabla: {
            "filas_entrada": filas_sin_limpiar,
            "filas_salida": len(tabla),
            "filas_eliminadas": (
                filas_sin_limpiar - len(tabla)
            ),
        },
    )

    def detectar_columnas_servicio():
        columnas = _columnas_de_servicio(
            crudo.columns
        )
        if not columnas:
            raise ValueError(
                "La fuente de cirugía plástica no contiene columnas "
                "de servicio identificadas por código numérico."
            )
        return columnas

    columnas_servicio = _ejecutar_etapa(
        observador,
        "Validación",
        "Detección de columnas de servicio",
        detectar_columnas_servicio,
        lambda columnas: (
            f"Se identificaron {len(columnas)} columnas de servicio "
            "por su código numérico."
        ),
        lambda columnas: {
            "filas_entrada": len(crudo),
            "filas_salida": len(crudo),
            "columnas_entrada": len(crudo.columns),
            "columnas_salida": len(columnas),
        },
    )

    nombres_base = {
        "SEDE -NOMBRE": "sede",
        "DIRECCION": "direccion",
        "TELEFONO": "telefono",
        "CORREO ELECTRÓNICO": "correo",
        "NATURALEZA": "naturaleza",
        "TIPO DE PRESTADOR": "tipo_prestador",
    }

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

    def transformar_formato_largo():
        base = crudo.rename(
            columns=nombres_base
        )[
            list(nombres_base.values())
        ].copy()
        base["sede_id"] = (
            base.index.astype(str)
        )

        valores_servicio = crudo[
            columnas_servicio
        ].apply(
            lambda columna: (
                columna
                .fillna("")
                .str.strip()
                .str.upper()
            )
        )
        marcas = valores_servicio.eq("X")
        filas_sin_servicio = int(
            (~marcas.any(axis=1)).sum()
        )
        valores_no_reconocidos = valores_servicio.where(
            valores_servicio.ne("")
            & valores_servicio.ne("X")
        )
        marcadores_ignorados = int(
            valores_no_reconocidos.notna().to_numpy().sum()
        )
        ejemplos_marcadores = [
            str(valor)
            for valor in pd.unique(
                valores_no_reconocidos.to_numpy().ravel()
            )
            if pd.notna(valor)
        ][:5]
        marcas.index = base["sede_id"]
        cantidad_marcas = int(
            marcas.to_numpy().sum()
        )

        filas = []
        for columna in columnas_servicio:
            codigo, separador, nombre = (
                columna.partition(" - ")
            )
            codigo = codigo.strip()
            nombre_limpio = nombre.strip()
            nombre_final = (
                f"{codigo} · {nombre_limpio}"
                if separador and nombre_limpio
                else columna.strip()
            )
            for sede_id in marcas.index[
                marcas[columna]
            ]:
                filas.append(
                    {
                        "sede_id": sede_id,
                        "codigo_servicio": codigo,
                        "nombre_servicio": nombre_final,
                        "es_quirurgico": (
                            codigo in CODIGOS_QUIRURGICOS
                        ),
                    }
                )

        servicios = pd.DataFrame(
            filas,
            columns=[
                "sede_id",
                "codigo_servicio",
                "nombre_servicio",
                "es_quirurgico",
            ],
        )

        tabla = servicios.merge(
            base,
            on="sede_id",
            how="left",
            validate="many_to_one",
        )
        return (
            tabla[columnas_orden].reset_index(drop=True),
            cantidad_marcas,
            marcadores_ignorados,
            ejemplos_marcadores,
            filas_sin_servicio,
        )

    def metricas_transformacion(resultado):
        (
            tabla,
            marcas_aceptadas,
            marcadores_ignorados,
            ejemplos_marcadores,
            filas_sin_servicio,
        ) = resultado
        return {
            "nivel": (
                "advertencia"
                if marcadores_ignorados
                else "exito"
            ),
            "filas_entrada": len(crudo),
            "filas_salida": len(tabla),
            "filas_eliminadas": filas_sin_servicio,
            "columnas_entrada": len(crudo.columns),
            "columnas_salida": len(columnas_orden),
            "detalle": (
                f"{marcas_aceptadas} marcas 'X' aceptadas en "
                f"{tabla['sede_id'].nunique()} sedes. "
                f"{filas_sin_servicio} filas sin marca 'X' "
                "reconocida no generan registros de servicio. "
                f"{marcadores_ignorados} valores no vacíos distintos "
                "de 'X' se ignoraron en columnas de servicio. "
                f"Muestra: {', '.join(ejemplos_marcadores) or 'ninguna'}."
            ),
        }

    resultado_transformacion = _ejecutar_etapa(
        observador,
        "Transformación",
        "Transformación de formato ancho a largo",
        transformar_formato_largo,
        lambda resultado: (
            f"{len(columnas_servicio)} columnas de servicio se "
            f"convirtieron en {len(resultado[0])} registros "
            "sede-servicio. "
            f"{resultado[2]} valores de marca no reconocidos; "
            f"{resultado[4]} filas sin servicio marcado."
        ),
        metricas_transformacion,
    )
    tabla = resultado_transformacion[0]

    def validar_salida():
        if tabla.empty:
            raise ValueError(
                "La fuente no produjo registros de servicio; revisa "
                "las marcas 'X' de las columnas de servicio."
            )
        columnas_faltantes = set(columnas_orden).difference(
            tabla.columns
        )
        if columnas_faltantes:
            raise ValueError(
                "La salida transformada no contiene las columnas "
                "requeridas: "
                f"{', '.join(sorted(columnas_faltantes))}."
            )
        if tabla["sede_id"].isna().any():
            raise ValueError(
                "La salida transformada contiene registros sin "
                "identificador de sede."
            )
        return tabla

    return _ejecutar_etapa(
        observador,
        "Validación",
        "Control de integridad de la oferta",
        validar_salida,
        lambda salida: (
            f"Salida íntegra: {len(salida)} registros y "
            f"{salida['sede_id'].nunique()} sedes únicas."
        ),
        lambda salida: {
            "filas_entrada": len(salida),
            "filas_salida": len(salida),
            "columnas_entrada": len(salida.columns),
            "columnas_salida": len(salida.columns),
        },
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


def cargar_sedes_geocodificadas(
    observador=None,
):
    """Carga el resultado de la geocodificación.

    Se conservan tanto las sedes geocodificadas como las no resueltas.

    La columna ``coordenada_valida`` identifica cuáles registros pueden
    mostrarse en el mapa. Los registros no válidos permanecen en la tabla
    para facilitar su revisión y mantener la trazabilidad.
    """

    def leer_referencia():
        _validar_existencia(
            ARCHIVO_SEDES_GEOCODIFICADAS
        )
        return pd.read_csv(
            ARCHIVO_SEDES_GEOCODIFICADAS,
            encoding="utf-8-sig",
            dtype={
                "sede_id": str,
            },
        )

    tabla = _ejecutar_etapa(
        observador,
        "Enriquecimiento",
        "Lectura de referencia geográfica",
        leer_referencia,
        lambda referencia: (
            f"Referencia leída desde "
            f"'{ARCHIVO_SEDES_GEOCODIFICADAS.name}': "
            f"{len(referencia)} registros."
        ),
        lambda referencia: {
            "filas_salida": len(referencia),
            "columnas_salida": len(referencia.columns),
        },
    )

    def validar_referencia():
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
            ].unique().tolist()
            muestra_duplicados = ", ".join(
                duplicados[:10]
            )
            raise ValueError(
                "El archivo de sedes geocodificadas contiene "
                f"{len(duplicados)} identificadores duplicados: "
                f"{muestra_duplicados}."
            )
        return tabla

    tabla = _ejecutar_etapa(
        observador,
        "Validación",
        "Validación de referencia geográfica",
        validar_referencia,
        lambda referencia: (
            "La referencia contiene las columnas requeridas y no "
            "tiene identificadores de sede duplicados."
        ),
        lambda referencia: {
            "filas_entrada": len(referencia),
            "filas_salida": len(referencia),
            "columnas_entrada": len(referencia.columns),
            "columnas_salida": len(referencia.columns),
        },
    )

    def normalizar_coordenadas():
        referencia = tabla.copy()
        referencia["sede_id"] = (
            referencia["sede_id"].astype(str)
        )
        referencia["latitud"] = pd.to_numeric(
            referencia["latitud"],
            errors="coerce",
        )
        referencia["longitud"] = pd.to_numeric(
            referencia["longitud"],
            errors="coerce",
        )
        referencia["geocodificado"] = (
            referencia["geocodificado"].apply(
                _normalizar_booleano
            )
        )
        latitud_en_rango = referencia[
            "latitud"
        ].between(-90, 90, inclusive="both")
        longitud_en_rango = referencia[
            "longitud"
        ].between(-180, 180, inclusive="both")
        coordenadas_presentes = referencia[
            ["latitud", "longitud"]
        ].notna().all(axis=1)
        referencia["coordenada_valida"] = (
            referencia["geocodificado"]
            & coordenadas_presentes
            & latitud_en_rango
            & longitud_en_rango
        )
        return referencia

    return _ejecutar_etapa(
        observador,
        "Validación",
        "Normalización y control de coordenadas",
        normalizar_coordenadas,
        lambda referencia: (
            f"{int(referencia['coordenada_valida'].sum())} de "
            f"{len(referencia)} registros tienen coordenadas "
            "numéricas, completas y dentro de rango."
        ),
        lambda referencia: {
            "filas_entrada": len(referencia),
            "filas_salida": len(referencia),
            "filas_eliminadas": 0,
            "detalle": (
                f"{len(referencia) - int(referencia['coordenada_valida'].sum())} "
                "registros conservados como referencia sin coordenadas "
                "válidas para poder auditarlos."
            ),
        },
    )


def cargar_oferta_con_coordenadas(
    origen=None,
    nombre_fuente=None,
    observador=None,
):
    """Combina la oferta quirúrgica con las coordenadas.

    La unión se realiza por coincidencia única de nombre y dirección
    normalizados, no por el índice de fila. Así conserva la relación
    correcta aunque cambie el orden o la representación binaria del CSV.
    Los registros ambiguos o sin coincidencia permanecen sin coordenadas.

    Una sede puede aparecer en varias filas cuando registra más de un
    servicio, pero debe existir una sola fila de coordenadas por sede.

    Parámetros
    ----------
    origen : ruta, buffer o ``bytes``, opcional
        Fuente alternativa de la oferta de cirugía. Cuando es ``None`` se
        usa el archivo incluido, conservando el comportamiento histórico.
        Las coordenadas geocodificadas siempre provienen del archivo
        procesado del proyecto. Solo se reutilizan coordenadas cuando el
        nombre y la dirección coinciden de forma única.

    nombre_fuente : str, opcional
        Nombre descriptivo de la fuente para los mensajes de error.
    """

    oferta = cargar_cirugia_plastica(
        origen,
        nombre_fuente,
        observador=observador,
    )
    sedes = cargar_sedes_geocodificadas(
        observador=observador,
    )

    claves_identidad = [
        "_clave_sede",
        "_clave_direccion",
    ]

    sedes_total = oferta[
        "sede_id"
    ].nunique()

    def preparar_identidades():
        sedes_oferta = oferta[
            [
                "sede_id",
                "sede",
                "direccion",
            ]
        ].drop_duplicates(
            subset=["sede_id"]
        ).copy()
        referencia = sedes.copy()
        sedes_oferta["_clave_sede"] = (
            sedes_oferta["sede"].map(
                _normalizar_clave_sede
            )
        )
        sedes_oferta["_clave_direccion"] = (
            sedes_oferta["direccion"].map(
                _normalizar_clave_sede
            )
        )
        referencia["_clave_sede"] = (
            referencia["sede"].map(
                _normalizar_clave_sede
            )
        )
        referencia["_clave_direccion"] = (
            referencia["direccion"].map(
                _normalizar_clave_sede
            )
        )

        def filtrar_identidades(tabla):
            claves_presentes = tabla[
                claves_identidad
            ].ne("").all(axis=1)
            identidades_ambiguas = tabla.duplicated(
                subset=claves_identidad,
                keep=False,
            )
            return tabla.loc[
                claves_presentes & ~identidades_ambiguas
            ].copy()

        oferta_valida = filtrar_identidades(sedes_oferta)
        referencia_valida = filtrar_identidades(referencia)
        metricas = {
            "filas_entrada": len(sedes_oferta),
            "filas_salida": len(oferta_valida),
            "filas_eliminadas": (
                len(sedes_oferta) - len(oferta_valida)
            ),
            "detalle": (
                f"Se excluyeron {len(sedes_oferta) - len(oferta_valida)} "
                "identidades de origen vacías o ambiguas y "
                f"{len(referencia) - len(referencia_valida)} de la "
                "referencia geográfica."
            ),
        }
        return oferta_valida, referencia_valida, metricas

    sedes_oferta, sedes, _ = (
        _ejecutar_etapa(
            observador,
            "Enriquecimiento",
            "Normalización y depuración de identidades",
            preparar_identidades,
            lambda resultado: (
                f"{len(resultado[0])} identidades de oferta y "
                f"{len(resultado[1])} de referencia son únicas y "
                "aptas para el cruce."
            ),
            lambda resultado: resultado[2],
        )
    )

    columnas_para_union = [
        *claves_identidad,
        "direccion_normalizada",
        "latitud",
        "longitud",
        "geocodificado",
        "coordenada_valida",
    ]

    def cruzar_coordenadas():
        coordenadas_por_sede = sedes_oferta.merge(
            sedes[columnas_para_union],
            on=claves_identidad,
            how="inner",
            validate="one_to_one",
        )[
            [
                "sede_id",
                "direccion_normalizada",
                "latitud",
                "longitud",
                "geocodificado",
                "coordenada_valida",
            ]
        ]
        resultado = oferta.merge(
            coordenadas_por_sede,
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
        sedes_con_coincidencia = int(
            coordenadas_por_sede["sede_id"].nunique()
        )
        sedes_con_coordenadas = int(
            coordenadas_por_sede.loc[
                coordenadas_por_sede[
                    "coordenada_valida"
                ],
                "sede_id",
            ].nunique()
        )
        return (
            resultado,
            sedes_con_coincidencia,
            sedes_con_coordenadas,
        )

    def mensaje_cruce(resultado):
        _, coincidentes, coordenadas_validas = resultado
        return (
            f"{coincidentes} de {sedes_total} sedes coinciden de "
            "forma única por nombre y dirección; "
            f"{coordenadas_validas} tienen coordenadas válidas. "
            "Las identidades ambiguas o no coincidentes permanecen "
            "sin ubicación."
        )

    def metricas_cruce(resultado):
        tabla, coincidentes, coordenadas_validas = resultado
        nivel = (
            "exito"
            if coincidentes == sedes_total
            else "advertencia"
        )
        return {
            "nivel": nivel,
            "filas_entrada": len(oferta),
            "filas_salida": len(tabla),
            "detalle": (
                f"{sedes_total - coincidentes} sedes sin coincidencia "
                "segura; "
                f"{coincidentes - coordenadas_validas} sin coordenadas "
                "válidas."
            ),
        }

    tabla, _, _ = _ejecutar_etapa(
        observador,
        "Enriquecimiento",
        "Cruce de coordenadas",
        cruzar_coordenadas,
        mensaje_cruce,
        metricas_cruce,
    )
    return tabla