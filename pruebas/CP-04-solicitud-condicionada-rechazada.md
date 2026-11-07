# CP-04: Solicitud de orden de venta condicionada o rechazada

## 1. Identificación, objetivo y alcance

| Elemento | Definición |
|---|---|
| Identificador | CP-04, con los subescenarios **CP-04A** (condicionada) y **CP-04B** (rechazada) |
| Proceso | Frontera CRM–ERP, retorno al ámbito comercial dentro de [O2C](../procesos/o2c/flujo.md) |
| Tipo de escenario | Excepción, con datos enteramente **sintéticos [SIM]** |
| Estado de ejecución | **No ejecutado** |
| Responsables funcionales | VEN presenta la solicitud y gestiona el retorno al CRM; CMP y ALM aportan las evaluaciones; GER interviene en las excepciones y en la viabilidad de faltantes; el evaluador ([PEN-018](../producto/registro-pendientes.md)) está por designar. SIS prepara un entorno autorizado. |

El objetivo es comprobar que una solicitud interna de orden de venta cuya respuesta **no es aceptada** retorna al CRM con su motivo, conserva su historial y **no habilita la confirmación** de la orden. Así lo establecen [ADR-004](../arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md), [INT-01](../arquitectura/integraciones/INT-01-CRM-ERP.md), RN-006 y EXC-001. La base es [Odoo 19 Community](../arquitectura/decisiones/ADR-005-cambio-version-Odoo-18-Community-a-Odoo-19-Community.md), con [Odoo CRM](../arquitectura/decisiones/ADR-006-adopcion-crm-odoo.md) en la misma instancia.

- **CP-04A:** la respuesta es condicionada, el cliente renegocia y se presenta una nueva solicitud que conserva la anterior. El subescenario termina con la presentación de la nueva solicitud; su evaluación posterior sigue el recorrido de [CP-03](CP-03-solicitud-aceptada.md).
- **CP-04B:** la respuesta es rechazada, se conserva el historial y el cliente no renegocia, de modo que se registra el cierre comercial.

**Límite:** el caso no prueba la confirmación, la reserva, el despacho, la entrega, la emisión en KeyFacil ni el cobro.

**Distinción pendiente:** el criterio empresarial que separa una respuesta condicionada de una rechazada **no está definido** ([PEN-020](../producto/registro-pendientes.md)). Las causas elegidas para cada subescenario son **supuestos de prueba [SIM]** que ilustran ambas rutas. No constituyen criterios operativos aprobados por MIGAL ni límites de disponibilidad, de abastecimiento o de transporte.

## 2. Requisitos y trazabilidad que se verifican

| Criterio | Referencias vigentes | Alcance |
|---|---|---|
| Conformidad con una versión concreta y vigente | RN-002/RN-003, CT-002; EV-006; TR-14 | Ambos subescenarios parten de una aceptación vinculada a V01. |
| Presentación de la solicitud interna | RN-005, CT-003; EV-009; TR-15 | Solicitud con referencias y condiciones aceptadas; no equivale a orden confirmada. |
| Evaluaciones con resultado no favorable | RN-006, RN-015, CT-003, CT-008; EV-010/EV-012; TR-16 | En CP-04A, abastecimiento **condicionado**; en CP-04B, abastecimiento **no viable**. Se registran el criterio, el fundamento, el responsable, la fecha y el soporte. |
| Respuesta no aceptada con motivo | RN-006, CT-003, EXC-001; TR-17 | Respuesta condicionada (CP-04A) o rechazada (CP-04B), con motivo y, si corresponde, las condiciones requeridas. |
| Retorno al CRM sin confirmación | RN-006/RN-008, CT-003, EXC-001; TR-17/TR-18 | No existe EV-018 y la oportunidad no pasa a «Ganada». |
| Renegociación y nueva solicitud (CP-04A) | RN-003, CT-002, EXC-001; EV-016, EV-006, EV-009; TR-03, TR-14, TR-15 | Nuevas condiciones, nueva versión de la cotización, nueva conformidad y nueva solicitud vinculada, conservando la anterior. |
| Ausencia de reserva ficticia (CP-04A) | RN-015, CT-008 | No se reservan unidades faltantes ni se presenta la reposición futura como disponibilidad. |
| Cierre comercial (CP-04B) | RN-006/RN-008, EXC-001 | Cierre con motivo; la oportunidad no se marca «Ganada». |

