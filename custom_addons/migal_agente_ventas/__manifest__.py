{
    "name": "Agente MIGAL · Ventas",
    "version": "19.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Agente de ventas: cotizaciones, envío al cliente, seguimiento y solicitud de orden de venta",
    "description": """
Agente de ventas (responsable: Brenda Mirano)
=============================================

* Las herramientas comerciales existentes (cotizaciones por cliente y versión, WhatsApp, QR) siguen en el
  núcleo y pertenecen a este agente; se trasladarán aquí después de la entrega.
* Herramienta inicial: cotizaciones_por_vencer.
* Ofrece consultar_cotizaciones_perdidas a marketing (pendiente: hoy responde el simulador).
* Consume evaluar_cobertura_preliminar (suministro) y consultar_situacion_credito (cobranzas).
* Emite EV-018 (orden de venta confirmada). Escucha EV-027 (recepción validada) y EV-057 (campaña aprobada).

Ficha: producto/agentes/ventas.md · Contratos: arquitectura/integraciones/INT-02-contratos-agentes.md
""",
    "author": "Grupo 1 GE703 - ERP MIGAL",
    "website": "https://github.com/brendaf08/ERP-Migal",
    "license": "LGPL-3",
    "depends": ["migal_agente", "sale_management", "crm"],
    "data": [],
    "installable": True,
    "application": False,
}
