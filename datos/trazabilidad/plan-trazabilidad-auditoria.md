# Plan de trazabilidad y auditoría de ERP-MIGAL

## 1. Propósito, alcance y estado

Este plan define la evidencia necesaria para reconstruir operaciones de **CRM, O2C, P2P e inventario**: su origen, decisiones, responsables, documentos relacionados, hechos físicos y efectos económicos. Es una especificación de **trazabilidad requerida**, no una declaración de que Odoo 19 ya registra automáticamente todos estos datos ni de que se hayan ejecutado pruebas.

La autoridad funcional procede de [ADR-004](../../arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md), [ADR-005](../../arquitectura/decisiones/ADR-005-cambio-version-Odoo-18-Community-a-Odoo-19-Community.md), [ADR-006](../../arquitectura/decisiones/ADR-006-adopcion-crm-odoo.md), [INT-01](../../arquitectura/integraciones/INT-01-CRM-ERP.md), el [alcance](../../arquitectura/alcance.md), el [modelo de autorización](../../arquitectura/seguridad/modelo-autorizacion.md), el [catálogo de eventos](../../procesos/catalogo-eventos.md) y el [catálogo de reglas](../../procesos/catalogo-reglas.md). Los objetos y datos se definen en el [diccionario de datos](../diccionario-datos.md). Los flujos [comercial](../../procesos/comercial-crm/flujo-comercial.md), [O2C](../../procesos/o2c/flujo.md), [P2P](../../procesos/p2p/flujo.md) e [inventario](../../procesos/inventario/flujo.md) describen el orden funcional; este plan describe cómo demostrarlo.

Una **traza TR** es un requisito de reconstrucción y evidencia. Un **evento EV** identifica un hecho de negocio en el catálogo central. Una **regla RN**, un **control CT** o una **excepción EXC** establece el criterio aplicable. Ninguno de estos códigos prueba por sí solo que exista un campo, permiso, historial o automatización configurados. Los códigos locales de la secuencia de INT-01 no se usan aquí como equivalentes de los EV centrales cuando su correspondencia sigue abierta.

## 2. Cadenas de reconstrucción

| Recorrido | Secuencia y vínculos exigidos |
|---|---|
| Venta con seguimiento | Consulta y oportunidad cuando corresponda → cotización identificable y versión comunicada → conformidad del cliente → **solicitud interna de orden de venta** → evaluaciones de abastecimiento y despacho → respuesta aceptada, condicionada o rechazada → orden confirmada solo tras respuesta aceptada. La solicitud es un objeto funcional interno; su representación técnica sigue por definir. |
| Renegociación | Se conservan la cotización, la conformidad y la solicitud previas, conforme a [RN-003](../../procesos/catalogo-reglas.md); la nueva solicitud queda vinculada a la anterior (TR-15). Una respuesta condicionada o rechazada retorna a CRM con motivo y no confirma automáticamente la orden. |
| Venta inmediata | Venta de mostrador por Punto de Venta → entrega y cobro que correspondan → comprobante emitido en KeyFacil y referencia conciliada. No se crean artificialmente lead, oportunidad, cotización o solicitud interna para completar la cadena. |
| Abastecimiento P2P | Necesidad identificada → compra preparada por CMP y autorizada por GER → respuesta o incumplimiento del proveedor → recepción física real → documento y obligación → pago realizado y aplicado, con diferencias y saldos abiertos si existen. Una compra no constituye recepción. |
| Inventario y entrega | Producto y ubicación → existencia física o registrada y disponibilidad consultada → reserva propuesta solo para una orden confirmada y stock existente → preparación → despacho → recepción del cliente o incidencia. Traslados, conteos y ajustes conservan su causa y no se presentan como ventas. |
| Comprobante y conciliación | La emisión fiscal permanece en KeyFacil. Se vincula el soporte externo con una referencia registrada en la operación y se comparan importes y saldos; registrar la referencia no emite el comprobante ni presupone interfaz automática. |

El orden entre comprobante, entrega y cobro depende de las condiciones de cada operación; no se infiere una regla fiscal universal. Una entrega parcial, un pago parcial o una diferencia de recepción mantiene abierta la obligación correspondiente.

