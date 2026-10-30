# INT-01: Transición entre CRM y ERP en Odoo

- **Fecha:** 2026-10-29
- **Estado:** Propuesto
- **Responsable(s):** Equipo ERP-MIGAL
- **Decisiones relacionadas:** [ADR-004](../decisiones/ADR-004-odoo-community-fronteras-crm-erp.md)
- **Versión de arquitectura:** [VER-02](../versiones/VER-02-crm-erp.md)

Este documento es la referencia de los identificadores `INT`, `EV` y `F`. Especifica la frontera funcional entre la gestión comercial (CRM) y la ejecución empresarial (ERP) establecida en ADR-004. El contenido corresponde a la solución propuesta (TO-BE) y no acredita su implementación en Odoo.

## 1. Propósito y alcance

La gestión comercial de MIGAL produce compromisos con el cliente, mientras que la ejecución del pedido depende de condiciones operativas que solamente pueden verificarse en el ERP: existencias, autorizaciones y capacidad de atención. ADR-004 establece que **la aceptación de una cotización por el cliente no equivale a la confirmación de un pedido de venta**.

Esta integración especifica cómo se cruza esa frontera: qué evento la activa, qué información se transfiere, quién evalúa la solicitud y cuáles son los resultados posibles.

**Comprende:** desde la aceptación de la cotización por el cliente hasta la habilitación de la confirmación del pedido de venta, o el retorno de la gestión al ámbito comercial.

**No comprende:**

- La ejecución posterior del pedido (reserva, entrega, facturación y cobro), documentada en el proceso Order to Cash.
- La emisión de comprobantes con KeyFacil, pendiente de definición ([PEN-003](../../producto/registro-pendientes.md)).
- La comunicación con el cliente por WhatsApp o llamadas, cuyo registro en Odoo es manual.

## 2. Sistemas, aplicaciones y fronteras

CRM y ERP forman parte de una misma plataforma Odoo. La frontera es una separación de responsabilidades de negocio, no una separación técnica entre módulos ni una integración con un sistema independiente (ADR-004).

| Participante | Tipo | Responsabilidad en la integración |
|---|---|---|
| CRM (`crm`) | Aplicación de Odoo | Gestiona leads y oportunidades. Origina la solicitud de pedido. |
| Ventas (`sale_management`) | Aplicación de Odoo | Mantiene la cotización y, cuando se habilita, el pedido de venta. |
| Inventario (`stock`) | Aplicación de Odoo | Aporta la disponibilidad de productos para la evaluación. |
| Contactos (`contacts`) | Aplicación de Odoo | Mantiene los datos compartidos de clientes y contactos. |
| Conversaciones (`mail`) | Módulo requerido | Conserva el historial de actividades y mensajes de cada documento. |

| Frontera | Origen | Destino | Tipo de integración | Descripción |
|---|---|---|---|---|
| F-01 | CRM | ERP (Ventas e Inventario) | Interna a Odoo | Solicitud de pedido con las condiciones aceptadas por el cliente. |
| F-02 | ERP | CRM | Interna a Odoo | Resultado de la evaluación: aceptada, condicionada o rechazada. |

La relación entre aplicaciones y módulos se representa en la vista [Aplicaciones seleccionadas](../vistas/fuentes/c4-contenedores.puml) y en la vista [Módulos de Odoo y sus dependencias](../vistas/fuentes/c4-modulos-dependencias.puml).

## 3. Eventos

| ID | Evento | Origen | Destino | Disparador | Precondiciones | Resultado |
|---|---|---|---|---|---|---|
| EV-01 | Cotización aceptada por el cliente | CRM | CRM | El cliente comunica su aceptación, de forma presencial, por WhatsApp o por llamada. VEN la registra manualmente. | Oportunidad con una cotización emitida. Precios y descuentos especiales autorizados por GER, cuando correspondan. | Aceptación documentada. Habilita EV-02. |
| EV-02 | Solicitud de pedido registrada | CRM | ERP (F-01) | VEN genera la solicitud a partir de la cotización aceptada. | EV-01 completado. Información mínima completa (apartado 4). | El ERP dispone de las condiciones por evaluar. |
| EV-03 | Solicitud aceptada | ERP | CRM y ERP (F-02) | La evaluación concluye que se cumplen disponibilidad, autorizaciones y viabilidad de atención. | EV-02 completado. | Se habilita la confirmación del pedido de venta. |
| EV-04 | Solicitud condicionada | ERP | CRM (F-02) | La evaluación concluye que la atención es posible únicamente si se modifican las condiciones. | EV-02 completado. | La gestión retorna al ámbito comercial con las condiciones requeridas. |
| EV-05 | Solicitud rechazada | ERP | CRM (F-02) | La evaluación concluye que la solicitud no puede atenderse. | EV-02 completado. | La gestión retorna al ámbito comercial con el motivo del rechazo. |
| EV-06 | Pedido de venta confirmado | ERP | ERP | Un responsable autorizado confirma el pedido. | EV-03 completado. | El pedido continúa su ejecución operativa. |
| EV-07 | Condiciones renegociadas | CRM | CRM | El cliente y MIGAL acuerdan nuevas condiciones tras EV-04 o EV-05. | EV-04 o EV-05 completado. | Se reinicia el flujo desde EV-01 con las condiciones actualizadas. |

