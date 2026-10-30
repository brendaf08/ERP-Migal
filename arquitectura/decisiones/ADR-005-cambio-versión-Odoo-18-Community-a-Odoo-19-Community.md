# ADR-005: Sustituir Odoo 18 Community por Odoo 19 Community

- **Fecha:** 2026-10-28
- **Estado:** Aceptado
- **Responsable de la decisión:** Brenda Mirano

## 1. Contexto y problema

Mediante el **ADR-002** se seleccionó inicialmente **Odoo 18 Community** como versión y edición para el sistema de información de **Ferre & Inversiones MIGAL**.

Esta decisión se fundamentó principalmente en la mayor madurez de Odoo 18 y la disponibilidad de módulos comunitarios, especialmente porque inicialmente se contemplaba incorporar un complemento contable de terceros.

Sin embargo, durante el desarrollo del proyecto se identificaron nuevas condiciones:

- **Odoo 19 Community ya se encuentra instalado en la ferretería** y ha sido utilizado de manera exploratoria.
- Las funcionalidades revisadas inicialmente presentan un comportamiento similar al observado en Odoo 18, aunque todavía requieren pruebas más completas.
- La estrategia contable fue reconsiderada, priorizando las funcionalidades existentes de Facturación y el uso selectivo de complementos para reportes financieros.
- El proyecto se encuentra reorganizando su documentación y todavía no presenta dependencias técnicas significativas que obliguen a conservar Odoo 18.
- Se busca que la solución no sea únicamente un entregable académico, sino un sistema que MIGAL pueda adoptar y mantener a largo plazo.

Ante estas condiciones, se considera necesario reevaluar la versión seleccionada para favorecer la continuidad operativa y reducir la necesidad de una migración temprana.

## 2. Criterios de decisión

La reevaluación considera los siguientes criterios:

- **Continuidad operativa:** aprovechar la instalación y experiencia inicial de uso de Odoo 19 en MIGAL.
- **Cobertura funcional:** mantener las capacidades necesarias para CRM, ventas, inventario, compras, facturación y finanzas.
- **Madurez:** seleccionar una versión con suficiente trayectoria de uso y mantenimiento.
- **Compatibilidad:** disponer de módulos comunitarios que permitan cubrir las necesidades del proyecto.
- **Vida útil:** considerar el horizonte de mantenimiento y las futuras necesidades de actualización.
- **Esfuerzo de transición:** minimizar el impacto sobre la documentación, configuraciones y pruebas existentes.
- **Sostenibilidad económica:** conservar una solución compatible con los recursos técnicos y financieros de MIGAL.

## 3. Alternativas evaluadas

| Alternativa | Ventajas | Limitaciones |
|---|---|---|
| **A. Mantener Odoo 18 Community** | Mayor trayectoria de uso y disponibilidad de complementos comunitarios. | Menor horizonte de mantenimiento y posible necesidad de actualizar la versión en un plazo más corto. |
| **B. Adoptar Odoo 19 Community** | Instalación existente en MIGAL, mayor horizonte de mantenimiento que Odoo 18 y disponibilidad de complementos financieros relevantes. | Requiere validar funcionalidades y compatibilidad de los componentes seleccionados. |
| **C. Adoptar Odoo 20 Community** | Funcionalidades más recientes y mayor horizonte de mantenimiento previsto. | Versión recientemente publicada, con menor experiencia acumulada y disponibilidad de complementos específicos aún por verificar. |

Según el calendario oficial de Odoo, el soporte estándar de Odoo 18 está previsto hasta septiembre de 2027, mientras que el de Odoo 19 se extiende hasta septiembre de 2028.

Estas fechas corresponden al ciclo de mantenimiento de las versiones y no implican asistencia técnica personalizada gratuita para instalaciones Community.

