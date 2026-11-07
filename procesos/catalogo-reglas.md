# Catálogo de reglas y controles de negocio

Este catálogo centraliza las reglas aplicables al [flujo comercial](comercial-crm/flujo-comercial.md), [O2C](o2c/flujo.md), [P2P](p2p/flujo.md) e [inventario](inventario/flujo.md). Los códigos `RN`, `CT` y `EXC` se asignan aquí por significado; no representan funciones configuradas ni pruebas realizadas en Odoo. Los códigos `EV` pertenecen exclusivamente al [catálogo de eventos](catalogo-eventos.md).

## 1. Lectura y autoridad

**Decisión vigente** indica un criterio respaldado por el [alcance](../arquitectura/alcance.md), los ADR, [INT-01](../arquitectura/integraciones/INT-01-CRM-ERP.md) o el [modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md). **Propuesta** requiere validación empresarial; **pendiente de definición** carece todavía de un límite operativo suficiente. Incluso una decisión vigente puede requerir configuración y prueba técnica. GER valida las políticas empresariales; VEN, ALM, CMP y FCO aportan la evaluación de sus procesos, y SIS comprueba la implementación técnica sin aprobar decisiones funcionales.

Una **solicitud de orden de venta condicionada** vuelve a CRM conforme a INT-01 y no habilita la confirmación en el proceso propuesto. La confirmación con abastecimiento pendiente observada para fierro, agregados, ladrillos y cemento se registra en el [flujo comercial](comercial-crm/flujo-comercial.md) como práctica actual declarada por el equipo; no modifica esta regla arquitectónica.

## 2. Reglas

