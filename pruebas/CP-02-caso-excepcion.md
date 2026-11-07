# CP-02: Negociación excepcional de precio frente a la competencia

## 1. Identificación, objetivo y alcance

| Elemento | Definición |
|---|---|
| Identificador | CP-02 |
| Proceso | Gestión comercial CRM, tramo inicial de [O2C](../procesos/o2c/flujo.md) |
| Tipo de escenario | Excepción comercial con datos enteramente **sintéticos [SIM]** |
| Estado de ejecución | **No ejecutado** |
| Responsables funcionales | VEN plantea y documenta; GER evalúa y decide la excepción. SIS prepara un entorno autorizado. |

El objetivo es comprobar que una solicitud de mejora de precio por competencia no permite a VEN modificar unilateralmente la oferta; que GER decide con motivo y alcance identificables; que cada versión de cotización conserva sus condiciones; y que la elección comercial de una línea no transforma automáticamente la oportunidad en «Ganada» o «Ganada parcial».

El caso comprende V01, la propuesta excepcional V02, la selección de cemento por el cliente y una V03 limitada a esa línea, cuya conformidad se registra si continúa vigente. **Termina antes de presentar una solicitud interna de orden de venta.** No prueba su evaluación, respuesta, confirmación, reserva, despacho, entrega, emisión KeyFacil ni cobro. Conforme a [ADR-004](../arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md) e [INT-01](../arquitectura/integraciones/INT-01-CRM-ERP.md), la aceptación de V03 no confirma una orden. El uso de CRM y la base Odoo 19 proceden de [ADR-006](../arquitectura/decisiones/ADR-006-adopcion-crm-odoo.md) y [ADR-005](../arquitectura/decisiones/ADR-005-cambio-version-Odoo-18-Community-a-Odoo-19-Community.md).

## 2. Requisitos y trazabilidad que se verifican

| Criterio | Referencias vigentes | Alcance en CP-02 |
|---|---|---|
| Excepción de precio decidida por GER | RN-004, CT-002, EXC-002; EV-053; TR-04 | Conservar solicitud VEN, decisión GER, líneas, motivo, fecha y precios autorizados. No se presupone porcentaje máximo ni bloqueo automático. |
| Versiones y condiciones de cotización | RN-002/RN-003, CT-002; EV-003/EV-004; TR-03 | Comparar V01, V02 y V03 sin sobrescribir antecedentes. EV-005 solo se registra cuando exista modificación acordada, no por la autorización interna aislada. |
| Conformidad del cliente con propuesta concreta | RN-002/RN-003, CT-002; EV-006; TR-14 | Si el cliente acepta, vincular su conformidad exclusivamente a V03 y sus condiciones vigentes. |
| Estado de la oportunidad | RN-008; TR-02 | Mantenerla en seguimiento mientras no exista orden confirmada; registrar por separado el resultado de cemento y fierro. |
| Frontera comercial–operativa | RN-005/RN-006, CT-003; TR-15/TR-16/TR-17/TR-18 | Son referencias para el recorrido posterior, **no verificaciones ejecutadas en este caso**. No se inventa equivalencia para una respuesta condicionada. |

RN, CT y EXC se definen en el [catálogo de reglas](../procesos/catalogo-reglas.md); EV en el [catálogo central de eventos](../procesos/catalogo-eventos.md); TR en el [plan de trazabilidad](../datos/trazabilidad/plan-trazabilidad-auditoria.md). La adjudicación comercial de una línea describe la elección del cliente; no acredita venta confirmada, entrega ni cobro.

## 3. Precondiciones y datos de prueba

El caso se ejecutará únicamente en una instancia autorizada de Odoo 19 con CRM, Contactos y Ventas disponibles, versiones o evidencias equivalentes identificables y usuarios que permitan distinguir las actuaciones VEN y GER. La existencia de esos mecanismos y permisos debe verificarse al ejecutar. Una persona puede reunir ambos roles, pero la solicitud y la decisión deben quedar diferenciadas; no se presupone una segregación técnica ya configurada. Si no hay entorno, soporte de versiones o participación GER para la simulación, el caso queda **bloqueado**.

Los importes y la decisión favorable a V02 son **supuestos de prueba [SIM]**, no precios, márgenes, límites ni autorizaciones empresariales vigentes. El precio exacto de la competencia no consta en el escenario: solo se simula que el cliente solicita una mejora para fierro. GER debe registrar durante la prueba una decisión sobre cada ajuste antes de que VEN lo comunique. La vigencia concreta de cada versión se determina y registra para el ensayo antes de comunicarla; no se adopta un plazo general de MIGAL. No se envían propuestas a clientes reales.

| Referencia local [SIM] | Dato del escenario | Uso |
|---|---|---|
| CLI-SIM-002 | Julio César Rojas Cárdenas | Cliente de una obra ficticia y decisor comercial. |
| CON-SIM-003 | Julio César Rojas Cárdenas | Contacto que comunica la elección de materiales. |
| CON-SIM-004 | Víctor Hugo Palomino Chacón | Maestro de obra que informa de la competencia. |
| OPP-SIM-002 | Cemento y fierro para columnas | Oportunidad en seguimiento por VEN. |
| DEC-SIM-001 | Decisión excepcional de GER para el ensayo | Referencia local a motivos y precios por línea; no es un campo nativo de Odoo. |
| COT-SIM-002-V01/V02/V03 | Versiones sucesivas de la oferta | Referencias locales [SIM], conservadas de forma vinculada. |

