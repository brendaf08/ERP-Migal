# ADR-002: Adoptar Odoo 18 Community como versión y edición

- **Fecha:** 2026-09-25
- **Estado:** Aceptado
- **Responsable de la decisión:** Gabriel Martínez

## 1. Contexto y problema

Tras seleccionar Odoo como plataforma ERP para **Ferre & Inversiones MIGAL**, es necesario establecer la versión y edición que se utilizarán para desarrollar la solución.

La elección debe considerar no solo las funcionalidades disponibles, sino también la madurez de cada versión, la disponibilidad de documentación, la compatibilidad de módulos adicionales y los recursos técnicos del proyecto.

Este aspecto resulta especialmente importante porque, durante la evaluación inicial, se contemplaba incorporar un **módulo contable de terceros** para cubrir las necesidades financieras de MIGAL. Por ello, se buscaba una versión suficientemente consolidada y compatible con las herramientas comunitarias existentes.

## 2. Criterios de decisión

- **Estabilidad y madurez:** priorizar una versión con mayor recorrido de uso, mantenimiento y correcciones acumuladas.
- **Compatibilidad de módulos:** disponer de complementos comunitarios adecuados para ampliar las funcionalidades del ERP.
- **Costo:** utilizar una edición sin licenciamiento recurrente por usuario.
- **Cobertura funcional:** contar con las aplicaciones necesarias para los procesos empresariales de MIGAL.
- **Documentación y comunidad:** disponer de recursos técnicos que faciliten la implementación y resolución de problemas.
- **Mantenimiento:** reducir los riesgos asociados con versiones recientes y dependencias adicionales.

## 3. Alternativas evaluadas

Se compararon las versiones 18, 19 y 20 de Odoo Community. Asimismo, se consideró la edición Enterprise como alternativa comercial.

| Alternativa | Ventajas | Limitaciones |
|---|---|---|
| **A. Odoo 18 Community** | Mayor trayectoria de uso y mantenimiento, documentación disponible y ecosistema de módulos comunitarios más consolidado. | Menor horizonte de soporte restante frente a versiones posteriores. |
| **B. Odoo 19 Community** | Funcionalidades más recientes y mayor horizonte de soporte. | Menor trayectoria que Odoo 18 y necesidad de verificar la compatibilidad de los complementos requeridos. |
| **C. Odoo 20 Community** | Incorporación de nuevas funcionalidades y mejoras de la plataforma. | Versión recién publicada al momento de la decisión, con menor experiencia de uso acumulada y complementos pendientes de evaluación. |
| **D. Odoo Enterprise** | Funcionalidades adicionales y servicios comerciales. | Costos recurrentes de licenciamiento. |

La comparación considera que una versión más reciente no es necesariamente menos estable, pero puede presentar mayor incertidumbre respecto a la compatibilidad de módulos, la documentación comunitaria y la experiencia acumulada.

## 4. Decisión y justificación

Se decide adoptar la **Opción A: Odoo 18 Community** como versión y edición para el desarrollo del sistema de información de MIGAL.

La elección de **Odoo 18** responde principalmente a su mayor madurez frente a las versiones 19 y 20. Al llevar más tiempo disponible, se consideró que contaba con una trayectoria de uso, mantenimiento y correcciones que permitía reducir los riesgos técnicos de implementación.

Un factor determinante fue la **compatibilidad con módulos de terceros**, especialmente porque inicialmente se contemplaba incorporar un complemento contable comunitario. En este escenario, resultaba conveniente utilizar una versión con mayor disponibilidad de componentes y documentación técnica.

Aunque Odoo 19 y 20 incorporaban mejoras y funcionalidades más recientes, estas no justificaban asumir una mayor incertidumbre de compatibilidad para las necesidades identificadas en MIGAL.

Respecto a la edición, se seleccionó **Community** por su naturaleza de código abierto y la ausencia de licencias recurrentes de Enterprise, considerando las restricciones económicas del proyecto.

Por tanto, la selección de Odoo 18 Community se fundamenta en el equilibrio entre **madurez, compatibilidad, cobertura funcional y viabilidad económica**, priorizando una implementación confiable sobre la adopción de las funcionalidades más recientes.

## 5. Consecuencias

### Positivas

- Menor incertidumbre técnica al utilizar una versión con mayor trayectoria.
- Disponibilidad de documentación y recursos comunitarios.
- Mayor posibilidad de encontrar módulos de terceros adaptados a la versión seleccionada.
- Reducción de riesgos iniciales asociados con la compatibilidad de componentes.
- Ausencia de costos recurrentes de licenciamiento Enterprise.

### Limitaciones y riesgos

- No se dispone de todas las funcionalidades incorporadas en versiones posteriores.
- La compatibilidad y estabilidad de cada módulo adicional deben comprobarse individualmente.
- Odoo 18 cuenta con un horizonte de soporte más corto que Odoo 19 y 20, con finalización del soporte estándar prevista para septiembre de 2027.
- Una futura migración de versión puede requerir ajustes de configuración, adaptación de módulos, migración de datos y nuevas pruebas funcionales.
- La edición Community puede requerir complementos para cubrir determinadas necesidades.

## 6. Validación

La decisión se fundamenta en la evaluación de madurez, compatibilidad y disponibilidad de componentes para las versiones consideradas.

Para respaldar la viabilidad de Odoo 18 Community se requiere:

- Comprobar el funcionamiento de las aplicaciones incluidas en el alcance del proyecto.
- Verificar la compatibilidad y dependencias de los módulos comunitarios seleccionados.
- Validar los escenarios de integración entre aplicaciones.
- Considerar los requisitos de mantenimiento y una futura migración antes de finalizar el período de soporte previsto.

Las pruebas posteriores realizadas sobre Odoo 18 Community constituyen evidencia adicional de viabilidad, sin modificar los motivos que fundamentaron la selección inicial.