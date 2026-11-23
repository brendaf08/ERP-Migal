"""Normalización del texto ferretero (ADR-011, capa determinista).

Origen: MIGAL SmartOps, ``servicio-ocr/app/normalizador.py``. Adaptado a Odoo: la jerga
base se amplía con términos ferreteros y con los sinónimos editables desde Odoo
(``migal.ocr.sinonimo``), que llegan en el parámetro ``jerga_extra``.

Convierte una descripción leída (``"Cem. Sol 42,5 kgs x 2 bls"``, ``"F° 1/2\""``) a una forma comparable: minúsculas,
sin tildes, con la jerga expandida y con las medidas críticas en forma canónica. Las medidas se devuelven aparte porque
la regla de consistencia técnica del matcher las compara por tipo: ``1/2in`` frente a ``3/8in`` no es la misma pieza.
"""

import re
import unicodedata
from dataclasses import dataclass

# Jerga y abreviaturas frecuentes en notas de mostrador y guías. Se amplía con el conjunto de evaluación.
JERGA: dict[str, str] = {
    "kk": "king kong",
    "f°": "fierro",
    "fo": "fierro",
    "fe": "fierro",
    "fierr": "fierro",
    "bls": "bolsa",
    "bols": "bolsa",
    "bl": "bolsa",
    "bol": "bolsa",
    "cem": "cemento",
    "cmto": "cemento",
    "cto": "cemento",
    "lad": "ladrillo",
    "ladr": "ladrillo",
    "tub": "tubo",
    "und": "unidad",
    "unid": "unidad",
    "uds": "unidad",
    "pza": "pieza",
    "pzas": "pieza",
    "galv": "galvanizado",
    "corrug": "corrugado",
    "cor": "corrugado",
    # En las notas de venta el diámetro (ϕ, Ø) antes de una medida designa la varilla de fierro: "Ø 5/8".
    "φ": "fierro",
    "ø": "fierro",
    # El modelo a veces transcribe el símbolo de diámetro como letras: "fi 1/4", "phi 3/8".
    "fi": "fierro",
    "phi": "fierro",
    "ag": "agua",
    "gdon": "galon",
    "glon": "galon",
    "gln": "galon",
    "octagonal": "octogonal",
    # Ampliación MIGAL (Odoo): nombres coloquiales y abreviaturas de mostrador.
    "huincha": "wincha",
    "winchas": "wincha",
    "flexometro": "wincha",
    "fluxometro": "wincha",
    "temflex": "cinta aislante",
    "aislante": "cinta aislante",
    "teflon": "cinta teflon",
    "maskin": "masking",
    "maskintape": "masking",
    "terokal": "pegamento",
    "cola": "pegamento",
    "tarugo": "tarugo",
    "tarugos": "tarugo",
    "taco": "tarugo",
    "foco": "foco",
    "bombilla": "foco",
    "bombillo": "foco",
    "ampolla": "foco",
    "dicroico": "dicroico",
    "termica": "termomagnetico",
    "llave termica": "termomagnetico",
    "breaker": "termomagnetico",
    "tomacorriente": "tomacorriente",
    "enchufe": "tomacorriente",
    "toma": "tomacorriente",
    "calamina": "calamina",
    "eternit": "calamina",
    "triplay": "triplay",
    "plywood": "triplay",
    "desarmador": "desarmador",
    "destornillador": "desarmador",
    "atornillador": "desarmador",
    "alicate": "alicate",
    "pinza": "alicate",
    "amoladora": "amoladora",
    "esmeril": "amoladora",
    "moladora": "amoladora",
    "rotomartillo": "rotomartillo",
    "taladro": "taladro",
    "brocha": "brocha",
    "pincel": "brocha",
    "lija": "lija",
    "clavos": "clavo",
    "clv": "clavo",
    "alam": "alambre",
    "alamb": "alambre",
    "fierros": "fierro",
    "varillas": "fierro",
    "acero corrugado": "fierro corrugado",
    "pvc": "pvc",
    "sap": "pvc",
    "desague": "desague",
    "dsg": "desague",
    "cpvc": "cpvc",
    "cemento sol": "cemento sol",
    "andino": "andino",
    "yura": "yura",
    "pacasmayo": "pacasmayo",
    "arena gruesa": "arena gruesa",
    "piedra chancada": "piedra chancada",
    "chancada": "piedra chancada",
    "hormigon": "hormigon",
    "yeso": "yeso",
    "sika": "sika",
    "silicona": "silicona",
    "silicon": "silicona",
    "cable mellizo": "cable mellizo",
    "mellizo": "cable mellizo",
    "cbl": "cable",
    "tub": "tubo",
    "tuberia": "tubo",
    "cdo": "codo",
    "codos": "codo",
    "tee": "tee",
    "te": "tee",
    "unio": "union",
    "valvula": "valvula",
    "llave paso": "valvula",
    "llave de paso": "valvula",
    "caño": "grifo",
    "cano": "grifo",
    "grifo": "grifo",
    "pintura": "pintura",
    "latex": "pintura latex",
    "esmalte": "pintura esmalte",
    "thinner": "thinner",
    "tiner": "thinner",
    "disco corte": "disco corte",
    "pala": "pala",
    "lampa": "pala",
    "carretilla": "carretilla",
    "buggy": "carretilla",
    "pico": "pico",
    "barreta": "barreta",
    "malla": "malla",
    "tornillo": "tornillo",
    "tornillos": "tornillo",
    "perno": "perno",
    "pernos": "perno",
    "tuerca": "tuerca",
    "arandela": "arandela",
    "huacha": "arandela",
    "guacha": "arandela",
}

