"""Modelo de observabilidad del proceso ETL de Quirón.

Define estructuras ligeras para registrar, de forma trazable:

  - El histórico de pasos del ETL (``PasoETL``), con marca de tiempo,
    nivel, mensaje y duración.
  - La traza de mapeo de campos (``MapeoCampo``), que documenta cómo cada
    columna del origen se transforma en una columna del resultado.
  - Los errores encontrados durante el proceso.

La clase ``TrazaETL`` acumula esta información y la serializa a
estructuras simples (listas de diccionarios) aptas para enviarse a la
interfaz Dash a través de un ``dcc.Store``.
"""

from dataclasses import (
    dataclass,
    field,
)
from datetime import datetime
from enum import Enum
from zoneinfo import ZoneInfo


ZONA_HORARIA_COLOMBIA = ZoneInfo(
    "America/Bogota"
)


class NivelTraza(str, Enum):
    """Nivel de severidad de un paso del ETL."""

    INFO = "info"
    EXITO = "exito"
    ADVERTENCIA = "advertencia"
    ERROR = "error"


@dataclass
class PasoETL:
    """Un paso individual registrado durante el ETL."""

    orden: int
    nombre: str
    nivel: NivelTraza
    mensaje: str
    marca_tiempo: str
    duracion_ms: float
    filas: int | None = None
    fase: str = "Proceso"
    filas_entrada: int | None = None
    filas_salida: int | None = None
    filas_eliminadas: int | None = None
    columnas_entrada: int | None = None
    columnas_salida: int | None = None
    detalle: str | None = None

    def como_dict(self):
        """Serializa el paso a un diccionario simple."""

        return {
            "orden": self.orden,
            "fase": self.fase,
            "nombre": self.nombre,
            "nivel": self.nivel.value,
            "mensaje": self.mensaje,
            "marca_tiempo": self.marca_tiempo,
            "duracion_ms": round(
                self.duracion_ms,
                2,
            ),
            "filas": self.filas,
            "filas_entrada": self.filas_entrada,
            "filas_salida": self.filas_salida,
            "filas_eliminadas": self.filas_eliminadas,
            "columnas_entrada": self.columnas_entrada,
            "columnas_salida": self.columnas_salida,
            "detalle": self.detalle,
        }


@dataclass
class MapeoCampo:
    """Documenta la transformación de una columna origen a destino."""

    campo_origen: str
    campo_destino: str
    transformacion: str
    filas: int | None = None

    def como_dict(self):
        """Serializa el mapeo a un diccionario simple."""

        return {
            "campo_origen": self.campo_origen,
            "campo_destino": self.campo_destino,
            "transformacion": self.transformacion,
            "filas": self.filas,
        }


@dataclass
class TrazaETL:
    """Acumula el histórico, el mapeo de campos y los errores del ETL."""

    pasos: list = field(
        default_factory=list
    )
    mapeos: list = field(
        default_factory=list
    )
    errores: list = field(
        default_factory=list
    )
    _inicio: float = field(
        default=0.0,
        repr=False,
    )

    def __post_init__(self):
        import time

        self._reloj = time.perf_counter
        self._inicio = self._reloj()

    def _ahora_legible(self):
        return datetime.now(
            ZONA_HORARIA_COLOMBIA
        ).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    def registrar(
        self,
        nombre,
        mensaje,
        nivel=NivelTraza.INFO,
        filas=None,
        fase="Proceso",
        filas_entrada=None,
        filas_salida=None,
        filas_eliminadas=None,
        columnas_entrada=None,
        columnas_salida=None,
        detalle=None,
        duracion_ms=None,
    ):
        """Registra un paso y sus métricas de entrada y salida."""

        paso = PasoETL(
            orden=len(self.pasos) + 1,
            nombre=nombre,
            nivel=nivel,
            mensaje=mensaje,
            marca_tiempo=self._ahora_legible(),
            duracion_ms=(
                max(0.0, float(duracion_ms))
                if duracion_ms is not None
                else 0.0
            ),
            filas=(
                filas
                if filas is not None
                else filas_salida
            ),
            fase=fase,
            filas_entrada=filas_entrada,
            filas_salida=filas_salida,
            filas_eliminadas=filas_eliminadas,
            columnas_entrada=columnas_entrada,
            columnas_salida=columnas_salida,
            detalle=detalle,
        )

        self.pasos.append(paso)

        if nivel is NivelTraza.ERROR:
            self.errores.append(
                {
                    "fase": fase,
                    "paso": nombre,
                    "mensaje": mensaje,
                    "marca_tiempo": (
                        paso.marca_tiempo
                    ),
                }
            )

        return paso

    def registrar_error(
        self,
        nombre,
        mensaje,
        fase="Validación",
    ):
        """Atajo para registrar un paso con nivel de error."""

        return self.registrar(
            nombre,
            mensaje,
            nivel=NivelTraza.ERROR,
            fase=fase,
        )

    def mapear(
        self,
        campo_origen,
        campo_destino,
        transformacion,
        filas=None,
    ):
        """Añade una entrada a la traza de mapeo de campos."""

        mapeo = MapeoCampo(
            campo_origen=campo_origen,
            campo_destino=campo_destino,
            transformacion=transformacion,
            filas=filas,
        )

        self.mapeos.append(mapeo)

        return mapeo

    @property
    def tiene_errores(self):
        """Indica si se registró al menos un error."""

        return bool(self.errores)

    @property
    def duracion_total_ms(self):
        """Duración acumulada desde la creación de la traza."""

        return (
            self._reloj() - self._inicio
        ) * 1000.0

    def como_dict(self):
        """Serializa la traza completa a estructuras simples."""

        return {
            "pasos": [
                paso.como_dict()
                for paso in self.pasos
            ],
            "mapeos": [
                mapeo.como_dict()
                for mapeo in self.mapeos
            ],
            "errores": list(self.errores),
            "tiene_errores": self.tiene_errores,
            "duracion_total_ms": round(
                self.duracion_total_ms,
                2,
            ),
        }
