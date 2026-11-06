# Especificación del flujo agentico de Activos y Mantenimiento

## 1. Propósito

Asistir y controlar la gestión de activos y mantenimiento de MIGAL. El agente valida la información, registra activos, programa mantenimientos, controla órdenes de trabajo, identifica riesgos y escala decisiones sensibles.

| Etapa | Actuación del agente |
|---|---|
| Registro del activo | Verifica código único, descripción, categoría, ubicación y estado. |
| Asignación | Registra responsable, área, ubicación y fecha de asignación. |
| Mantenimiento preventivo | Controla fechas, frecuencia, horas de uso o kilometraje programado. |
| Mantenimiento correctivo | Registra la falla, prioridad, diagnóstico y acción requerida. |
| Orden de trabajo | Verifica responsable, actividades, repuestos, costo y fechas. |
| Cierre | Comprueba evidencias, resultado, costo y cambio de estado del activo. |



## 2. Entradas

El agente recibe información técnica, operativa y económica de los activos y sus mantenimientos.

### Datos del proceso

| Entrada | Propósito | Formato |
|---|---|---|
| Activo | Identificar el bien administrado. | `string` / identificador |
| Código | Garantizar identificación única. | `string` |
| Categoría | Clasificar el activo. | `string` |
| Ubicación | Registrar dónde se encuentra. | `string` |
| Responsable | Identificar al usuario o área responsable. | `string` |
| Estado | Conocer la situación operativa del activo. | `ACTIVO/EN_MANTENIMIENTO/FUERA_DE_SERVICIO/BAJA` |
| Criticidad | Determinar prioridad y riesgo operativo. | `BAJA/MEDIA/ALTA/CRITICA` |
| Tipo de mantenimiento | Diferenciar mantenimiento preventivo o correctivo. | `PREVENTIVO/CORRECTIVO` |
| Falla | Describir el problema detectado. | `string` |
| Costo | Registrar el importe del mantenimiento. | `number` decimal |
| Evidencia | Sustentar la actividad realizada. | Lista de archivos o referencias |

### Registro de trazabilidad

```json
{
  "flujo": "ACTIVOS_MANTENIMIENTO",
  "evento": "REGISTRO|ASIGNACION|PREVENTIVO|CORRECTIVO|ORDEN_TRABAJO|CIERRE",
  "usuario": "string",
  "rol": "GER|VEN|ALM|CMP|FCO|SIS",
  "fecha_hora": "ISO-8601",
  "activo_id": "string",
  "orden_trabajo_id": "string",
  "datos": {}
}
```

| Campo | Definición |
|---|---|
| `flujo` | Identifica el proceso; debe ser `ACTIVOS_MANTENIMIENTO`. |
| `evento` | Etapa específica ejecutada. |
| `usuario` | Usuario que registra o actualiza la operación. |
| `rol` | Rol funcional del usuario. |
| `fecha_hora` | Fecha y hora del evento en formato ISO-8601. |
| `activo_id` | Identificador único del activo. |
| `orden_trabajo_id` | Identificador de la orden de mantenimiento. |
| `datos` | Información específica de la operación. |



## 3. Salidas

El agente genera una respuesta auditable y, si cuenta con permisos, actualiza el registro del activo o la orden de trabajo.

```json
{
  "resultado": "APROBADO|OBSERVADO|ESCALADO|RECHAZADO",
  "flujo": "ACTIVOS_MANTENIMIENTO",
  "activo_id": "string",
  "orden_trabajo_id": "string",
  "validaciones": [],
  "acciones": [],
  "responsable": "GER|ALM|FCO|SIS",
  "fecha_hora": "ISO-8601",
  "trazabilidad_id": "string"
}
```

| Salida | Definición |
|---|---|
| `resultado` | Estado final de la validación. |
| `validaciones` | Controles ejecutados y sus resultados. |
| `acciones` | Actualizaciones, asignaciones o notificaciones realizadas. |
| `responsable` | Rol encargado de continuar o aprobar la operación. |
| `trazabilidad_id` | Identificador único del registro de auditoría. |

El agente no aprueba bajas, inversiones extraordinarias ni gastos sensibles sin autorización humana.



## 4. Fuentes

- Registros de activos y bienes de MIGAL.
- Inventario y ubicaciones de Odoo.
- Órdenes de trabajo y mantenimientos registrados.
- Historial de fallas, reparaciones, repuestos y costos.
- Datos de responsables y áreas usuarias.
- `arquitectura/seguridad/modelo-autorizacion.md`.
- `arquitectura/seguridad/analisis-roles-funcionales.md`.
- Evidencias documentales, fotografías, comprobantes y reportes técnicos.



