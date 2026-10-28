# ADR-001: Adoptar Odoo como plataforma ERP

- **Fecha:** 2026-09-25
- **Estado:** Aceptado
- **Responsable(s) de la decisión:** Equipo ERP-MIGAL

## 1. Contexto y problema

**Ferre & Inversiones MIGAL** requiere integrar sus procesos comerciales, operativos y administrativos debido a la dependencia de registros manuales, información distribuida y actividades que actualmente no se encuentran centralizadas.

La empresa cuenta con una tienda, dos almacenes, dos propietarios y dos trabajadores. Su operación requiere gestionar productos, ventas, compras, inventario, facturación e información financiera de manera coordinada.

Ante esta necesidad, se evaluaron diferentes plataformas ERP para seleccionar una solución que permita centralizar la información, integrar los procesos empresariales y adaptarse progresivamente a las características y recursos de MIGAL.

## 2. Criterios de decisión

- **Cobertura funcional:** disponer de funcionalidades para ventas, inventario, compras, facturación, contabilidad y gestión comercial.
- **Integración:** relacionar los procesos empresariales y reducir la duplicación de información.
- **Costo:** priorizar una solución económicamente viable para una pequeña empresa.
- **Escalabilidad y modularidad:** permitir la incorporación progresiva de funcionalidades.
- **Extensibilidad:** contar con mecanismos para integrar o desarrollar componentes adicionales.
- **Mantenimiento y soporte:** considerar la disponibilidad de documentación, herramientas y recursos técnicos.
- **Adecuación al negocio:** responder a las características operativas de MIGAL y considerar el contexto empresarial peruano.

## 3. Alternativas evaluadas

Se consideraron tres plataformas ERP:

| Alternativa | Descripción | Ventajas | Limitaciones |
|---|---|---|---|
| **A. StarSoft** | ERP orientado al mercado peruano, con funcionalidades administrativas, comerciales y contables. | Orientación a las necesidades empresariales y tributarias del Perú. | En la evaluación realizada se identificó menor disponibilidad de documentación técnica pública para analizar sus posibilidades de extensión e integración. |
| **B. Odoo** | Plataforma ERP modular con aplicaciones empresariales integradas y posibilidades de personalización. | Modularidad, disponibilidad de documentación técnica, comunidad de desarrolladores y alternativas de extensión. | Requiere configuración, evaluación de complementos y mantenimiento técnico según las funcionalidades incorporadas. |
| **C. Microsoft Dynamics 365** | Plataforma empresarial del ecosistema Microsoft con capacidades de gestión comercial, operaciones y finanzas. | Amplias funcionalidades empresariales y posibilidades de integración. | Su complejidad y esquema comercial representan mayores exigencias frente a las necesidades y recursos identificados en MIGAL. |

La comparación de alternativas se desarrolla con mayor detalle en [comparacion-erp.md](../comparacion-erp.md).

## 4. Decisión y justificación

Se decide adoptar **Odoo como plataforma ERP para Ferre & Inversiones MIGAL**, seleccionando la **Opción B**.

La elección se fundamenta principalmente en su arquitectura modular, que permite integrar diferentes áreas empresariales dentro de una misma plataforma y desarrollar la solución de manera progresiva.

Odoo ofrece aplicaciones para gestionar ventas, inventario, compras, facturación y relaciones comerciales, además de mecanismos de extensión mediante módulos y desarrollos personalizados.

Su disponibilidad de documentación técnica y recursos comunitarios constituye una ventaja para el equipo, considerando que MIGAL no dispone de un departamento de TI dedicado.

En comparación con las alternativas evaluadas, **Odoo presenta un equilibrio favorable entre cobertura funcional, flexibilidad y complejidad de implementación** para las necesidades del proyecto.

La selección específica de la versión y edición de Odoo constituye una decisión arquitectónica independiente, desarrollada en el ADR-002.

## 5. Consecuencias

### Positivas

- Centralización de la información comercial, operativa y administrativa.
- Integración de los procesos empresariales mediante una plataforma común.
- Implementación modular y progresiva de funcionalidades.
- Disponibilidad de documentación técnica y recursos comunitarios.
- Posibilidad de ampliar o adaptar el sistema mediante módulos adicionales.

### Limitaciones y riesgos

- La plataforma requiere configuración y adaptación a las operaciones de MIGAL.
- Los módulos complementarios deben evaluarse según su compatibilidad, dependencias y mantenimiento.
- Los desarrollos personalizados pueden incrementar la complejidad y los costos de mantenimiento.
- La disponibilidad de funcionalidades no garantiza por sí sola su adecuación a los requerimientos del negocio.
- La adopción del sistema requiere capacitación y participación de los usuarios.

## 6. Validación

La decisión se sustenta en la comparación realizada entre StarSoft, Odoo y Microsoft Dynamics 365, considerando los criterios y restricciones identificados para MIGAL.

Para confirmar la viabilidad de la solución seleccionada se requiere:

- Validar la cobertura de los procesos empresariales incluidos en el alcance.
- Comprobar la integración entre las aplicaciones seleccionadas.
- Evaluar las funcionalidades que requieren configuración o componentes adicionales.
- Verificar los requisitos técnicos, operativos y de mantenimiento de la solución.
- Realizar pruebas funcionales con escenarios representativos de MIGAL.

La adopción de Odoo se considera una **decisión arquitectónica aceptada**, mientras que la implementación y validación integral de sus componentes se desarrollará progresivamente.