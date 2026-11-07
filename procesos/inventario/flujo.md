# Flujo de gestión de inventario

**Estado:** proceso funcional propuesto. El inventario conecta [Compras y recepción de P2P](../p2p/flujo.md) con [ventas y entregas de O2C](../o2c/flujo.md); no sustituye esos procesos. El [alcance](../../arquitectura/alcance.md) contempla tienda, almacenes, recepciones, traslados, salidas, conteos y ajustes justificados. La configuración de ubicaciones, reservas y movimientos en Odoo 19 debe comprobarse en una instancia autorizada ([módulos y dependencias](../../arquitectura/modulos-y-dependencias.md)).

## 1. Conceptos y responsabilidades

| Concepto | Significado funcional |
|---|---|
| Existencia física | Cantidad material observada en tienda o almacén. Puede diferir del registro. |
| Disponibilidad consultada | Información utilizada para evaluar una venta o compra; no aparta unidades para una orden. |
| Reserva | Asignación de unidades disponibles a una orden de venta confirmada; se propone, pero su comportamiento en Odoo 19 está pendiente de prueba. No se reservan unidades aún no abastecidas. |
| Recepción | Entrada física; su validación documenta cantidad apta y diferencias. No se infiere de la orden de compra. |
| Traslado | Cambio físico entre ubicaciones de MIGAL, sin alterar por ello la cantidad total de la empresa. |
| Ajuste | Corrección justificada de una diferencia; se distingue de compra, venta o traslado. |
| Despacho | Salida de mercancía hacia el cliente o transportista. No acredita recepción conforme. |
| Entrega | Recepción física por cliente o persona autorizada, con conformidad o incidencia documentada. |

**ALM** registra operaciones ordinarias, conteos, recepciones, traslados y salidas. **VEN** consulta disponibilidad y comunica necesidades comerciales; **CMP** gestiona abastecimiento; **GER** autoriza ajustes extraordinarios; **SIS** configura permisos técnicos, sin asumir decisiones de negocio. Esta distribución procede del [modelo de autorización](../../arquitectura/seguridad/modelo-autorizacion.md). El criterio que distingue ajustes ordinarios de extraordinarios **no está definido por MIGAL**: no se presupone que cualquier diferencia pueda corregirse sin revisión.

## 2. Entradas, salidas y flujo

| Situación | Entrada y actividad | Evidencia de salida | Referencia |
|---|---|---|---|
| Consulta para cotizar o evaluar | VEN consulta información por producto y ubicación; ALM verifica la realidad física cuando exista duda. | Disponibilidad informada con incertidumbre identificada, sin crear reserva. | RN-015; [CRM](../comercial-crm/flujo-comercial.md). |
| Orden confirmada | Se propone reservar solo unidades efectivamente disponibles; las cantidades pendientes de abastecimiento permanecen diferenciadas. | Referencia de orden y, si se valida técnicamente, reserva efectiva con cantidad y ubicación. | RN-015; EV-018. |
| Compra recibida | ALM cuenta y examina los productos que llegan del proveedor, separando cantidad apta, dañada y pendiente. | Productos recibidos (EV-026) y recepción validada con diferencias (EV-027). | RN-013; [P2P](../p2p/flujo.md). |
| Traslado interno | ALM registra origen, destino, producto, unidad, cantidad y fecha del movimiento físico. | Traslado completado (EV-030) y existencia por ubicación actualizada o pendiente de conciliación. | RN-016. |
| Conteo y diferencia | ALM compara registro y existencia física, identifica causa y documenta la discrepancia antes de corregir. | Diferencia identificada (EV-028), conteo y decisión de tratamiento. | RN-016/RN-017, EXC-004. |
| Ajuste justificado | ALM realiza un ajuste ordinario solo una vez definido ese tipo de caso; GER autoriza los extraordinarios. | Causa, cantidades anteriores y nuevas, responsable y autorización cuando corresponda; EV-029/EV-056 describen correcciones autorizadas en el [catálogo](../catalogo-eventos.md), y su aplicación a ajustes ordinarios queda pendiente de definición. | RN-017, CT-009. |
| Preparación y despacho | ALM prepara la cantidad realmente disponible por viaje y registra la salida efectiva, no la totalidad prometida cuando difiere. | Preparación (EV-033), despacho (EV-034), cantidades pendientes y documentación de traslado cuando corresponda. | RN-018; [O2C](../o2c/flujo.md). |
| Entrega o incidencia | Se documenta la recepción del cliente separada de la salida del almacén; los faltantes o daños permanecen abiertos. | Entrega (EV-035), incidencia (EV-036) y regularización posterior si procede (EV-037). | RN-018, EXC-005. |

Los eventos citados describen hechos de negocio, no botones o estados nativos de Odoo. La salida por venta de mostrador y su momento de descuento de stock requieren prueba específica; el registro en POS no demuestra por sí solo un movimiento correcto o una entrega externa.

## 3. Excepciones y controles

- **Recepción parcial o dañada:** registrar cantidad apta real y mantener visible la diferencia; no copiar como recibida la cantidad comprada ni usar un ajuste para ocultar un incumplimiento del proveedor (RN-013, EXC-003).
- **Stock registrado que no coincide con el físico:** suspender la promesa basada en la cantidad dudosa, verificar y clasificar la corrección; GER interviene si el ajuste es extraordinario (RN-017, EXC-004).
- **Faltante en una orden:** consultar disponibilidad y comunicar la necesidad a [P2P](../p2p/flujo.md); una compra futura no equivale a una reserva ni a una entrega comprometida.
- **Salida parcial o entrega no conforme:** registrar cantidades realmente despachadas, recibidas y pendientes por separado, con responsable y siguiente acción (RN-018, EXC-005).
- **Pérdida o deterioro:** registrar el hecho (EV-031), aislar material no apto y determinar tratamiento; no clasificarlo como venta ni ejecutar un ajuste extraordinario sin GER.

## 4. Validaciones pendientes

MIGAL debe definir qué causas o límites distinguen un ajuste ordinario de uno extraordinario. Deben verificarse la representación de tienda y dos almacenes como almacenes o ubicaciones, el stock por ubicación, la reserva real, la relación con órdenes de venta, las recepciones parciales, el comportamiento de POS y los permisos de ALM/GER en Odoo 19. Los [controles CT-008 y CT-009](../catalogo-reglas.md) especifican la evidencia esperada; no acreditan una prueba ejecutada.
