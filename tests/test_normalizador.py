"""Pruebas del normalizador de direcciones de Bogotá.

Cada caso de esta suite corresponde a una dirección REAL tomada del
archivo fuente del proyecto (no son ejemplos inventados), para asegurar
que los cambios futuros no rompan silenciosamente un patrón que ya
sabemos que funciona.
"""

from quiron.geocoding.normalizador import normalizar_direccion_bogota


def test_expande_prefijo_avenida_calle():
    resultado = normalizar_direccion_bogota("AC 127 # 71 96")
    assert resultado == "AVENIDA CALLE 127 # 71 96, Bogotá, Colombia"


def test_expande_prefijo_avenida_carrera():
    resultado = normalizar_direccion_bogota("AK 9 No. 116 - 20 Cs 220 - OF 224")
    assert resultado == "AVENIDA CARRERA 9 # 116-20, Bogotá, Colombia"


def test_expande_prefijo_carrera_abreviado_kr():
    resultado = normalizar_direccion_bogota("KR 10 No. 96 - 25 CS 403")
    assert resultado == "CARRERA 10 # 96-25, Bogotá, Colombia"


def test_expande_prefijo_carrera_abreviado_cra():
    resultado = normalizar_direccion_bogota("CRA 16 # 84 A 09 CONS 620")
    assert resultado == "CARRERA 16 # 84 A 09, Bogotá, Colombia"


def test_expande_prefijo_calle():
    resultado = normalizar_direccion_bogota("CL 50 # 9 67")
    assert resultado == "CALLE 50 # 9 67, Bogotá, Colombia"


def test_expande_prefijo_diagonal():
    resultado = normalizar_direccion_bogota("DG 115 A No. 70 C - 75 CASA 15 CS 4")
    assert resultado == "DIAGONAL 115 A # 70 C-75, Bogotá, Colombia"


def test_expande_prefijo_transversal():
    resultado = normalizar_direccion_bogota("TV 59 No 104B -86 CONS 704")
    assert resultado == "TRANSVERSAL 59 # 104B-86, Bogotá, Colombia"


def test_recorta_informacion_de_piso():
    resultado = normalizar_direccion_bogota(
        "CALLE 167 72 07 PISO 1,PISO 2 (EXCEPTO CONSULTORIOS 215 Y 216),"
        "PISO 3, PISO 4,PISO 5,PISO 6,PISO 7 Y PISO 8"
    )
    assert resultado == "CALLE 167 72 07, Bogotá, Colombia"


def test_recorta_informacion_de_oficina():
    resultado = normalizar_direccion_bogota("Carrera 45 # 106-71 Oficina 304")
    assert resultado == "CARRERA 45 # 106-71, Bogotá, Colombia"


def test_recorta_informacion_de_torre():
    resultado = normalizar_direccion_bogota(
        "AC 26 No. 69C-03 T. A y T. B Ofc. 3-01 y 5-01"
    )
    assert resultado == "AVENIDA CALLE 26 # 69C-03, Bogotá, Colombia"


def test_convierte_no_con_punto_a_numeral():
    resultado = normalizar_direccion_bogota("CRA 7A No. 123 - 23 OFICINA 6A")
    assert "# 123-23" in resultado


def test_convierte_no_sin_punto_a_numeral():
    resultado = normalizar_direccion_bogota("Calle 97 No 23 - 37 Cs 405, 406, 407")
    assert "# 23-37" in resultado


def test_convierte_n_suelta_entre_numeros_a_numeral():
    resultado = normalizar_direccion_bogota("AK 19 N 100-28")
    assert resultado == "AVENIDA CARRERA 19 # 100-28, Bogotá, Colombia"


def test_no_confunde_nomenclatura_real_con_letra_n():
    """La 'N' pegada a un número (ej. 'Carrera 7N') es parte real de la
    nomenclatura catastral bogotana, no un marcador de numeral — no debe
    modificarse."""
    resultado = normalizar_direccion_bogota("CARRERA 7N No 123-45")
    assert "7N" in resultado


def test_siempre_agrega_contexto_de_ciudad():
    resultado = normalizar_direccion_bogota("CL 50 # 9 67")
    assert resultado.endswith("Bogotá, Colombia")


def test_direccion_vacia_devuelve_none():
    assert normalizar_direccion_bogota("") is None


def test_direccion_none_devuelve_none():
    assert normalizar_direccion_bogota(None) is None


def test_direccion_solo_espacios_devuelve_none():
    assert normalizar_direccion_bogota("   ") is None


def test_direccion_que_queda_vacia_tras_limpieza_devuelve_none():
    """Si toda la dirección es solo un token de unidad interna, no debe
    fabricarse una dirección falsa: debe devolver None."""
    assert normalizar_direccion_bogota("PISO 3") is None