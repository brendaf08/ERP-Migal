# Flujo comercial CRM y transición a la orden de venta

**Estado:** proceso propuesto, con observaciones de la operación actual identificadas por separado. CRM integra el tramo comercial de [O2C](../o2c/flujo.md); no constituye un proceso de venta desconectado. [ADR-006](../../arquitectura/decisiones/ADR-006-adopcion-crm-odoo.md) adopta Odoo CRM y [ADR-004](../../arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md) separa la aceptación comercial de la confirmación operativa. [INT-01](../../arquitectura/integraciones/INT-01-CRM-ERP.md) especifica la frontera funcional propuesta.

## 1. Alcance y participantes

El flujo empieza con una consulta o necesidad del cliente y termina al comunicar el resultado de la evaluación interna y, si procede, al confirmar la **orden de venta**. La venta inmediata de mostrador puede seguir el recorrido de Punto de Venta sin recorrer etapas de CRM ([RN-007](../catalogo-reglas.md)). La ejecución posterior —reserva, preparación, entrega, comprobante y cobro— se desarrolla en [O2C](../o2c/flujo.md).

**VEN** atiende, registra, cotiza y presenta la solicitud interna de orden de venta. **CMP** aporta información de abastecimiento y **ALM** evalúa disponibilidad y despacho o transporte según sus funciones; el responsable final de consolidar la evaluación ordinaria aún debe designarse. **GER** decide excepciones comerciales y evalúa directamente la viabilidad de faltantes de otras familias de productos cuando corresponda. La distribución de permisos y la confirmación técnica deben contrastarse con el [modelo de autorización](../../arquitectura/seguridad/modelo-autorizacion.md). No se crea un rol adicional denominado «Transporte».

## 2. Entradas, salidas y evidencias

| Entrada | Resultado o evidencia |
|---|---|
| Consulta presencial, llamada, WhatsApp u otro canal documentado. | Necesidad, contacto, canal y responsable de seguimiento cuando corresponda. |
| Productos, cantidades, condiciones de precio, entrega y vigencia acordadas para cotizar. | Cotización identificable y comunicada; autorizaciones GER para excepciones. |
| Conformidad del cliente con una cotización vigente. | Aceptación vinculada a la propuesta concreta (EV-006). |
| Cotización aceptada y datos necesarios para evaluar el compromiso. | **Solicitud de orden de venta interna** presentada por VEN a quienes evalúan abastecimiento y despacho (EV-009). Todavía no es una orden confirmada. |
| Evaluaciones y autorizaciones. | Respuesta aceptada, condicionada o rechazada con responsable, fecha y motivo; confirmación solo cuando la respuesta sea aceptada. |

La solicitud es un **documento funcional interno**. INT-01 indica que Odoo no proporciona de manera estándar un documento específico con ese nombre; su representación y enlace con la cotización siguen pendientes de validación técnica.

## 3. Secuencia propuesta

| Momento | Actividad y decisión | Responsable | Referencia y control |
|---|---|---|---|
| Atención | Identificar al cliente y su necesidad; revisar posibles contactos existentes. Para ventas que requieren seguimiento, registrar oportunidad y próxima actividad propuesta. | VEN | EV-001/EV-002; RN-001/RN-019. No se obliga a toda venta de mostrador a pasar por CRM. |
| Cotización | Elaborar y comunicar una propuesta con condiciones identificables. Consultar disponibilidad sin convertirla en reserva. Solicitar aprobación GER para precio, descuento o crédito excepcionales. | VEN/GER; ALM si hay duda física | EV-003/EV-004; RN-002/RN-004/RN-015. |
| Seguimiento | Registrar cambios negociados conservando la propuesta anterior y una nueva versión vinculada. La representación de versiones en Odoo 19 debe comprobarse. | VEN | EV-005; RN-003, CT-002. |
| Aceptación | Comprobar que la propuesta continúa vigente y registrar la conformidad del cliente. Si venció o cambian condiciones antes de aceptar, presentar una propuesta actualizada. No se fija una vigencia universal. | VEN; GER si hay excepción | EV-006 o EV-008; RN-002. |
| Solicitud interna | Presentar la solicitud de orden de venta con las condiciones aceptadas a las funciones de abastecimiento y despacho o transporte. | VEN | EV-009; RN-005, CT-003. |
| Evaluación | Revisar disponibilidad, posibilidad de suministro, autorizaciones y atención logística; mantener por separado resultados favorables, condicionados y no viables. | CMP/ALM; GER para excepciones; responsable ordinario final por designar | EV-010/EV-012; INT-01. |
| Respuesta | Comunicar a VEN si la solicitud fue aceptada, condicionada o rechazada. La condicionada o rechazada retorna a CRM con motivo; si cambian las condiciones del cliente, negociar y obtener nueva conformidad. | Evaluador por designar/VEN | RN-006, EXC-001; EV-014 tiene una equivalencia semántica aún pendiente en INT-01. |
| Confirmación | Solo tras respuesta aceptada, confirmar la orden de venta y marcar la oportunidad como «Ganada». La representación y restricción efectivas en Odoo 19 deben probarse. | Confirmador por designar; VEN actualiza CRM | EV-018; RN-006/RN-008. |

