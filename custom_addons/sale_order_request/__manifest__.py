{
    "name": "sale_order_request",
    "version": "19.0.1.0.0",
    "category": "Sale Management",
    "summary": "Solicitud de Pedido (sale_order_request)",
    "description": """
Addon integrado de Solicitud de Pedido (lógica e interfaz).

Integra la lógica funcional y la interfaz de usuario del flujo de Solicitud de
Pedido:

1. El vendedor crea una Solicitud de Pedido vinculada a una cotización
   vigente y su revisión correspondiente.
2. El sistema evalúa la disponibilidad de inventario.
3. El sistema determina las aprobaciones requeridas según la matriz de
   disponibilidad y modalidad de entrega.
4. Los responsables aprueban de forma independiente y paralela mediante
   Tier Validation.
5. El vendedor ejecuta la aceptación final y el sistema confirma la
   cotización vigente.

No se crea un segundo sale.order al finalizar el flujo.
""",
    "author": "",  # No verifiable project author information available in repository
    "website": "",
    "license": "AGPL-3",
    "depends": [
        "sale_management",
        "sale_stock",
        "base_tier_validation",
        "sale_tier_validation",
        "base_revision",
        "sale_order_revision",
        "sale_revision_tier_compat",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "security/ir.rule.xml",
        "data/ir_sequence.xml",
        "data/tier_definitions.xml",
        "data/tier_validation_buttons.xml",
        "views/sale_order_request_views.xml",
        "views/sale_order_request_history_views.xml",
        "views/sale_order_views.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
