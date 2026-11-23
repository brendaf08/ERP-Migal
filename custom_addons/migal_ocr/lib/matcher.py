"""Asignación de productos por similitud difusa (ADR-011 y ADR-012, punto 6).

Origen: MIGAL SmartOps, ``servicio-ocr/app/matcher.py``, con la misma calibración
(pesos, penalizaciones por medida/material/tipo y corrección de errores de escritura).
Adaptado a Odoo: el catálogo son ``product.product`` y no depende de Pydantic.

El modelo de visión nunca elige el producto: este módulo compara cada línea leída
con el catálogo activo, así que solo se sugieren productos que existen.
"""
from collections import Counter
from dataclasses import dataclass

from .normalizador import PALABRAS_VACIAS, TextoNormalizado, normalizar, tipo_de_medida

try:  # RapidFuzz (C++) si está instalado; si no, equivalentes en Python puro.
    from rapidfuzz import fuzz as _fuzz
    from rapidfuzz.distance import DamerauLevenshtein as _DL

    def ratio(a, b):
        return _fuzz.ratio(a, b)

    def token_sort_ratio(a, b):
        return _fuzz.token_sort_ratio(a, b)

    def token_set_ratio(a, b):
        return _fuzz.token_set_ratio(a, b)

    def distancia(a, b, maxima):
        return _DL.distance(a, b, score_cutoff=maxima)

    MOTOR = "rapidfuzz"
except ImportError:  # pragma: no cover - depende del entorno
    from difflib import SequenceMatcher

    def ratio(a, b):
        if not a and not b:
            return 100.0
        return SequenceMatcher(None, a, b).ratio() * 100

    def token_sort_ratio(a, b):
        return ratio(" ".join(sorted(a.split())), " ".join(sorted(b.split())))

    def token_set_ratio(a, b):
        sa, sb = set(a.split()), set(b.split())
        comun = " ".join(sorted(sa & sb))
        resto_a = " ".join(sorted(sa - sb))
        resto_b = " ".join(sorted(sb - sa))
        t1 = comun
        t2 = (comun + " " + resto_a).strip()
        t3 = (comun + " " + resto_b).strip()
        if comun and (not resto_a or not resto_b):
            return 100.0
        return max(ratio(t1, t2), ratio(t1, t3), ratio(t2, t3))

    def distancia(a, b, maxima):
        # Distancia de Damerau-Levenshtein (alineamiento óptimo de cadenas).
        la, lb = len(a), len(b)
        d = [[0] * (lb + 1) for _ in range(la + 1)]
        for i in range(la + 1):
            d[i][0] = i
        for j in range(lb + 1):
            d[0][j] = j
        for i in range(1, la + 1):
            for j in range(1, lb + 1):
                costo = 0 if a[i - 1] == b[j - 1] else 1
                d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + costo)
                if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                    d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
        return d[la][lb] if d[la][lb] <= maxima else maxima + 1

    MOTOR = "difflib"

PESO_ORDEN = 0.6
PESO_CONJUNTO = 0.4
FACTOR_MEDIDA_INCOMPATIBLE = 0.3
FACTOR_TIPO_DISTINTO = 0.7
SIMILITUD_TIPO = 80
MATERIALES = frozenset({"pvc", "cpvc", "bronce", "galvanizado", "cobre", "acero"})
MAXIMO_COINCIDENCIAS = 3
LONGITUD_MINIMA_CORRECCION = 4
LONGITUD_DOS_ERRORES = 8
FACTOR_PALABRA_CORREGIDA = 0.95
CANDIDATOS_PREFILTRO = 50


@dataclass(frozen=True)
class Candidato:
    """Producto del catálogo con su texto normalizado."""

    producto_id: int
    normalizado: TextoNormalizado


@dataclass(frozen=True)
class Coincidencia:
    producto_id: int
    confianza: float


def preparar_catalogo(productos, jerga_extra=None):
    """``productos``: iterable de (id, texto) con nombre, marca y presentación."""
    return [Candidato(pid, normalizar(texto, jerga_extra)) for pid, texto in productos if texto]


def vocabulario(candidatos):
    palabras = Counter()
    for c in candidatos:
        for palabra in set(c.normalizado.texto.split()):
            if (palabra not in c.normalizado.medidas and palabra.isalpha()
                    and len(palabra) >= LONGITUD_MINIMA_CORRECCION):
                palabras[palabra] += 1
    return palabras