Si cambian las condiciones aceptadas, se aplica [RN-003](../catalogo-reglas.md): se conserva el historial y, si ya se presentó una solicitud de orden de venta, la nueva queda vinculada a la anterior, conforme a INT-01.

El cliente puede rechazar una cotización (EV-007) antes de que exista solicitud interna. Es diferente del rechazo de la **solicitud de orden de venta** por la evaluación operativa. Ninguno produce automáticamente una nueva cotización; esta se prepara si se negocian condiciones distintas.

## 4. Operación observada y diferencia con la propuesta

Según observación directa comunicada por integrantes del equipo y corroborada por una integrante cercana a la operación de MIGAL, para **fierro, agregados, ladrillos y cemento** se ha confirmado una orden de venta con abastecimiento pendiente aun sin existencias disponibles. Se utiliza la expresión «solicitud condicionada» para ese caso. La identidad de observadores, fecha y circunstancias concretas deben incorporarse a [fuentes del negocio](../../fuentes/fuentes-negocio.md) antes de tratar esta observación como evidencia plenamente trazable. La programación mensual de productos de alta rotación se describe en [P2P](../p2p/flujo.md) con la misma limitación de procedencia.

Esta práctica **AS-IS** no se incorpora como autorización automática al flujo **TO-BE** de INT-01: allí una solicitud condicionada retorna a CRM y solo la aceptada habilita confirmar la orden. Si una solicitud de orden de venta combina productos de esas cuatro familias con otros faltantes, GER evalúa el caso particular; no se extrapola una política general de confirmación. La diferencia entre práctica y arquitectura queda abierta para validación empresarial y, si se decide cambiar el diseño, requerirá revisar formalmente ADR-004 e INT-01.

## 5. Excepciones y asuntos pendientes

| Situación | Tratamiento |
|---|---|
| Cotización vencida o cambios no aceptados | Revisar condiciones, comunicar nueva propuesta y registrar conformidad antes de presentar la solicitud interna. |
| Contacto aparentemente duplicado | Revisar coincidencias; no se presupone bloqueo automático por nombre o teléfono. |
| Disponibilidad dudosa | Solicitar comprobación de ALM; consultar stock no equivale a reservar ni a prometer entrega. |
| Solicitud condicionada o rechazada | Registrar motivo, retornar a CRM y renegociar solo si hay condiciones nuevas. |
| Crédito o descuento excepcional | GER decide y se conserva la autorización antes de asumir el compromiso. |

Permanecen pendientes el criterio de vigencia de cotizaciones, los datos mínimos de la solicitud interna, el responsable ordinario de evaluación y confirmación, las condiciones que separan una respuesta condicionada de una rechazada y la prueba de etapas, versiones, permisos e historial en Odoo 19. El [catálogo de eventos](../catalogo-eventos.md) mantiene los identificadores canónicos; este flujo no resuelve las equivalencias ambiguas de INT-01 ni crea eventos nuevos.
