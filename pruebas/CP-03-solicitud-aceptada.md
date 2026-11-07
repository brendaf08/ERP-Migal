# CP-03: Solicitud de orden de venta aceptada y confirmación posterior

## 1. Identificación, objetivo y alcance

| Elemento | Definición |
|---|---|
| Identificador | CP-03 |
| Proceso | Frontera CRM–ERP, transición del tramo comercial a la ejecución de [O2C](../procesos/o2c/flujo.md) |
| Tipo de escenario | Normal, con datos enteramente **sintéticos [SIM]** |
| Estado de ejecución | **No ejecutado** |
| Responsables funcionales | VEN registra la aceptación y presenta la solicitud; CMP y ALM aportan las evaluaciones; el evaluador ([PEN-018](../producto/registro-pendientes.md)) y el confirmador ([PEN-019](../producto/registro-pendientes.md)) están por designar; GER supervisa. SIS prepara un entorno autorizado. |

El objetivo es comprobar que una cotización aceptada por el cliente recorre la frontera definida en [ADR-004](../arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md) e [INT-01](../arquitectura/integraciones/INT-01-CRM-ERP.md). VEN presenta la **solicitud interna de orden de venta** y se registran las evaluaciones de abastecimiento y despacho. La respuesta resulta **aceptada** y solo después la orden de venta se confirma. El caso comprueba también que la sola aceptación comercial no confirma la orden. La base es [Odoo 19 Community](../arquitectura/decisiones/ADR-005-cambio-version-Odoo-18-Community-a-Odoo-19-Community.md), con [Odoo CRM](../arquitectura/decisiones/ADR-006-adopcion-crm-odoo.md) en la misma instancia.

**Límite:** el caso termina con la orden de venta confirmada y la cadena documental reconstruida. No prueba la reserva, la preparación, el despacho, la entrega, la emisión en KeyFacil ni el cobro, que continúan en [O2C](../procesos/o2c/flujo.md). Las respuestas condicionada y rechazada se prueban en [CP-04](CP-04-solicitud-condicionada-rechazada.md).

El caso distingue dos tipos de comprobación:

- **Resultado funcional esperado:** lo que el diseño vigente exige que ocurra y quede registrado.
- **Mecanismo técnico por validar:** cómo lo soporta Odoo 19. Al ejecutar se registra si existe o no; no se presupone. En particular, Odoo no ofrece de forma estándar un documento de solicitud de orden de venta, y la cotización y la orden son un mismo registro (`sale.order`) que cambia de estado (INT-01 §9).

## 2. Requisitos y trazabilidad que se verifican

| Criterio | Referencias vigentes | Alcance en CP-03 |
|---|---|---|
| Cotización identificable y vigente | RN-002, CT-002; EV-003/EV-004; TR-03 | Verificar que V01 existe, que se comunicó y que su condición de vigencia del ensayo seguía aplicable al aceptarse. No se fija una vigencia universal. |
| Conformidad del cliente con una versión concreta | RN-002/RN-003, CT-002; EV-006; TR-14 | Vincular la aceptación exclusivamente a V01, con fecha, medio y soporte. La aceptación no confirma la orden. |
| Presentación de la solicitud interna | RN-005, CT-003; EV-009; TR-15 | Presentar la solicitud con las referencias y condiciones aceptadas. EV-009 se usa como hecho de presentación (TR-15). |
| Evaluaciones de abastecimiento y despacho | RN-006, RN-015, CT-003, CT-008; EV-010/EV-012; TR-16 | Registrar el criterio, el resultado (favorable, condicionado o no viable), el responsable, la fecha y el soporte. Consultar la disponibilidad no reserva unidades. |
| Verificación de autorizaciones | RN-004, CT-002 | Comprobar que no existen precio, descuento ni crédito especiales pendientes de decisión de GER. |
| Respuesta aceptada | RN-006, CT-003; TR-17 | Registrar la respuesta aceptada con su responsable y fecha. EV-014 es solo candidato; véase la tabla de correspondencias. |
| Confirmación posterior de la orden | RN-006/RN-008, CT-003; EV-018; TR-18 | Confirmar la orden solo después de la respuesta aceptada, con referencia a la solicitud. La oportunidad se marca «Ganada» únicamente tras la confirmación. |
| Ausencia de confirmación por la sola aceptación | RN-006, CT-003; TR-18 | Comprobar que entre la aceptación y la respuesta aceptada no existe orden confirmada. |

Los identificadores RN y CT proceden del [catálogo de reglas](../procesos/catalogo-reglas.md); los EV, del [catálogo central de eventos](../procesos/catalogo-eventos.md); los TR, del [plan de trazabilidad](../datos/trazabilidad/plan-trazabilidad-auditoria.md). Los objetos funcionales siguen el [diccionario de datos](../datos/diccionario-datos.md), apartado 3.