Los identificadores RN, CT y EXC proceden del [catálogo de reglas](../procesos/catalogo-reglas.md); los EV, del [catálogo central de eventos](../procesos/catalogo-eventos.md); los TR, del [plan de trazabilidad](../datos/trazabilidad/plan-trazabilidad-auditoria.md). Los objetos funcionales siguen el [diccionario de datos](../datos/diccionario-datos.md), apartado 3.

### Correspondencia entre los códigos locales de INT-01 y el catálogo central

INT-01 utiliza códigos **locales** EV-01 a EV-07, que no son identificadores del catálogo central. Este caso no crea equivalencias nuevas y conserva las pendientes:

| Hecho del caso | Código local de INT-01 | EV central | Estado de la correspondencia |
|---|---|---|---|
| Cotización aceptada | EV-01 | EV-006 | Confirmada. |
| Solicitud presentada | EV-02 | EV-009 | Pendiente: «registrada» frente a «presentada». |
| Evaluación con resultado condicionado o no viable | — | EV-010 / EV-012 | Evento central propio. El resultado de **una evaluación** es distinto de la **respuesta** a la solicitud. |
| Respuesta condicionada (CP-04A) | EV-04 | **Sin equivalente exacto** | Pendiente: se registra como resultado funcional condicionado y **no se equipara a EV-014**. |
| Respuesta rechazada (CP-04B) | EV-05 | EV-014 (candidato) | Pendiente: debe confirmarse la equivalencia semántica conservando el motivo y el retorno al CRM. |
| Condiciones renegociadas (CP-04A) | EV-07 | EV-016 | Confirmada. |

El rechazo de la **solicitud** por la evaluación operativa no es EV-007 («Cotización rechazada»), que corresponde al rechazo de la propuesta por el cliente ([flujo comercial](../procesos/comercial-crm/flujo-comercial.md) §3).

## 3. Precondiciones y datos de prueba

### Condiciones de ejecución

Se requiere una instancia autorizada de Odoo 19 con `crm`, `sale_management`, `sale_crm`, `stock`, `sale_stock` y `contacts`, con la versión, los módulos, los usuarios y los permisos efectivos identificados. Si falta alguno de estos elementos, el caso queda **bloqueado**. Los datos [SIM] solo se usan en un entorno permitido.

| Pendiente | Efecto sobre la ejecución |
|---|---|
| [PEN-016](../producto/registro-pendientes.md): mecanismo de representación de la solicitud | Debe registrarse cómo se representan la solicitud, su respuesta no aceptada y el vínculo entre la solicitud anterior y la nueva. Sin un mecanismo acordado, el caso queda **bloqueado**. |
| [PEN-018](../producto/registro-pendientes.md): responsable de la evaluación | GER puede autorizar una designación provisional **solo para el ensayo**, registrada como [SIM]; el resultado no cierra PEN-018. |
| [PEN-020](../producto/registro-pendientes.md): criterio condicionada/rechazada | El caso usa causas [SIM] para cada ruta. Su resultado **no valida** un criterio de clasificación ni cierra PEN-020. |
| [PEN-004](../producto/registro-pendientes.md) y [PEN-005](../producto/registro-pendientes.md): permisos | Solo afectan a la comprobación opcional de que un usuario no pueda confirmar una orden sobre una solicitud no aceptada (pasos A6b y B5b). |

### Separación entre decisiones vigentes y supuestos de prueba

| Tipo | Contenido en CP-04 |
|---|---|
| Decisión vigente | Una respuesta condicionada o rechazada retorna al CRM con motivo y no habilita la confirmación (RN-006, EXC-001). Tras una renegociación se conserva la solicitud anterior y se presenta una nueva (RN-003, INT-01 §5). GER evalúa los faltantes de otras familias cuando corresponda ([flujo comercial](../procesos/comercial-crm/flujo-comercial.md) §1). |
| Supuesto de prueba [SIM] | Clientes, materiales, cantidades, precios y existencias; la causa del condicionamiento (faltante parcial) y la del rechazo (producto descontinuado sin proveedor); la opción que elige cada cliente; las designaciones provisionales. |
| Pendiente | Criterio condicionada/rechazada (PEN-020), mecanismo (PEN-016), evaluador (PEN-018), equivalencias con EV-009 y EV-014, y vigencia general de las cotizaciones (PEN-015). |

Los materiales de ambos subescenarios se eligen deliberadamente **fuera** de las cuatro familias (fierro, agregados, ladrillos y cemento) para las que el [flujo comercial](../procesos/comercial-crm/flujo-comercial.md) §4 describe una práctica actual distinta. Así el caso no interfiere con esa diferencia AS-IS/TO-BE, que sigue abierta para validación empresarial.

