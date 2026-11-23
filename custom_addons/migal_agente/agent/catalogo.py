"""Catálogo de contratos entre agentes de MIGAL (versión 1).

Fuente única de verdad para el orquestador:
- AGENTES: quién es quién (código, nombre, responsable, módulo, roles que atiende).
- CONSULTAS: preguntas que un agente puede hacerle a otro (quién la ofrece, quién puede usarla,
  entrada, salida de ejemplo). La salida de ejemplo es la que devuelve el SIMULADOR mientras el
  agente dueño no la implemente, para que cada integrante avance sin esperar a los demás.
- EVENTOS: avisos entre agentes. Usan los códigos del catálogo de eventos del repositorio
  (procesos/catalogo-eventos.md). Solo el agente dueño emite su evento.

Documento legible: arquitectura/integraciones/INT-02-contratos-agentes.md.
Cambios: agregar un campo opcional se puede en cualquier momento; cambiar o quitar algo requiere el
acuerdo del agente que lo consume y subir la versión del contrato.
"""

VERSION = "1"

ROLES = ("VEN", "ALM", "CMP", "FCO", "GER", "SIS")

AGENTES = {
    "orquestador": {"nombre": "Orquestador", "responsable": "Luis Núñez", "modulo": "migal_agente",
                    "roles": ROLES},
    "ventas": {"nombre": "Ventas", "responsable": "Brenda Mirano", "modulo": "migal_agente_ventas",
               "roles": ("VEN", "GER")},
    "marketing": {"nombre": "Marketing", "responsable": "Brenda Mirano", "modulo": "migal_agente_marketing",
                  "roles": ("GER", "VEN")},
    "suministro": {"nombre": "Cadena de suministro", "responsable": "Alejandro Flores",
                   "modulo": "migal_agente_suministro", "roles": ("CMP", "ALM", "GER", "VEN")},
    "cobranzas": {"nombre": "Cuentas por cobrar", "responsable": "Gabriel Martínez",
                  "modulo": "migal_agente_cobranzas", "roles": ("FCO", "GER")},
    "pagos": {"nombre": "Cuentas por pagar", "responsable": "Diego Pinedo", "modulo": "migal_agente_pagos",
              "roles": ("FCO", "GER")},
    "contabilidad": {"nombre": "Contabilidad", "responsable": "César Joaquín",
                     "modulo": "migal_agente_contabilidad", "roles": ("FCO", "GER")},
}

# Herramientas del núcleo anteriores al registro de agentes: a qué agente pertenecen.
DUENO_HERRAMIENTAS_NUCLEO = {
    "preparar_whatsapp_cotizacion": "ventas",
    "registrar_envio_whatsapp": "ventas",
    "generar_qr_cotizacion": "ventas",
    "buscar_cotizaciones": "ventas",
    "consultar_cotizacion": "ventas",
    "generar_estado_cuenta": "cobranzas",
    "compartir_estado_cuenta": "cobranzas",
}