| ID | Ámbito y regla | Fundamento | Responsable funcional | Estado |
|---|---|---|---|---|
| RN-001 | En ventas que requieren seguimiento, VEN registra la necesidad, el contacto y la próxima actividad; el carácter obligatorio de esta última debe validarse. | [ADR-006](../arquitectura/decisiones/ADR-006-adopcion-crm-odoo.md) | VEN | Propuesta |
| RN-002 | Una cotización solo puede aceptarse bajo las condiciones que continúen vigentes; no se presume una duración universal. | [Fuentes y vacíos](../fuentes/supuestos-y-vacios.md), EV-006/EV-008 | VEN; GER para condiciones excepcionales | Propuesta pendiente de política de vigencia |
| RN-003 | Si cambian productos, cantidad, precio o entrega después de la aceptación, se conserva el historial y se registra la conformidad del cliente con las nuevas condiciones. Si la solicitud interna ya fue presentada, se conserva la anterior y se presenta una nueva tras la renegociación; si aún no se presentó, se presenta la primera con las condiciones actualizadas. | [INT-01](../arquitectura/integraciones/INT-01-CRM-ERP.md), EV-005/EV-006 | VEN; GER si hay excepción | Propuesta funcional |
| RN-004 | Descuentos especiales, condiciones de crédito y cambios de precios maestros requieren decisión de GER; VEN no recibe un porcentaje autónomo de descuento. | [Modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md) | GER | Decisión vigente |
| RN-005 | VEN presenta internamente la solicitud de orden de venta después de la aceptación de una cotización vigente. La solicitud conserva referencias y condiciones aceptadas y no equivale a una orden confirmada. | [ADR-004](../arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md), INT-01 | VEN | Presentación de la solicitud: decisión vigente; política de vigencia y mecanismo técnico pendientes |
| RN-006 | Solo una solicitud aceptada habilita la confirmación de la orden de venta; una condicionada o rechazada retorna a CRM con motivo. La equivalencia de estos resultados con EV-014 permanece abierta. | INT-01 | Responsable de evaluación por designar; GER en excepciones | Decisión vigente; responsables y mecanismo pendientes |
| RN-007 | La venta inmediata de mostrador puede seguir el recorrido POS sin exigir etapas de CRM ni una cotización previa. VEN realiza el cobro ordinario; FCO revisa y concilia. | [Alcance](../arquitectura/alcance.md), modelo de autorización, EV-017 | VEN/FCO | Decisión de diseño; operación técnica pendiente de prueba |
| RN-008 | La oportunidad comercial se marca «Ganada» al confirmarse la orden de venta, no al aceptar una cotización; la representación en Odoo CRM debe validarse. | ADR-004, INT-01 | VEN | Propuesta funcional |
| RN-009 | KeyFacil conserva la emisión fiscal. La referencia del comprobante se relaciona con la operación y se concilia; el momento de emisión sigue pendiente de definición. | Alcance, [PEN-003](../producto/registro-pendientes.md) | FCO/GER | Decisión de frontera; procedimiento pendiente |
| RN-010 | La operación O2C permanece en seguimiento mientras existan entregas, pagos o incidencias sin conciliar. Una cancelación de orden de venta confirmada la decide GER y conserva sus efectos y evidencias. | Modelo de autorización, EV-020 | GER/FCO/ALM | Propuesta funcional |
| RN-011 | Una necesidad de abastecimiento puede originarse en programación mensual de alta rotación, reposición detectada o demanda sin stock suficiente. No se presumen cantidades mínimas ni órdenes automáticas. | Observación comunicada por el equipo, pendiente de corroboración empresarial; EV-021 | ALM/CMP | Programación declarada como práctica observada; formalización propuesta |
| RN-012 | ALM identifica la necesidad; CMP revisa y gestiona la compra ordinaria; GER autoriza el compromiso y gestiona excepciones con proveedores. | Modelo de autorización, EV-022 | ALM/CMP/GER | Decisión vigente para roles; detalle de excepciones propuesto |
| RN-013 | ALM registra la cantidad físicamente recibida y apta, mantiene visibles daños y diferencias, y no convierte una recepción parcial en una compra completa. | EV-026/EV-027, modelo de autorización | ALM/CMP | Propuesta funcional |
| RN-014 | FCO ejecuta y concilia pagos ordinarios al proveedor; GER supervisa y decide excepciones. Pago, recepción y documento del proveedor se distinguen. | Modelo de autorización, EV-040/EV-046/EV-055 | FCO/GER | Decisión de roles; procedimiento pendiente |
| RN-015 | La consulta de disponibilidad no constituye reserva. Se propone reservar únicamente existencias disponibles para una orden confirmada; el mecanismo debe probarse en Odoo 19. | [Mapa de procesos](mapa-procesos.md), INT-01 | VEN/ALM | Propuesta técnica por validar |
| RN-016 | ALM registra traslados ordinarios con origen, destino y cantidad. Las diferencias de conteo se documentan antes de cualquier ajuste. | Modelo de autorización, EV-028/EV-030 | ALM | Decisión de responsabilidad; registro por validar |
| RN-017 | ALM puede ejecutar ajustes ordinarios; los extraordinarios requieren autorización de GER. No se aplicará una clasificación automática hasta que MIGAL defina el criterio que los separa. La aplicación de EV-029/EV-056 a los ajustes ordinarios queda pendiente de definición. | Modelo de autorización, EV-029/EV-056 para correcciones autorizadas | ALM/GER | Criterio de clasificación y correspondencia de eventos pendientes |
| RN-018 | Preparación, despacho y entrega son hechos distintos; cada entrega parcial o incidencia conserva cantidad, fecha, receptor y saldo pendiente. | EV-033/EV-034/EV-035/EV-036 | ALM | Propuesta funcional |
| RN-019 | La posible duplicidad de contactos se revisa antes de crear otro registro; no se presupone un bloqueo automático por nombre o teléfono. | ADR-006 | VEN | Control propuesto |
| RN-020 | El tipo de comprobante se consulta cuando sea relevante para la operación; el momento y los datos exigibles se definirán con MIGAL. | Alcance, PEN-003 | VEN/FCO | Propuesta pendiente de validación |
| RN-021 | Un reclamo inicial conserva la referencia a la venta y sus evidencias; el proceso completo de devoluciones se documentará por separado. | EV-047, [alcance](../arquitectura/alcance.md) | VEN/GER | Propuesta funcional |

