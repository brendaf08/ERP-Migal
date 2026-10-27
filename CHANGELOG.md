
# Changelog

Registro de los cambios relevantes en la evolución del proyecto **Ferre & Inversiones MIGAL — Grupo 1**.

Este documento no reemplaza el historial de Git ni registra cada commit. Resume las decisiones, incorporaciones y modificaciones significativas del proyecto.

## Criterio de actualización

Registrar únicamente cambios relevantes y efectivamente incorporados al proyecto.

Los cambios menores de redacción, formato o correcciones triviales permanecen en el historial de Git.

Los hitos históricos conservan sus fechas originales. Las rutas mencionadas pueden haber cambiado mediante reorganizaciones posteriores.

## [En desarrollo]

Esta sección reúne cambios integrados en `main` que todavía no forman parte de un hito académico cerrado.

No incluir borradores ni Pull Requests pendientes.

Sin entradas documentadas por ahora.

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

**Referencias:** [Módulos y dependencias](arquitectura/modulos-y-dependencias.md) · [VER-01](arquitectura/versiones/VER-01-erp-base.md).

## 2026-10-17 — Consolidación documental e integración CRM–ERP

### Agregado

- Se incorporó el contrato funcional INT-01 para describir los eventos y la frontera CRM–ERP.
- Se estructuró el registro de versiones de arquitectura.
- Se incorporaron plantillas y casos de prueba para la validación de escenarios.

### Modificado

- Se consolidaron las reglas de negocio de CRM, O2C y P2P en un catálogo común.
- Se alinearon documentos de procesos, datos, permisos, riesgos y diagramas con las decisiones arquitectónicas.

### Consolidado

- Se fusionaron o retiraron documentos redundantes, preservando sus contenidos relevantes en los artefactos correspondientes.

### Impacto

Se redujo la dispersión de reglas y se establecieron documentos responsables para la integración, la trazabilidad y los controles.

**Referencias:** [INT-01](arquitectura/integraciones/INT-01-CRM-ERP.md) · [ADR-004](arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md).

## 2026-10-16 — Organización inicial y escenario comercial CRM

### Organización inicial

- Se incorporaron `CHANGELOG.md` y `CONTRIBUTING.md`.
- Se establecieron convenciones de ramas, commits, Pull Requests y revisión.
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

Algunos documentos iniciales de PC2 fueron posteriormente consolidados en otros archivos; sus nombres históricos no deben interpretarse como rutas vigentes.

**Referencias:** [Flujo comercial](procesos/comercial-crm/flujo-comercial.md) · [Plan de trazabilidad](datos/trazabilidad/plan-trazabilidad-auditoria.md).