## 5. Herramientas

| Herramienta | Uso en Activos y Mantenimiento |
|---|---|
| Inventario de Odoo | Registrar ubicación, movimientos y estado físico del activo. |
| Mantenimiento de Odoo | Crear planes preventivos y órdenes de trabajo. |
| Contactos de Odoo | Consultar responsables, áreas y proveedores. |
| Facturación/Contabilidad | Registrar costos, facturas y pagos de mantenimiento. |
| Registro de auditoría | Conservar usuario, fechas, cambios, evidencias y decisiones. |
| Almacenamiento documental | Asociar fotografías, informes y comprobantes a la orden. |



## 6. Reglas operativas

1. Todo activo debe tener código único, categoría, ubicación, responsable y estado.
2. No se permite duplicar el código de un activo.
3. Todo mantenimiento debe clasificarse como `PREVENTIVO` o `CORRECTIVO`.
4. El mantenimiento preventivo se programa por fecha, horas de uso o kilometraje.
5. Una falla crítica genera una orden de trabajo inmediata.
6. La orden debe incluir diagnóstico, responsable, actividades, repuestos y costo estimado.
7. El activo cambia a `EN_MANTENIMIENTO` mientras exista una orden abierta.
8. El cierre exige registrar trabajo realizado, costo, evidencia y resultado.
9. Un activo no puede pasar a `ACTIVO` si la orden no tiene cierre validado.
10. Todo cambio de estado debe registrar usuario, fecha, motivo y documento relacionado.



## 7. Permisos

| Rol | Significado | Permisos en Activos y Mantenimiento |
|---|---|---|
| **GER** | Gerencia | Supervisar y autorizar bajas, gastos extraordinarios y decisiones sensibles. |
| **VEN** | Atención y Ventas | Consultar activos disponibles cuando estén relacionados con una operación comercial. |
| **ALM** | Almacén y Despacho | Registrar activos, ubicaciones, estados, incidencias y ejecutar mantenimientos operativos. |
| **CMP** | Compras y Abastecimiento | Consultar necesidades y gestionar proveedores o cotizaciones de servicios y repuestos. |
| **FCO** | Facturación, Contabilidad y Cobros | Registrar y controlar facturas, costos y pagos de mantenimiento. |
| **SIS** | Administración del Sistema | Administrar usuarios, permisos y configuración técnica, sin autorizar gastos ni bajas. |

Se aplican los principios de mínimo privilegio, segregación de funciones y trazabilidad.



## 8. Responsable Humano

| Responsabilidad | Rol responsable |
|---|---|
| Supervisión y autorización de excepciones | **GER — Gerencia** |
| Registro, ubicación y operación del activo | **ALM — Almacén y Despacho** |
| Gestión de proveedores y repuestos | **CMP — Compras y Abastecimiento** |
| Control de costos, facturas y pagos | **FCO — Facturación, Contabilidad y Cobros** |
| Configuración técnica y permisos | **SIS — Administración del Sistema** |
| Consulta relacionada con ventas | **VEN — Atención y Ventas** |

El responsable humano valida las excepciones, autoriza las operaciones restringidas y asume la decisión final.



## 9. Escalamiento

El agente genera el estado `ESCALADO` cuando:

- El activo tiene criticidad `ALTA` o `CRITICA`.
- Existe riesgo de seguridad, incendio, electricidad o lesiones.
- El activo permanece fuera de servicio por más de **4 horas**.
- El costo estimado supera el presupuesto autorizado.
- Se requiere una baja, sustitución o adquisición extraordinaria.
- Se detectan diferencias entre el activo físico y el registro.
- Existen datos incompletos, duplicidad o falta de evidencia.
- El agente no puede validar la operación con fuentes confiables.

La escalada debe registrar:

```json
{
  "activo_id": "string",
  "orden_trabajo_id": "string",
  "motivo": "string",
  "evidencia": [],
  "responsable": "GER|ALM|CMP|FCO|SIS",
  "fecha_limite": "ISO-8601",
  "estado": "PENDIENTE|RESUELTO"
}
```

GER resuelve las excepciones operativas, económicas y de baja. ALM gestiona las incidencias del activo, CMP atiende proveedores y repuestos, FCO controla los costos y SIS atiende únicamente incidentes técnicos o de permisos.
