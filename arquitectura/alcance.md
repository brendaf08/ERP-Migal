# Alcance del sistema de información ERP-MIGAL

Este documento delimita los procesos, operaciones, participantes y necesidades de **Ferre & Inversiones MIGAL** que serán abordados por el proyecto, estableciendo sus límites funcionales y las actividades excluidas de la implementación inicial.

## 1. Objetivo y ámbito del proyecto

El proyecto busca mejorar la gestión integrada de las operaciones comerciales, logísticas y administrativas de MIGAL, reduciendo la dependencia de registros manuales, consultas informales e información dispersa.

El alcance comprende las operaciones de la empresa en:

- **Tienda física:** atención, ventas y operaciones comerciales.
- **Almacén 1 y Almacén 2:** almacenamiento, control de existencias y movimientos de productos.
- **Gestión administrativa:** compras, proveedores, documentos comerciales, cobranzas, pagos y supervisión.

Participan los propietarios, trabajadores, clientes, maestros de obra y proveedores, según su intervención en los procesos.

El proyecto aborda la **gestión interna de las operaciones de MIGAL**, sin extenderse a la administración de las obras o actividades propias de sus clientes.

## 2. Procesos y capacidades incluidos

### 2.1. Macroprocesos principales

| Macroproceso | Inicio y fin | Capacidades comprendidas |
|---|---|---|
| **Order to Cash (O2C)** | Desde la consulta o intención de compra hasta la atención del pedido, el registro del cobro y el cierre de la operación. | Gestión comercial, clientes, oportunidades, cotizaciones, pedidos, ventas de mostrador, preparación y entrega, comprobantes relacionados, créditos y cobranzas. |
| **Procure to Pay (P2P)** | Desde la identificación de una necesidad de abastecimiento hasta la recepción y el pago al proveedor. | Gestión de proveedores, solicitudes de cotización, órdenes de compra, recepción de productos, verificación de documentos y seguimiento de pagos. |

Ambos macroprocesos incluyen el tratamiento de sus excepciones, autorizaciones y registros necesarios para mantener la trazabilidad.

Los procedimientos, actividades y reglas específicas se definen en los documentos de procesos correspondientes.

### 2.2. Operaciones de soporte incluidas

| Ámbito | Capacidades comprendidas |
|---|---|
| **Inventario y almacenes** | Registro de existencias por ubicación, recepciones, transferencias, salidas, conteos y ajustes justificados. |
| **Datos maestros** | Organización de productos y variantes, clientes, proveedores y demás datos necesarios para los procesos incluidos. |
| **Gestión de precios** | Consulta, mantenimiento y autorización de precios y descuentos, conforme a las decisiones de los propietarios. |
| **Administración financiera operativa** | Registro y seguimiento de documentos comerciales, pagos, cobranzas, saldos pendientes y conciliaciones aplicables. |
| **Control y trazabilidad** | Identificación de responsables, autorizaciones, cambios relevantes y evidencias de operaciones sensibles. |

El **inventario es una operación de soporte transversal a O2C y P2P**, no un tercer macroproceso principal.

La incorporación de estas capacidades podrá realizarse progresivamente. Su inclusión en el alcance no implica que todas estén implementadas o validadas.

## 3. Límites de la solución

### 3.1. Canales y sistemas existentes

| Elemento | Tratamiento dentro del alcance |
|---|---|
| **Atención presencial** | Incluida como canal de consultas, cotizaciones y ventas. |
| **Teléfono y WhatsApp** | Incluidos como canales de comunicación comercial, con registro de la información pertinente mediante procedimientos manuales. |
| **KeyFacil** | Se mantiene la emisión de comprobantes mediante el sistema existente y se contempla su registro relacionado y conciliación con las operaciones administradas por el proyecto. |
| **Proveedores y servicios de transporte** | Participan como actores externos cuando intervienen en compras, abastecimiento o entregas. |

Las responsabilidades sobre los datos y los mecanismos de intercambio entre sistemas se especifican en los documentos de integración.

### 3.2. Actividades fuera del alcance inicial

| Exclusión | Límite establecido |
|---|---|
| **Integración automática con WhatsApp** | No se desarrollará una conexión que registre o responda automáticamente conversaciones. |
| **Integración automática con KeyFacil** | No se implementará inicialmente sincronización mediante API u otro conector automático. |
| **Sustitución inmediata del sistema de comprobantes** | La emisión tributaria mediante una nueva plataforma no se considera comprometida en esta etapa. |
| **Contabilidad tributaria integral automatizada** | No se garantiza generar desde la solución todos los libros, declaraciones o reportes fiscales oficiales sin validar previamente sus capacidades y requisitos. |
| **Comercio electrónico** | No se contempla implementar una tienda virtual para clientes. |
| **Campañas y automatización de marketing** | No se implementarán inicialmente campañas automatizadas ni herramientas de marketing especializadas. |
| **Gestión de obras de clientes** | No incluye presupuestos integrales, cronogramas ni seguimiento de ejecución de construcciones. |
| **Recursos humanos y planillas** | No se abordará la administración de nóminas y procesos laborales. |
| **Gestión especializada de transporte** | No se contempla desarrollar seguimiento de vehículos, rutas optimizadas o administración de flotas. |
| **Fijación completamente automática de precios** | No se delegarán decisiones de precios o descuentos excepcionales a reglas automáticas no aprobadas por Gerencia. |

Estas exclusiones delimitan la implementación inicial y podrán revisarse si cambian las necesidades de MIGAL mediante una decisión documentada.