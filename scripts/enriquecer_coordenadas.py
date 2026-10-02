"""Script de mantenimiento: geocodifica las sedes con oferta quirúrgica.

Este NO es un módulo que la aplicación importe en cada arranque — es una
tarea que se ejecuta manualmente, de vez en cuando (cuando llega un corte
de datos nuevo), y que deja su resultado guardado en un archivo CSV. El
dashboard luego simplemente LEE ese archivo, sin volver a geocodificar
nada ni depender de internet para funcionar.

Por qué está separado así:
  - Geocodificar 360 direcciones a 1 solicitud/segundo toma varios
    minutos. No tiene sentido hacer esperar al usuario del dashboard cada
    vez que lo abre.
  - Si el proceso se interrumpe a mitad de camino (se cierra la terminal,
    se cae la conexión), la caché en disco de `cliente.py` ya dejó
    guardado el trabajo hecho hasta ese punto — simplemente se vuelve a
    correr el script y continúa donde quedó, sin repetir direcciones ya
    resueltas.

Uso:
    python scripts/enriquecer_coordenadas.py
"""

import sys
from pathlib import Path

import pandas as pd

RAIZ_DEL_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_DEL_PROYECTO))

from quiron.data.loader import cargar_cirugia_plastica
from quiron.geocoding.normalizador import normalizar_direccion_bogota
from quiron.geocoding.cliente import geocodificar_lote

RUTA_SALIDA = RAIZ_DEL_PROYECTO / "quiron" / "data" / "processed" / "sedes_geocodificadas.csv"


def _obtener_sedes_quirurgicas_sin_duplicar(tabla_completa):
    """La tabla de loader.py trae una fila por cada (sede, servicio), así
    que una misma sede física puede aparecer varias veces (una por cada
    código de servicio que ofrece). Para geocodificar solo necesitamos
    una fila por sede, no una por combinación de servicio."""
    sedes_quirurgicas = tabla_completa[tabla_completa["es_quirurgico"]]
    columnas_de_sede = ["sede_id", "sede", "direccion"]
    return sedes_quirurgicas[columnas_de_sede].drop_duplicates(subset=["sede_id"]).reset_index(drop=True)


def _construir_tabla_enriquecida(sedes_unicas, mapa_coordenadas):
    filas_enriquecidas = []

    for _, fila in sedes_unicas.iterrows():
        direccion_normalizada = normalizar_direccion_bogota(fila["direccion"])
        coordenadas = mapa_coordenadas.get(direccion_normalizada) if direccion_normalizada else None

        if coordenadas:
            latitud, longitud = coordenadas
        else:
            latitud, longitud = None, None

        filas_enriquecidas.append({
            "sede_id": fila["sede_id"],
            "sede": fila["sede"],
            "direccion": fila["direccion"],
            "direccion_normalizada": direccion_normalizada,
            "latitud": latitud,
            "longitud": longitud,
            "geocodificado": coordenadas is not None,
        })

    return pd.DataFrame(filas_enriquecidas)


def _imprimir_resumen(tabla_enriquecida):
    total = len(tabla_enriquecida)
    exitosas = int(tabla_enriquecida["geocodificado"].sum())
    fallidas = total - exitosas
    porcentaje_exito = (exitosas / total * 100) if total else 0

    print()
    print("=" * 60)
    print("RESUMEN DE GEOCODIFICACIÓN")
    print("=" * 60)
    print(f"Sedes quirúrgicas procesadas : {total}")
    print(f"Geocodificadas con éxito     : {exitosas} ({porcentaje_exito:.1f}%)")
    print(f"Sin coordenadas              : {fallidas}")

    if fallidas:
        print()
        print("Sedes que quedaron SIN coordenadas (revisar manualmente):")
        sedes_sin_coordenadas = tabla_enriquecida[~tabla_enriquecida["geocodificado"]]
        for _, fila in sedes_sin_coordenadas.iterrows():
            print(f"  - {fila['sede']}: {fila['direccion']!r}")

    print()
    print(f"Archivo guardado en: {RUTA_SALIDA}")
    print("=" * 60)


def ejecutar():
    print("Cargando sedes con oferta quirúrgica desde el archivo fuente...")
    tabla_completa = cargar_cirugia_plastica()
    sedes_unicas = _obtener_sedes_quirurgicas_sin_duplicar(tabla_completa)
    print(f"Se encontraron {len(sedes_unicas)} sedes únicas con oferta quirúrgica.")

    print("Normalizando direcciones...")
    direcciones_normalizadas = [
        normalizar_direccion_bogota(direccion)
        for direccion in sedes_unicas["direccion"]
    ]
    direcciones_a_consultar = sorted({d for d in direcciones_normalizadas if d})

    sedes_sin_direccion_util = sum(1 for d in direcciones_normalizadas if d is None)
    if sedes_sin_direccion_util:
        print(
            f"Aviso: {sedes_sin_direccion_util} sede(s) no tienen una dirección "
            f"utilizable después de la limpieza (ver sección de fallidas al final)."
        )

    print(f"Se consultarán {len(direcciones_a_consultar)} direcciones distintas contra Nominatim.")
    print("Esto puede tardar varios minutos (1 solicitud por segundo). No cierres esta ventana.")
    print()

    mapa_coordenadas = geocodificar_lote(direcciones_a_consultar, mostrar_progreso=True)

    tabla_enriquecida = _construir_tabla_enriquecida(sedes_unicas, mapa_coordenadas)

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    tabla_enriquecida.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")

    _imprimir_resumen(tabla_enriquecida)


if __name__ == "__main__":
    ejecutar()