## 3. Contenido mínimo de una traza y calidad de la evidencia

Cada traza debe poder responder, según aplique, **qué ocurrió, sobre qué objeto, a partir de qué antecedente, quién actuó, con qué rol, cuándo, qué decidió, por qué y qué resultado produjo**. Para ello se propone conservar referencia de la operación y sus documentos, tipo de hecho, responsable, fecha y contexto horario, estado o valor anterior y posterior cuando hubo cambio, motivo, autorización exigible, soporte disponible y siguiente acción si la operación queda abierta. El [diccionario](../diccionario-datos.md) distingue estos datos funcionales de los campos técnicos aún no verificados.

| Nivel de constatación | Criterio de uso |
|---|---|
| Requisito documental | El proceso o control exige una referencia o evidencia; todavía no se ha identificado cómo se obtiene en la instancia. |
| Evidencia localizada | Existe un documento, registro, comunicación o soporte identificable con fecha, responsable y vínculo a la operación; su interpretación puede requerir contraste. |
| Verificación efectuada | Un revisor comparó las fuentes pertinentes, registró resultado, entorno, fecha, responsable y discrepancias. Solo una prueba con resultado observado puede declararse ejecutada. |

La ausencia de evidencia se registra como **brecha**, no se completa con un evento, usuario, fecha o aprobación supuesto. Una corrección conserva el hecho anterior y su motivo; no se sustituyen retrospectivamente las decisiones originales. El acceso, la conservación, la exportación y la eventual protección técnica de evidencias requieren políticas y pruebas específicas. SIS administra mecanismos técnicos, pero no autoriza decisiones empresariales por ejercer ese rol.

## 4. Catálogo de requisitos de trazabilidad

La numeración conserva un identificador únicamente cuando su objeto de reconstrucción mantiene el mismo significado. **TR-05 y TR-13 no se asignan a requisitos vigentes ni se reutilizan para otro significado.** Los requisitos adicionales comienzan en TR-14. Los enlaces RN, CT y EXC remiten al catálogo vigente; las menciones EV remiten exclusivamente al catálogo central. Un guion indica que no existe una correspondencia EV definida para ese hito.

