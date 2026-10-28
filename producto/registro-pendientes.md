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
| PEN-003 | Definir cómo se comunicarán **Odoo ERP y KeyFacil** para emitir boletas y facturas. | Precisar quién realiza la emisión, en qué momento, qué datos se intercambian, el mecanismo de conexión y cómo se manejan respuestas, errores y comprobantes emitidos. | Brenda Mirano | — | [Facturación](../procesos/o2c/facturacion.md), [Integraciones](../arquitectura/integraciones/) |
| PEN-004 | Verificar los permisos disponibles en Odoo e identificar las restricciones que requieren configuración o personalización. | Permisos y restricciones comprobados y reflejados en la matriz detallada. | Brenda Mirano | — | [Matriz de permisos](../arquitectura/seguridad/matriz-permisos.xlsx), [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) |
| PEN-005 | Validar los roles, permisos y restricciones con usuarios representativos. | Casos de prueba ejecutados, resultados documentados y evidencias registradas. | Brenda Mirano | — | [Pruebas](../pruebas/README.md), [Matriz de permisos](../arquitectura/seguridad/matriz-permisos.xlsx) |
| PEN-008 | Incorporar al nuevo repositorio el modelo de autorización actualizado, incluyendo la asignación de roles, las autorizaciones de compras y la ampliación de las responsabilidades contables de FCO. | Versión actualizada integrada en el repositorio y referencias relacionadas revisadas. | Brenda Mirano | — | [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md), [Revisión de roles](../arquitectura/seguridad/revision-roles-funcionales.md), [README de seguridad](../arquitectura/seguridad/README.md) |
| PEN-009 | Precisar las responsabilidades de programación, transporte, entrega y conformidad de recepción de pedidos. | Responsables y actividades definidos y reflejados en los documentos funcionales correspondientes. | Brenda Mirano | — | [Revisión de roles](../arquitectura/seguridad/revision-roles-funcionales.md), [Flujo O2C](../procesos/o2c/flujo.md) |
| PEN-010 | Definir quién elabora, emite y gestiona las guías de remisión cuando correspondan. | Responsables, momento de emisión y procedimiento documentados y validados. | Brenda Mirano | — | [Revisión de roles](../arquitectura/seguridad/revision-roles-funcionales.md), [Flujo O2C](../procesos/o2c/flujo.md) |
| PEN-011 | Verificar el complemento de Contabilidad descargado para Odoo 18 Community, sus funcionalidades y sus mecanismos de acceso. | Identificar nombre técnico, versión, dependencias, estado de instalación, funciones disponibles y grupos o restricciones aplicables a FCO, GER y SIS. | Brenda Mirano | — | [Módulos y dependencias](../arquitectura/modulos-y-dependencias.md), [ADR-003](../arquitectura/decisiones/ADR-003-contabilidad.md), [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) |
| PEN-012 | Actualizar la documentación del proyecto para incorporar Contabilidad y Finanzas al alcance funcional. | Alcance, dependencias, decisión arquitectónica y procesos relacionados revisados y alineados con la incorporación de Contabilidad. | Brenda Mirano | — | [Alcance](../arquitectura/alcance.md), [Módulos y dependencias](../arquitectura/modulos-y-dependencias.md), [ADR-003](../arquitectura/decisiones/ADR-003-contabilidad.md), [Facturación](../procesos/o2c/facturacion.md), [P2P](../procesos/p2p/flujo.md) |

### 2.2. Pendientes resueltos

| ID | Pendiente | Criterio de cierre | Registrado por | Resuelto por | Documentos relacionados |
|---|---|---|---|---|---|
| PEN-001 | Definir la distribución funcional inicial de roles entre propietarios y trabajadores. | Dueña: GER, VEN, ALM, CMP y FCO; dueño: GER, VEN, ALM y FCO; trabajador 1: VEN y ALM; trabajador 2: ALM. | Brenda Mirano | Brenda Mirano | [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) |
| PEN-002 | Definir quién autoriza descuentos negociados, compras, créditos y ajustes extraordinarios de inventario. | GER conserva estas autorizaciones; ambos propietarios pueden aprobar compras, aunque el dueño no tenga CMP. | Brenda Mirano | Brenda Mirano | [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md), [Políticas operativas](../procesos/politicas-operativas.md) |
| PEN-006 | Confirmar si el dueño tendrá asignado CMP. | Se acuerda que el dueño no tendrá CMP, pero podrá autorizar órdenes de compra mediante GER. | Brenda Mirano | Brenda Mirano | [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) |
| PEN-007 | Designar al responsable de administración técnica del sistema. | Se designa a Brenda Mirano como responsable inicial del rol SIS. | Brenda Mirano | Brenda Mirano | [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) |

Los pendientes resueltos se conservan para mantener la trazabilidad de las decisiones. Si una decisión cambia, se documentará la nueva modificación sin reutilizar el identificador anterior para otro asunto.