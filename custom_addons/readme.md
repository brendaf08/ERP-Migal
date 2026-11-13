# Addons de Odoo 19 para ERP-MIGAL

Seleccionamos nueve módulos para complementar Odoo 19 en ERP-MIGAL. Con ellos incorporamos gestión de presupuestos y contabilidad, relaciones entre contactos y un flujo de solicitudes de venta con revisiones y aprobaciones por niveles. Conservamos los manifiestos, los avisos de autoría y las licencias de los módulos. Los enlaces de OCA apuntan a los proyectos de origen. La revisión exacta de esas copias queda por identificar.

| Módulo | Procedencia | Licencia declarada |
|---|---|---|
| `base_account_budget`, `base_accounting_kit` | Cybrosys Technologies, según los avisos de copyright | LGPL-3 |
| `base_revision` | [OCA/server-ux](https://github.com/OCA/server-ux) | AGPL-3 |
| `base_tier_validation`, `sale_tier_validation` | [OCA/tier-validation](https://github.com/OCA/tier-validation) | AGPL-3 |
| `sale_order_revision` | [OCA/sale-workflow](https://github.com/OCA/sale-workflow) | AGPL-3 |
| `partner_relation_multi`, `sale_order_request`, `sale_revision_tier_compat` | Versión usada por el equipo ERP-MIGAL | AGPL-3 |

Textos de licencia [AGPL 3](licenses/agpl-3.0.txt), [LGPL 3](licenses/lgpl-3.0.txt) y [GPL 3](licenses/gpl-3.0.txt), según corresponda. La instalación y configuración se describen en la [guía del entorno Odoo](../infra/odoo/readme.md).

## Solicitudes de orden de venta

La revisión del 12 de noviembre de `sale_order_request` permite aceptar una solicitud con stock insuficiente cuando el flujo la deja aprobada. La aceptación vuelve a consultar el inventario y comprueba que las líneas, productos, unidades y cantidades coincidan con la cotización. La orden puede quedar con abastecimiento pendiente. El addon conserva las aprobaciones de Abastecimiento y Transporte según el caso.

El equipo registró **175 pruebas automatizadas sin fallos ni errores** en su instalación de origen. La suite incluye la regresión de compra futura sin orden de compra registrada. Quedan pendientes la reproducción en Docker y la revisión de dos casos: un faltante que aparece después de aprobar y una revisión coordinada que conserva una referencia distinta a la cotización original.
