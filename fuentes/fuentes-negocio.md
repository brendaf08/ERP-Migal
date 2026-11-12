# Fuentes y evidencia del negocio de MIGAL

Este registro permite distinguir información observada o recogida sobre **Ferre & Inversiones MIGAL**, interpretaciones del equipo y referencias usadas para diseñar la solución. Una decisión arquitectónica o una propuesta de proceso no constituye por sí misma evidencia de que la empresa ya opere de esa manera.

## 1. Criterio de lectura

| Tipo | Uso en la documentación |
|---|---|
| Evidencia empresarial | Afirmación atribuible a una fuente primaria identificable y consultada. Su alcance se limita a lo que esa fuente documenta. |
| Interpretación | Conclusión del equipo derivada de evidencia, que debe exponer su fundamento y admitir contraste con MIGAL. |
| Decisión arquitectónica | Elección formal del proyecto, registrada en un ADR; no acredita instalación ni uso efectivo. |
| Propuesta | Funcionamiento deseado sujeto a aprobación o validación. |
| Pendiente de corroboración | Afirmación para la que aún falta consultar la fuente primaria o recibir confirmación empresarial. |

## 2. Registro de fuentes

| ID | Fuente | Fecha indicada | Disponibilidad y alcance |
|---|---|---|---|
| FN-01 | *Ferre & Inversiones MIGAL*, monografía del curso SI704V. | 15/10/2026, según portada | Documento consultado. Describe contexto, personal, infraestructura, canales, cotizaciones y operación comercial. Su disponibilidad para consulta independiente y las afirmaciones que requieran confirmación directa con propietarios siguen pendientes. |
| FN-02 | Aclaraciones de campo atribuidas a Brenda Mirano sobre la operación familiar. | 16/10/2026, fecha por corroborar | No se dispone del documento original para consulta independiente. Las afirmaciones que dependan exclusivamente de esta fuente permanecen pendientes de corroboración. |
| FN-03 | [Contexto de la empresa](../arquitectura/contexto-empresa.md). | Según el documento | Síntesis del proyecto que debe contrastarse con FN-01, FN-02 y confirmaciones posteriores; no sustituye una fuente primaria. |
| FN-04 | Fotografías de activos de MIGAL (vehículos, maquinaria, equipos de pesaje, cobro, videovigilancia y herramientas de apoyo). | 10/11/2026 y 12/11/2026, fechas de recepción por el equipo; fecha de captura por confirmar | Las imágenes no se adjuntan al repositorio. Respaldan la identificación de marca, modelo y datos legibles en el [catálogo de activos](../procesos/catalogo-activos.md). Autor y lugar de captura por confirmar. |

FN-01 se ha consultado, pero su texto íntegro no se adjunta a este registro. Su consulta independiente requiere disponer de una copia autorizada y comprobar que corresponde a la versión citada. FN-02 se mantiene identificada para facilitar la corroboración de las afirmaciones que se le atribuyen.

## 3. Matriz de afirmaciones y respaldo

| Afirmación sobre la operación actual | Respaldo y límite | Tratamiento |
|---|---|---|
| MIGAL opera una tienda principal y dos almacenes cercanos; cuenta con dos propietarios y dos trabajadores. | FN-01, descripción de infraestructura y personal. | Evidencia empresarial documentada; confirmar cambios posteriores con MIGAL. |
| Atiende ventas de mostrador y pedidos vinculados con obras; usa atención presencial, teléfono y WhatsApp para coordinar consultas y cotizaciones. | FN-01, descripción de modalidades de venta y funcionamiento comercial. | Evidencia empresarial documentada; no implica integración automática de canales. |
| La empresa dispone de dos camiones para apoyar el reparto. | FN-01, descripción de infraestructura. | Evidencia empresarial documentada; la asignación y disponibilidad por pedido requieren confirmación operativa. |
| Los propietarios concentran conocimiento de costos, precios y descuentos; el material consultado no presenta un porcentaje máximo formalizado. | FN-01, descripción de precios, atención y necesidades. | Evidencia documental; cualquier política cuantitativa futura requiere aprobación de GER. |
| Los pedidos de obra pueden involucrar a un maestro de obra y a un cliente responsable. | FN-01, descripción de clientes y participantes comerciales. | Evidencia documental; identidad, facultad de compra y relación contractual deben verificarse por operación. |
| KeyFacil participa en la emisión de comprobantes y el registro comercial no está plenamente integrado. | FN-01 y [contexto](../arquitectura/contexto-empresa.md). | Evidencia documental de uso; mecanismo, datos y conciliación futuros siguen pendientes. |
| MIGAL cuenta con montacargas y vehículo eléctrico, o aplica una espera máxima de 30 minutos en obra. | Afirmaciones atribuidas a FN-02 y propuestas funcionales sin fuente primaria disponible para consulta. | Pendiente de corroboración. No se presenta como capacidad o política aprobada. |

La [adopción de Odoo 19](../arquitectura/decisiones/ADR-005-cambio-version-Odoo-18-Community-a-Odoo-19-Community.md), la [adopción de Odoo CRM](../arquitectura/decisiones/ADR-006-adopcion-crm-odoo.md) y la [frontera CRM–ERP](../arquitectura/decisiones/ADR-004-odoo-community-fronteras-crm-erp.md) son **decisiones arquitectónicas** del proyecto. La operación propuesta se describe en el [alcance](../arquitectura/alcance.md), [INT-01](../arquitectura/integraciones/INT-01-CRM-ERP.md) y el [mapa de procesos](../procesos/mapa-procesos.md); ninguno de ellos prueba por sí solo una práctica actual de MIGAL.

## 4. Referencias docentes y límites de uso

Los materiales del curso sobre CRM, los catálogos de ejemplo y las rúbricas pueden orientar conceptos y formato. Sus clientes, segmentos, porcentajes, vigencias, límites de crédito y cargos organizacionales **no son hechos de MIGAL**. En particular, no se adopta un descuento máximo del 5 %, una vigencia universal de tres días ni una jefatura comercial sin respaldo empresarial y autorización correspondiente.

## 5. Verificaciones pendientes

- Facilitar una copia autorizada de FN-01 para consulta independiente y confirmar si existen rectificaciones posteriores.
- Localizar el original de FN-02, registrar su autoría y fecha, y contrastar sus afirmaciones con los propietarios.
- Confirmar políticas de precios, descuentos, crédito, reparto y participación de maestros de obra antes de convertir observaciones en reglas.
- Mantener enlazadas las afirmaciones pendientes con [supuestos y vacíos](supuestos-y-vacios.md), sin elevarlas a hechos por repetición en otros documentos.
