{
    "name": "Agente MIGAL · Cuentas por pagar",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "summary": "Agente de cuentas por pagar: facturas de proveedor, cruce con la recepción y programación de pagos",
    "description": """
Agente de cuentas por pagar (responsable: Diego Pinedo)
=======================================================

* Herramientas iniciales: facturas_por_vencer y resumen_obligaciones (la usa contabilidad).
* Por hacer: leer facturas de proveedor con OCR (migal_ocr), cruzar orden de compra, recepción y factura
  (consulta consultar_recepcion a suministro) y proponer el programa de pagos.
* No aprueba ni ejecuta pagos (RN-014).
* Emite EV-040 (comprobante de compra recibido) y EV-055 (pago a proveedor aplicado). Escucha EV-027 y EV-058.

Ficha: producto/agentes/pagos.md · Contratos: arquitectura/integraciones/INT-02-contratos-agentes.md
""",
    "author": "Grupo 1 GE703 - ERP MIGAL",
    "website": "https://github.com/brendaf08/ERP-Migal",
    "license": "LGPL-3",
    "depends": ["migal_agente", "purchase", "account"],
    "data": [],
    "installable": True,
    "application": False,
}