CONSULTAS = {
    "evaluar_cobertura_preliminar": {
        "proveedor": "suministro", "consumidores": ("ventas",),
        "descripcion": "¿Alcanza el stock (con reposiciones previstas) para una cotización y desde cuándo?",
        "entrada": {"cotizacion": "Referencia de la cotización, p. ej. S00573", "fecha_requerida": "AAAA-MM-DD (opcional)"},
        "ejemplo_salida": {
            "ok": True, "estado": "cubierta_condicionada", "titulo": "Cobertura preliminar (simulada)",
            "mensaje": "Se podría atender completo con stock y reposiciones previstas.",
            "datos": {"cotizacion": "S00000", "fecha_atencion": "2026-12-01", "lineas": []},
        },
    },
    "consultar_recepcion": {
        "proveedor": "suministro", "consumidores": ("pagos",),
        "descripcion": "Cantidades pedidas, recibidas y pendientes de una orden de compra (cruce con la factura).",
        "entrada": {"orden_compra": "Referencia de la orden de compra, p. ej. P00020"},
        "ejemplo_salida": {
            "ok": True, "estado": "parcial", "titulo": "Recepción de P00000 (simulada)",
            "mensaje": "Recibido 80 de 100.",
            "datos": {"orden_compra": "P00000", "estado_recepcion": "parcial", "tabla": {"columnas": ["Producto", "Pedido", "Recibido", "Pendiente"], "filas": [["[PRUEBA] Producto", 100, 80, 20]]},
                      "productos": [{"producto": "[PRUEBA] Producto", "pedido": 100, "recibido": 80, "pendiente": 20}]},
        },
    },
    "consultar_baja_rotacion": {
        "proveedor": "suministro", "consumidores": ("marketing",),
        "descripcion": "Productos con stock y pocas o ninguna venta en los últimos días.",
        "entrada": {"dias": "Ventana de análisis en días (opcional, 90 por defecto)"},
        "ejemplo_salida": {
            "ok": True, "estado": "ok", "titulo": "Baja rotación (simulada)",
            "mensaje": "3 productos con stock sin ventas en 90 días.",
            "datos": {"dias": 90, "productos": [{"producto": "[PRUEBA] Producto", "stock": 40, "vendido": 0}]},
        },
    },
    "consultar_situacion_credito": {
        "proveedor": "cobranzas", "consumidores": ("ventas", "marketing"),
        "descripcion": "Deuda total y vencida de un cliente frente a su límite de crédito.",
        "entrada": {"cliente": "Nombre, RUC/DNI o referencia del cliente"},
        "ejemplo_salida": {
            "ok": True, "estado": "ok", "titulo": "Situación de crédito (simulada)",
            "mensaje": "Sin deuda vencida.",
            "datos": {"cliente": "[PRUEBA] Cliente", "deuda_total": 0.0, "deuda_vencida": 0.0,
                      "dias_max_vencido": 0, "limite_credito": 0.0, "excede_limite": False, "excluir": False},
        },
        # Mínimo privilegio: marketing solo sabe si debe excluir al cliente de una campaña.
        "campos_por_consumidor": {"marketing": ("cliente", "excluir")},
    },
    "consultar_cotizaciones_perdidas": {
        "proveedor": "ventas", "consumidores": ("marketing",),
        "descripcion": "Cotizaciones y oportunidades perdidas o vencidas, con su motivo.",
        "entrada": {"dias": "Ventana de análisis en días (opcional, 90 por defecto)"},
        "ejemplo_salida": {
            "ok": True, "estado": "ok", "titulo": "Cotizaciones perdidas (simuladas)",
            "mensaje": "2 oportunidades perdidas en 90 días.",
            "datos": {"dias": 90, "perdidas": [{"referencia": "[PRUEBA] Oportunidad", "cliente": "[PRUEBA] Cliente",
                                                "monto": 1000.0, "motivo": "Precio"}]},
        },
    },
    "resumen_cartera": {
        "proveedor": "cobranzas", "consumidores": ("contabilidad",),
        "descripcion": "Total por cobrar y vencido por tramos de antigüedad.",
        "entrada": {},
        "ejemplo_salida": {
            "ok": True, "estado": "ok", "titulo": "Cartera (simulada)", "mensaje": "Por cobrar S/ 0.00.",
            "datos": {"por_cobrar": 0.0, "vencido": 0.0, "tramos": {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "+90": 0.0}},
        },
    },
    "resumen_obligaciones": {
        "proveedor": "pagos", "consumidores": ("contabilidad",),
        "descripcion": "Total por pagar a proveedores, vencido y por vencer en 7 días.",
        "entrada": {},
        "ejemplo_salida": {
            "ok": True, "estado": "ok", "titulo": "Obligaciones (simuladas)", "mensaje": "Por pagar S/ 0.00.",
            "datos": {"por_pagar": 0.0, "vencido": 0.0, "proximos_7_dias": 0.0},
        },
    },
}

EVENTOS = {
    "EV-018": {"nombre": "Orden de venta confirmada", "emisor": "ventas", "escuchan": ("suministro", "cobranzas"),
               "datos": {"orden": "S00000", "cliente": "...", "monto": 0.0, "lineas": "[{producto, cantidad}]"}},
    "EV-027": {"nombre": "Recepción validada", "emisor": "suministro", "escuchan": ("ventas", "pagos"),
               "datos": {"recepcion": "WH/IN/00000", "orden_compra": "P00000", "proveedor": "...",
                         "lineas": "[{producto, recibido}]"}},
    "EV-038": {"nombre": "Comprobante de venta emitido", "emisor": "cobranzas", "escuchan": ("contabilidad",),
               "datos": {"factura": "...", "cliente": "...", "monto": 0.0, "vencimiento": "AAAA-MM-DD"}},
    "EV-040": {"nombre": "Comprobante de compra recibido", "emisor": "pagos", "escuchan": ("contabilidad",),
               "datos": {"factura": "...", "proveedor": "...", "monto": 0.0, "orden_compra": "P00000"}},
    "EV-043": {"nombre": "Pago aplicado a deuda", "emisor": "cobranzas", "escuchan": ("contabilidad",),
               "datos": {"pago": "...", "cliente": "...", "monto": 0.0}},
    "EV-055": {"nombre": "Pago a proveedor aplicado a obligación", "emisor": "pagos", "escuchan": ("contabilidad",),
               "datos": {"pago": "...", "proveedor": "...", "monto": 0.0}},
    "EV-057": {"nombre": "Campaña comercial aprobada", "emisor": "marketing", "escuchan": ("ventas",),
               "datos": {"campana": "...", "productos": "[...]", "vigencia": "AAAA-MM-DD"}},
    "EV-058": {"nombre": "Inconsistencia contable detectada", "emisor": "contabilidad",
               "escuchan": ("cobranzas", "pagos"), "datos": {"tipo": "...", "documento": "...", "detalle": "..."}},
}


def consultas_de(agente):
    """(ofrece, consume) del agente."""
    ofrece = [k for k, c in CONSULTAS.items() if c["proveedor"] == agente]
    consume = [k for k, c in CONSULTAS.items() if agente in c["consumidores"]]
    return ofrece, consume


def eventos_de(agente):
    """(emite, escucha) del agente."""
    emite = [k for k, e in EVENTOS.items() if e["emisor"] == agente]
    escucha = [k for k, e in EVENTOS.items() if agente in e["escuchan"]]
    return emite, escucha