### Correspondencia entre los códigos locales de INT-01 y el catálogo central

INT-01 utiliza códigos **locales** EV-01 a EV-07, que no son identificadores del catálogo central. En este caso se registran los EV centrales y se conserva el estado de cada correspondencia tal como lo establece INT-01 §3:

| Hecho del caso | Código local de INT-01 | EV central | Estado de la correspondencia |
|---|---|---|---|
| Cotización aceptada por el cliente | EV-01 | EV-006 | Confirmada. |
| Solicitud de orden de venta presentada o registrada | EV-02 | EV-009 | Pendiente: confirmar si «registrada» y «presentada» son el mismo hecho. |
| Evaluación de abastecimiento | — | EV-010 | Evento central propio; su resultado es favorable, condicionado o no viable. |
| Evaluación de despacho | — | EV-012 | Evento central propio; mismos resultados posibles. |
| Respuesta aceptada | EV-03 | EV-014 (candidato) | Pendiente: EV-014 expresa «aprobar o rechazar». La aceptación se conserva como estado funcional diferenciado y no se declara equivalente. |
| Orden de venta confirmada | EV-06 | EV-018 | Confirmada, sujeta a la precondición de respuesta aceptada. |

## 3. Precondiciones y datos de prueba

### Condiciones de ejecución

Antes de ejecutar, SIS y el responsable de la prueba deben identificar una instancia autorizada de Odoo 19, su versión, los módulos instalados (`crm`, `sale_management`, `sale_crm`, `stock`, `sale_stock` y `contacts`), los usuarios y los permisos efectivos. Si CRM, Ventas o Inventario no están disponibles, el caso queda **bloqueado**, no fallido. Los registros [SIM] solo se cargan en un entorno permitido y no se envían propuestas a destinatarios externos reales.

La ejecución depende de los siguientes pendientes:

| Pendiente | Efecto sobre la ejecución |
|---|---|
| [PEN-016](../producto/registro-pendientes.md): mecanismo de representación de la solicitud | Debe registrarse qué mecanismo representa la solicitud, su evaluación y su respuesta (por ejemplo, la propuesta preliminar A+B de INT-01 §9: estado o etiqueta sobre la cotización y actividad asignada al evaluador). Si no hay ningún mecanismo acordado, el caso queda **bloqueado**. |
| [PEN-018](../producto/registro-pendientes.md): responsable de la evaluación | Mientras siga abierto, la ejecución no valida la asignación del rol. GER puede autorizar una **designación provisional solo para el ensayo**, registrada como supuesto [SIM]; su resultado no cierra PEN-018. |
| [PEN-019](../producto/registro-pendientes.md): responsable de la confirmación | Mismo tratamiento que PEN-018. El análisis de roles asigna a VEN la confirmación de órdenes ordinarias, pero INT-01 §7 deja su autorización por definir; el caso no resuelve esa diferencia. |
| [PEN-004](../producto/registro-pendientes.md) y [PEN-005](../producto/registro-pendientes.md): permisos | Solo afectan a la comprobación opcional de restricciones de usuario (paso 3b). Sin permisos verificados, esa comprobación se registra como no realizada. |

### Separación entre decisiones vigentes y supuestos de prueba

| Tipo | Contenido en CP-03 |
|---|---|
| Decisión vigente | La aceptación comercial no confirma la orden (ADR-004, RN-006). La solicitud la presenta VEN (RN-005). Solo una respuesta aceptada habilita la confirmación (RN-006). La oportunidad se marca «Ganada» al confirmarse la orden (RN-008). |
| Supuesto de prueba [SIM] | Clientes, materiales, cantidades, precios, existencias, condición de pago al contado, fecha de entrega de prueba, resultados favorables de las evaluaciones y designaciones provisionales del evaluador y el confirmador. |
| Pendiente | Vigencia general de las cotizaciones (PEN-015), mecanismo de la solicitud (PEN-016), evaluador (PEN-018), confirmador (PEN-019) y equivalencia de la respuesta aceptada con EV-014. |

### Datos sintéticos