# Palabras que no distinguen un producto de otro: conectores, unidades de venta y medidas de longitud o volumen que
# las notas escriben junto a la cantidad ("20 varillas", "mtrs arena gruesa", "Kg clavo"). Se descartan en ambos lados
# de la comparación, igual que los tokens de una sola letra ("tipo I", "N° 16").
PALABRAS_VACIAS: frozenset[str] = frozenset(
    {
        "de", "del", "la", "el", "los", "las", "para", "con", "y", "x", "tipo", "inc",
        "varilla", "bolsa", "unidad", "pieza", "millar", "ciento", "docena", "juego",
        "kg", "kilo", "m", "mt", "mts", "mtr", "mtrs", "metro", "m3", "cm", "galon", "litro",
        # Ampliación MIGAL: «mil» (millar), «id»/«idem» (ídem: igual a la línea anterior), «pul».
        "mil", "id", "idem", "pul", "niu",
    }
)  # fmt: skip

# Lecturas habituales de las notas de venta manuscritas de MIGAL (fotos reales de Documentos-Escanear):
# abreviaturas y letras que el transcriptor confunde. Se aplican antes que la jerga.
_CORRECCIONES = [
    # «Cem sol», «cemto sol», «Com sal», «Coul sal», «cen sol» -> cemento sol
    (re.compile(r"\b(?:cemento|cemto|cmto|cem|cto|com|coul|cen|cemt)\.?\s*s[aeo]l\b\.?"), "cemento sol"),
    # «A. gruesa», «4. gruesa», «Ar. gruesa», «aren fin», «Mt de fina», «bol. fina» -> arena gruesa / arena fina
    (re.compile(r"\b(?:a|4|ar|are|aren|ae)\.?\s+(gruesa|fina?)\b"), r"arena \1"),
    (re.compile(r"\b(?:mt|mts|mtrs|m3|bol|bls|bolsa)\.?\s+(?:de\s+)?(gruesa|fina?)\b"), r"arena \1"),
    (re.compile(r"\barena fin\b"), "arena fina"),
    # «P. ch.», «P. chancada», «pdra chancada» -> piedra chancada
    (re.compile(r"\b(?:p|pdra|pied)\.?\s*ch(?:ancada|anc|\.)?(?=\s|$|\d)"), "piedra chancada "),
    # Unidad mal leída delante de alambre o clavo («f° alambre 16» es «kg alambre 16»).
    (re.compile(r"(?:\bkg|\bkl|\bk|f°|\bfo|\bfe)\.?\s+(?=alambre|clavo)"), ""),
    # Códigos internos de facturas y guías de proveedores: «[3029]», «(MAST525R)», «(77460434)».
    (re.compile(r"\[[^\]]*\]"), " "),
    (re.compile(r"\((?=[^)\"]*\d)[a-z0-9\-/.]{4,}\)"), " "),
]
_CODIGO = re.compile(r"^(?!\d+x\d+$)(?=.*\d)(?=.*[a-z])[a-z0-9\-]{5,}$|^\d{5,}$")

# Envases que una nota escribe después de la cantidad ("2 cajas clavo 3\""): no son el tipo de producto. Tras una
# cantidad inicial se mueven al final para que la primera palabra siga siendo el producto. Sin cantidad, "caja
# octogonal" sí es el producto y no se toca.
EMPAQUES: frozenset[str] = frozenset({"caja", "saco", "balde", "rollo", "paquete", "galonera", "lata", "frasco"})

# Palabras que terminan como un plural sin serlo: "arnés" no es el plural de "arn".
NO_SINGULARIZAR: frozenset[str] = frozenset(
    {"arnes", "compas", "gas", "mes", "tres", "seis", "dos", "ingles", "pais", "atlas", "lunes", "martes", "jueves"}
)

