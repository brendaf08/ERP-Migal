# Módulos de Odoo 19 y dependencias de ERP-MIGAL

## 1. Propósito, versión y nivel de evidencia

Este inventario distingue las **aplicaciones seleccionadas**, los módulos requeridos por sus manifiestos y los módulos de enlace que pueden instalarse al coexistir aplicaciones. La base tecnológica vigente es **Odoo 19 Community** ([ADR-005](decisiones/ADR-005-cambio-version-Odoo-18-Community-a-Odoo-19-Community.md)); CRM forma parte de la plataforma ([ADR-006](decisiones/ADR-006-adopcion-crm-odoo.md)). El [alcance](alcance.md) incluye Compras, además de CRM, Contactos, Ventas, Punto de Venta, Inventario y Facturación.

Las relaciones de este documento se comprobaron en los archivos `__manifest__.py` de la rama pública `19.0` de [odoo/odoo](https://github.com/odoo/odoo/tree/198e0814cec5040cb343ce998569c324fd869955), fijada para esta revisión en el commit `198e0814cec5040cb343ce998569c324fd869955` (consulta del 06/11/2026). **Verificado en manifiesto** significa que una dependencia figura en el código fuente consultado; no demuestra que un módulo esté instalado, configurado o probado en la instancia de MIGAL. La revisión definitiva debe contrastar versión desplegada, módulos instalados y `ir.module.module.dependency_ids` en una instancia autorizada.

## 2. Aplicaciones seleccionadas

| Aplicación | Módulo visible o principal | Papel funcional; estado |
|---|---|---|
| CRM | [`crm`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/crm/__manifest__.py) | Leads y oportunidades; decisión de uso en ADR-006, comportamiento local pendiente de prueba. |
| Contactos | [`contacts`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/contacts/__manifest__.py) | Gestión compartida de contactos; deduplicación y permisos pendientes de prueba. |
| Ventas | [`sale_management`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/sale_management/__manifest__.py) | Cotizaciones y pedidos; controles de confirmación sujetos a INT-01. |
| Punto de Venta | [`point_of_sale`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/point_of_sale/__manifest__.py) | Venta de mostrador; stock y permisos efectivos pendientes de prueba. |
| Inventario | [`stock`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/stock/__manifest__.py) | Existencias y movimientos; ubicaciones y reservas pendientes de definición. |
| Compras | [`purchase`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/purchase/__manifest__.py) | Órdenes de compra para P2P; CMP gestiona y GER autoriza conforme al modelo vigente. |
| Facturación | [`account`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/account/__manifest__.py) | Registro financiero operativo; no sustituye por decisión implícita a KeyFacil ni acredita reportes tributarios. |

## 3. Dependencias directas comprobadas en manifiestos 19.0

La tabla transcribe la clave `depends` de los manifiestos vinculados. Los nombres indican módulos técnicos; no equivalen a aplicaciones de menú ni a permisos concedidos.

| Módulo | Dependencias directas (`depends`) | Consecuencia de arquitectura |
|---|---|---|
| `crm` | `base_setup`, `sales_team`, `mail`, `calendar`, `resource`, `utm`, `web_tour`, `contacts`, `digest`, `phone_validation` | Contactos y módulos auxiliares acompañan a CRM. |
| `contacts` | `base`, `mail` | Comparte base de contactos e historial; calidad de datos y permisos por validar. |
| `sale_management` | `sale`, `digest` | La aplicación Ventas utiliza el módulo base `sale`. |
| [`sale`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/sale/__manifest__.py) | `sales_team`, `account_payment`, `utm` | Mediante [`account_payment`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/account_payment/__manifest__.py), que depende de `account` y `payment`, Ventas incorpora Facturación. |
| `point_of_sale` | `resource`, `stock_account`, `barcodes`, `html_editor`, `digest`, `phone_validation`, `partner_autocomplete`, `iot_base`, `google_address_autocomplete` | Mediante [`stock_account`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/stock_account/__manifest__.py), que depende de `stock` y `account`, POS requiere Inventario y Facturación. |
| `stock` | `product`, `barcodes_gs1_nomenclature`, `digest` | Inventario no requiere directamente Compras; ambas aplicaciones sí forman parte del alcance. |
| `purchase` | `account` | Compras requiere Facturación y se relaciona con la preparación y autorización del abastecimiento. |
| `account` | `base_setup`, `onboarding`, `product`, `analytic`, `portal`, `digest` | La presencia del módulo no acredita configuración peruana, reportes, conciliación ni autorizaciones. |

## 4. Módulos de enlace

Los siguientes manifiestos de Odoo 19 declaran `auto_install: True`. Su instalación efectiva depende de que se cumplan sus dependencias en la instancia; el alcance funcional y la configuración deben comprobarse aparte.

| Módulo | Dependencias declaradas | Relación que aporta; límite |
|---|---|---|
| [`sale_crm`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/sale_crm/__manifest__.py) | `sale`, `crm` | Relaciona oportunidades con cotizaciones. No implementa por sí solo la evaluación y respuesta de [INT-01](integraciones/INT-01-CRM-ERP.md). |
| [`sale_stock`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/sale_stock/__manifest__.py) | `sale`, `stock_account` | Relaciona Ventas e Inventario; generación y validación de entregas requieren prueba funcional. |
| [`purchase_stock`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/purchase_stock/__manifest__.py) | `stock_account`, `purchase` | Relaciona órdenes de compra y recepciones; no equivale a recepción física validada. |
| [`pos_sale`](https://github.com/odoo/odoo/blob/198e0814cec5040cb343ce998569c324fd869955/addons/pos_sale/__manifest__.py) | `point_of_sale`, `sale_management` | Relaciona POS y Ventas; el uso para liquidar pedidos y sus controles requiere definición. |

## 5. Consecuencias transversales y verificación

- **Frontera CRM–ERP:** compartir plataforma y módulos no elimina la separación entre aceptación comercial, evaluación operativa y confirmación establecida por [ADR-004](decisiones/ADR-004-odoo-community-fronteras-crm-erp.md).
- **Compras:** `purchase` y `purchase_stock` se incluyen en el análisis. La orden preparada por CMP requiere autorización de GER según el [modelo de autorización](seguridad/modelo-autorizacion.md); el manifiesto no demuestra que la restricción esté configurada.
- **Facturación y KeyFacil:** `account` llega por varias dependencias, pero el [alcance](alcance.md) mantiene KeyFacil como emisor externo y no presupone sincronización automática.
- **Complementos OCA:** la necesidad y compatibilidad de `account_financial_report`, `mis_builder` y otros complementos requieren versión fijada, manifiesto propio, instalación autorizada y pruebas. No se presentan aquí como instalados o compatibles por defecto.
- **Diagramas:** las [vistas C4](vistas/consolidado-diagramas.md) representan relaciones arquitectónicas documentadas; cualquier actualización de dependencias debe coordinarse con sus fuentes y renders.

| Verificación pendiente | Evidencia de cierre |
|---|---|
| Identificar versión exacta y módulos instalados en MIGAL. | Inventario exportado de instancia autorizada, con fecha y responsable. |
| Contrastar dependencias efectivas. | Consulta de `ir.module.module.dependency_ids` comparada con manifiestos 19.0 fijados. |
| Probar CRM, Ventas, POS, Compras, Inventario y Facturación. | Casos y resultados registrados, incluidos enlaces `sale_crm`, `sale_stock`, `purchase_stock` y `pos_sale`. |
| Verificar grupos y autorizaciones. | Matriz de permisos y pruebas con GER, VEN, ALM, CMP, FCO y SIS. |
| Evaluar OCA y reportes. | Versiones, dependencias, compatibilidad y salidas de prueba verificables. |

Estas verificaciones pendientes se relacionan con [supuestos y vacíos](../fuentes/supuestos-y-vacios.md) y el [registro de riesgos](riesgos-y-controles.md). La rama `19.0` puede evolucionar; cualquier revisión posterior debe comparar su nuevo estado con el commit fijado aquí.
