
# Registro de cambios

Registro de los cambios relevantes en la evolución del proyecto **Ferre & Inversiones MIGAL — Grupo 1**.

Este documento resume las decisiones y avances significativos en la documentación del proyecto.

## Criterio de actualización

Registrar únicamente cambios relevantes y efectivamente incorporados al proyecto.

Los cambios menores de redacción, formato o correcciones triviales no constituyen hitos documentales.

Los hitos históricos conservan sus fechas originales. Las rutas mencionadas pueden haber cambiado mediante reorganizaciones posteriores.

## [En desarrollo]

Esta sección reúne avances que todavía no forman parte de un hito académico cerrado.

No incluir borradores ni resultados pendientes de aprobación.

- **Entorno local Odoo:** se incorpora la [configuración Docker reproducible](infra/odoo/readme.md) junto con los [nueve addons](custom_addons/readme.md) y sus dependencias.

## 2026-11-07 — Corrección, pruebas de frontera y cierre de la consolidación documental

### Cambiado

- **Corrección y cierre documental (PR #11):** el README se alinea con el alcance (Compras incluido en P2P) y enlaza todos los documentos vigentes; INT-01, VER-02, el contexto de la empresa y el CHANGELOG sustituyen referencias «pendientes» por enlaces a documentos existentes; el contexto indica el respaldo de cada recurso de infraestructura (FN-01 o FN-02 pendiente de corroboración).
- **Registro de pendientes (PR #11):** se trasladan desde INT-01 PEN-018 a PEN-020 y se añade la verificación de criterios de cierre (§2.3), sin cerrar ningún pendiente.

### Agregado

- **Declaración de uso de IA (PR #11):** [fuentes/uso-ia.md](fuentes/uso-ia.md).
- **Pruebas de la frontera CRM–ERP (PR #12):** [CP-03](pruebas/CP-03-solicitud-aceptada.md) (solicitud aceptada y confirmación posterior) y [CP-04](pruebas/CP-04-solicitud-condicionada-rechazada.md) (respuestas condicionada y rechazada), ambos en estado **No ejecutado**.

### Eliminado

- **Limpieza (PR #13):** 37 placeholders `B-` vacíos clasificados como cubiertos, prescindibles o sustituidos, y dos archivos `.DS_Store`. Se conservan cinco placeholders complementarios y se completa `.gitignore`.

### Impacto

La consolidación documental queda cerrada. La ejecución de los casos de prueba y la configuración de la frontera CRM–ERP dependen de PEN-016 y PEN-018 a PEN-020.

## 2026-11-06 — Fundamentos, procesos, datos y casos de prueba de ERP-MIGAL

### Agregado

- **Fundamentos (PR #7):** [fuentes del negocio](fuentes/fuentes-negocio.md) y [supuestos y vacíos](fuentes/supuestos-y-vacios.md), que distinguen evidencia empresarial, interpretación y afirmaciones pendientes de corroboración; [módulos y dependencias](arquitectura/modulos-y-dependencias.md) según los manifiestos de Odoo 19, y el [mapa de procesos](procesos/mapa-procesos.md) de nivel 1.
- **Procesos y reglas (PR #8):** flujos [comercial CRM](procesos/comercial-crm/flujo-comercial.md), [O2C](procesos/o2c/flujo.md), [P2P](procesos/p2p/flujo.md) e [inventario](procesos/inventario/flujo.md), y el [catálogo de reglas](procesos/catalogo-reglas.md) con RN-001–RN-021, CT-001–CT-009 y EXC-001–EXC-006.
- **Datos y trazabilidad (PR #9):** [diccionario de datos](datos/diccionario-datos.md) funcional, sin campos técnicos de Odoo verificados, y [plan de trazabilidad y auditoría](datos/trazabilidad/plan-trazabilidad-auditoria.md) con 25 requisitos TR.
- **Pruebas (PR #10):** casos [CP-01](pruebas/CP-01-caso-normal.md) y [CP-02](pruebas/CP-02-caso-excepcion.md) con datos sintéticos, en estado **No ejecutado**.

### Impacto

La documentación cubre procesos, reglas, datos y trazabilidad de CRM, O2C, P2P e inventario. Su implementación en Odoo 19 y la ejecución de los casos de prueba permanecen pendientes.

## 2026-11-06 — Evolución de la arquitectura y los procesos de ERP-MIGAL

- Se documentó Odoo 19 Community como versión base en [ADR-005](arquitectura/decisiones/ADR-005-cambio-version-Odoo-18-Community-a-Odoo-19-Community.md) y la adopción de Odoo CRM en [ADR-006](arquitectura/decisiones/ADR-006-adopcion-crm-odoo.md), manteniendo la frontera funcional definida en ADR-004.
- Se incorporaron el contrato funcional [INT-01](arquitectura/integraciones/INT-01-CRM-ERP.md), las versiones VER-01 y VER-02 y las vistas C4 de contexto, aplicaciones, dependencias y componentes.
- El [catálogo de eventos](procesos/catalogo-eventos.md) centraliza los identificadores de negocio. INT-01 distingue las respuestas aceptada, condicionada y rechazada; algunas correspondencias requieren validación funcional.
- Se amplió el [registro de riesgos](arquitectura/riesgos-y-controles.md) a RSK-001–RSK-027 y el [registro de pendientes](producto/registro-pendientes.md) a PEN-001–PEN-017, con controles y criterios de cierre para las validaciones aún abiertas.

## 2026-10-23 — Dependencias y arquitectura técnica de Odoo

### Agregado

- Se documentaron los módulos de Odoo 18 Community y sus dependencias obligatorias y complementarias.
- Se identificaron los módulos de apoyo a CRM, Ventas, Inventario, Punto de Venta y Facturación.
- Se incorporó el diagrama de dependencias entre módulos.
- Se registraron hallazgos técnicos, ajustes de arquitectura y riesgos relacionados.

### Modificado

- Se precisó la inclusión técnica de `account` y el papel transversal de Contactos.
- Se actualizaron las vistas C4 conforme a las dependencias identificadas.

### Impacto

Se fortaleció la consistencia entre el alcance funcional propuesto y las dependencias técnicas de Odoo, sin acreditar todavía su implementación o configuración.

**Referencias:** [Módulos y dependencias](arquitectura/modulos-y-dependencias.md) (versión vigente, actualizada a Odoo 19) · [VER-01](arquitectura/versiones/VER-01-erp.md).

## 2026-10-17 — Evolución documental e integración CRM–ERP

### Agregado

- Se incorporó el contrato funcional INT-01 para describir los eventos y la frontera CRM–ERP.
- Se estructuró el registro de versiones de arquitectura.
- Se incorporaron plantillas y casos de prueba para la validación de escenarios.

### Modificado

- Se consolidaron las reglas de negocio de CRM, O2C y P2P en un catálogo común.
- Se alinearon documentos de procesos, datos, permisos, riesgos y diagramas con las decisiones arquitectónicas.

### Impacto

Se redujo la dispersión de reglas y se establecieron documentos responsables para la integración, la trazabilidad y los controles.

**Referencias:** [INT-01](arquitectura/integraciones/INT-01-CRM-ERP.md) · [ADR-004](arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md).

## 2026-10-16 — Organización inicial y escenario comercial CRM

### Organización inicial

- Se incorporaron `CHANGELOG.md` y `CONTRIBUTING.md`.
- Se establecieron criterios de revisión y trazabilidad de los entregables.
- Se organizó la documentación en áreas de arquitectura, procesos, datos, producto, pruebas y fuentes.
- Se separaron los diagramas editables de sus representaciones generadas.
- Se reorganizaron documentos de procesos, arquitectura y trazabilidad para facilitar la navegación.

### Escenario comercial y evidencias de PC2

- Se desarrolló el escenario comercial CRM con sus etapas, decisiones, reglas y excepciones.
- Se incorporaron fuentes editables y representaciones gráficas del flujo comercial.
- Se documentaron las autorizaciones, la segregación de funciones y los controles asociados.
- Se incorporaron el plan y la matriz de trazabilidad y auditoría.
- Se prepararon artefactos documentales y datos de apoyo para las evaluaciones del curso.

### Impacto

Se estableció una base documental para gestionar de forma incremental los entregables y las decisiones del proyecto.

Asimismo, se amplió el alcance del ERP base hacia la gestión comercial y se fortaleció la documentación de controles y evidencias.

**Referencias:** [Flujo comercial](procesos/comercial-crm/flujo-comercial.md) · [Plan de trazabilidad](datos/trazabilidad/plan-trazabilidad-auditoria.md) (versiones vigentes).
