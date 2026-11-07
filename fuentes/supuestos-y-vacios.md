# Supuestos, vacíos y límites de validación

Este registro identifica condiciones que afectan el diseño de ERP-MIGAL y evita confundir la operación observada con una solución aprobada o probada. Su base documental es [fuentes del negocio](fuentes-negocio.md); el [alcance](../arquitectura/alcance.md), los ADR y el [catálogo de eventos](../procesos/catalogo-eventos.md) establecen las decisiones y convenciones vigentes.

## 1. Estados utilizados

| Estado | Significado |
|---|---|
| Evidencia empresarial | Hecho descrito en una fuente empresarial identificada; no equivale necesariamente a verificación presencial reciente. |
| Interpretación | Lectura razonada del equipo, pendiente de contraste cuando afecte una decisión. |
| Decisión arquitectónica | Selección registrada en un ADR aceptado; su implementación puede continuar pendiente. |
| Propuesta funcional | Comportamiento esperado aún sujeto a definición, aprobación o prueba. |
| Validación pendiente | Pregunta abierta, con comprobación o decisión necesaria para cerrarla. |

## 2. Base y decisiones vigentes

| Asunto | Estado | Fundamento y límite |
|---|---|---|
| Tienda principal, dos almacenes, dos propietarios, dos trabajadores y dos camiones. | Evidencia empresarial documentada | FN-01; confirmar vigencia y detalle operativo antes de configurar ubicaciones o logística. |
| Atención presencial, por teléfono y WhatsApp; ventas de mostrador y pedidos para obras. | Evidencia empresarial documentada | FN-01; el registro automático de conversaciones no está incluido en el [alcance](../arquitectura/alcance.md). |
| Odoo 19 Community como plataforma y Odoo CRM como solución comercial. | Decisión arquitectónica | [ADR-005](../arquitectura/decisiones/ADR-005-cambio-version-Odoo-18-Community-a-Odoo-19-Community.md) y [ADR-006](../arquitectura/decisiones/ADR-006-adopcion-crm-odoo.md); no prueban capacidades configuradas. |
| CRM y ERP comparten plataforma con responsabilidades diferenciadas. | Decisión arquitectónica | [ADR-004](../arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md); [INT-01](../arquitectura/integraciones/INT-01-CRM-ERP.md) especifica una transición propuesta. |
| Compras y abastecimiento forman parte de P2P. | Alcance vigente | [Alcance](../arquitectura/alcance.md) y [modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md): CMP prepara y gestiona; GER autoriza y confirma. |
| KeyFacil mantiene la emisión de comprobantes; la integración automática no integra el alcance inicial. | Alcance vigente | [Alcance](../arquitectura/alcance.md); registro relacionado y conciliación requieren procedimiento. |

## 3. Propuestas funcionales y límites

| Propuesta | Límite que debe conservarse | Comprobación necesaria |
|---|---|---|
| Relacionar oportunidad, cotización, solicitud y pedido sin duplicar contactos. | La aceptación de la cotización no confirma el pedido. | Validar continuidad, identidades y trazabilidad en Odoo 19 según INT-01. |
| Evaluar disponibilidad, autorizaciones y despacho antes de confirmar una orden de venta. | Aceptada, condicionada y rechazada son respuestas diferentes; una solicitud condicionada retorna a gestión comercial. | Acordar mecanismo y responsables; probar restricciones y estados. |
| Registrar existencias por tienda y almacenes, recepciones, transferencias y ajustes justificados. | Consultar stock no crea reserva; registrar compra no equivale a recepción física; una pérdida no es una venta. | Definir almacenes o ubicaciones, movimientos, conteos y permisos en la instancia. |
| Formalizar abastecimiento mediante solicitudes, órdenes de compra, recepción y pago. | La inclusión de Compras no demuestra automatización de reabastecimiento ni aprobación automática. | Precisar flujo P2P y probar `purchase` y sus dependencias en Odoo 19. |
| Vincular entregas, comprobantes KeyFacil y cobros con la operación comercial. | Confirmar pedido no demuestra despacho, entrega conforme, emisión fiscal ni pago. | Definir referencias, excepciones y conciliación con responsables. |

## 4. Vacíos abiertos y cierre esperado

| Vacío | Decisión o evidencia requerida | Responsable de validación propuesto |
|---|---|---|
| Política de precios, descuentos, crédito y vigencia de cotizaciones. | Condiciones confirmadas por propietarios, sin porcentajes o plazos inferidos de material docente. | GER, con apoyo de VEN y FCO. |
| Ubicaciones físicas y disponibilidad por producto. | Representación de tienda y almacenes; diferencia entre stock físico, disponible y reservado; prueba de movimientos. | ALM y SIS, con aprobación de GER cuando proceda. |
| Compromisos de entrega y tratamiento de faltantes. | Momento en que puede prometerse fecha, recursos disponibles y manejo de entregas parciales o no conformes. | GER y ALM, con información de VEN. |
| Espera máxima de 30 minutos en obra y recursos logísticos adicionales citados en documentación anterior. | Original de FN-02 y decisión explícita de los propietarios; hasta entonces, no son políticas ni recursos confirmados. | GER. |
| Frontera entre Facturación de Odoo y KeyFacil. | Procedimiento para evitar duplicidad de comprobantes, registrar referencias y conciliar importes. | FCO y GER; definición técnica por SIS. |
| Complementos financieros OCA. | Versiones compatibles, instalación autorizada y reportes requeridos probados. | FCO y SIS, con decisión de GER. |
| Roles y permisos efectivos. | Comparación entre [modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md), grupos de Odoo y pruebas con usuarios representativos. | SIS y GER. |
| Correspondencias ambiguas de eventos CRM–ERP. | Decisión funcional sobre los candidatos del catálogo, sin inventar códigos ni equiparar automáticamente la respuesta condicionada con EV-014. | GER y responsables de proceso. |

Los responsables indicados señalan **a quién consultar para validar**, no asignaciones de trabajo ni aprobaciones ya obtenidas. El [registro de pendientes](../producto/registro-pendientes.md) conserva el seguimiento formal de asuntos abiertos.

## 5. Reglas para evitar inferencias indebidas

No se presume descuento fijo del 5 %, vigencia general de tres días, DNI/RUC obligatorio para toda consulta, integración automática con WhatsApp o KeyFacil, reserva por simple consulta, salida física al confirmar un pedido ni emisión fiscal automática desde Odoo. Los resultados de pruebas en Odoo 18 no validan por sí mismos Odoo 19. Las verificaciones técnicas se documentarán en [módulos y dependencias](../arquitectura/modulos-y-dependencias.md) y en las evidencias de prueba que correspondan.
