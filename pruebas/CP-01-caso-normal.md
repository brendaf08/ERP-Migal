# CP-01: Cotización ordinaria de materiales para una obra

## 1. Identificación, objetivo y alcance

| Elemento | Definición |
|---|---|
| Identificador | CP-01 |
| Proceso | Gestión comercial CRM, tramo inicial de [O2C](../procesos/o2c/flujo.md) |
| Tipo de escenario | Normal, con datos enteramente **sintéticos [SIM]** |
| Estado de ejecución | **No ejecutado** |
| Responsable funcional de la prueba | VEN; SIS prepara un entorno autorizado sin asumir decisiones comerciales |

El objetivo es comprobar que VEN identifica al cliente y sus contactos sin duplicarlos innecesariamente, registra una necesidad que requiere seguimiento, prepara y comunica una cotización ordinaria con condiciones explícitas y conserva una próxima acción. El caso aplica la [frontera CRM–ERP](../arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md) y la [adopción de Odoo CRM](../arquitectura/decisiones/ADR-006-adopcion-crm-odoo.md) en la plataforma [Odoo 19 Community](../arquitectura/decisiones/ADR-005-cambio-version-Odoo-18-Community-a-Odoo-19-Community.md).

**Límite:** termina en la cotización comunicada y su seguimiento. No simula aceptación del cliente, solicitud interna de orden de venta, evaluación operativa, confirmación, reserva, despacho, entrega, comprobante KeyFacil ni cobro. Elaborar o comunicar la cotización **no confirma una venta** ni permite marcar la oportunidad como «Ganada». Esas etapas se rigen por [INT-01](../arquitectura/integraciones/INT-01-CRM-ERP.md) y los [flujos CRM](../procesos/comercial-crm/flujo-comercial.md) y O2C.

## 2. Requisitos y trazabilidad que se verifican

| Criterio | Referencias vigentes | Alcance en CP-01 |
|---|---|---|
| Consulta, identificación y revisión de posibles duplicados | RN-019, CT-001; EV-001/EV-002; TR-01 | Verificar búsqueda y vínculo manual con cliente y contactos existentes; no prometer bloqueo automático. |
| Oportunidad y seguimiento cuando la venta lo requiere | RN-001, CT-001; TR-02 | Registrar necesidad, responsable y próxima actividad propuesta; comprobar el soporte disponible sin afirmar obligatoriedad técnica. |
| Cotización, condiciones y versión | RN-002, CT-002; EV-003/EV-004; TR-03 | Comparar las tres líneas y condiciones comunicadas con V01; no comprobar una aceptación que no ocurre en el caso. |
| Disponibilidad informativa | RN-015, CT-008; TR-06 | Si se consulta stock, comprobar que la consulta no se presenta como reserva ni promesa de entrega. La reserva efectiva queda fuera. |
| Estado comercial y frontera de confirmación | RN-005/RN-006/RN-008, CT-003; INT-01 | Comprobar por ausencia de transición que no se registra solicitud, orden confirmada ni estado «Ganada». No se ensaya el mecanismo técnico de bloqueo. |
| Tipo de comprobante, solo si es relevante | RN-020 | Registrar que permanece por definir en este escenario; no exigir RUC para una consulta ni emitir comprobante. |

Los identificadores RN y CT proceden del [catálogo de reglas](../procesos/catalogo-reglas.md), EV del [catálogo de eventos](../procesos/catalogo-eventos.md) y TR del [plan de trazabilidad](../datos/trazabilidad/plan-trazabilidad-auditoria.md). No se asigna un evento EV a la mera creación de una oportunidad porque el catálogo no define uno exclusivo.

## 3. Precondiciones y datos de prueba

Antes de ejecutar, SIS y el responsable de la prueba deben identificar una instancia autorizada de Odoo 19, su versión, módulos instalados, usuarios y permisos efectivos. CRM, Contactos y Ventas deben estar disponibles para recorrer el caso; si no lo están, el resultado se clasifica como **bloqueado**, no como prueba fallida. Los registros [SIM] se cargan o identifican únicamente en un entorno permitido; no se usan clientes reales ni se envía una propuesta a destinatarios externos reales. La representación de versiones, actividades y permisos se verifica durante la ejecución: su presencia no se presupone por el diseño.

La vigencia, modalidad de pago y condiciones de entrega que se comuniquen deben quedar expresas en la propuesta de prueba y ser autorizadas para el ensayo antes de enviarla. **No se fija aquí un plazo universal, una política de crédito ni una fecha de entrega de MIGAL.** Si esas condiciones no pueden determinarse, se documenta la preparación de V01 y se deja la comunicación pendiente.

| Referencia local [SIM] | Dato del escenario | Uso |
|---|---|---|
| CLI-SIM-001 | Rosa Elena Huamán Salcedo | Cliente responsable económico de una obra ficticia. |
| CON-SIM-001 | Rosa Elena Huamán Salcedo | Contacto que decide sobre la propuesta. |
| CON-SIM-002 | Luis Fernando Salcedo Poma | Maestro de obra que comunica la lista de materiales; no sustituye a la cliente. |
| DIR-SIM-001 | Ampliación de tercer piso, San Martín de Porres | Contexto de la consulta; no es una entrega programada. |
| OPP-SIM-001 | Materiales para tercer piso, consulta por WhatsApp simulado | Oportunidad que requiere seguimiento por VEN. |
| COT-SIM-001-V01 | Primera versión de cotización | Documento de prueba, no nombre de un campo o identificador nativo de Odoo. |

