# Registro de pendientes del proyecto

Este documento centraliza las decisiones, actividades y validaciones pendientes identificadas durante el desarrollo de **ERP-MIGAL**, facilitando su seguimiento, asignación de responsabilidades y cierre documentado.

El registro comprende asuntos relacionados con arquitectura, procesos empresariales, integraciones, seguridad y validación del sistema.

## 1. Organización del registro

Cada pendiente recibe un identificador único (`PEN-001`, `PEN-002`, etc.) y contiene:

- **Pendiente:** asunto que requiere resolución.
- **Responsable:** persona o rol encargado de resolverlo.
- **Creado por y fecha:** quién registró el pendiente y cuándo.
- **Criterio de cierre:** condición necesaria para considerarlo resuelto.
- **Páginas afectadas:** documentos relacionados con su resolución.
- **Resuelto por y fecha de cierre:** responsable y fecha de su resolución.

Los registros se organizan en **pendientes activos** y **pendientes resueltos**, sin utilizar una columna adicional de estado.

Un pendiente únicamente se considera resuelto cuando cumple su criterio de cierre. La aprobación documental de una decisión no implica que sus configuraciones o pruebas técnicas estén completadas.

Los datos históricos que no fueron registrados se mantienen como «—», sin asignar fechas o responsables de manera retroactiva.

## 2. Registro de pendientes

### 2.1. Pendientes activos

| ID | Pendiente | Responsable | Creado por | Fecha | Criterio de cierre | Páginas afectadas | Resuelto por | Fecha de cierre |
|---|---|---|---|---|---|---|---|---|
| **PEN-003** | Definir el procedimiento de emisión y conciliación de comprobantes entre Odoo y KeyFacil, sin integración automática inicial. | Por asignar (GER/FCO) | Brenda Mirano | — | Procedimiento documentado para emisión, registro de referencias, conciliación y tratamiento de discrepancias. | `arquitectura/alcance.md`, `procesos/o2c/`, `arquitectura/integraciones/` | — | — |
| **PEN-004** | Verificar los permisos disponibles en Odoo e identificar las restricciones que requieren configuración adicional. | SIS (Brenda Mirano) | Brenda Mirano | — | Permisos y restricciones comprobados y registrados en la matriz correspondiente. | `arquitectura/seguridad/modelo-autorizacion.md`, `arquitectura/seguridad/matriz-permisos.xlsx` | — | — |
| **PEN-005** | Validar los roles y restricciones de acceso con usuarios representativos. | Por asignar | Brenda Mirano | — | Casos de prueba ejecutados, resultados documentados y evidencias registradas. | `arquitectura/seguridad/`, `pruebas/` | — | — |
| **PEN-008** | Incorporar al nuevo repositorio el modelo de autorización actualizado, incluyendo la asignación de roles y responsables. | Brenda Mirano | Brenda Mirano | — | Documentos incorporados al repositorio y referencias internas verificadas. | `arquitectura/seguridad/modelo-autorizacion.md`, `arquitectura/seguridad/revision-roles-funcionales.md` | — | — |
| **PEN-009** | Precisar las responsabilidades de programación, transporte, entrega y conformidad de recepción de pedidos. | Por definir con GER | Brenda Mirano | — | Responsables y actividades definidos y reflejados en los procesos correspondientes. | `arquitectura/seguridad/revision-roles-funcionales.md`, `procesos/o2c/` | — | — |
| **PEN-010** | Definir quién elabora, emite y gestiona las guías de remisión cuando correspondan. | Por definir con GER/FCO | Brenda Mirano | — | Responsables, condiciones y procedimiento de emisión documentados y validados. | `arquitectura/seguridad/revision-roles-funcionales.md`, `procesos/o2c/` | — | — |
| **PEN-011** | Validar el mecanismo funcional de transición CRM–ERP mediante la solicitud de pedido y la respuesta operativa. | Por asignar | Brenda Mirano | 2026-10-28 | Mecanismo documentado y comprobado en Odoo, diferenciando aceptación comercial, validación operativa y confirmación del pedido. | `arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md`, `arquitectura/integraciones/`, `procesos/o2c/` | — | — |
| **PEN-012** | Evaluar e implementar, si corresponde, los complementos OCA para reportes contables y financieros. | Por asignar (SIS/FCO) | Brenda Mirano | 2026-10-28 | Compatibilidad verificada y reportes financieros requeridos generados correctamente, o alternativa documentada si los módulos no resultan adecuados. | `arquitectura/decisiones/ADR-003-contabilidad.md`, `arquitectura/modulos-y-dependencias.md` | — | — |
| **PEN-013** | Documentar la gestión interna de inventario como proceso de apoyo a O2C y P2P. | Por asignar | Brenda Mirano | 2026-10-28 | Flujo documentado para transferencias internas, conteos, ajustes y pérdidas, sin duplicar los movimientos propios de ventas y compras. | `arquitectura/alcance.md`, `procesos/flujo-inventario.md` | — | — |
| **PEN-014** | Completar la documentación de módulos técnicos y dependencias conforme a las decisiones arquitectónicas actualizadas. | Compañero asignado | Brenda Mirano | 2026-10-28 | Documento incorporado y revisado, con aplicaciones, módulos, complementos, dependencias y estado de validación diferenciados. | `arquitectura/modulos-y-dependencias.md`, `arquitectura/decisiones/` | — | — |
| **PEN-015** | Validar con los propietarios las reglas comerciales y operativas pendientes, incluyendo descuentos, créditos, vigencia de cotizaciones y reservas de stock. | GER (propietarios) | Brenda Mirano | 2026-10-28 | Condiciones y autorizaciones definidas con MIGAL y reflejadas en las reglas y procesos correspondientes. | `procesos/`, `arquitectura/seguridad/modelo-autorizacion.md`, `arquitectura/integraciones/` | — | — |

