from dataclasses import dataclass


@dataclass(frozen=True)
class Paleta:
    morado_profundo: str = "#330968"
    morado: str = "#6E48B1"
    morado_claro: str = "#9B7FD4"
    rosa: str = "#FA7AF0"
    rosa_suave: str = "#FDE8FB"
    lienzo: str = "#F5F3FA"
    tarjeta: str = "#FFFFFF"
    texto: str = "#231942"
    texto_tenue: str = "#6B6480"
    borde: str = "#E4DEF2"


MARCA = Paleta()

# Secuencia de colores para series de gráficos (se usará cuando lleguen
# los primeros Figure de Plotly en la siguiente rama).
SECUENCIA_GRAFICOS = [MARCA.morado, MARCA.rosa, MARCA.morado_claro, MARCA.morado_profundo]