### Datos sintéticos de CP-04A

| Referencia local [SIM] | Dato del escenario | Uso |
|---|---|---|
| CLI-SIM-004 | Carmen Rosa Villanueva Torres | Cliente responsable económica y contacto que acepta. |
| DIR-SIM-003 | Remodelación de baños, Independencia | Destino de entrega acordado para el ensayo. |
| OPP-SIM-004 | Instalaciones sanitarias para remodelación | Oportunidad en seguimiento. |
| COT-SIM-004-V01 y COT-SIM-004-V02 | Versión aceptada original y versión renegociada | Versiones vinculadas; V01 no se sobrescribe. |
| SOL-SIM-004-01 y SOL-SIM-004-02 | Solicitud original (condicionada) y nueva solicitud tras la renegociación | La segunda remite a la primera. |
| EVA-SIM-004-A y EVA-SIM-004-D | Evaluaciones de abastecimiento y de despacho de SOL-01 | Resultados condicionado y favorable. |
| RES-SIM-004-01 | Respuesta a SOL-01 | **Condicionada**. |

| Línea [SIM] | Material | V01 cantidad | Precio unitario | V01 importe | V02 cantidad | V02 importe |
|---|---|---:|---:|---:|---:|---:|
| 1 | Tubería PVC SAP 4" × 3 m | 50 unidades | S/ 38.00 | S/ 1,900.00 | 30 unidades | S/ 1,140.00 |
| 2 | Codo PVC SAP 4" × 90° | 40 unidades | S/ 7.50 | S/ 300.00 | 40 unidades | S/ 300.00 |
| | **Subtotal de líneas** | | | **S/ 2,200.00** | | **S/ 1,440.00** |

Comprobación numérica: V01 = 50 × 38.00 + 40 × 7.50 = 1,900.00 + 300.00 = **S/ 2,200.00**; V02 = 30 × 38.00 + 40 × 7.50 = 1,140.00 + 300.00 = **S/ 1,440.00**.

Existencias registradas para el ensayo [SIM]: 30 tuberías y 60 codos. La reposición del faltante no tiene fecha comprometida en el escenario; el caso no fija plazos de proveedor.

### Datos sintéticos de CP-04B

| Referencia local [SIM] | Dato del escenario | Uso |
|---|---|---|
| CLI-SIM-005 | Jorge Luis Paredes Mendoza | Cliente responsable económico y contacto que acepta. |
| OPP-SIM-005 | Acabados para sala y comedor | Oportunidad en seguimiento. |
| COT-SIM-005-V01 | Versión aceptada | Propuesta de origen. |
| SOL-SIM-005-01 | Solicitud interna | Termina con respuesta rechazada. |
| EVA-SIM-005-A | Evaluación de abastecimiento | Resultado **no viable**. |
| RES-SIM-005-01 | Respuesta a SOL-01 | **Rechazada**. |

| Línea [SIM] | Material | Cantidad | Precio unitario | Importe |
|---|---|---:|---:|---:|
| 1 | Porcelanato 60 × 60, modelo «Mármol Gris» [SIM] | 45 m² | S/ 42.00 | S/ 1,890.00 |
| 2 | Pegamento para porcelanato, 25 kg | 12 bolsas | S/ 28.00 | S/ 336.00 |
| | **Subtotal de líneas** | | | **S/ 2,226.00** |

Comprobación numérica: 45 × 42.00 + 12 × 28.00 = 1,890.00 + 336.00 = **S/ 2,226.00**.

Causa del ensayo [SIM]: no hay existencias del modelo y el proveedor habitual informa que se descontinuó, sin proveedor alternativo identificado.

Todos los importes son subtotales referenciales, sin impuestos ni transporte y sin valor fiscal. Ningún dato de estas tablas es un precio, una existencia o una condición vigente de MIGAL.

## 4. Procedimiento reproducible

### CP-04A: solicitud condicionada