| Referencia local [SIM] | Dato del escenario | Uso |
|---|---|---|
| CLI-SIM-003 | Ana María Quispe Rojas | Cliente responsable económico de una obra ficticia. |
| CON-SIM-005 | Ana María Quispe Rojas | Contacto que acepta la propuesta. |
| CON-SIM-006 | Ricardo Alonso Vega Huertas | Maestro de obra que coordina los materiales; no sustituye a la cliente. |
| DIR-SIM-002 | Vivienda de dos pisos, Los Olivos | Destino de entrega acordado para el ensayo. |
| OPP-SIM-003 | Materiales para techo del primer piso | Oportunidad en seguimiento por VEN. |
| COT-SIM-003-V01 | Versión única de la cotización | Propuesta aceptada por la cliente. |
| SOL-SIM-003-01 | Solicitud interna de orden de venta | Referencia local de prueba; no es un documento ni un campo nativo de Odoo. |
| EVA-SIM-003-A y EVA-SIM-003-D | Evaluaciones de abastecimiento y de despacho | Referencias locales de las evaluaciones. |
| RES-SIM-003-01 | Respuesta a la solicitud | Resultado **aceptado** en el escenario. |
| OV-SIM-003 | Orden de venta confirmada | Representa la confirmación del mismo documento de Ventas. |

| Línea [SIM] | Material | Cantidad | Precio unitario referencial | Importe referencial |
|---|---|---:|---:|---:|
| 1 | Cemento Portland tipo I, 42.5 kg | 150 bolsas | S/ 31.00 | S/ 4,650.00 |
| 2 | Fierro corrugado 1/2" × 9 m | 80 varillas | S/ 40.50 | S/ 3,240.00 |
| 3 | Alambre negro N.° 16 | 10 kg | S/ 6.50 | S/ 65.00 |
| | **Subtotal de líneas** | | | **S/ 7,955.00** |

Comprobación numérica: 150 × 31.00 + 80 × 40.50 + 10 × 6.50 = 4,650.00 + 3,240.00 + 65.00 = **S/ 7,955.00**. Es un subtotal referencial, sin impuestos ni transporte y sin valor fiscal.

La propuesta no incluye descuento especial ni crédito, de modo que no requiere decisión de GER (RN-004). La condición de pago (al contado) y la fecha de entrega se fijan **solo para el ensayo [SIM]**. Las existencias registradas para el ensayo cubren las cantidades solicitadas (cemento 400 bolsas, fierro 200 varillas, alambre 50 kg [SIM]); ALM las contrasta físicamente si hay duda (CT-008). Estos valores no son precios, existencias ni condiciones vigentes de MIGAL.

## 4. Procedimiento reproducible

| Paso | Actor | Acción | Resultado esperado |
|---|---|---|---|
| 1 | VEN | Verificar que COT-SIM-003-V01 existe, se vincula con OPP-SIM-003 y CLI-SIM-003 y se comunicó con las condiciones del ensayo. | V01 identificable, con líneas, subtotal S/ 7,955.00, fecha de comunicación y condición de vigencia aplicable (TR-03, RN-002). |
| 2 | VEN | Registrar la conformidad de la cliente con V01: medio, fecha y soporte. | Aceptación vinculada solo a V01 (EV-006, TR-14). OPP-SIM-003 permanece en seguimiento, sin marca «Ganada» (RN-008). |
| 3 | Revisor funcional | Comprobar que tras la aceptación no existe orden confirmada. | El documento de Ventas sigue sin confirmar; no hay EV-018 (CT-003, TR-18). |
| 3b | SIS y revisor (opcional) | Solo en un registro descartable COT-SIM-003-X, distinto de la cadena principal, comprobar si Odoo permite confirmar una cotización aceptada sin solicitud aceptada. | Se registra si existe o no una restricción técnica. Si Odoo permite confirmar, se anota una **brecha técnica**: el control es procedimental (INT-01 §9, PEN-016). No se modifica la cadena principal. |
| 4 | VEN | Presentar SOL-SIM-003-01 con las condiciones aceptadas, mediante el mecanismo registrado para PEN-016. | Solicitud con referencia a OPP-SIM-003 y V01, cliente responsable, contacto, destino, líneas, condición de pago, requerimiento de entrega, fecha y responsable (EV-009, TR-15, RN-005). No es una orden confirmada. |
| 5 | CMP y ALM | Evaluar el abastecimiento: existencias por ubicación y, si procede, disponibilidad con proveedores. | EVA-SIM-003-A con resultado **favorable**, fundamento, responsable, fecha y soporte (EV-010, TR-16). La consulta no crea una reserva (RN-015, CT-008). |
| 6 | ALM | Evaluar el despacho: materiales, destino DIR-SIM-002, acceso, carga y recursos de la fecha de prueba. | EVA-SIM-003-D con resultado **favorable**, fundamento, responsable, fecha y soporte (EV-012, TR-16). |
| 7 | Evaluador designado | Comprobar las autorizaciones aplicables y consolidar las evaluaciones en una respuesta. | Constancia de que no hay precio, descuento ni crédito especiales pendientes (RN-004, CT-002). RES-SIM-003-01 **aceptada**, con responsable y fecha (TR-17, RN-006). |
| 8 | VEN | Registrar en el CRM la respuesta aceptada recibida. | La respuesta aceptada es visible en la oportunidad, sin cambio automático a «Ganada». |
| 9 | Confirmador designado | Confirmar la orden de venta tomando como origen SOL-SIM-003-01 aceptada. | OV-SIM-003 confirmada, con referencia a la solicitud y sus condiciones, responsable y fecha (EV-018, TR-18, RN-006). |
| 10 | VEN | Marcar OPP-SIM-003 como «Ganada» después de la confirmación. | El cambio de estado es posterior a EV-018 (RN-008). |
| 11 | Revisor funcional | Reconstruir la cadena y comprobar el orden y la coincidencia de las condiciones. | Cadena V01 → conformidad → SOL-SIM-003-01 → EVA-A y EVA-D → RES-SIM-003-01 → OV-SIM-003 recuperable desde cualquiera de sus elementos. Las fechas siguen ese orden y las condiciones de la orden coinciden con las aceptadas (CT-002, CT-003, TR-14 a TR-18). |