_FRACCION_PALABRAS = {"media": "1/2", "medio": "1/2", "un cuarto": "1/4", "tres octavos": "3/8", "un octavo": "1/8"}

_NUMERO = r"\d+(?:[.,]\d+)?"
_PULGADA = re.compile(rf'(?<![\d/])(\d+\s*/\s*\d+|{_NUMERO})\s*(?:"|\'\'|”|pulgadas?|pulg\.?|plg\.?)')
_FRACCION_SUELTA = re.compile(r"(?<![\d/])(\d+)\s*/\s*(\d+)(?![\d/a-z])")
_KILOS = re.compile(rf"(?<![\d.,])({_NUMERO})\s*(?:kgs?|kilos?|kilogramos?)\b")
_HUECOS = re.compile(r"(?<!\d)(\d+)\s*huecos?\b")
# "KK18" es el ladrillo King Kong de 18 huecos, como lo nombran los catálogos. Solo pegado o con guion: en "KK 2 bls"
# el número es la cantidad.
_KING_KONG = re.compile(r"\bkk-?(\d+)\b(?!\s*huecos?)")
_AWG = re.compile(r"(?<!\d)(?:n[°o]\s*)?(\d+)\s*awg\b|\bawg\s*(\d+)\b")
_MILIMETROS = re.compile(rf"(?<![\d.,])({_NUMERO})\s*mm\b")
# Volumen: "1/4 galón", "4 L", "500 ml". Se reconoce antes que la fracción suelta, que la tomaría por pulgadas.
_VOLUMEN = re.compile(rf"(?<![\d/])(\d+\s*/\s*\d+|{_NUMERO})\s*(galones|galon|gal|gln|litros|litro|lts|lt|l|ml)\b")
_ONZAS = re.compile(rf"(?<![\d.,])({_NUMERO})\s*oz\b")
_VATIOS = re.compile(rf"(?<![\d.,])({_NUMERO})\s*w\b")
_GALON_SUELTO = re.compile(r"\b(?:galones|galon|gal|gln|glon|gdon)\b")
_UNIDAD_VOLUMEN = {"galones": "gal", "galon": "gal", "gal": "gal", "gln": "gal", "ml": "ml"}
_LARGO = re.compile(rf"\bx\s*({_NUMERO})\s*m\b")
_FORMATO = re.compile(r"(?<![\d/])(\d+)\s*x\s*(\d+)(?:\s*cm\b)?")
# Cantidad al inicio de la línea ("20 varillas F° 1/2\"", "10 bls cem sol"), salvo que sea la medida del producto.
_CANTIDAD_INICIAL = re.compile(
    rf"^\s*{_NUMERO}\s+(?!(?:kgs?|kilos?|kilogramos?|mm|huecos?|awg|pulg\w*|plg|gal\w*|gln|l|lts?|litros?|ml|oz|w)\b"
    rf"|[\"'”/])"
)
_SEPARADORES = re.compile(r"[^\w/.\s]")
_ESPACIOS = re.compile(r"\s+")


@dataclass(frozen=True)
class TextoNormalizado:
    """Texto comparable y medidas críticas detectadas, por ejemplo ``{"1/2in", "42.5kg"}``."""

    texto: str
    medidas: frozenset[str]


