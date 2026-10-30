# ADR-003: Utilizar Facturación de Odoo Community para la gestión contable y financiera

- **Fecha:** 2026-10-28
- **Estado:** Aceptado
- **Responsable de la decisión:** Brenda Mirano

## 1. Contexto y problema

**Ferre & Inversiones MIGAL** requiere integrar la gestión contable y financiera con sus operaciones de ventas, compras e inventario, permitiendo registrar facturas, cobros, pagos, cuentas por cobrar y pagar, asientos contables y reportes financieros.

La solución utilizará **Odoo 19 Community** como plataforma ERP. Esta edición dispone de la aplicación **Facturación**, que proporciona funcionalidades de facturación y registros contables asociados, aunque no incluye todas las herramientas avanzadas de la aplicación Contabilidad de Enterprise.

Inicialmente se consideró instalar un módulo contable completo de terceros. Sin embargo, las pruebas realizadas anteriormente en Odoo 18 Community demostraron que era posible ejecutar operaciones contables esenciales utilizando Facturación.

Por ello, se requiere determinar si resulta más conveniente aprovechar las funcionalidades existentes y complementarlas selectivamente, incorporar una solución contable completa o utilizar un sistema independiente.

## 2. Criterios de decisión

- **Cobertura funcional:** gestionar facturas, cobros, pagos, cuentas pendientes, registros contables y reportes financieros.
- **Integración empresarial:** relacionar la información contable con los procesos de ventas, compras, inventario y Punto de Venta.
- **Compatibilidad:** utilizar componentes disponibles y mantenidos para Odoo 19 Community.
- **Costo total:** evitar licencias recurrentes innecesarias y considerar los esfuerzos de instalación, configuración y mantenimiento.
- **Complejidad técnica:** minimizar dependencias, duplicidad de funcionalidades e integraciones externas.
- **Extensibilidad:** permitir incorporar reportes y herramientas adicionales según las necesidades de MIGAL.
- **Adecuación al negocio:** considerar la operación de una pequeña ferretería peruana y sus requerimientos contables y tributarios.

## 3. Alternativas evaluadas

| Alternativa | Descripción | Ventajas | Limitaciones |
|---|---|---|---|
| **A. Facturación de Odoo Community sin complementos** | Utilizar únicamente las funcionalidades disponibles en la aplicación Facturación. | Menor complejidad técnica y aprovechamiento de los componentes existentes. | Puede resultar insuficiente para obtener todos los reportes financieros requeridos. |
| **B. Facturación con complementos OCA específicos** | Utilizar Facturación como base e incorporar módulos comunitarios para ampliar las capacidades necesarias. | Integración en Odoo, ampliación selectiva y menor redundancia funcional. | Requiere evaluar compatibilidad, dependencias y mantenimiento de cada complemento. |
| **C. Solución contable completa de terceros** | Incorporar un módulo adicional que proporcione herramientas contables y financieras integrales. | Puede ofrecer múltiples funcionalidades mediante una sola solución complementaria. | Mayor dependencia de un proveedor o mantenedor y posible duplicidad con funcionalidades existentes. |
| **D. Sistema contable externo** | Utilizar un software independiente conectado con Odoo. | Posibilidad de utilizar una solución contable especializada. | Mayor complejidad de integración, sincronización y mantenimiento de información. |
| **E. Odoo Enterprise** | Utilizar la edición comercial con herramientas contables y financieras adicionales. | Funcionalidades avanzadas y servicios comerciales disponibles. | Costos recurrentes de licenciamiento. |

## 4. Decisión y justificación

Se decide adoptar la **Opción B: utilizar Facturación de Odoo 19 Community como base para la gestión contable y financiera, incorporando complementos específicos cuando sean necesarios**.

Esta alternativa presenta el mejor equilibrio entre cobertura funcional, integración, costo y complejidad técnica para las necesidades identificadas en MIGAL.

La aplicación Facturación permite trabajar con facturas de clientes y proveedores, pagos, cuentas pendientes y registros contables asociados. Por tanto, no se considera necesario incorporar inicialmente una solución contable completa que reproduzca funcionalidades ya disponibles.

