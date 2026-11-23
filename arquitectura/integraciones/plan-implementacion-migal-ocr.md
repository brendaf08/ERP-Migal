# Plan de implementación — `migal_ocr` (OCR + Fuzzy Matching) para Odoo 19 MIGAL

Versión 1.0 · 20/11/2026 · Proyecto ERP-MIGAL (GE703, Grupo 1)

**Estado propuesto.** Este plan describe la futura adaptación a Odoo 19 Community del OCR y el fuzzy matching de MIGAL SmartOps, integrada con el Agente MIGAL.

El paquete de referencia de SmartOps contiene el código y la documentación originales. Los puntos de extensión y la configuración vigente de ERP-Migal se consultan en [migal_agente](../../custom_addons/migal_agente/) y [Docker para Odoo](../../infra/odoo/).

---

## 1. Veredicto

**Es viable** y encaja con la arquitectura actual:

| Hecho comprobado (13–20/11/2026) | Consecuencia |
|---|---|
| Odoo 19 Community con `sale_management`, `purchase`, `purchase_stock`, `stock`, `point_of_sale`, `sale_order_request` y `migal_agente` instalados (100 módulos) | Los tres destinos posibles (ventas, compras, recepción) ya existen |
| Catálogo de **808** productos (el original midió con 818) | El matcher original y su calibración aplican casi directamente |
| `normalizador.py` y `matcher.py` son Python puro; solo dependen de `rapidfuzz` | Se reutilizan sin cambiar su lógica |
| `rapidfuzz` y `google-genai` **no** están instalados; `anthropic` 2.8.0 **sí** (lo usa el agente) | Hay que agregar `rapidfuzz` al entorno local y al Dockerfile |
| `queue_job` **no** está instalado | El procesamiento en segundo plano se hace con `ir.cron` + `_trigger()` |
| El agente ya tiene orquestador, contratos JSON Schema, vetos, roles, bitácora, widget flotante y capa LLM | El OCR se agrega como **herramientas nuevas del agente**, no como un sistema aparte |

Lo que **no** se reutiliza: el servicio FastAPI (`main.py`), los contratos HTTP del backend de SmartOps y `resultados.py`
(callback al backend). En Odoo los reemplazan modelos, vistas y una tarea programada.

---

## 2. Reglas no negociables

1. La IA **solo extrae** texto crudo y cantidad por línea. **No asigna productos.**
2. El producto lo propone el **matcher determinista** y lo **confirma una persona**.
3. El OCR **solo crea borradores**: líneas en `sale.order` o `purchase.order` en estado borrador, o cantidades de conteo
   en una recepción sin validar. **Nunca confirma, valida, factura ni reserva** (vetos RN-006, RN-009, RN-015 del agente).
4. **Precios**: nunca desde la foto. Ventas toma la tarifa; compras, el proveedor o el costo.
5. **Unidad de medida**: se compara la unidad leída con `uom_id` del producto. Si no coincide, la línea queda en «revisar».
6. **Duplicados**: hash SHA-256 del archivo, único por compañía. Si ya existe, se abre el documento existente.
7. **Trazabilidad**: el archivo queda adjunto. El chatter dice quién revisó y cuándo, y cada acción va a `migal.agente.log`.
8. **Secretos**: la clave de la IA va en `ir.config_parameter` (Ajustes), nunca en el código ni en el repositorio.
   El repositorio es **público**: no subir `.env`, respaldos, `odoo.conf` real ni credenciales.
9. **Privacidad**: enviar imágenes a un proveedor externo exige el consentimiento ya existente
   (`migal_agente.llm_data_ack`). Sin clave o sin consentimiento, el módulo funciona en **modo simulado**.
10. **No modificar el núcleo de Odoo.** Solo addons en `custom_addons/`.
11. La jerga y los umbrales se **editan desde Odoo**, no quedan fijos en el código.

---

## 3. Arquitectura propuesta