Fuente: [Odoo — Soporte estándar y extendido](https://www.odoo.com/documentation/19.0/es_419/administration/standard_extended_support.html).

## 4. Decisión y justificación

Se decide **sustituir la versión Odoo 18 Community, seleccionada en el ADR-002, por Odoo 19 Community como nueva base tecnológica de ERP-MIGAL**.

Esta decisión se fundamenta en los siguientes aspectos:

**1. Aprovechamiento de la instalación existente**

Odoo 19 Community ya se encuentra instalado en MIGAL. Esto permite continuar el desarrollo y las pruebas sobre una versión que la empresa ya tiene disponible, evitando mantener una versión distinta como referencia principal del proyecto.

**2. Madurez suficiente**

Odoo 19 fue publicado en septiembre de 2025, por lo que cuenta con aproximadamente un año de trayectoria al momento de esta decisión.

Aunque Odoo 18 tiene mayor antigüedad, no se ha identificado evidencia suficiente para considerar que Odoo 19 presenta una inestabilidad que impida su adopción. Por otra parte, Odoo 20 ofrece mejoras recientes, pero dispone de una trayectoria considerablemente menor.

**3. Cambio en los requerimientos de complementos contables**

La selección inicial de Odoo 18 consideraba especialmente la disponibilidad de módulos contables completos de terceros.

Posteriormente, las pruebas realizadas permitieron replantear la solución contable utilizando Facturación como base, con complementos específicos para los reportes financieros.

Además, se ha confirmado la publicación de versiones para Odoo 19 de los módulos comunitarios `account_financial_report` y `mis_builder`, lo que reduce una de las principales preocupaciones que motivaron la elección original.

La disponibilidad de estos componentes no garantiza su funcionamiento en MIGAL, por lo que su compatibilidad y configuración deberán comprobarse.

Fuentes: [OCA — Financial Reporting](https://github.com/OCA/account-financial-reporting/tree/19.0) y [OCA — MIS Builder](https://github.com/OCA/mis-builder/tree/19.0).

**4. Mayor horizonte de mantenimiento**

Odoo 19 cuenta con aproximadamente un año adicional de soporte estándar previsto respecto a Odoo 18.

Esta diferencia resulta relevante debido a que el objetivo del proyecto es proporcionar una solución que pueda continuar utilizándose después de finalizar el trabajo académico.

La adopción de Odoo 19 no elimina la necesidad de futuras actualizaciones, pero permite postergar la siguiente revisión de versión frente a la alternativa originalmente seleccionada.

**5. Bajo impacto de transición**

El proyecto se encuentra en una etapa de reorganización documental y validación progresiva.

Los procesos empresariales, roles, reglas de negocio y decisiones funcionales no dependen exclusivamente de Odoo 18. Por ello, el cambio puede incorporarse mediante la revisión de las referencias técnicas y las pruebas correspondientes, sin rediseñar necesariamente la arquitectura empresarial.

Adoptar Odoo 19 en esta etapa también evita acumular nuevas configuraciones y dependencias sobre una versión que posteriormente se tendría que sustituir.

En consecuencia, **Odoo 19 Community representa una alternativa más conveniente para las condiciones actuales de MIGAL**, al ofrecer un equilibrio entre madurez, continuidad operativa, compatibilidad y sostenibilidad.

Esta decisión sustituye la selección de versión establecida en el ADR-002, sin invalidar las razones que justificaron su elección original.

## 5. Consecuencias

### Positivas

- Aprovechamiento de la instalación existente de Odoo 19 en la ferretería.
- Mayor horizonte de mantenimiento frente a Odoo 18.
- Continuidad del desarrollo académico sobre la versión prevista para uso empresarial.
- Disponibilidad de complementos comunitarios relevantes para la gestión financiera.
- Menor probabilidad de requerir una migración de versión a corto plazo.
- Posibilidad de incorporar el cambio antes de acumular mayores dependencias técnicas.

### Limitaciones y riesgos

- Las pruebas realizadas sobre Odoo 18 no garantizan automáticamente el mismo comportamiento en Odoo 19.
- Los módulos complementarios requieren nuevas verificaciones de compatibilidad.
- Algunos reportes financieros pueden necesitar configuraciones o alternativas adicionales.
- La documentación técnica debe actualizarse para reflejar la nueva versión.
- La edición Community no incluye asistencia técnica personalizada ni migraciones automáticas del fabricante.
- MIGAL deberá gestionar el mantenimiento, los respaldos y las futuras actualizaciones del sistema.

## 6. Validación

La decisión se respalda en la instalación existente de Odoo 19 Community, la evaluación de las versiones disponibles y la verificación de componentes comunitarios relevantes.

Para confirmar su viabilidad técnica y operativa se requiere:

- Verificar los procesos O2C y P2P en Odoo 19 Community.
- Comprobar el funcionamiento de CRM, Contactos, Ventas, Punto de Venta, Inventario, Compras y Facturación.
- Validar las operaciones contables y los reportes financieros requeridos.
- Probar la compatibilidad de los complementos OCA seleccionados.
- Comprobar los roles, permisos y autorizaciones definidos.
- Revisar y actualizar las referencias técnicas a Odoo 18 en el repositorio.
- Verificar los mecanismos de respaldo y mantenimiento de la instalación existente.

La decisión de adoptar **Odoo 19 Community** queda aceptada a nivel arquitectónico. Las validaciones pendientes deberán completarse antes de considerar la solución preparada para su utilización empresarial integral.