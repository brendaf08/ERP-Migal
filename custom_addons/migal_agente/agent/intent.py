"""Intérprete de mensajes del chat.

Convierte un mensaje libre en (herramienta, argumentos). Si no reconoce la
intención devuelve ``("ayuda", {})``. El mismo contrato lo usa la capa de IA
opcional, por lo que ambos caminos ejecutan exactamente las mismas herramientas.

Antes de interpretar, ``corregir`` normaliza la forma en que la gente escribe:
errores ortográficos («cotisacion», «estdo de cuenta»), plurales («qrs»,
«deudas») y variantes coloquiales («wasap», «guasap», «kr»).
"""
import calendar
import difflib
import re
from datetime import date, timedelta

from .guardrails import normalize

ORDER_RE = re.compile(r"\b([a-z]{1,4}\d{3,}(?:-\d+)?)\b", re.I)
DATE_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b|\b(\d{4})-(\d{2})-(\d{2})\b")
# «para el 20/11», «hasta el 5/12»: día y mes sin año (año en curso).
DATE_SIN_ANIO_RE = re.compile(r"\b(?:el|para|al|del|hasta|desde)\s+(\d{1,2})/(\d{1,2})\b(?![/-]\d)")

MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
         "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}

# Vocabulario que el intérprete reconoce; una palabra mal escrita se corrige hacia la más parecida.
VOCABULARIO = {
    "cotizacion", "cotizaciones", "proforma", "proformas", "presupuesto", "presupuestos", "version", "versiones",
    "whatsapp", "cobertura", "stock", "disponibilidad", "disponible", "alcanza", "faltante", "faltantes",
    "estado", "cuenta", "deuda", "saldo", "debe", "pagos", "pago", "historial", "abonos", "movimientos",
    "registrar", "registra", "envio", "enviado", "envie", "enviar", "envia", "manda", "mandale", "mandar",
    "codigo", "presencial", "celular", "cliente", "muestrame", "mostrar", "muestra", "quiero", "reciente",
    "compartir", "comparte", "suficiente", "consultar", "buscar",
} | set(MESES)
SINONIMOS = {
    "wasap": "whatsapp", "guasap": "whatsapp", "guatsap": "whatsapp", "watsap": "whatsapp", "whatsap": "whatsapp",
    "wassap": "whatsapp", "wsp": "whatsapp", "wpp": "whatsapp", "whats": "whatsapp", "wap": "whatsapp",
    "kr": "qr", "qrs": "qr", "cuar": "qr", "coti": "cotizacion", "cotis": "cotizaciones", "cot": "cotizacion",
    "deudas": "deuda", "saldos": "saldo", "abono": "abonos", "stok": "stock", "estok": "stock", "stocks": "stock",
    "proformas": "proforma", "edo": "estado", "pagado": "pagos", "pague": "pagos", "pagaron": "pagos",
}
_TOKEN_RE = re.compile(r"[a-z]+")


def corregir(norm):
    """Corrige errores ortográficos y plurales de las palabras clave (no toca nombres ni referencias)."""
    def reemplazo(m):
        palabra = m.group(0)
        if palabra in SINONIMOS:
            return SINONIMOS[palabra]
        if palabra in VOCABULARIO or len(palabra) < 4:
            return palabra
        corte = 0.8 if len(palabra) >= 7 else 0.86
        # Misma inicial y largo parecido: corrige «cotisacion» pero no convierte nombres como
        # «Inversiones» en «versiones».
        vocab = [v for v in VOCABULARIO if v[0] == palabra[0] and abs(len(v) - len(palabra)) <= 2]
        parecida = difflib.get_close_matches(palabra, vocab, n=1, cutoff=corte)
        return parecida[0] if parecida else palabra
    texto = _TOKEN_RE.sub(reemplazo, norm)
    texto = re.sub(r"\bestado\s+(?:de\s+)?cuentas?\b", "estado de cuenta", texto)
    texto = re.sub(r"\bcodigo\s+qr\b|\bq\s*r\b", "qr", texto)
    texto = re.sub(r"\bx\s+(?=whatsapp|qr|correo|celular)", "por ", texto)
    return texto


