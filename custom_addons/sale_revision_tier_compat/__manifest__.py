{
    "name": "sale_revision_tier_compat",
    "version": "19.0.1.0.0",
    "category": "Sale Management",
    "summary": "Compatibilidad entre OCA Revision y Tier Validation",
    "description": """
Addon técnico genérico y reutilizable que permite usar conjuntamente:

- OCA ``base_revision`` y ``sale_order_revision`` (versionado de cotizaciones)
- Odoo ``base_tier_validation`` y ``sale_tier_validation`` (aprobaciones en etapas)

Problema resuelto
=================
Al crear una revisión de cotización con OCA Revision sobre un documento que
tiene registros ``tier.review``, Tier Validation elimina físicamente las
aprobaciones anteriores cuando la orden pasada pasa a ``state='cancel'``.

Este addon impide esa eliminación mediante el contexto
``preserve_tier_reviews_on_revision`` y un override limitado de
``_allow_to_remove_reviews()``. Solo afecta a la creación de revisiones;
las cancelaciones comerciales normales mantienen el comportamiento estándar
de Tier Validation.

Responsabilidades
=================
- Conservar íntegramente el historial ``tier.review`` de la cotización
  anterior al crear una nueva revisión.
- No copiar las aprobaciones anteriores a la nueva revisión (cada revisión
  genera su propio ciclo de aprobación).
- No desactivar globalmente Tier Validation.
- No alterar el comportamiento de operaciones ajenas al versionado.
- No modificar el código fuente de Odoo, OCA o Tier Validation.

Dependencias
============
- base_revision (OCA, rama 19.0)
- sale_order_revision (OCA, rama 19.0)
- base_tier_validation
- sale_tier_validation
""",
    "author": "OCA Compatibility",
    "website": "",
    "license": "AGPL-3",
    "depends": [
        "base_revision",
        "sale_order_revision",
        "base_tier_validation",
        "sale_tier_validation",
    ],
    "data": [],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": False,
    "test": ["tests/test_sale_revision_tier_compat.py"],
}