| Línea [SIM] | Cantidad | V01 unitario | V01 importe | V02 unitario autorizado en la simulación | V02 importe | Selección comunicada |
|---|---:|---:|---:|---:|---:|---|
| Cemento | 80 bolsas | S/ 31.20 | S/ 2,496.00 | S/ 31.00 | S/ 2,480.00 | Cliente elige esta línea. |
| Fierro | 60 unidades | S/ 40.50 | S/ 2,430.00 | S/ 40.10 | S/ 2,406.00 | Cliente no la elige por competencia. |
| **Subtotal de líneas** | | | **S/ 4,926.00** | | **S/ 4,886.00** | |

Comprobación numérica: V01 = 80 × 31.20 + 60 × 40.50 = **S/ 4,926.00**; V02 = 80 × 31.00 + 60 × 40.10 = **S/ 4,886.00**. La reducción **propuesta** en V02 es S/ 16.00 para cemento y S/ 24.00 para fierro, **S/ 40.00** en total. V03 contiene solo 80 bolsas de cemento a S/ 31.00, subtotal **S/ 2,480.00**. La reducción de la línea seleccionada es S/ 16.00; no se presenta la reducción de fierro como beneficio de una venta. Estos son subtotales referenciales, sin impuestos ni transporte y sin valor fiscal.

## 4. Procedimiento reproducible y evidencia

| Paso | Actor | Acción | Resultado esperado y evidencia por recoger |
|---|---|---|---|
| 1 | VEN | Identificar CLI-SIM-002 y contactos; registrar OPP-SIM-002 y preparar V01 con ambas líneas, precios y condiciones de prueba. | Identidades y oportunidad vinculadas; V01 recuperable con subtotal S/ 4,926.00, autor y fecha (TR-02/TR-03). |
| 2 | VEN | Documentar que el cliente solicita una mejora para fierro por competencia. Registrar la referencia de V01 y la línea afectada; no introducir un precio competidor inexistente. | Solicitud atribuible, motivo y alcance; V01 sin sobrescritura. VEN no concede por sí mismo una rebaja (EXC-002). |
| 3 | GER | Evaluar la propuesta de ensayo y decidir los ajustes de cemento por volumen y fierro por competencia, indicando precio autorizado por línea, motivo y fecha. | DEC-SIM-001 o soporte equivalente vinculado a V01; evidencia de GER para S/ 31.00 y S/ 40.10 antes de comunicarlos (TR-04, EV-053 cuando aplique). Si GER no autoriza la simulación, no se emite V02 con esos importes. |
| 4 | VEN | Elaborar V02 a partir de la decisión y cotejar líneas y subtotales sin borrar V01. | V01 y V02 distinguibles; importes S/ 2,480.00 y S/ 2,406.00, subtotal S/ 4,886.00, reducción propuesta S/ 40.00; motivo y autorización vinculados (TR-03/TR-04). |
| 5 | VEN | Comunicar V02 por canal controlado de prueba y registrar que el cliente elige cemento, pero no fierro. No convertir la elección parcial en aceptación de las dos líneas. | Comunicación y respuesta por línea con fecha y fuente; oportunidad todavía en seguimiento. La razón «competencia en fierro» es dato [SIM], no conclusión sobre márgenes de MIGAL. |
| 6 | VEN; GER si cambian condiciones especiales | Preparar V03 solo con cemento a S/ 31.00, conservando V01 y V02. Registrar conformidad del cliente con V03 mientras su condición de vigencia específica continúe aplicable. | V03 por S/ 2,480.00, versión aceptada y soporte de conformidad vinculados; decisión GER preservada (TR-03/TR-14, EV-006). Si no hay conformidad, no se registra aceptación. |
| 7 | VEN; revisor funcional | Revisar el estado de OPP-SIM-002 y la ausencia de documentos de ejecución operativa. | Elección de cemento y pérdida de la línea de fierro documentadas; oportunidad sin marca automática «Ganada» ni «Ganada parcial»; sin solicitud EV-009 ni orden EV-018 (RN-008). |

## 5. Criterios de aceptación y fallo

El caso **cumple** si la decisión GER precede a la comunicación de los precios excepcionales, V01/V02/V03 y sus motivos pueden reconstruirse, los cálculos coinciden, la conformidad se refiere solo a V03 vigente y el resultado por línea se conserva sin confirmar una orden ni cambiar automáticamente la oportunidad a «Ganada». La ausencia de un porcentaje máximo aprobado no se reemplaza con un límite inventado.

El caso **falla** si VEN modifica y comunica precios excepcionales sin decisión GER, se pierde V01, se altera el importe de una línea, se trata V02 completa como aceptada pese a la selección exclusiva de cemento, se registra una conformidad no demostrada o se marca la oportunidad como ganada por la elección o aceptación comercial. Si faltan permisos, soporte de versiones, política aplicable al ensayo o un actor GER disponible, se consigna **bloqueo o brecha de implementación**, no un resultado favorable supuesto.

## 6. Resultado obtenido y limitaciones

| Estado | Resultado observado | Evidencia recogida | Fecha y responsable |
|---|---|---|---|
| **No ejecutado** | No existe resultado observado. | Ninguna; la sección 4 describe evidencias por obtener. | Pendientes. |

La ejecución posterior debe registrar versión y módulos de Odoo 19, usuarios, roles, condiciones de vigencia del ensayo, capturas o soportes, resultados y diferencias. La representación técnica de versiones, aprobaciones y estados de CRM permanece por comprobar. Si se decidiera continuar hasta una venta, VEN tendría que presentar la [solicitud interna](../arquitectura/integraciones/INT-01-CRM-ERP.md), obtener evaluaciones y respuesta aceptada antes de confirmar la orden; una respuesta condicionada o rechazada volvería a CRM. Este caso **no** ensaya esas transiciones ni reservas, pagos o KeyFacil. La negociación comercial tampoco acredita existencias o abastecimiento, tratados en [inventario](../procesos/inventario/flujo.md) y [P2P](../procesos/p2p/flujo.md).
