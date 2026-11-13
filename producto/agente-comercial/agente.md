# Agente comercial MIGAL (A9)

El agente comercial MIGAL se integra en Odoo 19 Community.

## 1. Propósito y relevancia comercial

El Agente MIGAL apoya al equipo comercial durante la atención, la preparación y el seguimiento de una cotización, y facilita la consulta de saldos a los responsables autorizados. El usuario puede invocarlo desde el chat de Odoo o mediante el asistente y los botones de cotizaciones y contactos. Odoo sigue gestionando la cotización, sus revisiones, la Solicitud de Orden de Venta (SOV), el inventario y la contabilidad.

| Momento del proceso | Dificultad que atiende | Aporte del agente |
| --- | --- | --- |
| Preparar la respuesta al cliente | El vendedor necesita revisar varios productos, identificar faltantes y explicar qué podría entregarse en la fecha solicitada. | Reúne la cobertura de toda la cotización, indica qué depende de reposición y propone un mensaje que el vendedor puede revisar. |
| Compartir la propuesta | WhatsApp es un canal habitual de atención. Buscar el destinatario, redactar el mensaje y localizar el PDF introduce pasos y riesgo de usar una revisión anterior. | Prepara el enlace con el teléfono de la ficha, arma un borrador editable y comprueba la vigencia de la cotización antes de ofrecer el envío. |
| Atender en mostrador | Un cliente presencial puede querer llevarse la cotización en el celular sin dar su número. | Genera un QR para consultar el PDF desde una dirección accesible al cliente. |
| Consultar deuda y abonos | El cliente puede pedir un resumen cuando tiene varias compras, pagos parciales o cuotas vencidas. | Reúne cargos, abonos y saldos contables, presenta el vencido y deja las ventas por facturar en un apartado informativo. |

Para Comercial, el valor está en responder más rápido y con datos consistentes en tres puntos críticos del ciclo **pedido a cobro (O2C)**. Una respuesta sobre disponibilidad distingue existencias libres de una fecha estimada. Una cotización compartida identifica la revisión que recibió el cliente. Un estado de cuenta ayuda a explicar cuánto se debe y qué parte ya venció. Esos beneficios son esperados. El equipo puede medirlos comparando el tiempo para preparar un envío, el tiempo para entregar un estado de cuenta y las correcciones por revisión o destinatario antes y después de usar el agente.

## 2. Entradas

| Entrada | Formato y origen | Tratamiento |
| --- | --- | --- |
| Solicitud del usuario | Texto en el chat o acción desde un registro de Odoo. | Interpreta la intención en el chat. En los botones y asistentes, toma la acción y el registro de la pantalla. |
| Cotización | Referencia de Odoo, por ejemplo `S00627` o `S00627-01`. | Busca la cotización y comprueba la revisión vigente. Si falta la referencia en el chat, pide el dato. |
| Fecha requerida | Fecha opcional `AAAA-MM-DD` para cobertura. | Usa la fecha indicada, después la fecha comprometida de la cotización y, a falta de ambas, el día actual. Una fecha pasada se evalúa para hoy. |
| Cliente | Contacto seleccionado o identificador de búsqueda, como nombre, RUC/DNI o referencia interna. | Si encuentra varias coincidencias, las presenta para que el operador precise el cliente. |
| Período del estado de cuenta | Fechas opcionales `AAAA-MM-DD`. | Por defecto consulta desde el primer día del mes de corte hasta la fecha de corte. Si tampoco se indica el corte, usa el día actual. |
| Teléfono y confirmación de envío | Teléfono de la ficha del cliente y acción explícita del usuario después de enviar. | Valida el formato internacional para WhatsApp. El QR presencial de cotización puede generarse sin teléfono. |

## 3. Salidas

- **Cotización por WhatsApp.** Enlace `wa.me` dirigido al contacto, texto editable y acceso al PDF para adjuntarlo. El vendedor abre WhatsApp, revisa el destinatario, adjunta el PDF y envía. Luego puede registrar en Odoo el envío, la revisión y el destinatario. Ese registro refleja la confirmación del operador.
- **Cobertura preliminar.** Detalle por producto con cantidad requerida, stock físico, compromisos de otras ventas, cantidad libre, reposiciones previstas, faltante y fecha posible cuando se puede estimar. El resumen distingue cobertura con stock, cobertura condicionada y faltantes.
- **Estado de cuenta.** Saldo anterior, cargos y abonos del período, saldo al cierre, documentos abiertos, pagos sin aplicar, total pendiente y vencido a la fecha de consulta. El saldo al cierre del período y el pendiente actual pueden diferir. El operador puede generar el PDF o preparar una copia para compartir.
- **QR.** El de cotización abre el PDF del portal con un token. El de estado de cuenta usa una copia de solo lectura que expira a las 24 horas y puede revocarse. En ambos casos, el celular debe poder alcanzar la URL de Odoo. Generar un QR en una instalación local no configura acceso desde Internet.
- **Bitácora y avisos.** Odoo conserva el usuario, canal, modo, entrada, herramientas invocadas, resultado, latencia, reglas y destino de escalamiento cuando corresponde. La bitácora se guarda en `migal.agente.log` y dispone de exportación JSONL. Las evidencias compartidas deben usar datos de prueba o datos anonimizados.