```
Usuario (VEN / CMP / ALM)
   │  avatar flotante: «Leer nota (foto o PDF)»   ─ o ─  menú Agente MIGAL › Documentos OCR
   ▼
migal.agente (orquestador existente)
   │  vetos → permiso por rol → contrato JSON Schema → bitácora
   ▼
Herramientas nuevas (addon migal_ocr)
   ├─ leer_documento_ocr      crea migal.ocr.documento (hash, adjunto) y encola
   ├─ estado_documento_ocr    devuelve estado y líneas (para el widget)
   └─ crear_borrador_desde_ocr crea líneas en el borrador destino desde líneas REVISADAS
   ▼
ir.cron «Procesar documentos OCR» (se dispara con _trigger(); bloqueo FOR UPDATE SKIP LOCKED)
   ├─ Capa 1 · Proveedor de visión (intercambiable): simulado | Claude | Gemini
   │           → [{texto_crudo, cantidad, unidad}]   (respuesta estructurada, temperature 0)
   └─ Capa 2 · normalizador + matcher (código original) contra product.product
               → top 3 candidatos con confianza
   ▼
Pantalla de revisión (form editable de migal.ocr.documento con sus líneas)
   verde ≥ 0.85 · amarillo 0.60–0.85 «revisar» · rojo < 0.60 «elegir producto»
   ▼
«Crear borrador» → líneas en sale.order / purchase.order en borrador / conteo en stock.picking
```

### 3.1 Addon y dependencias

`custom_addons/migal_ocr/__manifest__.py` (Odoo 19, licencia LGPL-3):

- `depends`: `migal_agente`, `sale_management`, `purchase_stock`, `stock`, `mail`.
- `external_dependencies`: `{"python": ["rapidfuzz"]}`. Gemini (`google-genai`) es opcional y se importa de forma perezosa.

Estructura sugerida:

```
migal_ocr/
├─ __manifest__.py, __init__.py
├─ ocr/                       # Python puro, sin imports de Odoo
│  ├─ normalizador.py         # copia de referencia-smartops (lógica intacta)
│  ├─ matcher.py              # copia; solo cambian los imports (app.* → relativos)
│  ├─ esquemas.py             # dataclasses ProductoCatalogo / Coincidencia (sin pydantic)
│  └─ proveedores.py          # ProveedorVision: Simulado, Claude, Gemini
├─ models/
│  ├─ ocr_documento.py        # migal.ocr.documento (mail.thread)
│  ├─ ocr_linea.py            # migal.ocr.linea
│  ├─ ocr_jerga.py            # migal.ocr.jerga (abreviatura → expansión)
│  ├─ tool_ocr.py             # migal.agente.tool.ocr (herramientas del agente)
│  ├─ migal_agente.py         # _inherit para registrar herramientas y acciones del widget
│  └─ res_config_settings.py  # umbrales, proveedor, modelo
├─ wizard/ocr_carga.py        # carga del archivo (cuando no se usa el avatar)
├─ views/, security/, data/   # vistas, accesos, cron, jerga inicial, menús
├─ static/src/                # extensión del widget: botón de carga y estado
└─ tests/
   ├─ test_normalizador.py, test_matcher.py   # pruebas originales adaptadas
   └─ test_ocr.py                              # TransactionCase del flujo completo
```

### 3.2 Modelos

**`migal.ocr.documento`** (`_inherit = ["mail.thread"]`)

| Campo | Tipo | Notas |
|---|---|---|
| `name` | Char | Secuencia `OCR/2026/0001` |
| `tipo` | Selection | `solicitud_cliente` (→ ventas), `orden_compra` (→ compras), `documento_recepcion` (→ recepción) |
| `attachment_id` | Many2one `ir.attachment` | Archivo original (JPG, PNG, WEBP o PDF; máx. 10 MB) |
| `hash_archivo` | Char, index | SHA-256; restricción única (`hash_archivo`, `company_id`) |
| `estado` | Selection | `pendiente` → `procesando` → `por_revisar` → `aplicado`; `error` |
| `proveedor` / `modelo_usado` | Char | Qué IA leyó el documento |
| `res_model` / `res_id` | Char / Integer | Borrador destino (cotización, compra o recepción) |
| `partner_id` | Many2one | Cliente o proveedor, si se conoce |
| `linea_ids` | One2many `migal.ocr.linea` | |
| `revisado_por` / `fecha_revision` | Many2one / Datetime | Se llenan al crear el borrador |
| `error_mensaje` | Text | Motivo si falló |
| `company_id` | Many2one | Multicompañía |

