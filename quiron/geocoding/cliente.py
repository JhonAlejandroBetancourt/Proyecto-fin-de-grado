"""Cliente de geocodificación contra Nominatim (OpenStreetMap).

Nominatim es el servicio de geocodificación gratuito del proyecto
OpenStreetMap. Se eligió por dos razones: no requiere llave de API (a
diferencia de Google Maps) y su política de uso es clara y respetable
para un proyecto académico de bajo volumen.

Reglas que este módulo respeta, sin excepción:
  1. Máximo 1 solicitud por segundo (política de uso de Nominatim).
  2. Siempre se envía un encabezado "User-Agent" identificando la
     aplicación (requisito de la política de uso; las solicitudes sin
     este encabezado pueden ser bloqueadas).
  3. Toda dirección ya consultada se guarda en una caché en disco, para
     no volver a consultar lo mismo si el script se ejecuta de nuevo.
  4. Si una dirección no tiene coincidencia o la consulta falla, se
     registra explícitamente como "sin resultado" (None). Nunca se
     inventan coordenadas de relleno.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

NOMINATIM_ENDPOINT = "https://nominatim.openstreetmap.org/search"
IDENTIFICACION_DE_LA_APLICACION = "Quiron-ProyectoDeGrado-UCompensar/1.0"

# Nominatim exige máximo 1 solicitud por segundo. Se deja un margen de
# seguridad de 0.1s adicionales para no quedar justo en el límite.
SEGUNDOS_ENTRE_SOLICITUDES = 1.1

RUTA_CACHE = Path(__file__).resolve().parents[1] / "data" / "cache" / "geocodificacion_cache.json"


def _cargar_cache():
    if not RUTA_CACHE.exists():
        return {}
    with open(RUTA_CACHE, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def _guardar_cache(cache):
    RUTA_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_CACHE, "w", encoding="utf-8") as archivo:
        json.dump(cache, archivo, ensure_ascii=False, indent=2)


def _consultar_nominatim(direccion_normalizada):
    """Hace la solicitud HTTP real. Devuelve (latitud, longitud) o None
    si no hubo coincidencia, hubo un error de red, o la respuesta no
    trajo el formato esperado."""
    parametros = {
        "q": direccion_normalizada,
        "format": "json",
        "limit": 1,
        "countrycodes": "co",
    }
    url_completa = NOMINATIM_ENDPOINT + "?" + urllib.parse.urlencode(parametros)

    peticion = urllib.request.Request(
        url_completa,
        headers={"User-Agent": IDENTIFICACION_DE_LA_APLICACION},
    )

    try:
        with urllib.request.urlopen(peticion, timeout=10) as respuesta_http:
            cuerpo_crudo = respuesta_http.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return None

    try:
        resultados = json.loads(cuerpo_crudo)
    except json.JSONDecodeError:
        return None

    if not resultados:
        return None

    primer_resultado = resultados[0]
    try:
        latitud = float(primer_resultado["lat"])
        longitud = float(primer_resultado["lon"])
    except (KeyError, ValueError, TypeError):
        return None

    return latitud, longitud


def geocodificar_direccion(direccion_normalizada, cache=None):
    """Devuelve (latitud, longitud) para una dirección ya normalizada, o
    None si no se pudo geocodificar. Si se encuentra en caché, no se hace
    ninguna solicitud de red ni se respeta el límite de velocidad (no
    hace falta: no hubo consulta nueva)."""
    if not direccion_normalizada:
        return None

    cache_en_uso = cache if cache is not None else _cargar_cache()

    if direccion_normalizada in cache_en_uso:
        valor_cacheado = cache_en_uso[direccion_normalizada]
        if valor_cacheado is None:
            return None
        return tuple(valor_cacheado)

    coordenadas = _consultar_nominatim(direccion_normalizada)
    time.sleep(SEGUNDOS_ENTRE_SOLICITUDES)

    cache_en_uso[direccion_normalizada] = list(coordenadas) if coordenadas else None

    if cache is None:
        _guardar_cache(cache_en_uso)

    return coordenadas


def geocodificar_lote(direcciones_normalizadas, mostrar_progreso=True):
    """Geocodifica una lista de direcciones. La caché en disco se
    actualiza inmediatamente después de cada CONSULTA NUEVA (no después
    de los aciertos de caché, que no lo necesitan), para que si el
    proceso se interrumpe a mitad de camino, el trabajo ya hecho no se
    pierda y la siguiente ejecución continúe donde quedó."""
    cache = _cargar_cache()
    resultados = {}
    total_direcciones = len(direcciones_normalizadas)

    for indice, direccion in enumerate(direcciones_normalizadas, start=1):
        ya_estaba_en_cache = direccion in cache
        coordenadas = geocodificar_direccion(direccion, cache=cache)
        resultados[direccion] = coordenadas

        if mostrar_progreso:
            origen = "caché" if ya_estaba_en_cache else "consulta nueva"
            print(f"[{indice}/{total_direcciones}] ({origen}) {direccion} -> {coordenadas}")

        if not ya_estaba_en_cache:
            _guardar_cache(cache)

    return resultados