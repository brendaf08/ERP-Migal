"""Guardarraíles deterministas del Agente MIGAL.

Se evalúan SIEMPRE antes de cualquier herramienta y antes del LLM opcional.
Ninguna respuesta del LLM puede desactivarlos.

Referencias: procesos/catalogo-reglas.md y arquitectura/seguridad/modelo-autorizacion.md
del repositorio ERP-Migal.
"""
import re
import unicodedata

# (código, patrón, motivo, rol que decide)
VETOS = [
    ("RN-004", r"\b(descuento|dscto|rebaja|rebajar|precio especial|cambiar? (el )?precio|baja(r|me)? (el )?precio)",
     "Descuentos, precios especiales y cambios de precio requieren decisión de Gerencia; "
     "VEN no tiene un porcentaje autónomo de descuento.", "GER"),
    ("RN-004", r"\b(dar(le)? credito|otorga\w* credito|credito (al|para|a) |fiado|fiar(le)?|plazo de pago|pagar despues)",
     "El otorgamiento o modificación de crédito solo lo decide Gerencia.", "GER"),
    ("RN-006", r"\b(confirm\w*|aprueb\w*|aprob\w*|acept\w*)\b.{0,40}\b(venta|orden|pedido|cotizacion|sov|solicitud)",
     "Solo una solicitud de orden de venta aceptada por el flujo de aprobación habilita la "
     "confirmación; el agente no confirma ni aprueba.", "GER"),
    ("RN-015", r"\b(reserva(r|me|lo|la)?|separa(r|me|lo|la)?|aparta(r|me|lo|la)?)\b",
     "La consulta de disponibilidad no constituye reserva; el agente no reserva stock.", "ALM"),
    ("RN-009", r"\b(emit(e|ir)|genera(r)?|haz|crea(r)?)\b.{0,20}\b(factura|boleta|comprobante)",
     "La emisión de comprobantes no la realiza el agente (frontera con KeyFacil/FCO).", "FCO"),
    ("RN-014", r"\b(registra(r)?|aplica(r)?|anota(r)?)\b.{0,20}\b(pago|abono|cobro)",
     "El registro y la conciliación de pagos los ejecuta FCO; el agente solo informa.", "FCO"),
    ("RN-010", r"\b(anula(r)?|cancela(r)?)\b.{0,30}\b(venta|orden|pedido|factura)",
     "La anulación de operaciones la decide Gerencia.", "GER"),
]


def normalize(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text.lower()).strip()


def check_request(text):
    """Devuelve la lista de vetos activados por el texto de la solicitud."""
    norm = normalize(text)
    hits = []
    seen = set()
    for code, pattern, motivo, rol in VETOS:
        if re.search(pattern, norm) and (code, rol) not in seen:
            seen.add((code, rol))
            hits.append({"regla": code, "motivo": motivo, "escalar_a": rol})
    return hits


def user_roles(user, role_groups):
    return [role for role, xmlid in role_groups.items() if user.has_group(xmlid)]


def check_permission(user, tool_spec, role_groups):
    """True si el usuario tiene alguno de los roles autorizados para la herramienta."""
    roles = user_roles(user, role_groups)
    return any(r in tool_spec["roles"] for r in roles), roles
