{
    "name": "Agente MIGAL · Contabilidad",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "summary": "Agente de contabilidad: revisiones de cierre, conciliación, IGV referencial e inconsistencias",
    "description": """
Agente de contabilidad (responsable: César Joaquín)
===================================================

* Solo lectura: no crea ni modifica asientos. KeyFacil conserva la emisión fiscal (RN-009); los importes
  de IGV que muestra son referenciales.
* Herramienta inicial: pendientes_cierre (consulta resumen_cartera a cobranzas y resumen_obligaciones a pagos).
* Emite EV-058 (inconsistencia contable detectada): pendiente. Escucha EV-038, EV-040, EV-043 y EV-055.

Ficha: producto/agentes/contabilidad.md · Contratos: arquitectura/integraciones/INT-02-contratos-agentes.md
""",
    "author": "Grupo 1 GE703 - ERP MIGAL",
    "website": "https://github.com/brendaf08/ERP-Migal",
    "license": "LGPL-3",
    "depends": ["migal_agente", "account"],
    "data": [],
    "installable": True,
    "application": False,
}
