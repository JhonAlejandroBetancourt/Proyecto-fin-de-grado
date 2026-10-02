"""Normalización de direcciones con nomenclatura catastral de Bogotá.

Las direcciones del archivo fuente vienen en el formato abreviado propio
de Bogotá (ej. "AC 127 # 71 96", "KR 16 # 84 A 09 CONS 620"), mezclado con
información de unidad interna (consultorio, piso, oficina) que un servicio
de geocodificación no necesita y que, de hecho, suele confundirlo.

Este módulo hace dos cosas, y nada más que estas dos cosas:
  1. Expande las abreviaturas de vía (AC, AK, KR, CL, DG, TV...) a su forma
     completa, porque los servicios de geocodificación reconocen mejor
     "Avenida Calle 127" que "AC 127".
  2. Recorta todo lo que esté después del primer indicador de unidad
     interna (consultorio, piso, oficina, torre, local, casa...), porque
     esa información no forma parte de la dirección geocodificable y
     puede hacer fallar la búsqueda.

Principio de diseño: si una dirección queda vacía después de limpiarla,
se devuelve None explícitamente. Nunca se inventa ni se completa un dato
que no esté en la fuente.
"""

import re

# Abreviatura de vía -> forma expandida. El orden importa: se compara
# contra la PRIMERA palabra de la dirección, así que no hay ambigüedad
# entre, por ejemplo, "CR" (Carrera) y "CRA" (Carrera), ambas válidas.
PREFIJOS_VIA = [
    ("AC", "AVENIDA CALLE"),
    ("AK", "AVENIDA CARRERA"),
    ("AV", "AVENIDA"),
    ("DG", "DIAGONAL"),
    ("TV", "TRANSVERSAL"),
    ("CRA", "CARRERA"),
    ("CR", "CARRERA"),
    ("KR", "CARRERA"),
    ("CL", "CALLE"),
    ("CLL", "CALLE"),
]

# Cualquiera de estos tokens marca el inicio de información de unidad
# interna (no geocodificable). Se corta la dirección en la PRIMERA
# ocurrencia de cualquiera de ellos, sea cual sea.
TOKENS_DE_UNIDAD_INTERNA = [
    "PISO", "PI ", "CONSULTORIO", "CONS ", "CONS.", "CS ", "CS.", "CS-",
    "OFICINA", "OF ", "OF.", "OFC", "LOCAL", "LC ", "APTO", "APARTAMENTO",
    "TORRE", "TO ", "T.", "INTERIOR", "INT ", "CASA", "BODEGA", "MODULO",
]


def _quitar_contenido_entre_parentesis(texto):
    return re.sub(r"\([^)]*\)", " ", texto)


def _cortar_en_primer_token_de_unidad(texto):
    posiciones_encontradas = []
    for token in TOKENS_DE_UNIDAD_INTERNA:
        posicion = texto.find(token)
        if posicion != -1:
            posiciones_encontradas.append(posicion)

    if not posiciones_encontradas:
        return texto

    primera_posicion = min(posiciones_encontradas)
    return texto[:primera_posicion]


def _normalizar_marcador_de_numero(texto):
    """Unifica las distintas formas de escribir el separador de nomenclatura
    bogotana (No., No, N°, Nº, N suelta) a un único símbolo "#".

    Nota: esta función recibe el texto YA EN MAYÚSCULAS, por eso los
    patrones de búsqueda están en mayúsculas ("NO." y no "No.").
    """
    texto = re.sub(r"\bNO\.\s*(?=\d)", "# ", texto)
    texto = re.sub(r"\bNO\s+(?=\d)", "# ", texto)
    texto = texto.replace("N°", "#").replace("Nº", "#")

    # Variante sin punto ni símbolo: "19 N 100-28". Solo se activa si hay
    # un dígito a cada lado de la "N", para no alterar nomenclaturas reales
    # como "Carrera 7N" (donde la N va pegada al número, sin espacios).
    texto = re.sub(r"(?<=\d)\s+N\s+(?=\d)", " # ", texto)

    # Un guion seguido de dígito se compacta (sin espacios alrededor),
    # como se escribe convencionalmente: "71 - 96" -> "71-96".
    texto = re.sub(r"\s*-\s*(?=\d)", "-", texto)
    return texto


def _expandir_prefijo_de_via(texto):
    coincidencia = re.match(r"^([A-ZÑ]+)(\s|\.)", texto)
    if not coincidencia:
        return texto

    primera_palabra = coincidencia.group(1)
    for abreviatura, forma_expandida in PREFIJOS_VIA:
        if primera_palabra == abreviatura:
            resto_de_la_direccion = texto[len(primera_palabra):]
            return forma_expandida + resto_de_la_direccion

    return texto


def _colapsar_espacios_repetidos(texto):
    return " ".join(texto.split())


def normalizar_direccion_bogota(direccion_cruda):
    """Convierte una dirección cruda de Bogotá en una cadena apta para
    geocodificación. Devuelve None si la dirección de entrada está vacía,
    es nula, o queda vacía después de la limpieza (nunca se fabrica un
    valor de relleno)."""
    if not direccion_cruda:
        return None

    texto = direccion_cruda.upper()
    texto = _quitar_contenido_entre_parentesis(texto)
    texto = _cortar_en_primer_token_de_unidad(texto)
    texto = _normalizar_marcador_de_numero(texto)
    texto = _expandir_prefijo_de_via(texto)
    texto = _colapsar_espacios_repetidos(texto)
    texto = texto.strip(" ,.-")

    if not texto:
        return None

    return texto + ", Bogotá, Colombia"