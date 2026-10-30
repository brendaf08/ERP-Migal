# Versiones de arquitectura

Este documento registra la evolución de la arquitectura del sistema de información de **Ferre & Inversiones MIGAL**, basado en Odoo Community. Cada versión describe el conjunto de aplicaciones, procesos y fronteras funcionales considerados en un momento determinado del diseño.

Las versiones representan diseños propuestos. Su existencia no acredita que las aplicaciones o integraciones correspondientes estén implementadas en Odoo.

## 1. Criterio de versionado

Se registra una nueva versión cuando cambia el conjunto de aplicaciones de la solución o la frontera funcional entre sus áreas. Los cambios menores de redacción, configuración o detalle técnico no generan una versión.

Cada versión se documenta en un archivo propio, identificado como `VER-XX`. Los identificadores no se reutilizan.

## 2. Versiones registradas

| ID | Nombre | Alcance | Estado | Documento |
|---|---|---|---|---|
| VER-01 | Arquitectura ERP base | Aplicaciones de ERP: ventas, punto de venta, inventario, compras y facturación. | Superada por VER-02 | [VER-01](VER-01-erp.md) |
| VER-02 | Arquitectura CRM–ERP integrada | Incorporación del CRM e integración con el ERP mediante una frontera funcional. | Vigente (diseño) | [VER-02](VER-02-crm-erp.md) |

## 3. Evolución entre versiones

| Aspecto | VER-01 | VER-02 |
|---|---|---|
| Gestión comercial | Cotizaciones y pedidos en Ventas, sin gestión de leads ni oportunidades. | CRM para leads, oportunidades y seguimiento comercial. |
| Aplicaciones | Contactos, Ventas, Punto de Venta, Inventario, Compras y Facturación. | Las anteriores y CRM. |
| Frontera entre áreas | No existe una frontera diferenciada entre la aceptación comercial y la ejecución. | Solicitud de pedido evaluada por el ERP ([INT-01](../integraciones/INT-01-CRM-ERP.md)). |
| Decisiones principales | [ADR-001](../decisiones/ADR-001-seleccion-erp.md), [ADR-002](../decisiones/ADR-002-version-y-edicion.md) y [ADR-003](../decisiones/ADR-003-contabilidad.md). | Las anteriores y [ADR-004](../decisiones/ADR-004-odoo-community-fronteras-crm-erp.md). |

## 4. Relación con otros documentos

- Las [vistas de arquitectura](../vistas/consolidado-diagramas.md) representan la versión vigente. La versión VER-01 corresponde al subconjunto de aplicaciones que excluye el CRM.
- Los riesgos asociados a la arquitectura se registran en [riesgos y controles](../riesgos-y-controles.md).
- Los cambios relevantes del proyecto se resumen en el [CHANGELOG](../../CHANGELOG.md).
