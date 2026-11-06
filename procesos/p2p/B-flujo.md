# Especificación del flujo agentico P2P

## 1. Propósito

Asistir y controlar el proceso **Procure to Pay (P2P)** de MIGAL en Odoo 18 Community. El agente valida necesidades de compra, proveedores, órdenes, recepciones, facturas y pagos, identificando excepciones y escalando decisiones sensibles.

| Etapa | Actuación del agente |
|---|---|
| Necesidad de compra | Verifica producto, cantidad, motivo y fecha requerida. |
| Proveedor | Valida datos del proveedor y condiciones comerciales. |
| Cotización | Registra y compara precios, cantidades, plazos y condiciones. |
| Orden de compra | Comprueba que la orden esté completa antes de solicitar autorización. |
| Recepción | Contrasta los productos recibidos con la orden aprobada. |
| Facturación | Verifica la factura del proveedor contra la orden y recepción. |
| Pago | Consulta la obligación, vencimiento, importe y estado del pago. |



## 2. Entradas

El agente recibe información de abastecimiento, recepción y obligaciones con proveedores.

### Datos del proceso

| Entrada | Propósito | Formato |
|---|---|---|
| Proveedor | Identificar a la empresa proveedora. | `string` / identificador Odoo |
| Productos | Identificar los artículos solicitados. | Lista de objetos |
| Cantidades | Determinar unidades requeridas. | `number` positivo |
| Precios | Comparar y validar el costo de adquisición. | `number` decimal |
| Cotizaciones | Evaluar ofertas recibidas. | Lista de objetos |
| Fecha requerida | Determinar el plazo de abastecimiento. | `YYYY-MM-DD` |
| Orden de compra | Formalizar la adquisición autorizada. | Identificador Odoo |
| Recepción | Registrar cantidades y condiciones recibidas. | Objeto estructurado |
| Factura | Registrar la obligación con el proveedor. | Objeto estructurado |
| Pago | Registrar importe, método, estado y vencimiento. | Objeto estructurado |

### Registro de trazabilidad

```json
{
  "flujo": "P2P",
  "evento": "NECESIDAD|PROVEEDOR|COTIZACION|ORDEN_COMPRA|RECEPCION|FACTURACION|PAGO",
  "usuario": "string",
  "rol": "GER|ALM|CMP|FCO|SIS",
  "fecha_hora": "ISO-8601",
  "documento_id": "string",
  "datos": {}
}
```

| Campo | Definición |
|---|---|
| `flujo` | Identifica el proceso ejecutado; debe ser `P2P`. |
| `evento` | Etapa específica del proceso. |
| `usuario` | Usuario que origina o registra la operación. |
| `rol` | Rol funcional del usuario. |
| `fecha_hora` | Fecha y hora del evento en formato ISO-8601. |
| `documento_id` | Identificador de la solicitud, cotización, orden, recepción, factura o pago. |
| `datos` | Información específica de la operación. |


## 3. Salidas

El agente genera una respuesta auditable y, si cuenta con permisos, actualiza el registro correspondiente en Odoo.

