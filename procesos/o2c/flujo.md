# Especificación del flujo agentico O2C

## 1. Propósito

Asistir y controlar el proceso **Order to Cash (O2C)** de MIGAL en Odoo 18 Community. El agente valida información, aplica reglas, identifica excepciones y escala decisiones sensibles.

| Etapa | Actuación del agente |
|---|---|
| Cotización | Valida cliente, productos, precios vigentes y condiciones comerciales. |
| Pedido | Comprueba que la cotización esté completa y que el cliente sea válido. |
| Inventario | Consulta disponibilidad y verifica que exista stock suficiente. |
| Entrega | Confirma que el pedido esté aprobado antes de preparar y despachar. |
| Facturación | Verifica la información necesaria para generar la factura. |
| Cobro | Consulta el estado del pago, saldo pendiente y vencimientos. |



## 2. Entradas

El agente recibe datos comerciales, logísticos y financieros relacionados con el cliente y el pedido.

### Datos del proceso

| Entrada | Propósito | Formato |
|---|---|---|
| Cliente | Identificar al comprador y validar sus datos. | `string` / identificador Odoo |
| Productos | Identificar los artículos solicitados. | Lista de objetos |
| Cantidades | Determinar unidades requeridas. | `number` positivo |
| Precios | Calcular el importe de la operación. | `number` decimal |
| Descuento | Validar si la condición comercial está autorizada. | Porcentaje decimal |
| Stock | Confirmar disponibilidad para atender el pedido. | `number` entero o decimal |
| Entrega | Registrar fecha, ubicación y estado del despacho. | Objeto estructurado |
| Pago | Registrar importe, método, estado y vencimiento. | Objeto estructurado |

### Registro de trazabilidad

```json
{
  "flujo": "O2C",
  "evento": "COTIZACION|PEDIDO|INVENTARIO|ENTREGA|FACTURACION|COBRO",
  "usuario": "string",
  "rol": "GER|VEN|ALM|FCO|SIS",
  "fecha_hora": "ISO-8601",
  "documento_id": "string",
  "datos": {}
}
```

| Campo | Definición |
|---|---|
| `flujo` | Identifica el proceso ejecutado; debe ser `O2C`. |
| `evento` | Etapa específica del proceso. |
| `usuario` | Usuario que origina o registra la operación. |
| `rol` | Rol funcional del usuario. |
| `fecha_hora` | Fecha y hora del evento en formato ISO-8601. |
| `documento_id` | Identificador de la cotización, pedido, entrega, factura o cobro. |
| `datos` | Información específica de la operación. |



## 3. Salidas

El agente genera una respuesta auditable y, si cuenta con permisos, actualiza el registro correspondiente en Odoo.

```json
{
  "resultado": "APROBADO|OBSERVADO|ESCALADO|RECHAZADO",
  "flujo": "O2C",
  "documento_id": "string",
  "validaciones": [],
  "acciones": [],
  "responsable": "GER|VEN|ALM|FCO|SIS",
  "fecha_hora": "ISO-8601",
  "trazabilidad_id": "string"
}
```

| Salida | Definición |
|---|---|
| `resultado` | Estado final de la validación. |
| `validaciones` | Controles ejecutados y sus resultados. |
| `acciones` | Actualizaciones o notificaciones realizadas. |
| `responsable` | Rol encargado de continuar o aprobar la operación. |
| `trazabilidad_id` | Identificador único del registro de auditoría. |

El agente no modifica precios maestros, concede créditos ni aprueba ajustes financieros o de inventario.



## 4. Fuentes

- Odoo 18 Community:
  - CRM y Contactos.
  - Ventas.
  - Inventario.
  - Punto de Venta.
  - Facturación y Contabilidad.
- Datos maestros de clientes, productos, precios y existencias.
- Historial de pedidos, entregas, facturas y cobros.
- `arquitectura/alcance.md`.
- `arquitectura/seguridad/modelo-autorizacion.md`.
- `arquitectura/seguridad/analisis-roles-funcionales.md`.
- KeyFacil para la emisión de comprobantes electrónicos.
- WhatsApp y llamadas como fuentes externas registradas manualmente.



