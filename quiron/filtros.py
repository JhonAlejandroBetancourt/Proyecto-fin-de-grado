"""Reglas de filtrado para el dashboard Quirón.

Este módulo contiene funciones puras: reciben una tabla y valores de
filtro, y devuelven una nueva tabla sin modificar la original.

Los filtros disponibles corresponden únicamente a campos presentes en
la fuente procesada:

  - Código de servicio.
  - Naturaleza jurídica.
  - Tipo de prestador.
  - Nombre de la sede.

No se incluyen variables que todavía no existen en el conjunto de datos,
como localidad o subred. Agregar filtros sobre campos inexistentes
produciría una capacidad aparente que los datos actuales no respaldaldan.
"""

import unicodedata

import pandas as pd


COLUMNAS_REQUERIDAS = {
    "sede_id",
    "sede",
    "naturaleza",
    "tipo_prestador",
    "codigo_servicio",
    "nombre_servicio",
    "es_quirurgico",
}


def _validar_columnas(tabla):
    """Comprueba que la tabla pueda utilizarse en el sistema de filtros."""

    columnas_faltantes = COLUMNAS_REQUERIDAS.difference(
        tabla.columns
    )

    if columnas_faltantes:
        nombres = ", ".join(
            sorted(columnas_faltantes)
        )

        raise ValueError(
            "No es posible aplicar los filtros porque "
            f"faltan las columnas: {nombres}."
        )


def _normalizar_texto(valor):
    """Normaliza un valor para realizar búsquedas tolerantes.

    La comparación ignora mayúsculas, minúsculas, tildes y espacios
    repetidos. La función se utiliza únicamente para buscar; no modifica
    los valores originales que después se muestran en el dashboard.
    """

    if pd.isna(valor):
        return ""

    texto = str(valor).strip().lower()

    texto_sin_tildes = "".join(
        caracter
        for caracter in unicodedata.normalize(
            "NFKD",
            texto,
        )
        if not unicodedata.combining(
            caracter
        )
    )

    return " ".join(
        texto_sin_tildes.split()
    )


def _valores_seleccionados(valor):
    """Convierte un filtro individual o múltiple en una lista limpia."""

    if valor is None:
        return []

    if isinstance(
        valor,
        (
            list,
            tuple,
            set,
        ),
    ):
        valores = list(valor)
    else:
        valores = [valor]

    resultado = []

    for elemento in valores:
        if elemento is None:
            continue

        texto = str(elemento).strip()

        if texto:
            resultado.append(texto)

    return resultado


def _opciones_ordenadas(
    tabla,
    columna,
):
    """Genera opciones compatibles con ``dcc.Dropdown``."""

    valores = (
        tabla[columna]
        .dropna()
        .astype(str)
        .str.strip()
    )

    valores = valores[
        valores.ne("")
    ].drop_duplicates()

    valores_ordenados = sorted(
        valores.tolist(),
        key=_normalizar_texto,
    )

    return [
        {
            "label": valor,
            "value": valor,
        }
        for valor in valores_ordenados
    ]


def obtener_opciones_filtros(tabla):
    """Obtiene las opciones disponibles para cada filtro.

    Solo se consideran registros pertenecientes a los códigos quirúrgicos
    incluidos en el alcance actual del proyecto.
    """

    _validar_columnas(tabla)

    oferta_quirurgica = tabla.loc[
        tabla["es_quirurgico"]
        .fillna(False)
        .astype(bool)
    ].copy()

    servicios = (
        oferta_quirurgica[
            [
                "codigo_servicio",
                "nombre_servicio",
            ]
        ]
        .dropna(
            subset=[
                "codigo_servicio",
            ]
        )
        .drop_duplicates(
            subset=[
                "codigo_servicio",
            ]
        )
    )

    servicios = servicios.sort_values(
        "codigo_servicio",
        kind="stable",
    )

    opciones_servicio = []

    for _, fila in servicios.iterrows():
        codigo = str(
            fila["codigo_servicio"]
        ).strip()

        nombre = str(
            fila["nombre_servicio"]
        ).strip()

        opciones_servicio.append(
            {
                "label": nombre,
                "value": codigo,
            }
        )

    return {
        "servicios": opciones_servicio,
        "naturalezas": _opciones_ordenadas(
            oferta_quirurgica,
            "naturaleza",
        ),
        "tipos_prestador": _opciones_ordenadas(
            oferta_quirurgica,
            "tipo_prestador",
        ),
    }


def aplicar_filtros(
    tabla,
    servicios=None,
    naturalezas=None,
    tipos_prestador=None,
    texto_sede=None,
):
    """Aplica los filtros escogidos por el usuario.

    Todos los filtros se combinan mediante lógica AND:

      - La sede debe ofrecer alguno de los servicios seleccionados.
      - Debe pertenecer a alguna de las naturalezas seleccionadas.
      - Debe pertenecer a alguno de los tipos de prestador seleccionados.
      - El nombre debe contener el texto de búsqueda.

    Si un filtro está vacío, ese criterio no restringe los resultados.
    """

    _validar_columnas(tabla)

    resultado = tabla.loc[
        tabla["es_quirurgico"]
        .fillna(False)
        .astype(bool)
    ].copy()

    servicios_seleccionados = (
        _valores_seleccionados(
            servicios
        )
    )

    naturalezas_seleccionadas = (
        _valores_seleccionados(
            naturalezas
        )
    )

    tipos_seleccionados = (
        _valores_seleccionados(
            tipos_prestador
        )
    )

    if servicios_seleccionados:
        resultado = resultado.loc[
            resultado[
                "codigo_servicio"
            ]
            .astype(str)
            .isin(
                servicios_seleccionados
            )
        ]

    if naturalezas_seleccionadas:
        resultado = resultado.loc[
            resultado[
                "naturaleza"
            ]
            .astype(str)
            .isin(
                naturalezas_seleccionadas
            )
        ]

    if tipos_seleccionados:
        resultado = resultado.loc[
            resultado[
                "tipo_prestador"
            ]
            .astype(str)
            .isin(
                tipos_seleccionados
            )
        ]

    texto_buscado = _normalizar_texto(
        texto_sede
    )

    if texto_buscado:
        nombres_normalizados = resultado[
            "sede"
        ].apply(
            _normalizar_texto
        )

        resultado = resultado.loc[
            nombres_normalizados.str.contains(
                texto_buscado,
                regex=False,
                na=False,
            )
        ]

    return resultado.reset_index(
        drop=True
    )


def contar_sedes_unicas(tabla):
    """Cuenta sedes físicas únicas dentro de una tabla filtrada."""

    _validar_columnas(tabla)

    return int(
        tabla["sede_id"].nunique()
    )


def filtros_activos(
    servicios=None,
    naturalezas=None,
    tipos_prestador=None,
    texto_sede=None,
):
    """Indica si el usuario ha aplicado al menos un criterio."""

    return any(
        [
            bool(
                _valores_seleccionados(
                    servicios
                )
            ),
            bool(
                _valores_seleccionados(
                    naturalezas
                )
            ),
            bool(
                _valores_seleccionados(
                    tipos_prestador
                )
            ),
            bool(
                _normalizar_texto(
                    texto_sede
                )
            ),
        ]
    )