Las pruebas realizadas previamente en Odoo 18 Community respaldan la viabilidad de este enfoque. Sin embargo, su funcionamiento deberá comprobarse nuevamente en la instalación de Odoo 19 Community utilizada por MIGAL.

Para ampliar los reportes financieros se identificaron los siguientes complementos de la **Odoo Community Association (OCA)**:

| Complemento | Finalidad | Situación para Odoo 19 |
|---|---|---|
| `account_financial_report` | Incorporar reportes contables como libro mayor y balance de comprobación. | Versión 19.0 disponible; pendiente de instalación y pruebas. |
| `mis_builder` | Construir reportes financieros, indicadores y comparaciones entre períodos. | Versión 19.0 disponible; pendiente de instalación y pruebas. |
| `mis_template_financial_report` | Proporcionar plantillas predefinidas de balance general y estado de resultados. | Sin versión 19.0 confirmada en el repositorio OCA consultado; no se considera dependencia aprobada. |

La disponibilidad de los dos primeros componentes puede verificarse en los repositorios de [OCA Financial Reporting](https://github.com/OCA/account-financial-reporting/tree/19.0) y [OCA MIS Builder](https://github.com/OCA/mis-builder/tree/19.0).

La elección de complementos específicos, en lugar de una solución contable integral adicional, permite incorporar únicamente las capacidades necesarias y reducir la complejidad de mantenimiento.

Asimismo, mantener la información financiera dentro de Odoo favorece la trazabilidad de las operaciones de los macroprocesos **Order to Cash (O2C)** y **Procure to Pay (P2P)**.

La emisión fiscal de comprobantes continuará realizándose mediante **KeyFacil**, conforme al alcance establecido. Esta decisión no implica su sustitución ni la implementación de una integración automática con Odoo.

## 5. Consecuencias

### Positivas

- Aprovechamiento de las funcionalidades contables existentes en Odoo Community.
- Centralización de la información comercial, administrativa y financiera.
- Menor dependencia de soluciones contables completas de terceros.
- Reducción de componentes redundantes y de la complejidad de mantenimiento.
- Posibilidad de ampliar progresivamente los reportes financieros mediante módulos OCA.
- Continuidad con la plataforma Odoo 19 ya instalada en MIGAL.

### Limitaciones y riesgos

- Las funcionalidades contables esenciales todavía deben comprobarse en Odoo 19 Community.
- Los complementos OCA identificados no han sido instalados ni validados en la instancia de MIGAL.
- La generación del balance general y estado de resultados puede requerir configuración de reportes o plantillas adicionales.
- La edición Community no dispone de todas las herramientas avanzadas de Contabilidad Enterprise.
- La integración contable de ventas, compras, Punto de Venta e inventario depende de la configuración y de los módulos utilizados.
- Los módulos comunitarios requieren mantenimiento y revisión de compatibilidad ante futuras actualizaciones.
- La configuración contable y tributaria debe validarse conforme a los requerimientos aplicables a MIGAL.

## 6. Validación

Las pruebas realizadas anteriormente en Odoo 18 Community constituyen evidencia preliminar de las capacidades de Facturación, pero no sustituyen la validación de Odoo 19.

Para confirmar la viabilidad de la decisión se requiere:

- **Operaciones contables:** comprobar facturas de clientes y proveedores, pagos parciales, saldos pendientes, asientos y conciliación.
- **Integración:** verificar los registros contables generados desde Ventas, Punto de Venta, Compras e Inventario, según la configuración correspondiente.
- **Reportes financieros:** instalar y evaluar los complementos OCA seleccionados, verificando libro mayor, balance de comprobación, balance general y estado de resultados.
- **Configuración contable:** validar el plan de cuentas, impuestos, diarios y criterios contables aplicables a MIGAL.
- **Seguridad:** verificar los permisos y restricciones correspondientes a GER y FCO.
- **Convivencia con KeyFacil:** comprobar el procedimiento de registro y conciliación de la información fiscal con las operaciones de Odoo.

La decisión se considera **aceptada a nivel arquitectónico**. La incorporación definitiva de los complementos y la validación integral de las funcionalidades quedan condicionadas a los resultados de estas pruebas.