def _sin_tildes(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _numero(valor: str) -> str:
    """Número con punto decimal y sin ceros sobrantes: ``42,50`` → ``42.5``."""
    numero = valor.replace(",", ".")
    if "." in numero:
        numero = numero.rstrip("0").rstrip(".")
    return numero


def _fraccion(valor: str) -> str:
    return re.sub(r"\s+", "", valor)


def singular(palabra: str) -> str:
    """Singular aproximado del español para comparar ``codos`` con ``codo`` y ``uniones`` con ``union``."""
    if len(palabra) <= 3 or not palabra.isalpha() or palabra in NO_SINGULARIZAR:
        return palabra
    if palabra.endswith("ces") and len(palabra) > 4:
        return palabra[:-3] + "z"
    if palabra.endswith("es") and palabra[-3] in "rnlzd":
        return palabra[:-2]
    if palabra.endswith("s") and palabra[-2] in "aeiou":
        return palabra[:-1]
    return palabra


def normalizar(texto: str, jerga_extra: dict[str, str] | None = None) -> TextoNormalizado:
    """Normaliza una descripción y separa sus medidas críticas.

    ``jerga_extra``: sinónimos adicionales (por ejemplo, los editados en Odoo). Las claves de
    varias palabras se reemplazan como frase antes de separar las palabras.
    """
    jerga = dict(JERGA)
    if jerga_extra:
        jerga.update({_sin_tildes(k.lower()).strip(): _sin_tildes(v.lower()).strip()
                      for k, v in jerga_extra.items() if k and v})
    actual = _sin_tildes(texto.lower()).replace("º", "°")
    for patron, reemplazo in _CORRECCIONES:
        actual = patron.sub(reemplazo, actual)
    for frase in sorted((k for k in jerga if " " in k), key=len, reverse=True):
        actual = re.sub(rf"\b{re.escape(frase)}\b", jerga[frase], actual)
    # El símbolo de diámetro llega como `ø`, `φ`, `∅` o `⌀` según el modelo; los dos últimos no son letras.
    actual = actual.replace("∅", " ø ").replace("⌀", " ø ")
    con_cantidad = bool(_CANTIDAD_INICIAL.match(actual))
    actual = _CANTIDAD_INICIAL.sub("", actual, count=1)
    for palabras, fraccion in _FRACCION_PALABRAS.items():
        actual = re.sub(rf"\b{palabras}\s+pulgadas?\b", f'{fraccion}"', actual)

    medidas: set[str] = set()

    def registrar(medida: str) -> str:
        medidas.add(medida)
        return f" {medida} "

    def pulgadas(valor: str) -> str:
        return registrar(f"{_fraccion(valor) if '/' in valor else _numero(valor)}in")

    def largo(valor: str) -> str:
        # El largo de la pieza ("x 9 m") se conserva como medida, pero no se compara como texto: las notas no lo
        # escriben y restaría similitud a todas las líneas.
        medidas.add(f"{_numero(valor)}m")
        return " "

    actual = _KING_KONG.sub(lambda m: f" kk {m.group(1)} huecos ", actual)
    actual = _LARGO.sub(lambda m: largo(m.group(1)), actual)
    actual = _FORMATO.sub(lambda m: f" {m.group(1)}x{m.group(2)} ", actual)

    def volumen(valor: str, unidad: str) -> str:
        cantidad = _fraccion(valor) if "/" in valor else _numero(valor)
        return registrar(f"{cantidad}{_UNIDAD_VOLUMEN.get(unidad, 'l')}")

    actual = _VOLUMEN.sub(lambda m: volumen(m.group(1), m.group(2)), actual)
    actual = _ONZAS.sub(lambda m: registrar(f"{_numero(m.group(1))}oz"), actual)
    actual = _VATIOS.sub(lambda m: registrar(f"{_numero(m.group(1))}w"), actual)
    actual = _PULGADA.sub(lambda m: pulgadas(m.group(1)), actual)
    actual = _KILOS.sub(lambda m: registrar(f"{_numero(m.group(1))}kg"), actual)
    actual = _HUECOS.sub(lambda m: registrar(f"{m.group(1)}huecos"), actual)
    actual = _AWG.sub(lambda m: registrar(f"{m.group(1) or m.group(2)}awg"), actual)
    actual = _MILIMETROS.sub(lambda m: registrar(f"{_numero(m.group(1))}mm"), actual)
    # Una fracción sin unidad en ferretería es una medida en pulgadas ("fierro 1/2"), salvo que la línea hable de
    # galones con la unidad separada de la cantidad ("galón pegamento 1/4").
    unidad_suelta = "gal" if _GALON_SUELTO.search(actual) else "in"
    actual = _FRACCION_SUELTA.sub(lambda m: registrar(f"{m.group(1)}/{m.group(2)}{unidad_suelta}"), actual)

    actual = actual.replace("f°", " fierro ")
    palabras = []
    for palabra in _SEPARADORES.sub(" ", actual).split():
        palabra = palabra.strip(".")
        if not palabra:
            continue
        if palabra in medidas:
            palabras.append(palabra)
            continue
        if _CODIGO.match(palabra):
            continue  # código de proveedor («m01ao004», «0207tam», «006280»): no describe el producto
        palabra = jerga.get(palabra) or jerga.get(singular(palabra)) or singular(palabra)
        if not (len(palabra) == 1 and palabra.isalpha()) and palabra not in PALABRAS_VACIAS:
            palabras.append(palabra)
    if con_cantidad and len(palabras) > 1 and palabras[0] in EMPAQUES:
        palabras.append(palabras.pop(0))
    # La jerga puede repetir palabras («cinta temflex» -> «cinta cinta aislante»): se dejan una vez.
    unicas = []
    for palabra in " ".join(palabras).split():
        if palabra not in unicas:
            unicas.append(palabra)
    return TextoNormalizado(_ESPACIOS.sub(" ", " ".join(unicas)).strip(), frozenset(medidas))


def tipo_de_medida(medida: str) -> str:
    """Tipo de una medida canónica: ``in``, ``kg``, ``huecos``, ``awg``, ``mm``, ``m``, ``gal``, ``l``, ``ml``, ``oz``
    o ``w``."""
    return re.sub(r"^[\d./]+", "", medida)