Los eventos describen hechos de negocio. No presuponen un mecanismo técnico determinado.

## 4. Información intercambiada

Las definiciones de cada dato se conservan en el [diccionario de datos](../../datos/diccionario-datos.md).

| Dato | Origen | Destino | Obligatorio | Observaciones |
|---|---|---|---|---|
| Referencia de la oportunidad y de la cotización | CRM y Ventas | ERP | Sí | Garantiza la trazabilidad entre oportunidad, cotización, solicitud y pedido (ADR-004). |
| Cliente responsable económico | Contactos | ERP | Sí | Persona o empresa que realiza la compra o asume su responsabilidad económica. |
| Contacto o maestro de obra | Contactos | ERP | Condicionado | Cuando participe en la solicitud o la coordinación del pedido. |
| Obra y dirección de entrega | Contactos | ERP | Condicionado | La dirección de entrega puede diferir del domicilio del cliente. |
| Productos, cantidades y unidades | Ventas | ERP | Sí | Base de la evaluación de disponibilidad. |
| Precios y descuentos acordados | Ventas | ERP | Sí | Los precios o descuentos especiales requieren autorización previa de GER. |
| Condición de pago o crédito | Ventas | ERP | Condicionado | Solo GER decide el otorgamiento o la modificación de créditos. |
| Requerimiento de entrega | Ventas | ERP | Condicionado | Interpretación: se acuerda con el cliente antes de la solicitud. Su estructura está por definir. |
| Resultado de la evaluación | ERP | CRM | Sí | Aceptada, condicionada o rechazada. |
| Motivo y condiciones requeridas | ERP | CRM | Condicionado | Obligatorio cuando el resultado es condicionada o rechazada. |
| Responsable y fecha de la evaluación | ERP | CRM | Sí | Permite identificar quién evaluó y cuándo. |

## 5. Flujo y estados

1. VEN prepara la cotización con los precios y condiciones vigentes. Cuando el cliente solicita negociar precios o descuentos, GER decide y autoriza.
2. El cliente acepta la cotización y VEN registra la aceptación en el CRM (EV-01).
3. VEN registra la solicitud de pedido con las condiciones aceptadas (EV-02, F-01).
4. El ERP evalúa la solicitud según los criterios del apartado siguiente.
5. Si la solicitud es **aceptada**, se habilita la confirmación del pedido de venta y este continúa su ejecución (EV-03 y EV-06).
6. Si la solicitud es **condicionada o rechazada**, la gestión retorna al CRM con el motivo y las condiciones requeridas (EV-04 o EV-05, F-02).
7. Tras una renegociación, el flujo se reinicia con las nuevas condiciones (EV-07). La solicitud anterior se conserva en el historial y no se reutiliza.

### Criterios de evaluación

| Criterio | Aspectos considerados |
|---|---|
| Disponibilidad de productos | Existencias en tienda y almacenes, y disponibilidad con los proveedores. La disponibilidad registrada puede diferir de las existencias físicas. |
| Autorizaciones | Precios, descuentos y créditos autorizados por GER. |
| Viabilidad de atención | Tipo, cantidad y características de los materiales, ubicación y acceso al destino, capacidad de carga y transporte, disponibilidad de vehículos y trabajadores, y entregas ya coordinadas. |

Interpretación: la solicitud se considera aceptada cuando cumple los tres criterios, condicionada cuando puede atenderse si se modifican las condiciones, y rechazada cuando no puede atenderse. Los límites entre estos resultados están por definir.

### Estados de la solicitud

