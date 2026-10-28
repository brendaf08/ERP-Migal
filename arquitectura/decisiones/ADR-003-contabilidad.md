# ADR-003: Utilizar Facturación de Odoo Community para la gestión contable

- **Fecha:** 2026-10-28
- **Estado:** Aceptado
- **Responsable(s) de la decisión:** Equipo ERP-MIGAL

## 1. Contexto y problema

**Ferre & Inversiones MIGAL** requiere integrar la información contable y financiera con sus operaciones de ventas, compras e inventario, permitiendo gestionar facturas, pagos, cuentas por cobrar y pagar, registros contables y reportes financieros.

Durante la evaluación inicial de Odoo 18 Community se consideró incorporar un módulo contable completo de terceros, debido a las limitaciones que se atribuían a la edición Community.

Sin embargo, las pruebas realizadas posteriormente demostraron que la aplicación **Facturación** permite ejecutar las operaciones contables esenciales. La principal necesidad pendiente corresponde a la disponibilidad de reportes financieros completos.

Se requiere, por tanto, seleccionar una solución que cubra las necesidades contables de MIGAL aprovechando las funcionalidades existentes y evitando incorporar componentes innecesarios.

## 2. Criterios de decisión

- **Cobertura funcional:** gestionar facturas, cobros, pagos, cuentas pendientes, registros contables e información financiera.
- **Costo:** priorizar una solución sin licencias recurrentes de Odoo Enterprise.
- **Integración:** mantener la información contable relacionada con las operaciones del ERP.
- **Mantenimiento:** reducir dependencias y componentes adicionales que incrementen la complejidad técnica.
- **Extensibilidad:** permitir incorporar reportes y funcionalidades complementarias cuando sea necesario.
- **Compatibilidad:** utilizar componentes compatibles con Odoo 18 Community y validar los requerimientos contables aplicables a MIGAL.

## 3. Alternativas evaluadas

| Alternativa | Descripción | Ventajas | Limitaciones |
|---|---|---|---|
| **A. Odoo Enterprise** | Utilizar la edición comercial de Odoo para disponer de sus funcionalidades contables. | Solución integrada con herramientas financieras adicionales. | Costos recurrentes de licenciamiento. |
| **B. Software contable externo** | Incorporar una aplicación contable independiente e integrarla con Odoo. | Posibilidad de utilizar una solución especializada. | Mayor complejidad de integración, mantenimiento y sincronización de datos. |
| **C. Complemento contable completo de terceros** | Instalar un módulo adicional que amplíe las funcionalidades contables de Odoo Community. | Puede proporcionar funcionalidades adicionales dentro de la misma plataforma. | Dependencia de terceros y posibles incompatibilidades o redundancias. |
| **D. Facturación de Odoo Community con complementos específicos** | Utilizar las capacidades contables existentes y agregar únicamente los componentes necesarios para cubrir funcionalidades faltantes. | Menor complejidad, aprovechamiento de la plataforma y ampliación selectiva. | Requiere validar los reportes financieros y las funcionalidades complementarias. |

## 4. Decisión y justificación

Se decide adoptar la **Opción D: utilizar la aplicación Facturación de Odoo 18 Community como base para la gestión contable y financiera**, incorporando complementos específicos cuando las funcionalidades requeridas no estén disponibles.

Esta decisión se sustenta en las pruebas realizadas con una base de datos de Odoo 18 Community, donde se verificó el funcionamiento de facturas de clientes y proveedores, cobros, pagos parciales, saldos pendientes, asientos contables y conciliación.

La solución permite aprovechar las capacidades existentes del módulo técnico `account`, manteniendo la información financiera dentro del ERP y evitando la instalación de una solución contable completa adicional.

Para complementar la generación y análisis de reportes financieros se propone evaluar los siguientes módulos de la **Odoo Community Association (OCA)**:

- `account_financial_report`: reportes contables y financieros.
- `mis_builder`: construcción y análisis de reportes e indicadores.
- `mis_template_financial_report`: plantillas de balance general y estado de resultados.

Estos complementos se encuentran pendientes de instalación y validación. Su incorporación definitiva dependerá de los resultados de las pruebas y de las necesidades identificadas.

## 5. Consecuencias

### Positivas

- Aprovechamiento de las funcionalidades contables existentes en Odoo Community.
- Menor dependencia de soluciones contables completas de terceros.
- Reducción de la complejidad arquitectónica y de mantenimiento.
- Integración de la información contable con las operaciones empresariales.
- Posibilidad de ampliar selectivamente las capacidades de reportes financieros.

### Limitaciones y riesgos

- Algunos reportes financieros requieren componentes adicionales aún no validados.
- Los complementos OCA introducen dependencias técnicas que deben mantenerse.
- La configuración contable y tributaria peruana requiere validación.
- La integración contable de Ventas, Punto de Venta, Compras e Inventario debe comprobarse según la configuración definitiva.
- La disponibilidad de funcionalidades puede variar según los permisos y módulos instalados.

## 6. Validación

Las pruebas realizadas respaldan la utilización de Facturación para las operaciones contables esenciales, pero todavía se requiere comprobar:

- La instalación y compatibilidad de los complementos OCA seleccionados.
- La generación correcta del balance general, estado de resultados, balance de comprobación y libro mayor.
- La integración de los registros contables con Ventas, Punto de Venta, Compras e Inventario.
- La configuración contable y tributaria correspondiente a MIGAL.
- Los permisos y restricciones de acceso aplicables a los roles GER y FCO.

La decisión se considera **aceptada a nivel arquitectónico**, aunque su implementación y validación integral continúan pendientes.