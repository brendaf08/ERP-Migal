{
    "name": "Agente MIGAL · Cuentas por cobrar",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "summary": "Agente de cuentas por cobrar: deuda y crédito del cliente, antigüedad de cartera y cobranza",
    "description": """
Agente de cuentas por cobrar (responsable: Gabriel Martínez)
============================================================

* Las herramientas de estado de cuenta existentes siguen en el núcleo y pertenecen a este agente.
* Herramientas iniciales: consultar_situacion_credito (la usan ventas y, solo la bandera «excluir», marketing)
  y resumen_cartera (la usa contabilidad).
* No registra pagos ni otorga crédito (RN-004, RN-014).
* Emite EV-038 (comprobante de venta emitido) y EV-043 (pago aplicado). Escucha EV-018 y EV-058.

Ficha: producto/agentes/cobranzas.md · Contratos: arquitectura/integraciones/INT-02-contratos-agentes.md
""",
    "author": "Grupo 1 GE703 - ERP MIGAL",
    "website": "https://github.com/brendaf08/ERP-Migal",
    "license": "LGPL-3",
    "depends": ["migal_agente", "account"],
    "data": [],
    "installable": True,
    "application": False,
}
