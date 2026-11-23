# MIGAL Reportes — Odoo 19 Community

Módulo independiente con **dos diseños coordinados**: A4 (azul corporativo, márgenes generosos) y papel térmico **58 mm** (monocromático, compacto). Utiliza el logotipo autorizado de Ferre & Inversiones MIGAL incluido en `static/img/` (versión actualizada del logotipo: sin marco azul exterior).

## Qué incluye (v1)

| Documento | Modelo Odoo | A4 | 58 mm | Acceso |
| --- | --- | --- | --- | --- |
| Estado de cuenta | `migal.agente.estado.cuenta.wizard` | Sí | Sí | Asistente de estado de cuenta; avatar del Agente MIGAL |
| Cotización / orden comercial | `sale.order` | Sí | Sí | Menú **Imprimir** en cotizaciones/ventas |
| Comprobante de venta / factura / boleta / nota de crédito según localización | `account.move` | Sí | Sí | Menú **Imprimir** en Facturación |
| Resumen interno de entrega | `stock.picking` | Sí | Sí | Menú **Imprimir** en Inventario |
| Constancia interna de pago | `account.payment` | Sí | Sí | Menú **Imprimir** en Pagos |

La numeración y clasificación de facturas y boletas se obtiene de la configuración contable y de la localización existente (`l10n_latam_document_type_id`, cuando esté disponible). **El PDF comercial de este módulo no sustituye un CPE válido de SUNAT.** El comprobante electrónico original de Odoo sigue disponible y debe ser el entregado con los elementos fiscales exigidos (incluido QR fiscal). Las plantillas de este módulo no emiten, firman, validan ni envían XML a SUNAT.

La salida de entregas es un **resumen operativo interno**, no una guía de remisión electrónica. La salida de pagos es una **constancia interna**, no un comprobante tributario.

## Instalación en el entorno del repositorio

1. Descomprima el paquete y copie **la carpeta `migal_reportes` entera** a `ERP-Migal/custom_addons/` (junto a `migal_agente`).
2. Abra Docker Desktop. Desde `ERP-Migal/infra/odoo`, ejecute `docker compose up -d` y, si Odoo ya estaba activo, `docker compose restart odoo`.
3. Active el modo desarrollador de Odoo, vaya a **Aplicaciones > Actualizar lista de aplicaciones**, busque **MIGAL | Reportes corporativos A4 y 58 mm** e instálelo. No cambie ni elimine el módulo `migal_agente` existente.
4. Revise el estado de cuenta desde **Contactos > Cliente > Estado de cuenta**. Después de **Generar** verá los nuevos botones **MIGAL · A4** y **MIGAL · Ticket 58 mm**. También podrá descargar ambos desde el avatar flotante del Agente MIGAL.
5. En **Ventas, Facturación, Inventario y Pagos**, abra el registro guardado y use el menú **Imprimir** para seleccionar la versión MIGAL correspondiente.

**Importante:** el estado de cuenta conserva los cálculos y roles de `migal_agente` y no altera la estructura contable. La ruta pública de compartir estado de cuenta mantiene su token y caducidad de 24 h, pero adopta la nueva plantilla A4.

## Impresión y límite conocido

El ticket se genera en papel personalizado **58 × 200 mm**, con márgenes de 3 mm por cada lado y 2 mm arriba/abajo; el contenido se distribuye en un ancho útil aproximado de **50–52 mm**. En documentos largos el motor PDF puede paginar. **La altura del ticket todavía no se ajusta automáticamente al contenido**. Configure el controlador de impresora térmica para el papel real y verifique los saltos de página antes de una puesta en producción.

La apariencia A4 y la monocromática comparten estructura, tipografía jerárquica, nombres de secciones y reglas de alineación. El diseño es deliberadamente sobrio: uso moderado de azul, bordes discretos y separación entre bloques.

## Comprobaciones recomendadas antes de aceptar el módulo

- Estado de cuenta sin movimientos, con 1 movimiento, con 30 movimientos, y con abonos sin aplicar.
- Cotización con una línea y con muchas líneas y nombres de productos extensos.
- Factura, boleta, nota de crédito (y nota de débito si la localización la genera): validar numeración, impuestos, totales y comparación con el reporte oficial.
- Estado de cuenta compartido con token: abrir enlace vigente, revocarlo y comprobar caducidad.
- Usuario vendedor: comprobar que no puede generar ni abrir por URL los PDFs de estado de cuenta.
- Ticket: medir ancho, legibilidad, márgenes y comportamiento en impresión real.

## Estructura y personalización

- `report/layouts.xml`: estilos y cabeceras/pies reutilizados por todos los documentos.
- `report/paperformats.xml`: tamaños A4 y 58 mm.
- `report/estado_cuenta.xml`, `cotizaciones.xml`, `comprobantes.xml`, `entregas.xml`, `recibos.xml`: contenido por familia.
- `models/`: acciones del asistente, integración con el avatar y control de acceso.
- `static/img/logo_migal.png` y `logo_migal_bw.png`: imagen proporcionada para este proyecto.

