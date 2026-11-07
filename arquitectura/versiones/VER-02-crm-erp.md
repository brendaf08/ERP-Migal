# VER-02: Arquitectura CRM–ERP integrada

- **Estado:** Vigente (diseño), sujeta a validación técnica
- **Responsable(s):** Equipo ERP-MIGAL
- **Versión anterior:** [VER-01](VER-01-erp.md)
- **Decisiones relacionadas:** [ADR-003](../decisiones/ADR-003-contabilidad.md), [ADR-004](../decisiones/ADR-004-odoo-community-fronteras-crm-erp.md) (frontera funcional), [ADR-005](../decisiones/ADR-005-cambio-version-Odoo-18-Community-a-Odoo-19-Community.md) (versión vigente) y [ADR-006](../decisiones/ADR-006-adopcion-crm-odoo.md) (adopción de CRM)
- **Integración relacionada:** [INT-01](../integraciones/INT-01-CRM-ERP.md)

Esta versión incorpora el CRM a la arquitectura de **Ferre & Inversiones MIGAL** y lo integra con las aplicaciones de ERP. Representa un diseño propuesto y no acredita su implementación en Odoo.

## 1. Propósito y alcance

La versión responde a la fragmentación de la información comercial descrita en el [contexto de la empresa](../contexto-empresa.md): contactos, antecedentes y cotizaciones distribuidos entre teléfonos, conversaciones y registros manuales, sin seguimiento de las propuestas enviadas.

El CRM se incorpora para gestionar leads, oportunidades, cotizaciones y su seguimiento. Para evitar que la aceptación comercial se confunda con la ejecución operativa, se establece una frontera funcional entre ambas áreas.

## 2. Cambios respecto a VER-01

| Aspecto | Cambio |
|---|---|
| Aplicaciones | Se incorpora **CRM**. Contactos pasa a ser un dato compartido por CRM y ERP. |
| Gestión comercial | Las consultas se registran como leads y oportunidades. Las cotizaciones se originan en la oportunidad. |
| Frontera funcional | Se establece la solicitud de orden de venta, registrada a partir de una cotización aceptada y evaluada por el ERP (ADR-004). |
| Integración | Se documenta la transición entre CRM y ERP en INT-01: eventos, información, estados y responsables. |
| Roles | El rol de Atención y Ventas (VEN) incorpora la gestión de CRM. Se identifican las autorizaciones de GER sobre la evaluación. |
| Dependencias técnicas | CRM requiere módulos adicionales, como Conversaciones, Calendario y Equipos de ventas. Se instala automáticamente el módulo de enlace `sale_crm`. |

## 3. Aplicaciones incluidas

| Aplicación | Funcionalidades principales |
|---|---|
| CRM | Leads, oportunidades y seguimiento comercial. |
| Contactos | Clientes, proveedores y contactos comerciales. |
| Ventas | Cotizaciones, órdenes de venta y condiciones comerciales. |
| Punto de Venta | Ventas de mostrador y operaciones de caja. |
| Inventario | Existencias, ubicaciones, movimientos y despachos. |
| Compras | Solicitudes de presupuesto, órdenes de compra y abastecimiento. |
| Facturación | Facturas, cobros, pagos, cuentas pendientes, contabilidad y reportes financieros, con complementos de la Odoo Community Association (OCA) pendientes de validación (ADR-003). |

## 4. Frontera entre CRM y ERP

La frontera se establece mediante una **solicitud de orden de venta**, registrada por VEN a partir de una cotización aceptada por el cliente.

- **CRM:** gestiona el proceso comercial hasta la aceptación de las condiciones por el cliente.
- **ERP:** evalúa la viabilidad operativa de las condiciones aceptadas y gestiona las órdenes de venta confirmadas, el inventario, las compras, las entregas, la facturación y las finanzas.

Si la solicitud es aceptada, se habilita la confirmación de la orden de venta. Si es condicionada o rechazada, la gestión retorna al ámbito comercial.

El detalle de eventos, información intercambiada, estados y responsabilidades se encuentra en [INT-01](../integraciones/INT-01-CRM-ERP.md).

## 5. Módulos y dependencias

Las aplicaciones seleccionadas requieren otros módulos de Odoo. Algunos, como Facturación, resultan obligatorios para el funcionamiento de varias aplicaciones, y otros amplían los menús y permisos por revisar. Estas relaciones se representan en la vista [Módulos de Odoo y sus dependencias](../vistas/fuentes/c4-modulos-dependencias.puml); su análisis detallado se encuentra en [módulos y dependencias](../modulos-y-dependencias.md).

## 6. Limitaciones y riesgos

- La versión corresponde a un diseño. El mecanismo de representación de la solicitud de orden de venta y los controles de transición requieren validación en la instancia de Odoo.
- KeyFacil y WhatsApp permanecen como sistemas externos, sin integración automática.
- Riesgos relacionados, registrados en [riesgos y controles](../riesgos-y-controles.md): RSK-002 (Facturación como núcleo obligatorio), RSK-003 (módulos de enlace), RSK-004 (módulos instalados sin uso previsto) y RSK-005 (historial dependiente de Conversaciones).

## 7. Representación

Las [vistas de arquitectura](../vistas/consolidado-diagramas.md) representan esta versión.