## 5. Herramientas

| Herramienta | Uso dentro de O2C |
|---|---|
| CRM de Odoo | Consultar oportunidades y antecedentes comerciales. |
| Ventas de Odoo | Crear y consultar cotizaciones y pedidos. |
| Inventario de Odoo | Consultar stock, reservas, transferencias y despachos. |
| Punto de Venta | Registrar ventas y cobros ordinarios de mostrador. |
| Facturación/Contabilidad | Gestionar facturas, saldos, cobros y estados de cuenta. |
| KeyFacil | Emitir comprobantes electrónicos. |
| Registro de auditoría | Conservar usuario, fecha, documento, validaciones y decisiones. |

La integración automática con KeyFacil y WhatsApp no se considera habilitada inicialmente.



## 6. Reglas operativas

1. **Cotización:** VEN utiliza únicamente precios y condiciones vigentes.
2. **Pedido:** debe existir un cliente válido, productos registrados y cantidades definidas.
3. **Disponibilidad:** el agente verifica stock antes de confirmar la atención del pedido.
4. **Descuentos:** todo precio especial o descuento negociado requiere autorización de GER.
5. **Despacho:** ALM solo prepara y entrega pedidos confirmados.
6. **Facturación:** FCO valida la información del pedido antes de registrar la factura.
7. **Cobro:** FCO controla el importe recibido, método de pago, saldo y vencimiento.
8. **Emisión fiscal:** el comprobante se genera mediante KeyFacil según el procedimiento aprobado.
9. **Trazabilidad:** cada acción debe registrar usuario, fecha, documento, resultado y motivo.
10. **Datos incompletos:** la operación queda en estado `OBSERVADO` hasta completar la información.



## 7. Permisos

| Rol | Permisos en O2C |
|---|---|
| **GER** | Supervisar y autorizar descuentos especiales, créditos, anulaciones y decisiones sensibles. |
| **VEN** | Gestionar clientes, oportunidades, cotizaciones, pedidos y ventas ordinarias. |
| **ALM** | Consultar pedidos y gestionar preparación, existencias y entregas. |
| **FCO** | Gestionar facturas, cobros, saldos y conciliaciones autorizadas. |
| **SIS** | Administrar usuarios, grupos y configuración técnica, sin autorizar operaciones comerciales o financieras. |

Se aplican los principios de mínimo privilegio, segregación de funciones y trazabilidad.



## 8. Responsable Humano

| Responsabilidad | Rol responsable |
|---|---|
| Supervisión y autorización de excepciones | **GER — Gerencia** |
| Gestión comercial y preparación de pedidos | **VEN — Atención y Ventas** |
| Control de inventario y despacho | **ALM — Almacén y Despacho** |
| Facturación, cobros y saldos | **FCO — Facturación, Contabilidad y Cobros** |
| Configuración técnica y permisos | **SIS — Administración del Sistema** |

El responsable humano valida las excepciones, autoriza las operaciones restringidas y asume la decisión final.



## 9. Escalamiento

El agente genera el estado `ESCALADO` cuando:

- Se solicita un descuento o precio especial.
- Se requiere otorgar o modificar crédito.
- Existe una anulación o ajuste financiero.
- El inventario presenta una diferencia extraordinaria.
- El pago permanece vencido por más de **7 días**.
- Existen datos incompletos, duplicidad documental o inconsistencias.
- El agente no puede validar la operación con fuentes confiables.
- Se detecta un posible fraude o incumplimiento de permisos.

La escalada debe registrar:

```json
{
  "documento_id": "string",
  "motivo": "string",
  "evidencia": [],
  "responsable": "GER|SIS",
  "fecha_limite": "ISO-8601",
  "estado": "PENDIENTE|RESUELTO"
}
```

GER resuelve las excepciones comerciales, operativas y financieras. SIS atiende únicamente incidentes técnicos o relacionados con permisos.