## 4. Fuentes de información

| Fuente | Datos de trabajo |
| --- | --- |
| Ventas y Contactos | Cotizaciones, revisión vigente, vigencia, autorizaciones, partidas, precios registrados y teléfono del cliente. |
| Inventario | Existencia física, entregas pendientes y reposiciones registradas para el almacén de la cotización. |
| Reglas internas de cobertura | Categoría, plazo habitual y límite de faltante. La instalación incluye reglas simuladas para agregados, cemento y aglomerantes, fierro y acero de construcción, y ladrillos y bloques cuando existen esas categorías. El equipo debe validar los plazos y límites antes de usarlos como criterio operativo. |
| Contabilidad | Apuntes contabilizados de cuentas por cobrar de la compañía activa, vencimientos, saldos residuales y conciliaciones. |
| Ventas y Punto de Venta | Órdenes con importe por facturar y tickets de caja sin movimiento contable en los casos previstos por el módulo. Se muestran aparte del saldo contable. |

Para la demo, el profesor levanta Odoo 19 Community con Docker y los módulos del proyecto, incluido `migal_agente`. Después restaura la copia de la base y sus adjuntos desde el respaldo que el equipo comparte por un canal privado. Esa copia contiene los módulos instalados, la configuración y los datos de prueba. Una vez restaurada, el profesor puede abrir Odoo y probar el agente con las cotizaciones y los estados de cuenta preparados.

## 5. Herramientas y funcionamiento

| Herramienta implementada | Qué hace |
| --- | --- |
| `preparar_whatsapp_cotizacion` | Valida la cotización y el teléfono, y prepara el mensaje y el enlace para el usuario. |
| `registrar_envio_whatsapp` | Registra el envío confirmado por el operador y agrega una nota al historial de la cotización. |
| `generar_qr_cotizacion` | Genera el QR de la versión PDF para atención presencial y crea el token del portal cuando corresponde. |
| `evaluar_cobertura_preliminar` | Compara la demanda de la cotización con las existencias libres y las reposiciones que podrían llegar a tiempo. Aplica la regla habitual de la categoría cuando corresponde. |
| `generar_estado_cuenta` | Consolida los movimientos y saldos del cliente en el período seleccionado y permite obtener un PDF. |
| `compartir_estado_cuenta` | Crea una copia temporal del estado de cuenta y prepara QR y mensaje para que el operador los comparta. |

El coordinador interno del módulo identifica qué herramienta corresponde a la solicitud. Antes de ejecutarla valida la estructura de los argumentos y los permisos. La herramienta consulta Odoo, aplica sus controles y devuelve datos estructurados, que el asistente transforma en una respuesta que el operador puede revisar.

El modo por reglas reconoce las solicitudes previstas y funciona con la configuración por defecto. El módulo incluye un modelo de lenguaje opcional para interpretar y redactar. Se habilita por configuración, requiere autorización para transferir datos y credenciales del proveedor, y vuelve al modo por reglas si el servicio falla. Las decisiones y permisos se aplican en el código del módulo.

## 6. Reglas y controles

1. **Cotización compartible.** Para WhatsApp y QR debe corresponder a la revisión vigente, estar en borrador o enviada, seguir dentro de vigencia si tiene fecha límite y superar el control de autorizaciones de la cotización. WhatsApp requiere además un teléfono válido.
2. **Disponibilidad informativa.** La cobertura preliminar descuenta cantidades comprometidas y distingue reposiciones previstas de existencias libres. Una fecha estimada requiere revisión humana antes de comprometer una entrega. La consulta respeta RN-011 y RN-015.
3. **Estado de cuenta conciliado con la fuente contable.** El saldo usa apuntes contabilizados y residuales. Un abono parcial reduce el saldo del documento según la conciliación registrada. Los abonos sin aplicar se identifican aparte. El vencido se calcula sobre el pendiente de los plazos acordados ya excedidos.
4. **Límite de actuación.** Los controles del chat vetan cambios de precio, descuentos, crédito, aprobación o confirmación de ventas, reservas, emisión o anulación de comprobantes y registro de pagos, según la solicitud. Las operaciones permitidas escriben registros de auditoría y de uso del asistente, como la confirmación del envío, el token de cotización o la copia temporal.
5. **Versión comercial del alcance.** La lectura automática o importación de chats externos de WhatsApp, la generación de pedidos desde esos chats y el cálculo de capacidad de vehículos quedan fuera de la versión descrita.

Consulta el [catálogo de reglas](../../procesos/catalogo-reglas.md) y el [contrato CRM–ERP INT-01](../../arquitectura/integraciones/INT-01-CRM-ERP.md) para el flujo formal.

## 7. Permisos

