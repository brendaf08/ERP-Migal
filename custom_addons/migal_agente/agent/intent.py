"""Intérprete determinista (modo REGLAS) de mensajes del chat.

Convierte un mensaje libre en (herramienta, argumentos). Si no reconoce la
intención devuelve ``("ayuda", {})``. El mismo contrato lo usa el LLM opcional,
por lo que ambos modos ejecutan exactamente las mismas herramientas.
"""
import re
from datetime import date

from .guardrails import normalize

ORDER_RE = re.compile(r"\b([a-z]{1,4}\d{3,}(?:-\d+)?)\b", re.I)
DATE_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b|\b(\d{4})-(\d{2})-(\d{2})\b")


def _dates(text):
    out = []
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
        out.append(d.isoformat())
    return out


def _order(text):
    m = ORDER_RE.search(text)
    return m.group(1).upper() if m else None


def _cliente(norm):
    # «estado de cuenta de/del cliente X [del dd/mm/aaaa al dd/mm/aaaa]»
    m = re.search(
        r"(?:estado de cuenta|deuda|saldo|cuanto debe|debe)\s+(?:de(?:l)?\s+)?(?:cliente\s+)?(.+)$", norm)
    if not m:
        return None
    cliente = m.group(1)
    cliente = re.split(r"\s+(?:desde|del|entre)\s+\d|\s+(?:al|hasta)\s+\d|\s+\d{1,2}[/-]\d|\s+\d{4}-\d{2}", cliente)[0]
    cliente = cliente.strip(" .,;:?¿!¡")
    return cliente or None


def parse(text):
    norm = normalize(text)
    if not norm or re.fullmatch(r"(hola|ayuda|help|menu|\?|que (puedes|sabes) hacer.*|buen(os|as) .*)", norm):
        return "ayuda", {}

    fechas = _dates(norm)
    order = _order(norm)

    if re.search(r"\bregistr\w*\b.*\b(envio|enviado|whatsapp|wsp)\b|\b(ya )?(lo )?envie\b", norm) and order:
        return "registrar_envio_whatsapp", {"cotizacion": order}

    if re.search(r"\bestado de cuenta\b", norm) and re.search(
            r"\b(compart\w*|envi\w*|manda\w*|qr|whatsapp|wsp|mostrar(le)?)\b", norm):
        args = {}
        m = re.search(r"estado de cuenta\s+(?:de(?:l)?\s+)?(?:cliente\s+)?(.+)$", norm)
        if m:
            cliente = re.split(r"\s+(?:por|al|en|del|desde)\s+(?:whatsapp|wsp|qr|celular|\d)|\s+\d{1,2}[/-]\d", m.group(1))[0]
            cliente = re.sub(r"\b(por|en|con)\s+(whatsapp|wsp|qr)\b", "", cliente).strip(" .,;:?!")
            if cliente:
                args["cliente"] = cliente
        if len(fechas) >= 2:
            args["fecha_desde"], args["fecha_hasta"] = fechas[0], fechas[1]
        return "compartir_estado_cuenta", args

    if re.search(r"\b(qr|codigo qr|presencial|mostrar(le)? al cliente|en su celular)\b", norm):
        return "generar_qr_cotizacion", {"cotizacion": order} if order else {}

    if re.search(r"\b(whatsapp|wsp|wasap|whats app|wa)\b", norm):
        return "preparar_whatsapp_cotizacion", {"cotizacion": order} if order else {}

    if re.search(r"\b(cobertura|stock|disponib\w*|alcanza|faltante\w*|hay suficiente|abastec\w*)\b", norm):
        args = {"cotizacion": order} if order else {}
        if fechas:
            args["fecha_requerida"] = fechas[0]
        return "evaluar_cobertura_preliminar", args

    if re.search(r"\b(estado de cuenta|deuda|saldo|cuanto debe|debe)\b", norm):
        args = {}
        cliente = _cliente(norm)
        if cliente:
            args["cliente"] = cliente
        if len(fechas) >= 2:
            args["fecha_desde"], args["fecha_hasta"] = fechas[0], fechas[1]
        elif len(fechas) == 1:
            args["fecha_desde"] = fechas[0]
        return "generar_estado_cuenta", args

    return "ayuda", {}