| Estado | Descripción | Transiciones posibles |
|---|---|---|
| Registrada | Solicitud generada a partir de una cotización aceptada. | En evaluación. |
| En evaluación | El ERP verifica disponibilidad, autorizaciones y viabilidad. | Aceptada, Condicionada o Rechazada. |
| Aceptada | Se habilita la confirmación del pedido de venta. | Cierre, una vez confirmado el pedido. |
| Condicionada | La atención depende de modificar las condiciones. | Cierre, al iniciarse una nueva solicitud tras la renegociación. |
| Rechazada | La solicitud no puede atenderse. | Cierre, comercial o por una nueva solicitud tras la renegociación. |

Los estados constituyen una propuesta funcional. No presuponen un campo, un objeto o un flujo específicos en Odoo.

## 6. Reglas, controles y excepciones

Las reglas, controles y excepciones de la integración se incorporan al [catálogo de reglas](../../procesos/catalogo-reglas.md), responsable de sus identificadores. Hasta su incorporación, se referencian por su descripción.

| Condición o control | Aplicación en la integración |
|---|---|
| La aceptación de una cotización no confirma un pedido de venta. | No se confirma un pedido sin una solicitud aceptada. |
| Los precios y descuentos especiales los autoriza GER. | La autorización se verifica antes de EV-02 y durante la evaluación. |
| Solo GER decide créditos. | Una solicitud con crédito no autorizado se registra como condicionada o rechazada. |
| Toda respuesta que no sea aceptada indica su motivo. | El motivo y las condiciones requeridas se registran en EV-04 y EV-05. |
| Cada evento identifica al usuario responsable y la fecha. | Se verifica mediante el historial del documento. |
| La disponibilidad registrada puede diferir de la física. | La evaluación contrasta el registro con las existencias físicas cuando existan dudas. |

### Excepciones

| Situación | Tratamiento previsto |
|---|---|
| El cliente modifica las condiciones después de aceptar. | Se trata como renegociación (EV-07) y se registra una nueva solicitud. |
| Existencias insuficientes o disponibles solo de forma parcial. | La solicitud se condiciona: reducción de cantidades, producto alterno, entrega parcial o espera del abastecimiento. |
| Crédito no autorizado. | La solicitud se condiciona al pago acordado o se rechaza, según la decisión de GER. |
| Entrega inviable por ubicación, acceso o capacidad de transporte. | La solicitud se condiciona a un cambio de fecha, modalidad o destino. |
| Dirección de entrega distinta del domicilio del cliente. | Se registra la obra o dirección de entrega en la solicitud. |
| Cotización sin vigencia fija. | Pendiente de definición: criterio para exigir una actualización previa a la solicitud. |

## 7. Responsabilidades y autorizaciones

Las responsabilidades se derivan del [modelo de autorización](../seguridad/modelo-autorizacion.md) y del [análisis de roles funcionales](../seguridad/analisis-roles-funcionales.md).

| Evento | Prepara | Ejecuta | Autoriza | Verifica |
|---|---|---|---|---|
| EV-01 | VEN | VEN | GER, para precios y descuentos especiales | GER |
| EV-02 | VEN | VEN | — | GER |
| EV-03, EV-04 y EV-05 | ALM, para la disponibilidad | Por definir | GER, para precios, descuentos y créditos | GER |
| EV-06 | VEN | VEN | Por definir | GER |
| EV-07 | VEN | VEN | GER, para nuevas condiciones especiales | GER |

El responsable de ejecutar la evaluación y de autorizar la confirmación del pedido permanece por definir. El análisis de roles asigna a VEN la confirmación de pedidos ordinarios, mientras que ADR-004 exige una verificación previa de la viabilidad operativa.

Los propietarios acumulan los roles GER, VEN y ALM. Cuando una misma persona prepare, evalúe y confirme una solicitud, el control se sustenta en el registro de cada paso con su usuario y fecha, y en la revisión posterior de GER.

## 8. Trazabilidad y auditoría

- **Registro de eventos:** cada evento deja constancia del usuario, la fecha y el resultado en el historial de la oportunidad, la cotización o el pedido.
- **Relación entre documentos:** se conserva la cadena oportunidad, cotización, solicitud de pedido y pedido de venta, de modo que cada registro pueda reconstruirse desde cualquiera de los demás.
- **Decisiones:** la evaluación conserva el responsable, la fecha, el resultado y, cuando corresponda, el motivo y las condiciones requeridas.
- **Referencia:** [Plan de trazabilidad y auditoría](../../datos/trazabilidad/plan-trazabilidad-auditoria.md).