| Línea [SIM] | Material | Cantidad | Precio unitario referencial | Importe referencial |
|---|---|---:|---:|---:|
| 1 | Cemento | 100 bolsas | S/ 31.00 | S/ 3,100.00 |
| 2 | Fierro | 40 unidades | S/ 40.50 | S/ 1,620.00 |
| 3 | Tubería PVC | 20 unidades | S/ 20.00 | S/ 400.00 |
| | **Subtotal de líneas** | | | **S/ 5,120.00** |

Los precios son datos [SIM], no precios vigentes de MIGAL. El subtotal se obtiene de 100 × 31.00 + 40 × 40.50 + 20 × 20.00 = **S/ 5,120.00**; no incluye impuestos, transporte ni descuentos y no constituye un total fiscal.

## 4. Procedimiento reproducible y evidencia

| Paso | Actor | Acción | Resultado esperado y evidencia por recoger |
|---|---|---|---|
| 1 | VEN | Registrar la consulta simulada del maestro de obra, canal y materiales solicitados. Buscar primero cliente y contactos existentes. | Consulta con fecha y responsable; evidencia de la búsqueda y de los vínculos con CLI-SIM-001, CON-SIM-001 y CON-SIM-002, sin duplicación innecesaria (TR-01). |
| 2 | VEN | Relacionar la necesidad con OPP-SIM-001 y señalar a Rosa como responsable de la decisión comercial. | Oportunidad abierta, necesidad y contactos diferenciados; captura o registro de vínculos, actor y fecha (TR-02). No se asigna probabilidad «Alta» por defecto. |
| 3 | VEN; ALM si hay duda física | Revisar materiales, unidades y precios de referencia del escenario. Consultar disponibilidad solo como dato informativo. | Lista de entradas cotejada con el [diccionario](../datos/diccionario-datos.md); consulta documentada si se realizó, sin reserva ni compromiso de stock (TR-06). |
| 4 | VEN | Preparar COT-SIM-001-V01 con las tres líneas y el subtotal comprobado. Registrar las condiciones específicas autorizadas para el ensayo, sin descuento especial ni crédito supuesto. | Versión y líneas recuperables; importes S/ 3,100.00, S/ 1,620.00 y S/ 400.00; subtotal S/ 5,120.00; soporte de condiciones y autoría (TR-03). |
| 5 | VEN | Comunicar V01 únicamente por un canal controlado de prueba, si se cumplieron las precondiciones comerciales. No prometer una fecha de entrega no evaluada. | Evidencia de versión, destinatario simulado, fecha, canal y condiciones efectivamente comunicadas (EV-004, TR-03). Si no hay condición autorizada, registrar paso pendiente. |
| 6 | VEN | Programar y registrar la siguiente acción de seguimiento para una fecha de prueba elegida al ejecutar. | Responsable, acción y fecha recuperables cuando el soporte lo permita; si no existe mecanismo, registrar brecha técnica sin afirmar control automático (TR-02). |
| 7 | VEN; revisor funcional | Comprobar el estado final de la oportunidad y la ausencia de transición operativa. | Oportunidad abierta o en seguimiento; sin aceptación EV-006, solicitud EV-009, orden EV-018, reserva, comprobante ni cobro. Evidencia del estado y de los documentos existentes. |

## 5. Criterios de aceptación y fallo

El caso **cumple** cuando los contactos están relacionados sin duplicación injustificada; V01 conserva las tres líneas, cantidades, unidades, precios y subtotal correctos; las condiciones comunicadas coinciden con la propuesta; el seguimiento queda atribuible; y no se documenta venta confirmada. Una consulta de stock, si se efectuó, no puede presentarse como reserva.

El caso **falla** si se pierde una línea o condición, se calcula incorrectamente el subtotal, VEN concede una excepción no autorizada, se duplica un contacto sin revisión, se comunica una condición no aprobada o la oportunidad pasa a «Ganada» por la sola cotización. Una funcionalidad necesaria pero no disponible, una política aún sin definir o la falta de entorno autorizado se registra como **bloqueo o brecha**, con evidencia, y no como éxito ni fallo de una prueba que no pudo ejecutarse.

## 6. Resultado obtenido y limitaciones

| Estado | Resultado observado | Evidencia recogida | Fecha y responsable |
|---|---|---|---|
| **No ejecutado** | No existe resultado observado. | Ninguna; las evidencias de la sección 4 son requisitos de captura. | Pendientes. |

La verificación futura debe anotar versión y módulos de Odoo 19, usuarios y roles, datos cargados, resultados observados, diferencias y soportes. Este caso no acredita la implementación de campos del [diccionario](../datos/diccionario-datos.md), controles automáticos, historial completo, permisos efectivos ni integración con KeyFacil. Los faltantes, el abastecimiento y los movimientos físicos corresponden a [P2P](../procesos/p2p/flujo.md) e [inventario](../procesos/inventario/flujo.md), fuera de este ensayo. La política general de vigencia de cotizaciones y las reglas de promesa de entrega permanecen pendientes en [supuestos y vacíos](../fuentes/supuestos-y-vacios.md).