```json
{
  "resultado": "APROBADO|OBSERVADO|ESCALADO|RECHAZADO",
  "flujo": "P2P",
  "documento_id": "string",
  "validaciones": [],
  "acciones": [],
  "responsable": "GER|ALM|CMP|FCO|SIS",
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

El agente no confirma órdenes de compra, aprueba pagos ni modifica proveedores sin autorización correspondiente.



## 4. Fuentes

- Odoo 18 Community:
  - Contactos.
  - Compras.
  - Inventario.
  - Facturación y Contabilidad.
- Datos maestros de proveedores, productos y precios.
- Solicitudes, cotizaciones y órdenes de compra.
- Registros de recepción y movimientos de inventario.
- Facturas, cuentas por pagar y pagos.
- `arquitectura/alcance.md`.
- `arquitectura/seguridad/modelo-autorizacion.md`.
- `arquitectura/seguridad/analisis-roles-funcionales.md`.
- Documentos y cotizaciones proporcionados por proveedores.



## 5. Herramientas

| Herramienta | Uso dentro de P2P |
|---|---|
| Contactos de Odoo | Consultar y gestionar datos de proveedores. |
| Compras de Odoo | Registrar cotizaciones y preparar órdenes de compra. |
| Inventario de Odoo | Registrar recepciones, cantidades y diferencias. |
| Facturación/Contabilidad | Gestionar facturas, cuentas por pagar y pagos. |
| Registro de auditoría | Conservar usuarios, fechas, documentos, validaciones y decisiones. |
| Almacenamiento documental | Asociar cotizaciones, facturas, guías y evidencias de recepción. |

---

## 6. Reglas operativas

1. **Necesidad:** debe indicar producto, cantidad, motivo y fecha requerida.
2. **Proveedor:** debe existir un registro válido y no duplicado.
3. **Cotización:** CMP registra y compara las ofertas disponibles.
4. **Orden:** debe incluir proveedor, productos, cantidades, precios y condiciones.
5. **Autorización:** GER confirma toda compra que comprometa a MIGAL.
6. **Recepción:** ALM recibe contra la orden de compra aprobada.
7. **Diferencias:** las cantidades y precios recibidos se comparan con la orden.
8. **Facturación:** FCO valida la factura contra la orden y la recepción.
9. **Pago:** FCO controla importe, vencimiento, estado y cuenta por pagar.
10. **Trazabilidad:** cada acción debe registrar usuario, fecha, documento, resultado y motivo.
11. **Datos incompletos:** la operación queda en estado `OBSERVADO` hasta completar la información.
12. **Separación de funciones:** preparar una compra no equivale a autorizarla.

## 7. Permisos

| Rol | Significado | Permisos en P2P |
|---|---|---|
| **GER** | Gerencia | Supervisar y autorizar órdenes de compra, excepciones y decisiones sensibles. |
| **VEN** | Atención y Ventas | Consultar la demanda o disponibilidad relacionada con ventas. |
| **ALM** | Almacén y Despacho | Registrar recepciones, cantidades recibidas y diferencias físicas. |
| **CMP** | Compras y Abastecimiento | Gestionar proveedores, cotizaciones y preparar órdenes de compra. |
| **FCO** | Facturación, Contabilidad y Cobros | Gestionar facturas de proveedores, cuentas por pagar y pagos autorizados. |
| **SIS** | Administración del Sistema | Administrar usuarios, grupos y configuración técnica, sin autorizar compras o pagos. |

Se aplican los principios de mínimo privilegio, segregación de funciones y trazabilidad.

## 8. Responsable Humano

| Responsabilidad | Rol responsable |
|---|---|
| Supervisión y autorización de compras | **GER — Gerencia** |
| Gestión de proveedores y cotizaciones | **CMP — Compras y Abastecimiento** |
| Recepción y verificación física | **ALM — Almacén y Despacho** |
| Facturas, cuentas por pagar y pagos | **FCO — Facturación, Contabilidad y Cobros** |
| Consulta de demanda relacionada con ventas | **VEN — Atención y Ventas** |
| Configuración técnica y permisos | **SIS — Administración del Sistema** |

El responsable humano valida las excepciones, autoriza las operaciones restringidas y asume la decisión final.

## 9. Escalamiento

El agente genera el estado `ESCALADO` cuando:

- La compra requiere autorización de GER.
- La diferencia de cantidad o precio supera el **10 %** respecto de la orden aprobada.
- La compra supera el monto autorizado o el presupuesto disponible.
- El proveedor presenta datos incompletos, duplicados o inconsistentes.
- La recepción no coincide con la orden de compra.
- La factura no coincide con la orden o la recepción.
- Una cuenta por pagar permanece vencida por más de **7 días**.
- Se detecta una compra duplicada, posible fraude o incumplimiento de permisos.
- El agente no puede validar la operación con fuentes confiables.

La escalada debe registrar:

```json
{
  "documento_id": "string",
  "motivo": "string",
  "evidencia": [],
  "responsable": "GER|CMP|ALM|FCO|SIS",
  "fecha_limite": "ISO-8601",
  "estado": "PENDIENTE|RESUELTO"
}
```

GER resuelve las excepciones de autorización y decisiones sensibles. CMP atiende proveedores y cotizaciones, ALM las diferencias de recepción, FCO las facturas y pagos, y SIS únicamente los incidentes técnicos o de permisos.
