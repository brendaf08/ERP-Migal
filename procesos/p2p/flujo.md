# Flujo Procure to Pay (P2P)

**Estado:** proceso funcional propuesto para compras y abastecimiento. El [alcance](../../arquitectura/alcance.md) incluye Compras; la [decisión de plataforma](../../arquitectura/decisiones/ADR-005-cambio-version-Odoo-18-Community-a-Odoo-19-Community.md) establece Odoo 19 Community. La presencia de `purchase` y `purchase_stock` en los [manifiestos documentados](../../arquitectura/modulos-y-dependencias.md) no acredita su instalación, configuración o uso en MIGAL.

## 1. Inicio, fin y responsables

P2P comienza cuando se identifica una necesidad de abastecimiento y termina con recepción y obligación económica conciliadas, o con una excepción explícita en seguimiento. La necesidad puede proceder de tres situaciones: **programación mensual de productos de alta rotación**, **faltante o reposición detectada**, o **demanda comercial sin stock suficiente**. La programación mensual fue comunicada como práctica observada por el equipo; persona, fecha y detalle de observación permanecen pendientes de incorporar a [fuentes del negocio](../../fuentes/fuentes-negocio.md). No se fijan cantidades, mínimos ni generación automática de compras.

**ALM** identifica necesidades físicas y verifica recepciones; **CMP** revisa, prepara y gestiona compras ordinarias; **GER** autoriza el compromiso de compra y gestiona excepciones con proveedores; **FCO** registra y concilia documentos, obligaciones y pagos ordinarios bajo supervisión de GER. **SIS** verifica configuración y permisos, sin sustituir las decisiones de negocio. La distribución se rige por el [modelo de autorización](../../arquitectura/seguridad/modelo-autorizacion.md), incluso cuando una misma persona reúne varios roles.

## 2. Entradas, salidas y secuencia

| Momento | Actividad y decisión | Responsable | Resultado y referencia |
|---|---|---|---|
| Necesidad | Registrar producto, unidad, cantidad estimada, causa y fecha requerida si existe. Distinguir programación mensual, reposición física y demanda de una orden de venta. | ALM/CMP; VEN comunica demanda comercial | Necesidad identificada (EV-021); RN-011. |
| Revisión | Contrastar existencias, traslados, recepciones y compras pendientes para evitar compromisos duplicados. Señalar cualquier dato incierto. | CMP, con ALM | Revisión documentada; CT-006 y [flujo de inventario](../inventario/flujo.md). |
| Preparación | Consultar proveedores y condiciones de producto, precio, cantidad, plazo, entrega y pago; preparar la orden de compra. | CMP | Propuesta de compra trazable; RN-012. |
| Autorización y compromiso | GER revisa y confirma la compra que compromete a MIGAL. La autorización comercial no equivale a recepción del producto. | GER | Pedido a proveedor formalizado (EV-022), condiciones autorizadas. |
| Seguimiento | Confirmar respuesta del proveedor, cambios o incumplimientos; GER gestiona excepciones y CMP conserva el seguimiento ordinario. | CMP/GER | Confirmación (EV-023) o incumplimiento (EV-024), motivo y siguiente acción. |
| Recepción física | ALM cuenta, inspecciona y registra cantidad apta real, daños y diferencias sin copiar automáticamente la cantidad comprada. | ALM | Productos recibidos y recepción validada (EV-026/EV-027); RN-013. |
| Documento y obligación | Relacionar orden autorizada, recepción real y documento del proveedor; mantener visibles diferencias de precio, cantidad o estado. | FCO, con CMP/ALM | Comprobante de compra recibido (EV-040), obligación y discrepancias. |
| Pago | FCO ejecuta el pago ordinario conforme a las condiciones autorizadas y registra su aplicación; GER supervisa y decide excepciones. | FCO/GER | Pago realizado (EV-046), aplicación a obligación (EV-055), soporte y saldo; RN-014. |
| Cierre | Conciliar cantidades recibidas, documentos, pagos y pendientes. Si permanece una diferencia, conservar el caso abierto o la excepción documentada. | CMP/FCO; GER en excepción | Estado físico y económico diferenciados; CT-007. |

Los identificadores `EV` pertenecen al [catálogo central](../catalogo-eventos.md). Las reglas RN-011 a RN-014 y los controles CT-006/CT-007 se definen en el [catálogo de reglas](../catalogo-reglas.md); esta secuencia describe su aplicación sin crear reglas paralelas.

## 3. Excepciones

| Situación | Tratamiento funcional |
|---|---|
| Proveedor cambia precio, cantidad, plazo o no confirma | CMP documenta la diferencia y GER gestiona y autoriza el compromiso revisado o una alternativa; no se considera válida la autorización anterior para condiciones distintas. |
| Recepción parcial o dañada | ALM registra solo cantidad apta, conserva saldo e incidencia y comunica la diferencia. GER gestiona la excepción con el proveedor (EXC-003). |
| Pago anticipado o parcial | FCO registra el pago y su aplicación separadamente; no lo presenta como recepción ni cierre de la compra. Cualquier excepción a las condiciones acordadas se eleva a GER. |
| Anulación o devolución | Registrar motivo, decisión GER y efectos físicos y económicos; no borrar la compra ni ocultar pagos o mercancía ya recibidos. |
| Necesidad originada por venta con stock faltante | Comunicar plazo e incertidumbre al [flujo O2C](../o2c/flujo.md). La compra iniciada no prueba disponibilidad inmediata ni confirma por sí misma una orden de venta. |

## 4. Verificaciones pendientes

Confirmar con MIGAL la periodicidad, responsables y cantidades de la programación de alta rotación; los criterios para proveedor alternativo, compra parcial y pago anticipado; y el tratamiento de documentos con discrepancias. En Odoo 19 se deben probar `purchase`, `purchase_stock`, permisos CMP/GER/FCO, recepción parcial y relación con inventario. Ningún paso presupone reabastecimiento automático ni un control técnico de autorización ya configurado.