**`migal.ocr.linea`**

| Campo | Tipo | Notas |
|---|---|---|
| `texto_crudo` | Char(500) | Como lo leyó la IA |
| `texto_normalizado` | Char | Salida del normalizador (para auditar) |
| `cantidad_leida` / `unidad_leida` | Float / Char | |
| `candidatos_json` | Json | Top 3: `[{product_id, confianza}]` |
| `product_sugerido_id` / `confianza` | Many2one / Float | Mejor candidato |
| `estado_match` | Selection | `propuesto` (≥ alto), `revisar` (≥ bajo), `sin_coincidencia` |
| `product_id` / `cantidad` | Many2one / Float | **Valores finales editados por la persona** |
| `uom_ok` | Boolean | Unidad leída compatible con `product_id.uom_id` |
| `incluir` | Boolean | La persona puede descartar líneas |

**`migal.ocr.jerga`**: `abreviatura`, `expansion`, `activo`. Datos iniciales = el diccionario de `normalizador.py`.
El normalizador recibe la jerga como parámetro opcional (por defecto, la del archivo original), así las pruebas originales
siguen pasando y Odoo inyecta la tabla editada.

**Ajustes** (`res.config.settings`, prefijo `migal_ocr.`): `umbral_alto` (0.85), `umbral_bajo` (0.60), `proveedor`
(`simulado` | `claude` | `gemini`), `modelo` (lista separada por comas, con fallback), `gemini_api_key`.
Claude reutiliza `migal_agente.llm_api_key`, `migal_agente.llm_model` y `migal_agente.llm_data_ack`.

### 3.3 Catálogo para el matcher

- `product.product` activos, de la compañía; `sale_ok` para ventas y `purchase_ok` para compras y recepción.
- `sku` = `default_code` (o `str(id)` si no hay); `nombreOficial` = nombre; `presentacion` = nombre de la unidad;
  `unidadMedida` = `uom_id.name`; también la categoría si el matcher la usa.
- Cachear el catálogo preparado (`preparar_catalogo` + `vocabulario`) por compañía y tipo, invalidado por
  `max(write_date)` de productos. 808 productos se preparan en milisegundos, pero el cron puede procesar varios documentos.

### 3.4 Proveedores de visión (`ocr/proveedores.py`)

Interfaz: `extraer(contenido: bytes, mime: str) -> list[dict(texto_crudo, cantidad, unidad)]`.

