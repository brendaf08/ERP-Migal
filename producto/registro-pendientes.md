# Registro de pendientes del proyecto

Este documento centraliza las decisiones, correcciones y validaciones pendientes identificadas durante el desarrollo del sistema de información de **Ferre & Inversiones MIGAL**. Su finalidad es facilitar el seguimiento de los asuntos abiertos, dejar constancia de quién los registró o resolvió y proporcionar enlaces a los archivos relacionados.

## 1. Organización del registro

Cada asunto recibe un identificador único (`PEN-001`, `PEN-002`, etc.) y registra **el pendiente**, **el criterio de cierre**, **quién lo registró**, **quién lo resolvió** y **los documentos relacionados**.

Los asuntos se separan en dos tablas: **pendientes activos** y **pendientes resueltos**, por lo que no se necesita una columna adicional de estado. La columna «Resuelto por» permanece vacía (—) mientras el asunto esté abierto.

Al cerrar un pendiente, se conserva su identificador y se traslada a la tabla de resueltos. Resolver una decisión funcional no significa que su configuración o sus pruebas en Odoo también estén terminadas.

## 2. Registro de pendientes

### 2.1. Pendientes activos

| ID | Pendiente | Criterio de cierre | Registrado por | Resuelto por | Documentos relacionados |
|---|---|---|---|---|---|
| PEN-003 | Definir cómo se comunicarán **Odoo ERP y KeyFacil** para emitir boletas y facturas. | Precisar quién realiza la emisión, en qué momento, qué datos se intercambian, el mecanismo de conexión y cómo se manejan respuestas, errores y comprobantes emitidos. | Brenda Mirano | — | Facturación (pendiente de documentación), [Integraciones](../arquitectura/integraciones/) |
| PEN-004 | Verificar los permisos disponibles en Odoo e identificar las restricciones que requieren configuración o personalización. | Permisos y restricciones comprobados y reflejados en la matriz detallada. | Brenda Mirano | — | matriz de permisos (pendiente de elaboración), [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) |
| PEN-005 | Validar los roles, permisos y restricciones con usuarios representativos. | Casos de prueba ejecutados, resultados documentados y evidencias registradas. | Brenda Mirano | — | pruebas (ejecución y documentación pendientes), matriz de permisos (pendiente de elaboración) |
| PEN-008 | Incorporar al nuevo repositorio el modelo de autorización actualizado, incluyendo la asignación de roles, las autorizaciones de compras y la ampliación de las responsabilidades contables de FCO. | Versión actualizada integrada en el repositorio y referencias relacionadas revisadas. | Brenda Mirano | — | [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md), [análisis de roles](../arquitectura/seguridad/analisis-roles-funcionales.md), [README de seguridad](../arquitectura/seguridad/README.md) |
| PEN-009 | Precisar las responsabilidades de programación, transporte, entrega y conformidad de recepción de pedidos. | Responsables y actividades definidos y reflejados en los documentos funcionales correspondientes. | Brenda Mirano | — | [análisis de roles](../arquitectura/seguridad/analisis-roles-funcionales.md), flujo O2C (pendiente de documentación) |
| PEN-010 | Definir quién elabora, emite y gestiona las guías de remisión cuando correspondan. | Responsables, momento de emisión y procedimiento documentados y validados. | Brenda Mirano | — | [análisis de roles](../arquitectura/seguridad/analisis-roles-funcionales.md), flujo O2C (pendiente de documentación) |
| PEN-011 | Verificar el complemento de Contabilidad descargado para Odoo 18 Community, sus funcionalidades y sus mecanismos de acceso. | Identificar nombre técnico, versión, dependencias, estado de instalación, funciones disponibles y grupos o restricciones aplicables a FCO, GER y SIS. | Brenda Mirano | — | módulos y dependencias (pendiente de documentación), [ADR-003](../arquitectura/decisiones/ADR-003-contabilidad.md), [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) |
| PEN-012 | Actualizar la documentación del proyecto para incorporar Contabilidad y Finanzas al alcance funcional. | Alcance, dependencias, decisión arquitectónica y procesos relacionados revisados y alineados con la incorporación de Contabilidad. | Brenda Mirano | — | [Alcance](../arquitectura/alcance.md), módulos y dependencias (pendiente de documentación), [ADR-003](../arquitectura/decisiones/ADR-003-contabilidad.md), Facturación (pendiente de documentación), P2P (pendiente de documentación) |
| PEN-013 | Documentar la gestión interna de inventario como proceso de apoyo a O2C y P2P. | Flujo documentado para transferencias internas, conteos, ajustes y pérdidas, sin duplicar los movimientos de ventas y compras. | Brenda Mirano | — | [Alcance](../arquitectura/alcance.md), procesos de inventario (pendiente de documentación) |
| PEN-014 | Completar la documentación de módulos técnicos y dependencias conforme a las decisiones arquitectónicas. | Documento incorporado y revisado, diferenciando aplicaciones, módulos, complementos, dependencias y validación. | Brenda Mirano | — | [ADR-003](../arquitectura/decisiones/ADR-003-contabilidad.md), [Riesgos y controles](../arquitectura/riesgos-y-controles.md) |
| PEN-015 | Validar con los propietarios las reglas comerciales y operativas pendientes, incluidos descuentos, créditos y vigencia de cotizaciones. | Condiciones confirmadas con MIGAL y reflejadas en las reglas y procesos. | Brenda Mirano | — | [Alcance](../arquitectura/alcance.md), [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) |
| PEN-016 | Validar el mecanismo funcional de transición CRM–ERP mediante la solicitud de pedido y la respuesta operativa. | Mecanismo documentado y comprobado en Odoo, diferenciando aceptación comercial, validación operativa y confirmación del pedido. | Brenda Mirano | — | [ADR-004: fronteras CRM–ERP](../arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md), [INT-01](../arquitectura/integraciones/INT-01-CRM-ERP.md) |
| PEN-017 | Evaluar e implementar, si corresponde, complementos OCA para reportes contables y financieros. | Compatibilidad verificada y reportes requeridos generados, o alternativa documentada. | Brenda Mirano | — | [ADR-003](../arquitectura/decisiones/ADR-003-contabilidad.md), [Riesgos y controles](../arquitectura/riesgos-y-controles.md) |