def _dates(text, hoy=None):
    hoy = hoy or date.today()
    encontradas = []
    for m in DATE_RE.finditer(text):
        try:
            if m.group(4):
                d = date(int(m.group(4)), int(m.group(5)), int(m.group(6)))
            else:
                y = int(m.group(3))
                y = y + 2000 if y < 100 else y
                d = date(y, int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        encontradas.append((m.start(), d.isoformat()))
    for m in DATE_SIN_ANIO_RE.finditer(text):
        try:
            encontradas.append((m.start(1), date(hoy.year, int(m.group(2)), int(m.group(1))).isoformat()))
        except ValueError:
            continue
    return [d for _pos, d in sorted(encontradas)]


def periodo(norm, hoy=None):
    """Período con nombre: «de octubre», «octubre 2025», «este mes», «mes pasado», «este año»."""
    hoy = hoy or date.today()
    if re.search(r"\b(este|del?)\s+mes\b(?!\s+pasado)|\bmes actual\b", norm):
        return hoy.replace(day=1).isoformat(), hoy.isoformat()
    if re.search(r"\bmes pasado\b|\bmes anterior\b|\bultimo mes\b", norm):
        fin = hoy.replace(day=1) - timedelta(days=1)
        return fin.replace(day=1).isoformat(), fin.isoformat()
    if re.search(r"\b(este|del?) ano\b", norm):
        return date(hoy.year, 1, 1).isoformat(), hoy.isoformat()
    m = re.search(r"\b(" + "|".join(MESES) + r")\b(?:\s+(?:de|del)?\s*(\d{4}))?", norm)
    if m:
        mes = MESES[m.group(1)]
        anio = int(m.group(2)) if m.group(2) else (hoy.year if mes <= hoy.month else hoy.year - 1)
        return date(anio, mes, 1).isoformat(), date(anio, mes, calendar.monthrange(anio, mes)[1]).isoformat()
    return None


def _order(text):
    m = ORDER_RE.search(text)
    return m.group(1).upper() if m else None


_CORTE_PERIODO = (r"\s+(?:desde|del|entre|de|en|durante|hasta|al)\s+(?:\d|este|esta|el mes|mes|ano|"
                  + "|".join(MESES) + r")|\s+(?:al|hasta)\s+\d|\s+\d{1,2}[/-]\d|\s+\d{4}-\d{2}"
                  r"|\s+(?:este|mes pasado|mes anterior)\b|\s+(?:" + "|".join(MESES) + r")\b")
_ESTADO_RE = (r"(?:estado de cuenta|historial de pagos|historial|pagos|abonos|movimientos|deuda|saldo|"
              r"cuanto (?:me |nos )?debe|que debe|debe)")


def _limpiar_cliente(cliente):
    cliente = re.split(_CORTE_PERIODO, " " + cliente)[0]
    cliente = re.sub(r"\b(por favor|porfavor|porfa|gracias|cliente|senor|senora|sr|sra|don|dona)\b", " ", cliente)
    cliente = re.sub(r"^(?:la|el|los|las|al|a)\s+", "", re.sub(r"\s+", " ", cliente).strip(" .,;:?¿!¡"))
    return cliente if len(cliente) >= 2 and re.search(r"[a-z]", cliente) else None


def _cliente(norm):
    # «estado de cuenta de/del cliente X», «historial de pagos de X», «cuánto debe X [de octubre]»
    m = re.search(_ESTADO_RE + r"\s+(?:de(?:l)?\s+|a\s+|al\s+)?(?:cliente\s+)?(.+)$", norm)
    if not m:
        return None
    return _limpiar_cliente(m.group(1))


def _fechas_estado(norm, fechas):
    args = {}
    if len(fechas) >= 2:
        args["fecha_desde"], args["fecha_hasta"] = fechas[0], fechas[1]
    elif len(fechas) == 1:
        args["fecha_desde"] = fechas[0]
    else:
        rango = periodo(norm)
        if rango:
            args["fecha_desde"], args["fecha_hasta"] = rango
    return args


# Palabras que anuncian una cotización o una acción sobre ella; lo que sigue a
# «de/del/para/a/al» después de ellas se interpreta como el cliente.
_KEY_COT = (r"(?:cotizacion(?:es)?|proformas?|presupuestos?|version(?:es)?|whatsapp|wsp|wasap|qr|codigo qr|"
            r"cobertura|stock|disponibilidad|envio|enviado|envie)")
_CONSULTA_RE = re.compile(r"\b(cotizacion(es)?|proformas?|presupuestos?|versiones)\b")
_RELLENO_RE = re.compile(r"\b(por favor|porfavor|porfa|pls|please|gracias|ahora|hoy|nomas|no mas)\b")
_ARTICULO_RE = re.compile(r"^(?:la|el|las|los|una|un|mi|su|sus|esa|ese|esta|este)\s+")
_TRATAMIENTO_RE = re.compile(r"\b(?:cliente|clienta|senor|senora|sr|sra|srta|don|dona|empresa)\b")


def cliente_cotizacion(norm):
    """Cliente mencionado en lugar de la referencia: «cotización de Luis», «whatsapp para Pérez»."""
    m = re.search(r"\b" + _KEY_COT + r"\b.*?\b(?:de|del|para|a|al)\s+(.+)$", norm)
    if not m:
        return None
    hint = m.group(1)
    for _ in range(4):  # «whatsapp de la cotización de luis» -> «luis»
        hint = _ARTICULO_RE.sub("", hint.strip())
        m2 = re.match(_KEY_COT + r"\s+(?:(?:mas\s+)?(?:reciente|nueva|ultima|abierta)s?\s+)?"
                      r"(?:de|del|para|a|al)\s+(.+)$", hint)
        if not m2:
            break
        hint = m2.group(1)
    hint = re.split(
        r"\s+(?:por|via|en|con|mediante|para el|para la|hasta|desde|que|y|cuando)\s+"
        r"|\s+(?:del?|al|el)\s+\d|\s+\d{1,2}[/-]\d|\s+\d{4}-\d{2}", hint)[0]
    hint = _TRATAMIENTO_RE.sub(" ", _RELLENO_RE.sub(" ", hint))
    hint = _ARTICULO_RE.sub("", re.sub(r"\s+", " ", hint).strip(" .,;:?!"))
    if len(hint) < 2 or not re.search(r"[a-z]", hint) or hint in ("el", "la", "los", "las", "esa", "ese", "esta"):
        return None
    return hint


def _con_cotizacion(order, norm, extra=None):
    """Argumentos para herramientas sobre una cotización: referencia o, si falta, el cliente."""
    args = dict(extra or {})
    if order:
        args["cotizacion"] = order
    else:
        cliente = cliente_cotizacion(norm)
        if cliente:
            args["_cliente"] = cliente
    return args


def parse(text):
    norm = corregir(normalize(text))
    if not norm or re.fullmatch(r"(hola|ayuda|help|menu|\?|que (puedes|sabes) hacer.*|buen(os|as) .*|"
                                r"que haces|opciones|comandos)[ .!?]*", norm):
        return "ayuda", {}

    fechas = _dates(norm)
    order = _order(norm)

    if re.search(r"\bregistr\w*\b.*\b(envio|enviado|whatsapp)\b|\b(ya )?(se )?(lo |la )?(envie|enviado|mande)\b", norm):
        return "registrar_envio_whatsapp", _con_cotizacion(order, norm)

    if re.search(r"\bestado de cuenta\b|\bhistorial de pagos\b|\bdeuda\b", norm) and re.search(
            r"\b(compart\w*|envi\w*|manda\w*|qr|whatsapp|mostrar(le)?)\b", norm):
        args = {}
        m = re.search(r"(?:estado de cuenta|historial de pagos|deuda)\s+(?:de(?:l)?\s+|a\s+|al\s+|para\s+)?"
                      r"(?:cliente\s+)?(.+)$", norm)
        if m:
            cliente = re.split(r"\s+(?:por|al|en|del|desde|con)\s+(?:whatsapp|qr|celular|\d)|\s+\d{1,2}[/-]\d",
                               m.group(1))[0]
            cliente = re.sub(r"\b(por|en|con)\s+(whatsapp|qr)\b", "", cliente)
            cliente = _limpiar_cliente(cliente)
            if cliente:
                args["cliente"] = cliente
        args.update(_fechas_estado(norm, fechas))
        return "compartir_estado_cuenta", args

    if re.search(r"\b(qr|presencial|mostrar(le)? al cliente|en su celular)\b", norm):
        return "generar_qr_cotizacion", _con_cotizacion(order, norm)

    if re.search(r"\b(whatsapp|whats app|wa)\b", norm):
        return "preparar_whatsapp_cotizacion", _con_cotizacion(order, norm)

    consulta = _CONSULTA_RE.search(norm)
    cob = re.search(r"\b(cobertura|stock|disponib\w*|alcanza|faltante\w*|hay suficiente|abastec\w*)\b", norm)
    if cob and not (consulta and cob.group(1).startswith("disponib")):
        extra = {"fecha_requerida": fechas[0]} if fechas else {}
        return "evaluar_cobertura_preliminar", _con_cotizacion(order, norm, extra)

    # «quiero ver la cotización de Luis», «cotizaciones de Pérez», «S00637», «versiones de S00637»
    if consulta or (order and len(norm.split()) <= 3):
        return "consultar_cotizacion", _con_cotizacion(order, norm)

    if re.search(r"\b" + _ESTADO_RE + r"\b", norm):
        args = {}
        cliente = _cliente(norm)
        if cliente:
            args["cliente"] = cliente
        args.update(_fechas_estado(norm, fechas))
        return "generar_estado_cuenta", args

    return "ayuda", {}