- **Simulado**: devuelve líneas fijas de una nota ferretera típica (kk 18 huecos, f° 1/2", cemento bls…). Se usa en las
  pruebas, en la demo sin clave y en la fase 1.
- **Claude** (ya integrado en el agente): SDK oficial `anthropic`, imagen en base64 o PDF como `document`, salida
  estructurada con una herramienta `registrar_lineas` (JSON Schema). Reintento ante errores 429/5xx.
- **Gemini** (lo que proponen ADR-011/012): portar `extractor.py` (instrucciones, `response_schema`, cadena de modelos con
  fallback, `es_reintentable`, `cantidad_valida`). **Verificar los nombres de modelo vigentes el día que se conecte.**
- Las instrucciones de extracción de `extractor.py` (`INSTRUCCIONES`) se reutilizan para cualquier proveedor.
- Límites: tiempo máximo 20 s por llamada, `CANTIDAD_MAXIMA` y `TEXTO_MAXIMO` de `esquemas.py`, descartar cantidades
  imposibles (RUC, teléfonos).

### 3.5 Integración con el Agente MIGAL (puntos de extensión)

Ver [migal_agente](../../custom_addons/migal_agente/). Hoy el agente tiene sus registros como diccionarios de módulo:

- `agent/contracts.py`: `ROLE_GROUPS` (VEN, FCO, GER) y `TOOLS` (contrato y roles de cada herramienta).
- `models/migal_agente.py`: `TOOL_IMPL` (herramienta → modelo y método) y `ejecutar_herramienta()` (vetos, permiso,
  contrato, bitácora).
- `models/agente_widget.py`: `widget_contexto()` solo atiende `sale.order` y `res.partner`; `widget_ejecutar()` despacha
  acciones con un `if/elif`.
- `static/src/agente_widget/agente_widget.js`: el widget llama `widget_contexto`, `widget_ejecutar` y `widget_mensaje`.

**Paso previo recomendado (cambio pequeño en `migal_agente`, retrocompatible):**

1. Exponer los registros como métodos sobrescribibles: `_herramientas()` (contratos), `_implementaciones()`
   (`TOOL_IMPL`) y `_grupos_por_rol()`, que devuelvan copias de los diccionarios actuales.
2. En `widget_contexto()` llamar a un gancho `_widget_contexto_extra(res_model, record)` para modelos no conocidos, y en
   `widget_ejecutar()` despachar acciones desconocidas a `_widget_accion_<accion>()` si existe.
3. Añadir roles **CMP** (`purchase.group_purchase_user`) y **ALM** (`stock.group_stock_user`), ya definidos en el informe.
4. Correr las 29 pruebas actuales del agente: deben seguir pasando.

Con eso `migal_ocr` se integra con `_inherit = "migal.agente"` sin tocar más el código del agente.

**Herramientas nuevas (contratos):**

| Herramienta | Roles | Entrada | Salida |
|---|---|---|---|
| `leer_documento_ocr` | VEN (solicitud_cliente), CMP (orden_compra), ALM (documento_recepcion), GER | `tipo`, `attachment_id`, `res_model`, `res_id` | `documento_id`, `estado`, `duplicado` |
| `estado_documento_ocr` | los mismos | `documento_id` | estado, resumen por color, líneas |
| `crear_borrador_desde_ocr` | los mismos | `documento_id` | líneas creadas; error si hay líneas incluidas sin producto |

**Widget:**

- En `sale.order` en borrador, pestaña «Enviar cotización»: acción «Leer nota del cliente (foto o PDF)».
- En `purchase.order` en borrador y `stock.picking` de recepción sin validar: la misma acción con su tipo.
- Al elegir el archivo: subirlo como adjunto (`/web/binary/upload_attachment` o `ir.attachment.create` vía ORM), llamar a
  `leer_documento_ocr` y mostrar los pasos animados mientras se consulta `estado_documento_ocr` cada 2 s (máx. 60 s).
- Al terminar: resumen «12 líneas · 9 verdes · 2 por revisar · 1 sin producto» y botón «Revisar y crear borrador», que
  abre el formulario de `migal.ocr.documento`.
- Chat del agente (opcional): «lee esta nota» con un adjunto en Conversaciones.

**Vetos:** reutilizar `check_request` del agente. Además, `crear_borrador_desde_ocr` verifica que el destino siga en
borrador y que no haya líneas incluidas en rojo sin producto elegido.

### 3.6 Creación de borradores

- **Ventas**: `sale.order.line` con `product_id` y `product_uom_qty`; el precio lo calcula la tarifa del pedido. Si no
  hay cotización, crear una en borrador para el `partner_id` indicado.
- **Compras**: `purchase.order.line` con `product_id` y `product_qty`; el precio lo toma Odoo del proveedor o del costo.
- **Recepción**: escribir la cantidad leída como cantidad contada en los movimientos que coincidan por producto, mostrar
  diferencias contra lo esperado y **no validar** el picking.
- Mensaje en el chatter del documento destino y del documento OCR: «Líneas creadas desde OCR/2026/0007, revisado por X
  el 20/11/2026 15:42», con el adjunto.

### 3.7 Seguridad y accesos

- `ir.model.access.csv`: lectura y escritura de `migal.ocr.documento` y sus líneas para los grupos de ventas, compras e
  inventario; jerga y ajustes solo para el administrador o gerente.
- Regla de registro por compañía.
- El cron corre con `sudo()`, pero el documento guarda `create_uid` y las herramientas comprueban el rol del usuario que
  pide la acción.

### 3.8 Entorno y despliegue

- Local: `pip install rapidfuzz==3.13.0` en el Python que ejecuta Odoo.
- Docker (`infra/odoo/Dockerfile` del repo ERP-Migal): agregar `rapidfuzz==3.13.0` junto a `qifparse`. Si se elige
  Gemini, también `google-genai`.
- Actualizar `infra/odoo/GUIA_INSTALACION.md`: instalar `migal_ocr`, configurar el proveedor y probar con la nota de ejemplo.

---

## 4. Plan por fases

Cada fase termina con pruebas en verde y una demostración. **No pasar a la siguiente sin cerrar la anterior.**

### Fase 0 · Preparación (½ día)

- [ ] Instalar `rapidfuzz==3.13.0` y correr las pruebas originales de `referencia-smartops/1-codigo/tests`
      (`test_normalizador.py`, `test_matcher.py`) fuera de Odoo.
- [ ] Exportar el catálogo a `productos.csv` (`default_code`, nombre, unidad, categoría, `sale_ok`, `purchase_ok`).
- [ ] Pedir al equipo **20 a 50 líneas de notas reales** con su producto correcto (`texto_crudo;cantidad;default_code`),
      y 3 a 5 fotos de ejemplo sin datos personales.
- [ ] Confirmar las decisiones de la sección 6.

**Terminado:** las pruebas originales pasan en el Python de Odoo.

### Fase 1 · Addon base con IA simulada (1 día)

- [ ] Paso previo en `migal_agente` (sección 3.5) y sus 29 pruebas en verde.
- [ ] Copiar `normalizador.py` y `matcher.py` a `migal_ocr/ocr/` sin cambiar la lógica; adaptar imports y esquemas.
- [ ] Modelos, vistas (lista, formulario de revisión editable con colores por `estado_match`), menú bajo «Agente MIGAL».
- [ ] Wizard de carga con hash y detección de duplicados.
- [ ] Cron con `_trigger()` y proveedor simulado.
- [ ] Jerga inicial como datos XML y umbrales en Ajustes.

**Terminado:** se sube una imagen cualquiera y aparece el documento con líneas, candidatos y colores, sin usar IA.

### Fase 2 · Integración con el agente (½–1 día)

- [ ] Contratos y roles de las tres herramientas, registrados vía `_inherit`.
- [ ] Acciones del widget en cotización, compra y recepción; carga del archivo y consulta del estado.
- [ ] Bitácora de cada lectura y veto ante pedidos de confirmar o validar.

**Terminado:** desde el avatar de una cotización se sube la nota, se ven los pasos y se abre la revisión. Todo queda en la bitácora.

### Fase 3 · Crear borradores (½–1 día)

- [ ] Ventas, compras y recepción según la sección 3.6.
- [ ] Validación de unidad de medida y bloqueo de líneas rojas sin producto.
- [ ] Mensajes en el chatter y estado `aplicado`.

**Terminado:** las líneas aparecen en el borrador con precio de tarifa; nada se confirma.

### Fase 4 · IA real (1 día)

- [ ] Proveedor Claude y/o Gemini con salida estructurada, reintento y fallback de modelo.
- [ ] Consentimiento y clave obligatorios; sin ellos, modo simulado con aviso.
- [ ] Prueba con 3 a 5 fotos reales: lectura en menos de 30 s por documento.

**Terminado:** una foto real termina en `por_revisar` con sus líneas.

### Fase 5 · Calibración, pruebas y entrega (1 día)

- [ ] Adaptar `evaluar.py` para medir, con las líneas reales, aciertos en el top 1 y en el top 3 y la proporción de
      verdes, amarillos y rojos. Ajustar los umbrales si hace falta (documentar el antes y el después).
- [ ] `TransactionCase`: hash duplicado, cron, matcher con catálogo de prueba, creación de borradores, permisos por
      rol, vetos y modo simulado. Las pruebas originales del matcher también deben pasar.
- [ ] Datos de demo `[SIM-OCR]` y una nota de ejemplo en `herramientas/`.
- [ ] Dockerfile, guía de instalación y README del addon.
- [ ] Figura o captura para el informe (arquitectura del OCR y pantalla de revisión).

**Terminado:** pruebas del agente y del OCR en verde; instalación desde cero con Docker funcionando.

**Estimación total:** de 4 a 6 días de trabajo, más el tiempo que tome reunir las notas reales.

---

## 5. Pruebas mínimas

| Prueba | Qué verifica |
|---|---|
| Pruebas originales del normalizador y del matcher | La lógica copiada no cambió |
| Duplicado | Subir dos veces el mismo archivo devuelve el mismo documento |
| Cron | `pendiente` → `por_revisar` con el proveedor simulado; `error` con mensaje si el proveedor falla |
| Umbrales | Las líneas se clasifican en verde, amarillo y rojo según los Ajustes |
| Unidad | Una unidad leída incompatible marca `uom_ok = False` |
| Borrador de venta | Crea líneas con precio de tarifa; la cotización sigue en borrador |
| Borrador de compra | Crea líneas; la compra sigue en borrador |
| Recepción | Escribe cantidades sin validar el picking |
| Roles | VEN no puede leer una guía de recepción; ALM no puede crear cotizaciones |
| Vetos | «confirma la venta con esta nota» queda bloqueado (RN-006) |
| Sin clave | Funciona en modo simulado con aviso |

Comando local de referencia (base de desarrollo, por el `dbfilter` del `odoo.conf`):

```
python odoo\odoo-bin -c odoo.conf -d migal_agente_dev --db-filter=^migal_agente_dev$ -i migal_ocr -u migal_agente --test-tags migal_agente,migal_ocr --stop-after-init --http-port=8070
```

---

## 6. Decisiones pendientes (pedir al usuario antes de la fase 1)

1. **Destino inicial.** Recomendado: **ventas** (`solicitud_cliente`). El cliente que manda la foto de su lista por
   WhatsApp se convierte en cotización, y es el flujo más ligado al agente actual. Compras y recepción, después.
2. **Proveedor de IA.** Claude (ya integrado, reutiliza clave y consentimiento) o Gemini (lo que deciden ADR-011/012).
   Se puede dejar el modo simulado hasta decidir: las fases 1 a 3 no dependen de esto.
3. **Material real** para calibrar (fase 5): 20 a 50 líneas con su producto correcto.

---

## 7. Riesgos

| Riesgo | Mitigación |
|---|---|
| Letra manuscrita difícil | Revisión humana obligatoria; líneas rojas no se aplican sin elegir producto |
| Umbrales calibrados con datos de SmartOps | Recalibrar con las notas reales en la fase 5 |
| Costo o cuota de la IA | Cadena de modelos con fallback, límite de tamaño y hash para no reprocesar |
| Fotos con datos personales enviadas a un tercero | Consentimiento explícito; modo simulado por defecto; no guardar más de lo necesario |
| Nombres de modelos Gemini cambiantes | Configurables en Ajustes; verificarlos al conectar |
| Romper el agente al extenderlo | Cambios retrocompatibles y sus 29 pruebas como red de seguridad |

---

## 8. Definición de terminado

- [ ] `migal_ocr` se instala sobre la base restaurada sin errores y sin tocar el núcleo de Odoo.
- [ ] Flujo completo desde el avatar: subir → leer → revisar → crear borrador, con bitácora y chatter.
- [ ] Ningún camino confirma, valida, factura ni reserva.
- [ ] Pruebas del agente (29) y del OCR en verde.
- [ ] Jerga y umbrales editables desde Odoo; clave solo en Ajustes.
- [ ] Dockerfile y guía actualizados; nada sensible en el repositorio.
