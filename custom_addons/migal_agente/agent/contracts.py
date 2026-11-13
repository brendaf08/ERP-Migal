"""Contrato de herramientas del Agente MIGAL.

Cada herramienta declara:
- ``description``: propósito (lo que se muestra al LLM si está activo).
- ``input_schema``: parámetros en JSON Schema (validados antes de ejecutar).
- ``roles``: roles funcionales MIGAL autorizados (modelo de autorización del repo).
- ``escritura``: qué escribe en Odoo (solo registros propios del agente).

Correspondencia rol MIGAL -> grupo Odoo (Odoo 19 Community):
- VEN: ``sales_team.group_sale_salesman``
- FCO: ``account.group_account_invoice``
- GER: ``sales_team.group_sale_manager``
"""

ROLE_GROUPS = {
    "VEN": "sales_team.group_sale_salesman",
    "FCO": "account.group_account_invoice",
    "GER": "sales_team.group_sale_manager",
}

ORDER_REF = {
    "type": "string",
    "description": "Referencia de la cotización, por ejemplo S00573 (admite revisión S00573-01).",
    "pattern": r"^[A-Za-z]{1,4}\d{3,}(-\d+)?$",
    "maxLength": 30,
}

DATE = {"type": "string", "description": "Fecha ISO AAAA-MM-DD.", "pattern": r"^\d{4}-\d{2}-\d{2}$"}

TOOLS = {
    "preparar_whatsapp_cotizacion": {
        "description": (
            "Prepara el enlace de WhatsApp (wa.me) con un mensaje editable para enviar una "
            "cotización. Comprueba que sea la revisión vigente, que no tenga aprobaciones "
            "pendientes y que el contacto tenga un número válido en formato internacional. "
            "No envía nada: VEN revisa, adjunta el PDF y envía desde WhatsApp."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"cotizacion": ORDER_REF},
            "required": ["cotizacion"],
            "additionalProperties": False,
        },
        "roles": ["VEN", "GER"],
        "escritura": "Ninguna (solo bitácora).",
    },
    "registrar_envio_whatsapp": {
        "description": (
            "Registra en Odoo que VEN confirmó el envío por WhatsApp de una cotización "
            "(fecha, destinatario y versión). Solo debe usarse después de que VEN envió el mensaje."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"cotizacion": ORDER_REF},
            "required": ["cotizacion"],
            "additionalProperties": False,
        },
        "roles": ["VEN", "GER"],
        "escritura": "migal.agente.whatsapp.envio y nota en el historial de la cotización.",
    },
    "compartir_estado_cuenta": {
        "description": (
            "Prepara el estado de cuenta de un cliente para compartirlo: congela una copia de solo lectura "
            "(válida 24 horas), genera un QR con su PDF y un mensaje de WhatsApp con el resumen del saldo. "
            "No envía nada: FCO/GER revisa, adjunta el PDF y envía."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cliente": {"type": "string", "minLength": 2, "maxLength": 120,
                            "description": "Nombre, RUC/DNI o referencia interna del cliente."},
                "fecha_desde": DATE,
                "fecha_hasta": DATE,
            },
            "required": ["cliente"],
            "additionalProperties": False,
        },
        "roles": ["FCO", "GER"],
        "escritura": "Copia del estado de cuenta (migal.agente.estado.cuenta.publicacion) con token y caducidad.",
    },
    "generar_qr_cotizacion": {
        "description": (
            "Atención presencial: genera un código QR que abre en el celular del cliente la versión "
            "digital (PDF, solo lectura) de la cotización, sin pedirle su número. Comprueba que sea la "
            "revisión vigente, que esté vigente y sin autorizaciones pendientes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"cotizacion": ORDER_REF},
            "required": ["cotizacion"],
            "additionalProperties": False,
        },
        "roles": ["VEN", "GER"],
        "escritura": "Token de acceso del portal de la cotización (si aún no existe).",
    },
    "evaluar_cobertura_preliminar": {
        "description": (
            "Revisa por producto y cantidad si una cotización vigente puede cubrirse con el stock "
            "disponible en tienda y las reposiciones previstas hasta la fecha solicitada. Aplica la "
            "regla habitual para cementos, agregados, fierros y ladrillos. No reserva stock, no crea "
            "SOV ni compras y no garantiza entregas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cotizacion": ORDER_REF,
                "fecha_requerida": DATE,
            },
            "required": ["cotizacion"],
            "additionalProperties": False,
        },
        "roles": ["VEN", "GER"],
        "escritura": "Ninguna (solo bitácora).",
    },
    "generar_estado_cuenta": {
        "description": (
            "Genera el estado de cuenta de un cliente para un período a partir de la contabilidad "
            "(facturas y pagos publicados): saldo anterior, movimientos del período, saldo por "
            "documento, pagos pendientes de aplicación y total pendiente. Las ventas y ventas POS "
            "sin factura se informan aparte para no duplicar importes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cliente": {"type": "string", "minLength": 2, "maxLength": 120,
                            "description": "Nombre, RUC/DNI o referencia interna del cliente."},
                "fecha_desde": DATE,
                "fecha_hasta": DATE,
            },
            "required": ["cliente"],
            "additionalProperties": False,
        },
        "roles": ["FCO", "GER"],
        "escritura": "Ninguna (solo bitácora).",
    },
}


class ToolInputError(ValueError):
    """Los argumentos no cumplen el contrato de la herramienta."""


def validate_args(tool_name, args):
    """Validación estricta y sin dependencias del subconjunto de JSON Schema usado."""
    import re

    if tool_name not in TOOLS:
        raise ToolInputError("Herramienta no registrada: %s" % tool_name)
    schema = TOOLS[tool_name]["input_schema"]
    if not isinstance(args, dict):
        raise ToolInputError("Los argumentos deben ser un objeto.")
    props = schema["properties"]
    unknown = set(args) - set(props)
    if unknown and not schema.get("additionalProperties", True):
        raise ToolInputError("Parámetros no permitidos: %s" % ", ".join(sorted(unknown)))
    for req in schema.get("required", []):
        if args.get(req) in (None, ""):
            raise ToolInputError("Falta el parámetro obligatorio «%s»." % req)
    clean = {}
    for key, value in args.items():
        if value in (None, ""):
            continue
        spec = props[key]
        if spec["type"] == "string":
            if not isinstance(value, str):
                raise ToolInputError("«%s» debe ser texto." % key)
            value = value.strip()
            if len(value) > spec.get("maxLength", 500) or len(value) < spec.get("minLength", 0):
                raise ToolInputError("Longitud no válida para «%s»." % key)
            if spec.get("pattern") and not re.match(spec["pattern"], value):
                raise ToolInputError("Formato no válido para «%s»: %s" % (key, value))
        clean[key] = value
    return clean


def llm_tool_specs():
    """Definición de herramientas en el formato de tool use de la API de mensajes."""
    return [
        {"name": name, "description": spec["description"], "input_schema": spec["input_schema"]}
        for name, spec in TOOLS.items()
    ]
