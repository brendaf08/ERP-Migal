
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

Sin entradas documentadas por ahora.

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

**Referencias:** Módulos y dependencias (pendiente de documentación) · [VER-01](arquitectura/versiones/VER-01-erp.md).

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

**Referencias:** Flujo comercial (pendiente de documentación) · Plan de trazabilidad (pendiente de documentación).