**Observación sobre pruebas:** el paquete pasó validaciones estáticas de Python, XML, referencias y composición, pero **no se ejecutó todavía una instalación ni impresión real dentro de Odoo 19**. La representación fiscal de facturas y boletas necesita revisión normativa y validación final contra el sistema emisor antes de usarse como documento oficial.

## Dónde ver las plantillas en Odoo y configurar la información

Estas plantillas no tienen un panel de edición visual integrado. Se previsualizan abriendo un documento real y generando su PDF; los datos se editan en los modelos de Odoo.

| Tipo | Dónde verlo/descargarlo | De dónde obtiene los datos |
| --- | --- | --- |
| Estado de cuenta | Contactos > cliente > Estado de cuenta > Generar > MIGAL · A4 / MIGAL · Ticket 58 mm. También avatar del agente | Cliente, movimientos contables publicados, período, métodos de pago configurados en Agente MIGAL |
| Cotización | Ventas > Cotizaciones > abrir > Imprimir > reporte MIGAL A4/58 mm | Cotización, líneas, cantidades, condiciones, impuestos, cliente |
| Factura / boleta / nota | Facturación/Contabilidad > Facturas de cliente / Notas de crédito > abrir > Imprimir > reporte MIGAL | Comprobante contable, serie, tipo de documento según localización, datos de emisor y cliente |
| Entrega | Inventario > Operaciones > Entregas > abrir > Imprimir > resumen MIGAL | Albarán/transferencia y movimientos de stock |
| Pago | Contabilidad/Facturación > Clientes > Pagos (según menús instalados) > abrir > Imprimir > constancia MIGAL | Registro de pago interno |

**Datos comunes de la empresa**: Ajustes > Usuarios y empresas > Empresas > empresa MIGAL: razón social, RUC, dirección, teléfono, correo. Las cabeceras consultan `res.company`; el logo de los documentos está en `static/img/logo_migal.png`, por lo que cambiar el logo configurado en la ficha de empresa **no cambia automáticamente el logo de este módulo**.

**Datos del cliente**: Contactos > cliente. **Datos del documento**: edite el documento de origen si todavía es editable. **Medios de pago del estado de cuenta**: Ajustes > configuración de Agente MIGAL, si tiene permisos, con campos de Yape y cuentas bancarias. Si no aparece, en modo desarrollador busque los parámetros `migal_agente.pago_*` sin modificar otros parámetros.

**Diseño y formato de papel**: se cambian en `report/layouts.xml`, `report/*.xml`, `report/paperformats.xml`. Los tamaños también se pueden inspeccionar en modo desarrollador: Ajustes > Técnico > Informes > Formatos de papel. Modificar una plantilla desde el código requiere actualizar el módulo.

Para aplicar este logotipo si el módulo anterior ya está instalado: sustituya la carpeta del módulo por la versión 1.0.1, reinicie Odoo y actualice `migal_reportes` desde Aplicaciones; recargue el navegador si continúa mostrando una imagen en caché.

---

## Nuevo en v1.2 — Centro de plantillas

Después de instalar o **actualizar** `migal_reportes`, abre el menú superior **MIGAL → Plantillas de documentos**. Aparecerán cinco familias: estado de cuenta, cotizaciones/órdenes, factura/boleta/notas, resumen de entrega y constancia interna de pago. Cada familia mantiene una versión A4 y otra para rollo de 58 mm.

Selecciona una familia para ver **dos muestras ilustrativas** con el logo nuevo: A4 azul corporativo y ticket monocromático. Las muestras contienen importes ficticios y muestran la distribución del diseño; **no son un PDF renderizado ni una copia fiscal**. Para ver el documento auténtico, pulsa **Imprimir con datos de Odoo**, selecciona un documento existente, el formato y pulsa **Generar PDF**. Se aplican los permisos normales de Odoo; el estado de cuenta requiere Facturación/Cobranzas o Gerencia y utiliza el cálculo del Agente MIGAL.

Los usuarios administradores también encuentran:

- **MIGAL → Configuración de plantillas** (o **Configurar diseño** en cada familia): subtítulo de cabecera A4, teléfono, correo y sitio web opcionales, visibilidad del logo en ticket, texto del pie A4, despedida del ticket y modo A4 compacto. Estos valores se comparten automáticamente entre los diez formatos al volver a generar un PDF.
- **Datos de la empresa**: acceso a la ficha de `res.company` para razón social, RUC, dirección, teléfono, correo y página web. La RUC y los datos de identificación fiscal obligatorios **no se pueden ocultar** con estas opciones.
- **Ajustes del Agente MIGAL**: métodos de pago que aparecen en los estados de cuenta (Yape y transferencias), separados de la apariencia de los reportes.

Los cambios visuales en el panel requieren guardar la configuración. Si un PDF antiguo estaba abierto, genéralo de nuevo después de guardar. La previsualización muestra una aproximación del diseño, no necesariamente la disposición final del motor de PDF. El formato térmico sigue teniendo una altura de página fija de 200 mm que puede causar paginación en documentos largos.

### Si ya tenías v1.1 instalado

