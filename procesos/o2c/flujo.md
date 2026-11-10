# Flujo Order to Cash (O2C)

**Estado:** proceso funcional propuesto. O2C comprende la atención comercial, la orden de venta, la entrega, el comprobante y el cobro. Su entrada CRM se detalla en el [flujo comercial](../comercial-crm/flujo-comercial.md); este documento desarrolla la ejecución posterior a la evaluación interna y la venta inmediata de mostrador. La frontera vigente es [ADR-004](../../arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md) e [INT-01](../../arquitectura/integraciones/INT-01-CRM-ERP.md). El [alcance](../../arquitectura/alcance.md) conserva KeyFacil para la emisión fiscal.

## 1. Entradas, salidas y responsables

| Recorrido | Entrada | Salida funcional |
|---|---|---|
| Venta con seguimiento | Cotización vigente aceptada por el cliente; solicitud interna de orden de venta y evaluación operativa. | Orden confirmada solo tras solicitud aceptada, o retorno comercial con respuesta condicionada/rechazada. Después: entrega, comprobante, cobro y conciliación o asuntos abiertos. |
| Venta inmediata de mostrador | Necesidad atendible directamente en tienda. | Venta POS (EV-017), entrega inmediata cuando corresponda, comprobante externo y cobro conciliado. No se exige el recorrido completo de CRM. |

**VEN** gestiona la atención, la solicitud interna y el cobro ordinario de mostrador; **ALM** verifica existencias, prepara y registra despacho y entrega; **CMP** aporta información de abastecimiento cuando falta stock; **FCO** registra referencias de comprobantes, obligaciones, cobros y conciliaciones; **GER** decide descuentos, créditos, excepciones y cancelaciones de órdenes confirmadas. **SIS** valida la configuración técnica. La asignación del evaluador ordinario de la solicitud y de quien autoriza su confirmación sigue pendiente en INT-01; no se atribuye a un rol por inferencia.

## 2. Venta con orden de venta

| Momento | Actividad | Evidencia y control |
|---|---|---|
| Aceptación comercial | VEN registra la aceptación de una cotización aún vigente. Si cambian las condiciones aceptadas, aplica [RN-003](../catalogo-reglas.md) (conformidad con las nuevas condiciones y, si corresponde, nueva solicitud vinculada a la anterior). | Cotización y conformidad identificables; EV-006, RN-002/RN-003. |
| Solicitud interna | VEN presenta la **solicitud de orden de venta** a las funciones de abastecimiento y despacho o transporte. Es un documento de evaluación interna, no una orden confirmada ni un documento estándar acreditado de Odoo. | Solicitud, referencia a cotización, fecha, condiciones y responsable; EV-009, RN-005. |
| Evaluación y respuesta | Se comprueban disponibilidad, suministro, autorizaciones y viabilidad de despacho. La respuesta es aceptada, condicionada o rechazada. Solo la aceptada habilita confirmar la orden en el diseño vigente; las otras dos retornan a CRM con motivo. | Evaluaciones y decisión documentadas; RN-006, EXC-001, [INT-01](../../arquitectura/integraciones/INT-01-CRM-ERP.md). |
| Confirmación | El responsable aún por designar confirma la orden de venta después de la respuesta aceptada. VEN puede marcar la oportunidad «Ganada»; el mecanismo y permisos efectivos se probarán en Odoo 19. | Orden confirmada (EV-018), vínculo con solicitud y cotización; RN-008. |
| Disponibilidad y preparación | Se consulta la existencia por ubicación. Se propone reservar solo unidades disponibles para una orden confirmada; ALM prepara cantidades reales por viaje. Un faltante no se registra como reserva ficticia. | Disponibilidad, reserva si fue validada, preparación (EV-033), cantidades pendientes; RN-015. |
| Despacho y entrega | ALM registra cada salida efectiva y separadamente la recepción o incidencia del cliente. La documentación de traslado se determina según la operación. | Despacho (EV-034), entrega (EV-035) o incidencia (EV-036), receptor y saldos; RN-018. |
| Comprobante | El emisor autorizado utiliza **KeyFacil** conforme al procedimiento aplicable; FCO registra la referencia y concilia con la venta. El momento de emisión respecto al pago o entrega continúa pendiente de validación. | Comprobante (EV-038), tipo, serie, número, importe y diferencias; RN-009. |
| Cobro | VEN puede cobrar en mostrador según sus permisos; FCO registra, aplica y concilia cobros y saldos de la operación. GER decide nuevas condiciones de crédito. Un pago puede ocurrir antes o después de la entrega según condiciones autorizadas. | Pago recibido (EV-042), aplicado si corresponde (EV-043), soporte y saldo; RN-004/RN-010. |
| Seguimiento y cierre | Revisar entregas, comprobantes, cobros e incidencias. Mantener seguimiento funcional mientras haya obligaciones abiertas; el cierre no se infiere de un estado técnico de Odoo. | Referencias conciliadas o pendientes y responsable de siguiente acción; RN-010, CT-005. |

