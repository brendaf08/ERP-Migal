# ADR-001: Adoptar Odoo como plataforma ERP

- **Fecha:** 2026-09-25
- **Estado:** Aceptado
- **Responsable de la decisión:** Equipo ERP-MIGAL

Este documento registra y sustenta la elección de la plataforma ERP para Ferre & Inversiones MIGAL, a partir de la evaluación de las alternativas tecnológicas y las condiciones de la empresa.

## 1. Contexto y problema

**Ferre & Inversiones MIGAL** necesita integrar sus operaciones comerciales y administrativas, actualmente apoyadas en registros manuales, comunicaciones informales y herramientas que no comparten toda su información.

La empresa cuenta con una tienda, dos almacenes, dos propietarios y dos trabajadores. Requiere gestionar de manera coordinada ventas, inventario, compras, relaciones comerciales y operaciones financieras, manteniendo los controles necesarios sobre precios, descuentos y autorizaciones.

El objetivo no es únicamente construir una solución académica, sino establecer una base tecnológica que la ferretería pueda adoptar y mantener posteriormente.

Para seleccionar la plataforma se evaluaron **StarSoft, Odoo y Microsoft Dynamics 365 Business Central**, considerando sus capacidades, limitaciones y adecuación a los recursos de MIGAL.

La investigación detallada se encuentra en [Comparación de sistemas ERP](../comparacion-erp.md).

## 2. Criterios de decisión

La evaluación prioriza los siguientes criterios:

| Criterio | Importancia para MIGAL |
|---|---|
| **Cobertura funcional** | Cubrir los procesos comerciales, operativos y financieros sin depender de múltiples sistemas independientes. |
| **Integración** | Mantener información consistente entre ventas, compras, inventario y administración. |
| **Costo total** | Evitar compromisos económicos desproporcionados, considerando licencias, implementación y mantenimiento. |
| **Adecuación operativa** | Atender ventas de mostrador, pedidos de materiales y movimientos entre tienda y almacenes. |
| **Extensibilidad** | Incorporar nuevas funcionalidades y adaptar procesos sin sustituir completamente la plataforma. |
| **Adecuación peruana** | Considerar las obligaciones contables y tributarias que correspondan a la empresa. |
| **Sostenibilidad** | Permitir la continuidad del sistema después de finalizar el proyecto académico. |
| **Viabilidad técnica** | Contar con documentación, herramientas y capacidades de implementación accesibles para el equipo. |

Se consideran especialmente determinantes la cobertura funcional, integración, costo total y sostenibilidad.

No se asignan puntuaciones numéricas porque no se dispone de pruebas piloto equivalentes ni cotizaciones completas de las tres alternativas.

## 3. Alternativas evaluadas

| Alternativa | Fortalezas relevantes | Limitaciones y riesgos |
|---|---|---|
| **A. StarSoft** | Orientación al mercado peruano, módulos de ventas, inventarios, compras, contabilidad y facturación electrónica. Disponibilidad de servicios comerciales de soporte. | Costos sujetos a cotización, dependencia de las condiciones del proveedor y necesidad de verificar la cobertura del CRM y las posibilidades de personalización requeridas. |
| **B. Odoo** | Plataforma modular, aplicaciones integradas, edición Community de código abierto, documentación pública y posibilidades de ampliación mediante módulos propios o comunitarios. | Community presenta limitaciones frente a Enterprise, especialmente en contabilidad integral y servicios incluidos. La instalación y el mantenimiento requieren capacidad técnica. |
| **C. Microsoft Dynamics 365 Business Central** | Gestión financiera, comercial, compras e inventario integrados; ecosistema empresarial amplio y mantenimiento administrado en su modalidad Online. | Licenciamiento recurrente, posible necesidad de extensiones para POS y localización peruana mediante partners, además de servicios especializados de implementación. |

### Evaluación de las alternativas

**StarSoft** presenta una ventaja importante para las necesidades contables y tributarias de una empresa peruana. Su oferta incluye funcionalidades relevantes para la operación de MIGAL, por lo que no se descarta por insuficiencia funcional.

Sin embargo, la ausencia de una cotización específica y la necesidad de confirmar ciertas capacidades de integración y personalización impiden determinar su conveniencia económica y técnica para este proyecto.

**Odoo** permite integrar los procesos prioritarios mediante aplicaciones de una misma plataforma. La edición Community evita licencias recurrentes por usuario y proporciona acceso al código fuente, documentación y componentes adicionales.

Su principal desventaja es que estas facilidades trasladan parte de la responsabilidad técnica a MIGAL. Además, la cobertura de contabilidad avanzada y de los requerimientos fiscales peruanos debe verificarse en la edición y configuración utilizadas.

**Business Central** ofrece una cobertura empresarial amplia y un modelo de mantenimiento administrado. Sin embargo, su licenciamiento comercial y las posibles extensiones necesarias para ventas minoristas y localización peruana representan compromisos económicos adicionales.

Estas condiciones reducen su conveniencia para el tamaño, presupuesto y necesidades actuales de MIGAL.

## 4. Decisión y justificación

Se decide adoptar la **Opción B: Odoo como plataforma ERP para Ferre & Inversiones MIGAL**.

La decisión se sustenta en los siguientes fundamentos.

**1. Cobertura integrada de los procesos prioritarios**

Odoo dispone de aplicaciones relacionadas con CRM, Ventas, Punto de Venta, Inventario, Compras y Facturación.

Esta cobertura permite abordar los procesos de MIGAL mediante una plataforma común, evitando incorporar desde el inicio soluciones independientes para cada actividad.