| Paso | Actor | Acción | Resultado esperado |
|---|---|---|---|
| A1 | VEN | Registrar la conformidad de la cliente con COT-SIM-004-V01 vigente. | Aceptación vinculada a V01 (EV-006, TR-14); oportunidad sin «Ganada». |
| A2 | VEN | Presentar SOL-SIM-004-01 con las condiciones de V01. | Solicitud con referencias, líneas, destino DIR-SIM-003, fecha y responsable (EV-009, TR-15, RN-005). |
| A3 | CMP y ALM; GER para el faltante | Evaluar el abastecimiento: 30 tuberías disponibles frente a 50 solicitadas. | EVA-SIM-004-A **condicionado**, con fundamento (faltante de 20 unidades), responsable, fecha y soporte (EV-010, TR-16). No se reservan las 30 unidades ni se presenta la reposición como disponible (RN-015, CT-008). |
| A4 | ALM | Evaluar el despacho hacia DIR-SIM-003. | EVA-SIM-004-D **favorable**, registrado de forma independiente (EV-012, TR-16). |
| A5 | Evaluador designado | Consolidar las evaluaciones y emitir la respuesta con su motivo y las condiciones requeridas. | RES-SIM-004-01 **condicionada**: atención posible si se reduce la tubería a 30 unidades o se espera la reposición sin fecha comprometida [SIM]. Responsable y fecha registrados (TR-17, EXC-001). No se registra como EV-014. |
| A6 | VEN; revisor funcional | Registrar el retorno al CRM y comprobar que no hay confirmación. | Respuesta visible en OPP-SIM-004; no existe orden confirmada ni EV-018; la oportunidad no está «Ganada» (RN-006, RN-008, TR-18). |
| A6b | SIS y revisor (opcional) | Comprobar en un registro descartable si Odoo permite confirmar la cotización con la solicitud condicionada. | Se registra si existe una restricción técnica. Si Odoo permite confirmar, se anota como **brecha técnica** (INT-01 §9, PEN-016), sin alterar la cadena principal. |
| A7 | VEN | Comunicar las condiciones requeridas; la cliente elige reducir la tubería a 30 unidades [SIM]. | Nuevas condiciones acordadas a partir de las observaciones operativas (EV-016), con fecha y soporte. |
| A8 | VEN | Preparar COT-SIM-004-V02 sin sobrescribir V01 y registrar la conformidad de la cliente con V02. | V01 y V02 distinguibles y vinculadas; subtotal de V02 de S/ 1,440.00; conformidad vinculada solo a V02 (EV-006, TR-03, TR-14, RN-003, CT-002). El acuerdo de las nuevas condiciones ya consta como EV-016 en A7. |
| A9 | VEN | Presentar SOL-SIM-004-02 con las condiciones de V02, con referencia a SOL-SIM-004-01. | Nueva solicitud vinculada a la anterior (EV-009, TR-15, RN-003). SOL-01 se conserva con su evaluación y respuesta condicionada y no se reutiliza (INT-01 §5). |
| A10 | Revisor funcional | Reconstruir la cadena de CP-04A. | V01 → conformidad → SOL-01 → EVA-A y EVA-D → RES-01 condicionada → renegociación → V02 → conformidad → SOL-02, sin orden confirmada en ningún punto. La evaluación de SOL-02 queda fuera del subescenario. |

### CP-04B: solicitud rechazada

| Paso | Actor | Acción | Resultado esperado |
|---|---|---|---|
| B1 | VEN | Registrar la conformidad del cliente con COT-SIM-005-V01 vigente. | Aceptación vinculada a V01 (EV-006, TR-14); oportunidad sin «Ganada». |
| B2 | VEN | Presentar SOL-SIM-005-01 con las condiciones de V01. | Solicitud con referencias, líneas, fecha y responsable (EV-009, TR-15, RN-005). |
| B3 | CMP y ALM; GER para el faltante | Evaluar el abastecimiento del porcelanato. | EVA-SIM-005-A **no viable**, con fundamento (modelo descontinuado y sin proveedor alternativo [SIM]), responsable, fecha y soporte (EV-010, TR-16). |
| B4 | Evaluador designado | Emitir la respuesta con su motivo. | RES-SIM-005-01 **rechazada**, con motivo, responsable y fecha (TR-17, EXC-001). EV-014 se cita solo como candidato con la correspondencia pendiente. Si el procedimiento definido exige también la evaluación de despacho, se registra; el escenario no la requiere [SIM]. |
| B5 | VEN; revisor funcional | Registrar el retorno al CRM y comprobar que no hay confirmación. | Respuesta y motivo visibles en OPP-SIM-005; no existe orden confirmada ni EV-018; la evaluación conserva su historial (RN-006, TR-17, TR-18). El rechazo no se registra como EV-007. |
| B5b | SIS y revisor (opcional) | Mismo control técnico que A6b, con la solicitud rechazada. | Restricción técnica registrada, o brecha técnica anotada. |
| B6 | VEN | Comunicar el rechazo; el cliente no acepta alternativas [SIM]. Registrar el cierre comercial con su motivo. | Oportunidad cerrada sin «Ganada», con motivo y fecha; SOL-01, EVA-A y RES-01 conservados. Si el cliente hubiese aceptado otra propuesta, se seguiría la renegociación de CP-04A (pasos A7 a A9); esa variante no se ejecuta aquí. |
| B7 | Revisor funcional | Reconstruir la cadena de CP-04B. | V01 → conformidad → SOL-01 → EVA-A no viable → RES-01 rechazada → retorno y cierre comercial, sin orden confirmada. |