El orden de las filas facilita la lectura, pero **comprobante y cobro no son pasos necesariamente consecutivos a la entrega**. No se establece una regla tributaria sobre cuándo emitir en KeyFacil. La práctica observada de confirmar una orden de venta con abastecimiento pendiente para cuatro familias y su diferencia con INT-01 se documenta únicamente en el [flujo comercial](../comercial-crm/flujo-comercial.md); no se convierte aquí en una excepción TO-BE tácita.

## 3. Venta inmediata de mostrador

VEN registra la venta en Punto de Venta y realiza el cobro ordinario conforme a permisos habilitados. La entrega física, el eventual movimiento de stock, la emisión del comprobante en KeyFacil y la conciliación por FCO conservan evidencias diferenciadas. El ticket POS no se presume comprobante fiscal. El momento y mecanismo del descuento de stock y de los asientos correspondientes requieren prueba en Odoo 19 ([inventario](../inventario/flujo.md), [módulos](../../arquitectura/modulos-y-dependencias.md)). Esta ruta no exige crear lead, oportunidad, cotización ni solicitud de orden de venta para una venta inmediata (RN-007).

## 4. Excepciones y continuidad

| Situación | Tratamiento |
|---|---|
| Cotización rechazada por el cliente | No presentar solicitud interna. Preparar nueva cotización solo si se negocia otra propuesta. |
| Solicitud de orden de venta condicionada o rechazada | Registrar motivo y devolver a CRM; no confirmar automáticamente. Si cambian condiciones, obtener conformidad con la nueva propuesta. |
| Stock registrado distinto del físico | ALM verifica; no prometer mercancía dudosa ni convertir consulta en reserva. Una compra iniciada en [P2P](../p2p/flujo.md) no acredita disponibilidad actual. |
| Entrega parcial o no conforme | Registrar cantidades despachadas y recibidas, diferencia, receptor y acción pendiente; no cerrar como entrega completa (EXC-005). |
| Cobro parcial, vencido o sin soporte | Conservar saldo y seguimiento; no equiparar promesa de pago con cobro recibido. GER decide cambios de crédito. |
| Comprobante que no coincide con la venta | Mantener diferencia visible y conciliar con KeyFacil; no alterar la cotización para ocultarla. |
| Cancelación de orden confirmada | GER decide y se conservan efectos sobre reserva, salida, entrega, comprobante y pagos (EXC-006). |
| Reclamo posterior | Registrar la operación de origen y su tratamiento inicial; un flujo completo de devoluciones queda para documentación posterior (RN-021). |

## 5. Verificaciones pendientes

Se deben definir el evaluador y confirmador ordinarios de la solicitud, las condiciones de programación y entrega, el procedimiento fiscal y momento de emisión en KeyFacil, la conciliación de pagos y el tratamiento de entregas no conformes. En Odoo 19 deben probarse la representación de la solicitud interna, el control de confirmación, reservas, entregas parciales, POS, permisos e historial. El [catálogo de reglas](../catalogo-reglas.md) centraliza los controles propuestos; el [catálogo de eventos](../catalogo-eventos.md) conserva los códigos canónicos y las equivalencias ambiguas de INT-01 permanecen pendientes.