La integración de información constituye una ventaja relevante frente a la situación actual de registros y operaciones desconectados.

**2. Adecuación al tamaño y forma de operación de la empresa**

MIGAL necesita atender tanto ventas inmediatas de mostrador como pedidos de materiales que requieren cotización, consulta de disponibilidad y posterior entrega.

Odoo proporciona funcionalidades para ambos escenarios, además de herramientas para organizar existencias y operaciones en distintas ubicaciones.

La arquitectura modular permite introducir progresivamente los procesos definidos, sin exigir que todas las funcionalidades se implementen simultáneamente.

**3. Viabilidad económica y flexibilidad de implementación**

Odoo dispone de una edición Community gratuita y de código abierto, lo que evita compromisos recurrentes de licenciamiento por usuario.

Esta característica resulta especialmente favorable para una empresa pequeña y para un proyecto con recursos económicos limitados.

No obstante, **la ausencia de costos de licencia no implica un costo total nulo**. La infraestructura, configuración, capacitación, mantenimiento y posibles adaptaciones deberán considerarse durante la implementación.

Aunque no se puede afirmar que Odoo sea la alternativa de menor costo total sin cotizaciones comparables, su modelo de licenciamiento reduce una barrera económica importante para MIGAL.

**4. Autonomía tecnológica y capacidad de adaptación**

El acceso al código fuente, la documentación técnica y el ecosistema de módulos permite al equipo estudiar, configurar y ampliar la solución.

Esto favorece la adaptación progresiva del ERP a las necesidades de MIGAL y reduce la dependencia exclusiva de un fabricante para efectuar modificaciones.

Como contrapartida, cada complemento o desarrollo propio introduce responsabilidades de compatibilidad, seguridad y mantenimiento que deberán administrarse.

**5. Sostenibilidad y aprovechamiento del trabajo desarrollado**

La elección de Odoo permite construir capacidades técnicas reutilizables durante el proyecto académico y establecer una base para su adopción empresarial.

Posteriormente a la selección inicial, MIGAL también dispuso de una instalación de Odoo Community y comenzó a utilizarla de manera exploratoria. Esta experiencia constituye evidencia adicional de viabilidad, aunque no reemplaza las pruebas completas de operación.

La continuidad posterior al proyecto dependerá de definir responsables de administración, respaldos, actualizaciones y soporte técnico.

### Consideración de las alternativas no seleccionadas

La selección de Odoo **no implica que supere a StarSoft o Business Central en todos los criterios**.

StarSoft ofrece ventajas relevantes en gestión contable y tributaria peruana. Business Central dispone de una solución financiera amplia y de servicios de mantenimiento administrado.

Sin embargo, para las condiciones actuales de MIGAL, estas ventajas no compensan suficientemente las incertidumbres o compromisos económicos frente a la flexibilidad, integración y accesibilidad técnica de Odoo.

Por ello, **Odoo presenta el equilibrio más conveniente entre cobertura funcional, costo inicial, extensibilidad y viabilidad de implementación**, siempre que se atiendan sus limitaciones de mantenimiento y adecuación tributaria.

La versión y edición específicas de la plataforma se establecen mediante decisiones arquitectónicas independientes.

## 5. Consecuencias

### Positivas

- Centralización de los procesos empresariales en una plataforma modular.
- Integración de información entre las principales operaciones.
- Posibilidad de implementar funcionalidades progresivamente.
- Acceso a código fuente, documentación y complementos comunitarios.
- Reducción de costos iniciales asociados con licencias de software.
- Mayor capacidad de adaptación y ampliación futura.

### Limitaciones y riesgos

- La edición Community no incluye todas las funcionalidades y servicios de Enterprise.
- La gestión contable integral y el cumplimiento tributario peruano requieren validaciones específicas.
- La incorporación de módulos externos puede generar dependencias y costos de mantenimiento.
- La operación del sistema exige administración técnica, respaldos, seguridad y actualizaciones.
- El proyecto podría generar dependencia del equipo académico si no se establece un mecanismo de soporte posterior.
- Si las adaptaciones necesarias resultan excesivas, las ventajas económicas y técnicas de Odoo podrían reducirse.

La selección deberá reconsiderarse si las pruebas muestran limitaciones funcionales importantes, si el costo de mantenimiento resulta desproporcionado o si MIGAL no puede asegurar la continuidad técnica del sistema.

## 6. Validación

La decisión se fundamenta en la investigación comparativa documentada y en la evaluación de las necesidades operativas de MIGAL.

La selección de Odoo como plataforma se considera **aceptada a nivel arquitectónico**, sin que esto implique que todas sus funcionalidades se encuentren implementadas o validadas.

Para respaldar su adopción empresarial se requiere:

- Verificar la cobertura de las operaciones comerciales, de inventario, compras y finanzas.
- Comprobar la adecuación del sistema a las ventas de mostrador y los pedidos de materiales.
- Validar las funcionalidades contables y tributarias requeridas para la operación en Perú.
- Evaluar la compatibilidad y el mantenimiento de los complementos necesarios.
- Comprobar la facilidad de uso con los propietarios y trabajadores.
- Definir responsabilidades de soporte, respaldos, mantenimiento y recuperación del sistema.
- Revisar el costo operativo esperado y la dependencia de servicios externos.

Los resultados de estas verificaciones permitirán confirmar que la plataforma seleccionada no solo satisface los objetivos académicos, sino que puede mantenerse y aportar valor a Ferre & Inversiones MIGAL.