**Seguimiento de PEN-013 a PEN-017:** PEN-013 y PEN-016 requieren designar responsable; PEN-014 tiene un integrante del equipo asignado por identificar en el registro; PEN-015 corresponde a GER (propietarios); PEN-017 requiere asignación entre SIS y FCO. Estos responsables de seguimiento no sustituyen a la persona que registró cada asunto ni acreditan su resolución.

### 2.2. Pendientes resueltos

| ID | Pendiente | Criterio de cierre | Registrado por | Resuelto por | Documentos relacionados |
|---|---|---|---|---|---|
| PEN-001 | Definir la distribución funcional inicial de roles entre propietarios y trabajadores. | Dueña: GER, VEN, ALM, CMP y FCO; dueño: GER, VEN, ALM y FCO; trabajador 1: VEN y ALM; trabajador 2: ALM. | Brenda Mirano | Brenda Mirano | [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) |
| PEN-002 | Definir quién autoriza descuentos negociados, compras, créditos y ajustes extraordinarios de inventario. | GER conserva estas autorizaciones; ambos propietarios pueden aprobar compras, aunque el dueño no tenga CMP. | Brenda Mirano | Brenda Mirano | [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md), políticas operativas (pendiente de documentación) |
| PEN-006 | Confirmar si el dueño tendrá asignado CMP. | Se acuerda que el dueño no tendrá CMP, pero podrá autorizar órdenes de compra mediante GER. | Brenda Mirano | Brenda Mirano | [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) |
| PEN-007 | Designar al responsable de administración técnica del sistema. | Se designa a Brenda Mirano como responsable inicial del rol SIS. | Brenda Mirano | Brenda Mirano | [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) |

Los pendientes resueltos se conservan para mantener la trazabilidad de las decisiones. Si una decisión cambia, se documentará la nueva modificación sin reutilizar el identificador anterior para otro asunto.