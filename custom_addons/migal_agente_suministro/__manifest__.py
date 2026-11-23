{
    "name": "Agente MIGAL · Cadena de suministro",
    "version": "19.0.1.0.0",
    "category": "Inventory/Purchase",
    "summary": "Agente de cadena de suministro: disponibilidad, reposición, compras, recepciones y despachos",
    "description": """
Agente de cadena de suministro (responsable: Alejandro Flores)
==============================================================

MIGAL es una empresa comercial: su cadena de suministro es de distribución (planificar, abastecer,
almacenar, entregar y devolver), sin fabricación.

* Herramientas: evaluar_cobertura_preliminar (trasladada desde el núcleo), listar_compras_pendientes,
  consultar_recepcion.
* Ofrece a otros agentes: evaluar_cobertura_preliminar (ventas), consultar_recepcion (pagos),
  consultar_baja_rotacion (marketing, pendiente: hoy responde el simulador).
* Emite EV-027 (recepción validada). Escucha EV-018 (orden de venta confirmada).

Ficha: producto/agentes/suministro.md · Contratos: arquitectura/integraciones/INT-02-contratos-agentes.md
""",
    "author": "Grupo 1 GE703 - ERP MIGAL",
    "website": "https://github.com/brendaf08/ERP-Migal",
    "license": "LGPL-3",
    "depends": ["migal_agente", "purchase_stock"],
    "data": [],
    "installable": True,
    "application": False,
}
