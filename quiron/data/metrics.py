"""Cálculos de resumen sobre la tabla de oferta quirúrgica.

Todo lo que necesite sumar, contar o agrupar cifras para mostrarlas en
pantalla vive aquí, separado de cómo se leen los archivos (loader.py) y
de cómo se dibujan (layout.py). Así, si mañana cambia la fuente de datos
o cambia el diseño, este cálculo no se toca.
"""

import pandas as pd


def resumen_general(tabla):
    quirurgicas = tabla[tabla["es_quirurgico"]]

    total_sedes = tabla["sede_id"].nunique()
    sedes_quirurgicas = quirurgicas["sede_id"].nunique()
    tipos_servicio = quirurgicas["codigo_servicio"].nunique()

    sedes_publicas = quirurgicas.loc[quirurgicas["naturaleza"] == "Pública", "sede_id"].nunique()
    sedes_privadas = quirurgicas.loc[quirurgicas["naturaleza"] == "Privada", "sede_id"].nunique()

    resumen = {
        "sedes_totales": total_sedes,
        "sedes_con_oferta_quirurgica": sedes_quirurgicas,
        "registros_quirurgicos": len(quirurgicas),
        "tipos_de_servicio_quirurgico": tipos_servicio,
        "sedes_publicas": sedes_publicas,
        "sedes_privadas": sedes_privadas,
    }
    return resumen


def conteo_por_servicio(tabla):
    quirurgicas = tabla[tabla["es_quirurgico"]]
    agrupado = quirurgicas.groupby("nombre_servicio")["sede_id"].nunique()
    ordenado = agrupado.sort_values(ascending=False)
    conteo = ordenado.reset_index(name="sedes")
    return conteo


def conteo_por_naturaleza(tabla):
    quirurgicas = tabla[tabla["es_quirurgico"]]
    sin_repetidos = quirurgicas.drop_duplicates("sede_id")
    agrupado = sin_repetidos.groupby("naturaleza")["sede_id"].nunique()
    ordenado = agrupado.sort_values(ascending=False)
    conteo = ordenado.reset_index(name="sedes")
    return conteo