### 2.2. Pendientes resueltos

| ID | Pendiente | Responsable | Creado por | Fecha | Criterio de cierre | Páginas afectadas | Resuelto por | Fecha de cierre |
|---|---|---|---|---|---|---|---|---|
| **PEN-001** | Definir la distribución funcional inicial de roles entre propietarios y trabajadores. | Brenda Mirano | Brenda Mirano | — | Dueña: GER, VEN, ALM, CMP y FCO; dueño: GER, VEN, ALM y FCO; trabajador 1: VEN y ALM; trabajador 2: ALM. | `arquitectura/seguridad/modelo-autorizacion.md` | Brenda Mirano | — |
| **PEN-002** | Definir las responsabilidades de autorización para descuentos, compras, créditos y ajustes extraordinarios de inventario. | Brenda Mirano | Brenda Mirano | — | GER conserva estas autorizaciones; ambos propietarios pueden aprobar compras, aunque el dueño no tenga CMP. | `arquitectura/seguridad/modelo-autorizacion.md`, `procesos/` | Brenda Mirano | — |
| **PEN-006** | Confirmar si el dueño tendrá asignado CMP. | Brenda Mirano | Brenda Mirano | — | Se establece que el dueño no tendrá CMP, pero podrá autorizar compras mediante GER. | `arquitectura/seguridad/modelo-autorizacion.md` | Brenda Mirano | — |
| **PEN-007** | Designar al responsable de administración técnica del sistema. | Brenda Mirano | Brenda Mirano | — | Brenda Mirano es designada responsable inicial del rol SIS. | `arquitectura/seguridad/modelo-autorizacion.md` | Brenda Mirano | — |

## 3. Mantenimiento del registro

Para mantener la trazabilidad de los asuntos registrados se establecen las siguientes reglas:

1. Cada pendiente conserva su identificador, incluso después de resolverse.
2. Los nuevos asuntos reciben el siguiente identificador disponible.
3. Cuando un pendiente se resuelve, se registra quién lo resolvió, la fecha y se traslada a la tabla correspondiente.
4. No se considera resuelta una validación técnica únicamente porque su diseño haya sido documentado.
5. Si una decisión cambia, debe registrarse el nuevo asunto sin reutilizar el identificador anterior.
6. Las páginas afectadas deben revisarse cuando una resolución modifique decisiones, procesos o responsabilidades previamente documentadas.