| ID | Qué debe reconstruirse y evidencia mínima | Referencias vigentes |
|---|---|---|
| TR-01 | Lead o contacto surgido de una consulta que requiere seguimiento: canal, registro consultado o creado y resolución de una posible duplicidad, sin exigir identificación fiscal para toda consulta. | RN-019, CT-001; EV-001/EV-002 según el hecho. |
| TR-02 | Oportunidad que requiere seguimiento: necesidad, responsable, actividad prevista, cambios y resultado; no aplica obligatoriamente a POS. | RN-001/RN-008, CT-001; sin EV exclusivo para cada cambio de etapa. |
| TR-03 | Cotización comunicada, sus líneas, condiciones y versiones sucesivas; relación entre cambio, motivo y conformidad que corresponda. | RN-002/RN-003, CT-002; EV-003/EV-004/EV-005/EV-008 según el hecho. |
| TR-04 | Decisión de GER sobre precio, descuento o crédito excepcional: condición afectada, antecedentes, motivo, decisor y fecha. No se presume que iniciador y decisor sean siempre personas distintas. | RN-004, CT-002, EXC-002; EV-041/EV-052/EV-053 cuando correspondan. |
| TR-06 | Disponibilidad consultada frente a reserva efectiva propuesta: producto, ubicación, cantidad, orden confirmada y diferencia. Consultar stock no reserva unidades. | RN-015, CT-008; sin EV central específico de reserva. |
| TR-07 | Entrega física y conformidad o incidencia del receptor: despacho de origen, cantidades recibidas y pendientes, fecha y siguiente acción. | RN-018, CT-005, EXC-005; EV-035/EV-036/EV-037 según el hecho. |
| TR-08 | Comprobante emitido en KeyFacil, soporte externo, referencia vinculada a la venta y diferencias de conciliación; no se atribuye la emisión a Odoo. | RN-009/RN-020, CT-004; EV-038/EV-039 cuando correspondan. |
| TR-09 | Cobro de cliente y aplicación a saldo como hechos distintos: soporte, importe, fecha, obligación, aplicación y pendiente. | RN-010, CT-004/CT-005; EV-042/EV-043/EV-044/EV-045 según el hecho. |
| TR-10 | Reclamo inicial y operación de origen, evidencias, responsable y tratamiento; el proceso completo de devoluciones requiere documentación propia. | RN-021, CT-005; EV-047/EV-050 cuando correspondan. |
| TR-11 | Seguimiento y cierre funcional de O2C: entregas, comprobantes, cobros e incidencias conciliados, o pendientes con responsable. No se infiere de un estado técnico. | RN-010, CT-005; sin EV central exclusivo de cierre. |
| TR-12 | Accesos y cambios sensibles: solicitud, responsable, autorización aplicable, ejecución y revisión posterior. Para usuarios o configuración, GER autoriza cuando corresponde y SIS ejecuta; las decisiones comerciales y ajustes conservan además sus trazas específicas. Se verificará el soporte técnico real. | [Modelo de autorización](../../arquitectura/seguridad/modelo-autorizacion.md); sin EV central exclusivo de administración de accesos. |
| TR-14 | Aceptación del cliente de una versión concreta de cotización vigente, con fecha y medio de conformidad; no constituye confirmación de orden. | RN-002/RN-003, CT-002; EV-006. |
| TR-15 | Presentación por VEN de la solicitud interna con referencia a cotización y conformidad. Si sustituye una solicitud anterior por renegociación, se conserva el vínculo entre ambas. | RN-003/RN-005, CT-003; EV-009 como hecho de presentación. |
| TR-16 | Evaluaciones de abastecimiento y despacho: criterio, resultado, responsable, fecha, soporte y autorización excepcional aplicable. | RN-006, CT-003; EV-010/EV-012. |
| TR-17 | Respuesta aceptada, condicionada o rechazada: motivo, condiciones requeridas, responsable y retorno comercial cuando proceda. EV-014 no representa por sí solo los tres resultados; el condicionado carece de equivalencia central exacta. | RN-006, CT-003, EXC-001; EV-014 solo cuando su significado canónico sea aplicable; correspondencias pendientes en INT-01. |
| TR-18 | Orden confirmada: solicitud aceptada de origen, condiciones, responsable y fecha; verificar que la aceptación comercial o respuesta condicionada no la haya confirmado por sí sola. | RN-006/RN-008, CT-003; EV-018. |
| TR-19 | Necesidad de abastecimiento y compromiso de compra: origen, revisión de pendientes, propuesta CMP, autorización GER y condiciones comunicadas al proveedor. | RN-011/RN-012, CT-006; EV-021/EV-022. |
| TR-20 | Respuesta del proveedor, cambio de condiciones, incumplimiento o cancelación, con decisión GER para compromisos revisados. | RN-012, CT-006; EV-023/EV-024/EV-025 según el hecho. |
| TR-21 | Recepción física de proveedor: cantidades aptas, dañadas y pendientes, ubicación, ALM, documento de compra y diferencia abierta. | RN-013, CT-007, EXC-003; EV-026/EV-027. |
| TR-22 | Traslado entre ubicaciones: origen, destino, producto, unidad, cantidad, fecha y ALM; conciliación posterior si existe diferencia. | RN-016, CT-008; EV-030. |
| TR-23 | Conteo, diferencia y ajuste: causa, clasificación, cantidades anterior y posterior, ejecutor y autorización aplicable. ALM ejecuta ajustes ordinarios; GER autoriza extraordinarios. | RN-017, CT-009, EXC-004; EV-028; EV-029/EV-056 describen correcciones autorizadas y su aplicación a ordinarios sigue pendiente. |
| TR-24 | Preparación y despacho efectivos: cantidades por viaje, salida, responsable, pendientes y guía de remisión solo cuando corresponda. No se presume entrega conforme. | RN-018, CT-005, EXC-005; EV-033/EV-034 y EV-054 si aplica. |
| TR-25 | Documento y obligación de proveedor, pago realizado y aplicación a deuda: importes, soportes, diferencias y saldos conciliados por FCO. | RN-014, CT-007; EV-040/EV-046/EV-055 según el hecho. |
| TR-26 | Modificación o cancelación de orden confirmada: decisión GER, motivo y efectos sobre reserva, despacho, comprobante, cobro y pendientes. | RN-010, CT-005, EXC-006; EV-019/EV-020 cuando correspondan. |
| TR-27 | Venta inmediata POS: registro comercial, entrega o salida aplicable, cobro y referencia fiscal, sin imponer la ruta CRM. | RN-007, CT-004; EV-017. |