## 3. Controles y evidencias

Los controles siguientes describen comprobaciones **propuestas**, manuales o técnicas por definir. No se les atribuye ejecución automática.

| ID | Reglas | Comprobación y evidencia esperada | Estado |
|---|---|---|---|
| CT-001 | RN-001, RN-019 | Revisar contacto existente y próxima acción de las oportunidades con seguimiento. | Procedimiento y soporte técnico por validar |
| CT-002 | RN-002, RN-003, RN-004 | Comparar condiciones vigentes y autorizaciones con la cotización concreta aceptada; conservar versiones y conformidades. | Procedimiento por validar |
| CT-003 | RN-005, RN-006, RN-008 | Relacionar cotización, solicitud interna, evaluaciones, respuesta y orden confirmada; impedir confirmación sin aceptación mediante control por definir. | Mecanismo pendiente en INT-01 |
| CT-004 | RN-007, RN-009, RN-020 | Conciliar venta o cobro con referencia de KeyFacil y diferencias registradas. | Procedimiento pendiente |
| CT-005 | RN-010, RN-018, RN-021 | Revisar entregas, saldos, incidencias, cancelaciones y reclamos antes del cierre funcional. | Procedimiento propuesto |
| CT-006 | RN-011, RN-012 | Documentar origen de la necesidad, revisión de compras pendientes y autorización GER antes del compromiso. | Evidencia operativa por definir |
| CT-007 | RN-013, RN-014 | Cotejar compra, recepción real, documento del proveedor y pago aplicado; conservar diferencias abiertas. | Procedimiento propuesto |
| CT-008 | RN-015, RN-016 | Contrastar disponibilidad, reservas y traslados con existencias y ubicaciones efectivas. | Requiere pruebas en Odoo 19 |
| CT-009 | RN-017 | Conservar conteo, causa, clasificación y autorización cuando corresponda; el límite ordinario/extraordinario sigue pendiente. | Política por definir con MIGAL |

## 4. Excepciones

| ID | Situación | Tratamiento propuesto | Referencia |
|---|---|---|---|
| EXC-001 | Solicitud de orden de venta condicionada o rechazada | Registrar motivo; retornar a CRM y renegociar solo si cambian condiciones. | RN-005/RN-006, INT-01 |
| EXC-002 | Descuento o crédito excepcional | Solicitar decisión GER y conservarla antes de asumir el compromiso. | RN-004 |
| EXC-003 | Recepción parcial, dañada o con precio distinto | Registrar cantidad apta y diferencia; GER gestiona la excepción con proveedor. | RN-012/RN-013 |
| EXC-004 | Existencia registrada distinta de la física | Detener la promesa sobre stock dudoso, verificar conteo y clasificar ajuste antes de ejecutarlo. | RN-015/RN-017 |
| EXC-005 | Entrega parcial o no conforme | Registrar despacho y recepción reales, incidencia y saldo; no declarar la entrega completa. | RN-018 |
| EXC-006 | Cancelación de orden confirmada | GER decide y se conservan efectos sobre stock, comprobantes, pagos y entregas. | RN-010 |

## 5. Validaciones pendientes

GER y los responsables de proceso deben confirmar la vigencia de cotizaciones, el criterio de ajustes ordinarios y extraordinarios, los detalles de reposición mensual, las excepciones de proveedor, el momento de emisión en KeyFacil y las condiciones para cerrar cada operación. SIS debe comprobar qué controles pueden apoyarse en Odoo 19. Las correspondencias ambiguas `EV` de INT-01 no se resuelven mediante este catálogo.