| Perfil | Permiso en el agente | Grupo de Odoo que usa el contrato |
| --- | --- | --- |
| VEN — Ventas | Preparar y registrar envíos de cotización, generar QR de cotización y consultar cobertura preliminar. | `sales_team.group_sale_salesman` |
| FCO — Facturación, contabilidad y cobranzas | Generar y preparar para compartir estados de cuenta. | `account.group_account_invoice` |
| GER — Gerencia | Usar las herramientas comerciales y de estado de cuenta. Puede revisar la bitácora y gestionar las reglas de cobertura según sus grupos. | `sales_team.group_sale_manager` |
| ALM — Almacén | Recibe consultas de disponibilidad y verifica el stock o la fecha estimada en el proceso operativo. | El contrato actual no asigna un grupo ALM independiente para invocar herramientas. Si el usuario tiene un grupo autorizado, aplica ese permiso. |
| SIS — Administración del sistema | Revisa incidencias y administra el sistema. El acceso técnico a la bitácora y los permisos para usar cada herramienta se controlan por grupos. | `base.group_system` para acceso técnico a la bitácora. |

Las herramientas se ejecutan con los permisos del usuario y mantienen los controles de acceso a los registros de Odoo. El módulo aplica elevación puntual para operaciones internas, como la escritura de bitácora y ciertas lecturas auxiliares acotadas. Véase el [modelo de autorización](../../arquitectura/seguridad/modelo-autorizacion.md).

## 8. Responsable humano

- **VEN** revisa el cliente, la versión, los importes y el texto antes del envío. Confirma el registro del envío después de hacerlo. Si el cliente acepta, continúa el flujo formal de la SOV en Odoo.
- **ALM** valida existencias, reposiciones y fechas que requieran confirmación. **CMP** interviene cuando la falta de mercancía exige gestionar abastecimiento.
- **FCO** revisa el saldo y el detalle de los abonos antes de entregar el estado de cuenta. Corrige diferencias y concilia pagos mediante los procesos contables de Odoo.
- **GER** decide las excepciones comerciales y define, con las áreas responsables, los parámetros operativos de cobertura. **SIS** revisa errores de configuración e integración.

## 9. Escalamiento

| Situación | Destino | Respuesta esperada |
| --- | --- | --- |
| Descuento, cambio de precio, crédito, confirmación fuera del flujo o anulación | GER | El asistente bloquea la solicitud en el chat, explica la regla y registra el destino del escalamiento. |
| Reserva pedida al agente o faltante que requiere verificación | ALM, con CMP si corresponde | El asistente veta la reserva y presenta el detalle disponible para que el vendedor coordine la consulta. |
| Emisión de comprobante, registro de un abono o diferencia contable | FCO | El operador deriva el caso a Facturación o Cobranzas para que lo resuelva en Odoo. |
| Error interno de una herramienta | SIS | El asistente muestra un error controlado para revisión técnica. |
| Teléfono ausente, revisión vencida o coincidencias múltiples | Operador que inició la consulta | El asistente muestra el dato pendiente o la causa del bloqueo. El operador corrige la ficha, selecciona el registro o precisa el cliente. |

Cuando hay un escalamiento asociado a un registro compatible, el asistente puede dejar una nota en su historial. La derivación y su seguimiento siguen a cargo del equipo.

### Evolución hacia varios agentes

La PC3 entrega **un agente comercial**. El coordinador que hoy existe dentro de `migal_agente` selecciona herramientas del propio módulo. El orquestador entre agentes se desarrollará más adelante, cuando existan agentes especializados que puedan colaborar.

Por ejemplo, ante un faltante, el agente comercial podría enviar a un futuro agente de abastecimiento una consulta con la referencia de cotización, el producto, la cantidad, el almacén y la fecha requerida. El futuro orquestador identificaría al agente responsable, transmitiría el contexto mínimo, devolvería al agente comercial la respuesta con su estado y conservaría una referencia para el seguimiento. Las autorizaciones y decisiones de cada área seguirían el flujo de Odoo. El despliegue actual permite probar el valor comercial y definir qué información necesitarán esos otros agentes.

### Evidencia de la versión

En la base local de la demo se verificaron la preparación del enlace de WhatsApp para una cotización con teléfono, el bloqueo de una cotización cuyo contacto carecía de teléfono, la evaluación de cobertura con faltantes y la generación de un PDF de estado de cuenta con saldo pendiente y vencido. La validación local llegó a la preparación del enlace y a la generación del PDF.

Las pruebas corresponden a Agente MIGAL 19.0.1.1.0, en la revisión [`7c379c5`](https://github.com/brendaf08/ERP-Migal/commit/7c379c52f050c75ad7604455256e93b89ce5cb07). El equipo documentó las pruebas y la validación del entorno Docker en el [PR #19](https://github.com/brendaf08/ERP-Migal/pull/19).

La asignación del entregable y los criterios de aceptación están en la [distribución de actividades de la PC3](../pc3/02-distribucion-equipo-pc3.md#gabriel--a9-especificación-del-agente).