Los identificadores de esta tabla son **requisitos de trazabilidad**, no nombres de tablas ni una promesa de eventos automáticos. Cuando un EV se señala «según el hecho», no se afirma que todos los eventos citados ocurran en cada operación.

## 5. Procedimiento de revisión de una operación

| Paso | Comprobación | Resultado que debe registrarse |
|---|---|---|
| 1. Delimitar el caso | Identificar recorrido —venta con seguimiento, POS, P2P o movimiento de inventario—, período, documentos y responsable de la revisión. | Referencias iniciales y fuentes efectivamente disponibles. |
| 2. Reconstruir el origen | Seguir cliente o proveedor, necesidad, cotización o solicitud de abastecimiento y sus versiones. | Cadena documental y vacíos, sin crear objetos ficticios para recorridos que no los requieren. |
| 3. Contrastar decisiones | Comparar conformidad del cliente, evaluaciones, respuesta, autorizaciones GER y confirmación; en compras, distinguir propuesta CMP de compromiso autorizado. | Responsable, fecha, soporte, secuencia y discrepancias; una respuesta condicionada permanece diferenciada. |
| 4. Contrastar ejecución física | Comparar existencia, reserva propuesta, recepción, traslado, despacho y entrega o incidencia con cantidades reales. | Cantidades por ubicación y saldos pendientes; nunca equiparar compra con recepción ni despacho con entrega. |
| 5. Contrastar efecto económico | Relacionar emisión externa KeyFacil con su referencia, cobros o pagos, documentos del proveedor, aplicaciones y conciliaciones. | Importes, moneda, diferencias y obligaciones abiertas; no inferir integración automática. |
| 6. Cerrar la revisión | Comprobar cambios, cancelaciones, reclamos, autorizaciones y evidencias faltantes. | Conclusión «verificada», «discrepancia» o «pendiente de evidencia», con revisor y fecha; no declarar un caso de prueba ejecutado sin resultado observado. |

## 6. Validaciones pendientes y límites técnicos

- **Odoo 19:** comprobar en una instancia autorizada la representación de la solicitud interna, versiones de cotización, relación entre documentos, permisos, historial, reservas, recepciones y salidas. La presencia de módulos o de Conversaciones (mail) no acredita que todas las acciones queden registradas con el detalle requerido.
- **Autorizaciones:** definir con MIGAL el límite ordinario/extraordinario de ajustes y la correspondencia de EV-029/EV-056 con ajustes ordinarios; comprobar la evidencia de las decisiones GER y de la actuación ALM sin atribuir aprobaciones inexistentes.
- **INT-01 y EV:** resolver formalmente las correspondencias ambiguas de solicitud presentada, aceptada, condicionada y rechazada, manteniendo los tres resultados y sin crear un evento equivalente por suposición.
- **KeyFacil:** definir momento, emisor, soporte y procedimiento de conciliación. No se presupone API, sincronización, llave de idempotencia ni reintentos. Si se aprueba una interfaz futura, requerirá requisitos y trazas propios.
- **Evidencia empresarial:** corroborar la programación de compras de alta rotación y las políticas de vigencia, entrega y cierre que aún están abiertas en [supuestos y vacíos](../../fuentes/supuestos-y-vacios.md).
- **Gobierno de datos:** acordar custodia, acceso, corrección, retención y exportación de evidencias; no se atribuyen bloqueos de edición, huellas digitales ni conservación automática a una configuración no comprobada.

La aplicación de este plan se demostrará con casos, datos de entrada, resultados observados, capturas o registros pertinentes, versión de la instancia y fecha. **Este documento no informa pruebas ejecutadas ni resultados técnicos obtenidos.**
