"""Capa de observabilidad y orquestación del ETL de Quirón.

Este paquete expone una ejecución instrumentada del proceso de
extracción, transformación y carga (ETL) de la oferta quirúrgica. A
diferencia del ``loader``, que solo devuelve datos, esta capa registra
cada paso, los errores y la traza de mapeo de campos, de modo que el
dashboard pueda mostrar de forma transparente cómo se construyó el
conjunto de datos a partir del CSV fuente.
"""

from quiron.etl.observabilidad import (
    MapeoCampo,
    NivelTraza,
    PasoETL,
    TrazaETL,
)
from quiron.etl.pipeline import (
    ResultadoETL,
    ejecutar_etl,
)

__all__ = [
    "NivelTraza",
    "PasoETL",
    "TrazaETL",
    "MapeoCampo",
    "ResultadoETL",
    "ejecutar_etl",
]
