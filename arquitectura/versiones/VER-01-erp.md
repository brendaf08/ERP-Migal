# VER-01: Arquitectura ERP base

- **Estado:** Superada por [VER-02](VER-02-crm-erp.md)
- **Responsable(s):** Equipo ERP-MIGAL
- **Decisiones relacionadas:** [ADR-001](../decisiones/ADR-001-seleccion-erp.md), [ADR-002](../decisiones/ADR-002-version-y-edicion.md) y [ADR-003](../decisiones/ADR-003-contabilidad.md)

Esta versión es el primer diseño de la arquitectura de **Ferre & Inversiones MIGAL**. Comprende exclusivamente las aplicaciones de ERP de Odoo Community. Representa un diseño propuesto y no acredita su implementación.

## 1. Propósito y alcance

La versión establece una base operativa que centraliza las ventas, el inventario, las compras y la facturación en una misma plataforma, para reducir la dependencia de registros manuales y de información distribuida.

Los procesos comprendidos son:

- **Order to Cash (O2C):** desde la cotización y el pedido de venta hasta la entrega, la facturación y el cobro.
- **Procure to Pay (P2P):** desde la necesidad de compra hasta la recepción, la facturación y el pago al proveedor.
- **Gestión de inventario:** transferencias internas, conteos físicos, ajustes de existencias y control de pérdidas o productos dañados.

## 2. Aplicaciones incluidas

| Aplicación | Funcionalidades principales |
|---|---|
| Contactos | Clientes, proveedores y contactos comerciales. |
| Ventas | Cotizaciones, pedidos y condiciones comerciales. |
| Punto de Venta | Ventas de mostrador y operaciones de caja. |
| Inventario | Existencias, ubicaciones, movimientos y despachos. |
| Compras | Solicitudes de presupuesto, órdenes de compra y abastecimiento. |
| Facturación | Facturas, cobros, pagos, cuentas pendientes y registros contables. |

El tratamiento de la contabilidad y de los reportes financieros se desarrolla en ADR-003.

## 3. Sistemas externos

| Sistema o canal | Tratamiento |
|---|---|
| KeyFacil | Se mantiene para la emisión de comprobantes electrónicos, sin integración automática. |
| WhatsApp y llamadas | Se mantienen como canales de comunicación comercial. El registro en Odoo es manual. |

## 4. Limitaciones

- No existe gestión de leads ni de oportunidades comerciales. Las consultas se registran directamente como cotizaciones o pedidos.
- No se dispone de seguimiento estructurado de las cotizaciones enviadas, situación señalada en el [contexto de la empresa](../contexto-empresa.md).
- La cotización y el pedido se gestionan en la misma aplicación, por lo que no se distingue la aceptación comercial de la confirmación operativa.
- Las decisiones sobre precios, descuentos y créditos dependen de los propietarios, sin una etapa diferenciada de evaluación previa a la confirmación del pedido.

## 5. Representación

Las [vistas de arquitectura](../vistas/consolidado-diagramas.md) representan la versión vigente. Esta versión corresponde al subconjunto de aplicaciones que excluye el CRM.

## 6. Evolución

La [VER-02](VER-02-crm-erp.md) amplía esta versión con la incorporación del CRM y su integración con el ERP.