El historial depende del módulo Conversaciones (`mail`). Su configuración y el hábito de registrar las acciones en Odoo se consideran en el riesgo [RSK-005](../riesgos-y-controles.md).

## 9. Implementación en Odoo

| Elemento | Módulo o mecanismo | Clasificación |
|---|---|---|
| Oportunidad y cotización | `crm` y `sale_management`, vinculados mediante el módulo de enlace `sale_crm`, que se instala automáticamente | Propuesto |
| Clientes y contactos compartidos | `contacts` | Propuesto |
| Consulta de disponibilidad | `stock` y el módulo de enlace `sale_stock` | Propuesto |
| Historial de eventos y decisiones | `mail` | Propuesto |
| Representación de la solicitud de pedido | Por definir (alternativas a continuación) | Por validar |
| Restricción técnica de confirmación sin solicitud aceptada | Configuración de grupos o desarrollo adicional | Por validar |

### Alternativas para representar la solicitud

ADR-004 no exige crear un objeto nuevo en Odoo. Se consideran las siguientes alternativas:

| Alternativa | Ventajas | Limitaciones |
|---|---|---|
| **A. Estado o etiqueta sobre la cotización** | Menor intervención en la plataforma. | No impide técnicamente confirmar el pedido sin evaluación. |
| **B. Actividad de Odoo asignada al evaluador, con registro en el historial** | Utiliza funciones estándar y deja constancia del responsable y la fecha. | El control es procedimental. |
| **C. Objeto propio de Odoo** | Permite estados explícitos y un control técnico de la transición. | Requiere desarrollo y mantenimiento, lo que incrementa la complejidad (ADR-001). |

**Propuesta preliminar:** combinar las alternativas A y B, y evaluar la alternativa C únicamente si la validación demuestra que el control de la transición no puede asegurarse con ellas. Esta propuesta no constituye una decisión y está sujeta a la validación del apartado 10.

Hasta que se compruebe una restricción técnica, el control de que no se confirme un pedido sin una solicitud aceptada es procedimental y se verifica mediante el historial.

## 10. Validación, riesgos y pendientes

Se requiere comprobar en la instancia de Odoo:

- La continuidad de la información entre CRM, Contactos y Ventas.
- La relación entre la oportunidad, la cotización aceptada, la solicitud y el pedido.
- El mecanismo que representa y procesa la solicitud de pedido.
- La verificación de disponibilidad, autorizaciones y condiciones operativas antes de confirmar el pedido.
- El tratamiento de las solicitudes aceptadas, condicionadas y rechazadas.
- La trazabilidad de las decisiones y la participación de los responsables autorizados.
- El comportamiento de los módulos de enlace `sale_crm` y `sale_stock` frente a la frontera definida.
- Que los permisos de VEN, ALM y GER permitan la separación prevista.

**Riesgos relacionados:** [RSK-003](../riesgos-y-controles.md) y [RSK-005](../riesgos-y-controles.md).

**Pendientes relacionados:** [PEN-004](../../producto/registro-pendientes.md) y [PEN-005](../../producto/registro-pendientes.md), sobre permisos, y [PEN-009](../../producto/registro-pendientes.md), sobre programación, entrega y conformidad.

### Asuntos abiertos propios de la integración

Estos asuntos se trasladan al [registro de pendientes](../../producto/registro-pendientes.md) para su seguimiento.

| Asunto | Criterio de cierre |
|---|---|
| Responsable de ejecutar la evaluación de la solicitud. | Rol designado y reflejado en el modelo de autorización y en el flujo comercial. |
| Responsable de autorizar la confirmación del pedido de venta. | Rol designado, con la verificación previa de viabilidad operativa. |
| Criterios que distinguen una solicitud condicionada de una rechazada. | Criterios documentados y validados con los propietarios. |
| Vigencia de las cotizaciones previa a la solicitud. | Criterio definido y reflejado en las reglas comerciales. |
| Política de otorgamiento de créditos. | Criterios confirmados con los propietarios. |
| Mecanismo de representación de la solicitud en Odoo. | Alternativa validada en la instancia y registrada en este documento. |

Los casos de prueba que verifiquen esta integración se registran en la carpeta `pruebas/`. Deben cubrir, como mínimo, el flujo con solicitud aceptada y las excepciones con solicitud condicionada y rechazada.