## 5. Evidencias necesarias

| Pasos | Evidencia por recoger |
|---|---|
| A1, A8 y B1 | Soporte de cada conformidad, con fecha, medio y vínculo con la versión exacta. V01 y V02 de CP-04A se conservan por separado. |
| A2, A9 y B2 | Representación de cada solicitud según PEN-016, con sus datos mínimos (INT-01 §4); vínculo de SOL-SIM-004-02 con SOL-SIM-004-01. |
| A3, A4 y B3 | Registro de cada evaluación: criterio, resultado, fundamento, responsable, fecha y soporte, incluida la existencia consultada y la constancia de que no se reservó. |
| A5 y B4 | Respuesta con resultado, motivo, condiciones requeridas (CP-04A), responsable y fecha. |
| A6, B5 y B6 | Historial del CRM y del documento de Ventas sin confirmación; estado de la oportunidad; registro del cierre comercial con su motivo (CP-04B). |
| A6b y B5b | Resultado de la comprobación técnica opcional, o la constancia de que no se realizó. |
| A7 | Soporte de las nuevas condiciones acordadas (EV-016). |
| A10 y B7 | Tabla de reconstrucción de cada cadena, con las discrepancias encontradas. |

## 6. Criterios de aceptación y fallo

**CP-04A cumple** cuando la respuesta condicionada registra su motivo y las condiciones requeridas, retorna al CRM y no permite una confirmación funcional; cuando no se reservan unidades faltantes; y cuando la renegociación produce V02 y una nueva conformidad, y SOL-02 queda vinculada a SOL-01, que se conserva sin reutilizarse.

**CP-04B cumple** cuando la respuesta rechazada registra su motivo, el historial de evaluación se conserva, la gestión retorna al CRM sin orden confirmada y el cierre comercial se registra con su motivo, sin «Ganada».

**El caso falla** si se confirma una orden con una respuesta condicionada o rechazada; si falta el motivo de una respuesta no aceptada; si se sobrescriben V01, SOL-01 o sus evaluaciones; si la nueva solicitud no se vincula a la anterior; si la respuesta condicionada se registra como EV-014 o el rechazo de la solicitud como EV-007; si se reservan unidades no disponibles o se presenta la reposición como existencia; o si la oportunidad se marca «Ganada».

Se consigna como **bloqueo o brecha**, y no como éxito ni fallo:

- la falta de un mecanismo acordado para la solicitud y su vínculo (PEN-016);
- la falta de designación, siquiera provisional, del evaluador (PEN-018);
- la inexistencia de una restricción técnica que impida confirmar con una respuesta no aceptada (pasos A6b y B5b). En ese caso el control es procedimental conforme a INT-01 §9.

La clasificación «condicionada» o «rechazada» del ensayo no se evalúa como acierto ni error empresarial, porque su criterio sigue pendiente en PEN-020.

## 7. Resultado obtenido, estado de ejecución y limitaciones

| Subescenario | Estado | Resultado observado | Evidencia recogida | Fecha y responsable |
|---|---|---|---|---|
| CP-04A | **No ejecutado** | No existe resultado observado. | Ninguna. | Pendientes. |
| CP-04B | **No ejecutado** | No existe resultado observado. | Ninguna. | Pendientes. |

La ejecución futura debe registrar la versión y los módulos de Odoo 19, los usuarios y sus roles, el mecanismo usado para la solicitud y el vínculo entre solicitudes, las designaciones provisionales, los datos cargados, los resultados observados, las diferencias y los soportes.

Este caso no define el criterio entre respuestas condicionadas y rechazadas (PEN-020), no resuelve las equivalencias con EV-009 y EV-014 y no acredita estados, campos ni restricciones configurados en Odoo. Tampoco fija plazos de reposición, políticas de disponibilidad ni reglas de transporte. La evaluación de SOL-SIM-004-02 y la eventual confirmación posterior siguen el recorrido de [CP-03](CP-03-solicitud-aceptada.md). Las causas del ensayo y las elecciones de los clientes son supuestos [SIM], no decisiones de MIGAL.