def corregir_errores(linea, palabras):
    """Corrige palabras que no existen en el catálogo y están a una o dos letras de una que sí."""
    corregidas, cambio = [], False
    for palabra in linea.texto.split():
        corregida = palabra
        largo = len(palabra)
        if (largo >= LONGITUD_MINIMA_CORRECCION and palabra.isalpha() and palabra not in palabras
                and palabra not in PALABRAS_VACIAS and palabra not in linea.medidas):
            maxima = 2 if largo >= LONGITUD_DOS_ERRORES else 1
            mejor = None
            for existente, usos in palabras.items():
                if abs(len(existente) - largo) > maxima:
                    continue
                d = distancia(palabra, existente, maxima)
                if d > maxima:
                    continue
                clave = (d, -usos, existente)
                if mejor is None or clave < mejor:
                    mejor = clave
            if mejor is not None:
                corregida, cambio = mejor[2], True
        corregidas.append(corregida)
    if not cambio:
        return linea, False
    return TextoNormalizado(" ".join(corregidas), linea.medidas), True


def medidas_incompatibles(linea, candidato):
    for tipo in {tipo_de_medida(m) for m in linea}:
        de_linea = {m for m in linea if tipo_de_medida(m) == tipo}
        del_candidato = {m for m in candidato if tipo_de_medida(m) == tipo}
        if del_candidato and not de_linea & del_candidato:
            return True
    return False


def materiales_incompatibles(linea, candidato):
    de_linea = MATERIALES & set(linea.texto.split())
    del_candidato = MATERIALES & set(candidato.texto.split())
    return bool(de_linea and del_candidato and not de_linea & del_candidato)


def comparte_tipo_de_producto(linea, candidato):
    primera = next((p for p in linea.texto.split() if p not in linea.medidas), None)
    if primera is None:
        return True
    return any(ratio(primera, palabra) >= SIMILITUD_TIPO for palabra in candidato.texto.split())


def puntaje(linea, candidato):
    """Confianza de 0 a 1 de que la línea corresponda al candidato."""
    if not linea.texto or not candidato.texto:
        return 0.0
    base = (PESO_ORDEN * token_sort_ratio(linea.texto, candidato.texto)
            + PESO_CONJUNTO * token_set_ratio(linea.texto, candidato.texto)) / 100
    if medidas_incompatibles(linea.medidas, candidato.medidas) or materiales_incompatibles(linea, candidato):
        base *= FACTOR_MEDIDA_INCOMPATIBLE
    if not comparte_tipo_de_producto(linea, candidato):
        base *= FACTOR_TIPO_DISTINTO
    return round(min(max(base, 0.0), 1.0), 3)


def coincidencias(texto, candidatos, umbral_baja=0.35, jerga_extra=None, palabras=None):
    """Hasta tres coincidencias con confianza >= ``umbral_baja``, de mayor a menor.

    Devuelve (texto_normalizado, [Coincidencia], corregida).
    """
    palabras = palabras if palabras is not None else vocabulario(candidatos)
    linea, corregida = corregir_errores(normalizar(texto, jerga_extra), palabras)
    elegidos = candidatos
    if len(candidatos) > CANDIDATOS_PREFILTRO and linea.texto:
        puntuados = sorted(((token_set_ratio(linea.texto, c.normalizado.texto), i)
                            for i, c in enumerate(candidatos)), reverse=True)
        elegidos = [candidatos[i] for _p, i in puntuados[:CANDIDATOS_PREFILTRO]]
    factor = FACTOR_PALABRA_CORREGIDA if corregida else 1.0
    puntuados = [(round(puntaje(linea, c.normalizado) * factor, 3), c.producto_id) for c in elegidos]
    seleccionados = sorted((p for p in puntuados if p[0] >= umbral_baja), key=lambda p: (-p[0], p[1]))
    return linea.texto, [Coincidencia(pid, valor) for valor, pid in seleccionados[:MAXIMO_COINCIDENCIAS]], corregida


def relacionados(texto, candidatos, jerga_extra=None, palabras=None, maximo=8, umbral=0.0):
    """Productos del mismo tipo que la línea (la primera palabra: «cemento», «fierro», «ladrillo»...),
    de mayor a menor puntaje. Sirven para sugerir y para limitar el selector de producto."""
    palabras = palabras if palabras is not None else vocabulario(candidatos)
    linea, corregida = corregir_errores(normalizar(texto, jerga_extra), palabras)
    tipo = next((p for p in linea.texto.split() if p not in linea.medidas), None)
    if not tipo:
        return []
    mismos = [c for c in candidatos
              if any(ratio(tipo, p) >= SIMILITUD_TIPO for p in c.normalizado.texto.split())]
    puntuados = sorted(((puntaje(linea, c.normalizado), c.producto_id) for c in mismos), key=lambda p: (-p[0], p[1]))
    return [pid for valor, pid in puntuados if valor >= umbral][:maximo]