1. Conserva un respaldo y **sustituye la carpeta** `ERP-Migal/custom_addons/migal_reportes/` por la carpeta `migal_reportes` de este ZIP. No reemplaces ni borres `migal_agente`.
2. Abre Terminal en `ERP-Migal/infra/odoo` y ejecuta `docker compose restart odoo`.
3. En Odoo, activa el modo desarrollador, abre **Aplicaciones**, actualiza la lista de aplicaciones si hace falta, busca `MIGAL | Reportes corporativos A4 y 58 mm` y pulsa **Actualizar** (no solo «Abrir»). Esto carga modelos, permisos, datos y menús nuevos.
4. Refresca el navegador y busca **MIGAL → Plantillas de documentos**. Solo un administrador puede abrir **Configuración de plantillas** o editar datos de la empresa.

**Recomendación:** prueba el estado de cuenta real primero, luego una cotización corta y otra larga. Valida los saltos de página en 58 mm con una impresora térmica antes de usarlo en producción.

**Validación**: la versión 1.2 se verifica por compilación de Python y parseo de XML, pero todavía requiere instalación y prueba de impresión en una instancia Odoo 19 real. Los comprobantes fiscales siguen siendo vistas comerciales y no reemplazan la representación oficial para SUNAT.


---

## Nuevo en v1.3 — Impresión directa y menú limpio

**Descargas rápidas desde el documento (sin abrir Configuración):**

- En **Ventas > Cotizaciones / órdenes**, pulsa **Imprimir** y elige **PDF A4** o **Ticket 58 mm**. Junto a **Imprimir**, abre el botón circular de **Mensajes y actividad** para consultar el historial, registrar notas o gestionar actividades. Usa **Crear solicitud** para iniciar la aprobación y **Solicitud** para volver a la ficha vinculada. El acceso **Factura / boleta** aparece arriba cuando la orden tiene comprobantes asociados.
- Usa **Cotizaciones**, **Solicitudes** y **Órdenes** en la barra de Ventas para abrir las listas nativas. Los accesos superiores de cada documento enlazan con los registros asociados.
- En **Facturación > Facturas de cliente y notas**: botones `MIGAL · Vista A4` y `MIGAL · Vista 58 mm` en documentos contabilizados. **Son vistas comerciales; el CPE oficial permanece disponible**.
- En **Inventario > Entregas**: botones A4 y 58 mm en el encabezado. Son resúmenes internos, no guías de remisión.
- En **Pagos**: botones A4 y 58 mm para constancias internas (no comprobantes tributarios).
- En **Contactos > Cliente**: dos botones de estado de cuenta, que utilizan automáticamente el mes actual y los permisos/cálculos del Agente MIGAL. Para elegir otras fechas, abra el asistente de estado de cuenta.
- En **MIGAL > Impresión rápida**: seleccione tipo de documento, registro real y formato desde una sola ventana. No necesita pasar por el catálogo ni Configuración.
- El formulario de **Estado de cuenta** ahora muestra solo `Descargar PDF A4` y `Descargar Ticket 58 mm`, eliminando el botón duplicado del reporte anterior. En el avatar, también se diferencian los dos formatos.

**Menú Imprimir simplificado (reversible):**

En `MIGAL > Configuración de plantillas`, active o desactive **Mostrar solo reportes MIGAL en Imprimir**. Está activado por defecto en **cotizaciones, entregas y pagos**. Oculta otros reportes vinculados al menú Imprimir, pero **no elimina sus acciones ni sus documentos** y puede desactivarse cuando necesite los originales.

**Excepción de facturación:** `account.move` mantiene el reporte fiscal oficial de Odoo junto a los formatos MIGAL, porque la representación comercial de MIGAL todavía no sustituye un CPE SUNAT validado. Los botones estándar de acciones como `Enviar e imprimir` y otros flujos nativos de Odoo tampoco son eliminados por este ajuste.

**Actualizar desde v1.2:** reemplace la carpeta completa `custom_addons/migal_reportes`, reinicie Odoo, y en Aplicaciones pulse **Actualizar** sobre `migal_reportes`. No basta reiniciar: las nuevas vistas, botones, menú y ajustes se cargan mediante la actualización del módulo.

**Pruebas pendientes:** comprobación visual, descarga y papel real en la instalación Odoo 19 de MIGAL. Las comprobaciones estáticas no sustituyen esas pruebas.

### Cobros y comprobantes externos

- En una orden confirmada, **Registrar cobro** crea un pago de cliente y verifica que Odoo haya publicado el asiento. Se puede registrar un abono parcial o el saldo completo. Usar un diario de banco o caja con una **cuenta de cobros pendientes** en el método de entrada. Para cobros de una orden con factura contabilizada en Odoo, usar el pago de esa factura.
- El resumen comercial cuenta los cobros de este flujo con asiento publicado y excluye los cancelados o revertidos. **Pagos del cliente** abre los pagos de entrada del cliente y la compañía en una pantalla aparte.
- **Facturación → Clientes → Emisión en Key Fácil** muestra las órdenes confirmadas. Usa **Actualizar emisión** para marcar una boleta o factura pendiente o registrar la referencia de un comprobante emitido. **Pendientes de emisión** muestra las órdenes seleccionadas para emitir. El estado de cobro se consulta por separado.
