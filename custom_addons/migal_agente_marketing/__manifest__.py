{
    "name": "Agente MIGAL · Marketing",
    "version": "19.0.1.0.0",
    "category": "Sales/CRM",
    "summary": "Agente de marketing: segmentación de clientes, productos para promoción y campañas para aprobar",
    "description": """
Agente de marketing (responsable: Brenda Mirano)
================================================

* Analiza y redacta; no envía mensajes masivos sin aprobación de Gerencia (RN-022).
* Herramientas iniciales: clientes_inactivos (consulta a cobranzas a quién excluir, solo esa bandera) y
  productos_para_promocion (consulta consultar_baja_rotacion a suministro; hoy responde el simulador).
* Consume consultar_situacion_credito, consultar_baja_rotacion y consultar_cotizaciones_perdidas.
* Emite EV-057 (campaña comercial aprobada): pendiente.

Ficha: producto/agentes/marketing.md · Contratos: arquitectura/integraciones/INT-02-contratos-agentes.md
""",
    "author": "Grupo 1 GE703 - ERP MIGAL",
    "website": "https://github.com/brendaf08/ERP-Migal",
    "license": "LGPL-3",
    "depends": ["migal_agente", "sale_management", "crm"],
    "data": [],
    "installable": True,
    "application": False,
}