## 5. Evidencias necesarias

| Paso | Evidencia por recoger |
|---|---|
| 1 | Registro o captura de V01 con sus líneas, su subtotal, la fecha de comunicación y la condición de vigencia del ensayo. |
| 2 | Soporte de la conformidad (mensaje simulado o constancia de VEN), fecha y vínculo con V01; estado de la oportunidad. |
| 3 | Estado del documento de Ventas tras la aceptación y su historial. |
| 3b | Resultado de la comprobación técnica en COT-SIM-003-X, con fecha, usuario y versión de Odoo, o la constancia de que no se realizó. |
| 4 | Representación de SOL-SIM-003-01 según PEN-016 (estado, etiqueta, actividad u otro), con sus datos mínimos (INT-01 §4). |
| 5 y 6 | Registro de cada evaluación: criterio, resultado, fundamento, responsable, fecha y soporte. |
| 7 | Constancia de la verificación de autorizaciones y de la respuesta aceptada, con responsable y fecha. |
| 8 a 10 | Historial del CRM y del documento de Ventas con la respuesta, la confirmación y el cambio a «Ganada», en orden cronológico. |
| 11 | Tabla de reconstrucción de la cadena elaborada por el revisor, con las discrepancias encontradas. |

## 6. Criterios de aceptación y fallo

El caso **cumple** cuando la aceptación se vincula a V01 vigente; la solicitud se presenta después de la aceptación y conserva sus referencias y condiciones; las dos evaluaciones quedan registradas con responsable, fecha y soporte; la respuesta aceptada precede a la confirmación; la orden confirmada remite a la solicitud aceptada y mantiene las condiciones aceptadas; y la oportunidad pasa a «Ganada» solo después de la confirmación.

El caso **falla** si la orden se confirma antes de la respuesta aceptada o sin referencia a la solicitud; si la aceptación se registra sobre una versión distinta de V01; si se pierde o se sobrescribe una evaluación; si las condiciones confirmadas difieren de las aceptadas sin nueva conformidad; o si la oportunidad se marca «Ganada» al aceptar la cotización.

Se consigna como **bloqueo o brecha**, y no como éxito ni fallo:

- la ausencia de un mecanismo acordado para la solicitud (PEN-016);
- la falta de designación, siquiera provisional, del evaluador o del confirmador (PEN-018, PEN-019);
- la inexistencia de una restricción técnica que impida confirmar sin respuesta aceptada (paso 3b). En ese caso el control es procedimental conforme a INT-01 §9, y el caso puede cumplir si la cadena principal respeta el orden.

## 7. Resultado obtenido, estado de ejecución y limitaciones

| Estado | Resultado observado | Evidencia recogida | Fecha y responsable |
|---|---|---|---|
| **No ejecutado** | No existe resultado observado. | Ninguna; la sección 5 describe las evidencias por obtener. | Pendientes. |

La ejecución futura debe registrar la versión y los módulos de Odoo 19, los usuarios y sus roles, el mecanismo usado para la solicitud, las designaciones provisionales si las hubo, los datos cargados, los resultados observados, las diferencias y los soportes.

Este caso no acredita la configuración de campos, estados o restricciones de Odoo, la equivalencia de la respuesta aceptada con EV-014 ni la asignación definitiva de los roles de evaluación y confirmación. Tampoco prueba la reserva, el despacho, la entrega, el comprobante en KeyFacil ni el cobro, que corresponden a [O2C](../procesos/o2c/flujo.md) y a sus casos posteriores. Una designación provisional usada en el ensayo no constituye una decisión de MIGAL.
