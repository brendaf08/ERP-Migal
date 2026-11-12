# ERP MIGAL - Agente Comercial

## 1. Propósito

El **Agente Comercial O2C de ERP-MIGAL** es un componente de asistencia operativa y control determinista que opera en la frontera funcional entre CRM y ERP sobre **Odoo 19 Community**.

Su objetivo es asistir exclusivamente a **VEN** (Atención y Ventas), únicamente bajo invocación explícita, para transformar una **cotización aceptada por el cliente** en una **Solicitud de Orden de Venta (SOV)**, evaluar su viabilidad operativa con la información ya disponible en el sistema y emitir una recomendación consolidada y trazable sin sustituir ninguna decisión humana (validación dada por el usuario **VEN**).

### Qué hace el agente (alcance funcional)
1. **Generación asistida de SOV (F1 · EV-009, RN-005):** A partir de una referencia de cotización aceptada y una fecha de entrega requerida, lee sus datos en Odoo y precarga en memoria una propuesta de SOV (para que VEN la acepte, corrija o descarte sin redigitar información). Solo si VEN la acepta, formaliza la SOV como **registro local del agente**.
2. **Evaluación operativa de abastecimiento y despacho (F2, F3 · EV-010, EV-012):** Sobre la SOV creada, contrasta las cantidades solicitadas contra el stock libre en almacén y las compras ya programadas/confirmadas en tránsito cuya llegada esté prevista antes de la fecha de entrega requerida; además, calcula el peso total, evalúa únicamente vehículos operativos (excluyendo unidades en mantenimiento), estima los viajes necesarios y advierte si la carga excede la capacidad.
3. **Aviso de viabilidad a VEN (F4):** Registra localmente el aviso hacia **VEN** con el resultado de la evaluación operativa. Si el pedido no es viable o presenta observaciones, lo deja marcado en observación para que la comunicación y el arreglo con las áreas se realicen por fuera del agente.
4. **Consolidación y recomendación (F5 · EV-014):** Reúne la información consultada en el sistema (almacén, abastecimiento programado y flota) para emitir una recomendación no vinculante (**`FAVORABLE`**, **`REQUIERE_REVISION`** o **`NO_EVALUABLE`**) al plantear la propuesta de **SOV**.
5. **Control determinista y escalamiento (F6, F7 · RN-004, RN-006, EV-018):** Detecta descuentos o condiciones de crédito especiales para marcarlos y escalarlos a **GER** sin aplicarlos, y veta determinísticamente cualquier solicitud de confirmación directa de la orden de venta.
6. **Trazabilidad auditada:** Registra cada ejecución, consulta, regla activada, decisión de VEN sobre la propuesta, escalamiento y recomendación en una bitácora local (`audit_log.jsonl`).

### Límites del propósito (qué NO hace)
- **Solo lectura en Odoo 19:** En PC3 no crea ni confirma órdenes de venta (`sale.order`), no reserva inventario (RN-015), no asigna camiones ni genera despachos, no modifica stock ni proveedores, no emite comprobantes en KeyFacil (RN-009) ni registra cobros o pagos. La SOV, los avisos y las recomendaciones viven únicamente como registros locales del agente.
- **No reemplaza funciones nativas de Odoo ni gestiona comunicación externa:** Buscar o crear clientes (`res.partner`) y consultar stock al cotizar se realizan directamente en Odoo; tampoco gestiona ventas inmediatas de mostrador POS (RN-007), ni envía solicitudes o espera respuestas de abastecimiento/almacén para resolver observaciones (esa coordinación queda fuera del agente).
- **No bloquea fuera de política ni decide por humanos:** No restringe por vigencia de cotización (RN-002) ni realiza evaluación crediticia histórica (`account.move` retirado en DEC-01). El agente propone y recomienda; **VEN**, **ALM**, **CMP**, **GER** y el evaluador/confirmador designado conservan toda autoridad de resolución.
- **Modalidades de operación:** Opera en modo **MOCK** (línea base con datos sintéticos `[SIM]`) y en modo **LIVE** (lectura XML-RPC contra Odoo 19 condicionada a conexión, permisos y campos verificados).

---

## 2. Entradas

Todas las entradas del agente están tipadas y sujetas a validación determinista previa a cualquier consulta o regla de negocio. Si una entrada obligatoria falta o tiene formato inválido, el agente **no evalúa**, devuelve estado **`NO_EVALUABLE`** con el detalle del error y registra el evento en `audit_log.jsonl`.

### 2.1 Entrada principal de invocación (F1 · Invocada por VEN)

**VEN** invoca al agente indicando únicamente la cotización aceptada y los datos de entrega que no deben redigitarse desde cero:

| Campo | Tipo / Formato | Obligatorio | Actor | Validación y regla |
|---|---|---|---|---|
| `cotizacion_ref` | `string \| integer` (ej. `"S00042"` o ID `42`; en MOCK prefijo `[SIM]`) | Sí | VEN | Cadena no vacía o entero `> 0`. Debe existir en `sale.order` (LIVE) o fixture `[SIM]` (MOCK). |
| `fecha_entrega_requerida` | `string` (ISO-8601 `YYYY-MM-DD`) | Sí | VEN | Fecha válida; debe ser `>= fecha_actual` (o fecha de emisión). Sirve de corte para compras en tránsito (F2). |
| `usuario_invocador` | `string` | Sí | Sistema / VEN | Identificador del operador; debe corresponder al rol autorizado **VEN** (o dueño con rol VEN). |
| `requiere_despacho` | `boolean` | Condicionado | VEN / Cotización | Si viene en la cotización se hereda; si es `true`, activa la evaluación de flota (F3). Si es `false` (recojo en tienda), omite cálculo de camiones. |
| `ubicacion_entrega` | `string` | Opcional | VEN / Cotización | Dirección u obra de entrega cuando difiere del domicilio del cliente (`res.partner`, INT-01 §4). |
| `condicion_envio` | `string` | Pendiente | VEN | Campo marcado como `Condición de envío ?` en datos de cotización; su estructura exacta está **pendiente de definición** (INT-01 §4). |

### 2.2 Entradas del ciclo de propuesta de SOV (F1)

Una vez que el agente precarga la propuesta en memoria a partir de `cotizacion_ref`, recibe la decisión de **VEN**:

| Campo | Tipo / Formato | Obligatorio | Actor | Validación y regla |
|---|---|---|---|---|
| `accion_propuesta` | `enum`: `"ACEPTAR" \| "CORREGIR" \| "DESCARTAR"` | Sí | VEN | Define la transición del ciclo de propuesta (solo en memoria hasta `"ACEPTAR"`). |
| `ajustes_propuesta` | `object` (`{ fecha_entrega_requerida?, lineas?: [{ product_id, cantidad }], ubicacion_entrega?, requiere_despacho? }`) | Condicionado | VEN | Obligatorio solo cuando `accion_propuesta == "CORREGIR"`. Cada `cantidad` ajustada debe ser `> 0`. |
| `motivo_descarte` | `string` | Opcional | VEN | Registrado en bitácora si `accion_propuesta == "DESCARTAR"`. No genera documento SOV. |

### 2.3 Entradas de control determinista y configuración de ejecución

| Campo | Tipo / Formato | Obligatorio | Origen | Validación y regla |
|---|---|---|---|---|
| `ODOO_MOCK_MODE` | `boolean` (`True` / `False`) | Sí (entorno) | Config / `.env` | `True` usa fixtures `[SIM]`; `False` habilita lectura XML-RPC `LIVE` en Odoo 19. |

### 2.4 Datos de cotización NO solicitados como entrada manual (leídos de Odoo / fixture)

Para evitar redigitación (principio F1), el agente **no pide a VEN** los datos que ya residen en la cotización (`sale.order` / `sale.order.line`), sino que los lee automáticamente:
- **Campos leídos:** `Cliente` (obligatorio, solo nombre para visualización), `Productos` y `Cantidades` (obligatorios), `Precio Unitario`, `Monto`, `Comisión`, `Monto Total` (`Monto + Comisión`), `Fecha de Emisión`, `Fecha de Vencimiento` (obligatoria en cotización, **no bloqueante** por RN-002), `Responsable`, `Término de Pago` (por defecto *Inmediato*; si indica crédito activa F6), `Dscto` (opcional; si es `> 0 %` activa F6 / RN-004) y `Flete` (opcional).
- **Exclusión explícita:** `Metodo Pago` (registro aparte, ej. tarjeta) **no forma parte** de las entradas ni del alcance del agente (corresponde a cobro/POS/FCO).

---

## 3. Salidas

Todas las salidas del agente son **informativas, no vinculantes y locales** (almacenadas en `AGENT_OUT_DIR` o devueltas por consola/JSON). En **ninguna salida escribe, reserva ni confirma registros en Odoo 19**.

### 3.1 Salida del ciclo de propuesta y SOV local (F1 · EV-009, RN-005)

| Artefacto / Campo | Tipo / Formato | Condición de emisión | Contenido y límite |
|---|---|---|---|
| `propuesta_sov` | `object` (solo en memoria) | Estado `Propuesta` o `En corrección` | Datos precargados de `sale.order` (cliente, líneas, cantidades, precios referenciales, término de pago, descuento/flete, `fecha_entrega_requerida`). **No se persiste en disco ni en Odoo.** |
| `sov_local` (`sov_<id>.json`) | Archivo `JSON` en `AGENT_OUT_DIR` | Solo si VEN ejecuta `"ACEPTAR"` (`Creada`) | Registro formal local con `sov_id`, `cotizacion_ref`, líneas confirmadas por VEN, `estado: "CREADA"` y timestamp. **No es un `sale.order` de Odoo.** |
| `descarte_propuesta` | Evento en bitácora | Si VEN ejecuta `"DESCARTAR"` (`Descartada`) | No genera archivo `sov_local`; registra únicamente el descarte y su motivo en `audit_log.jsonl`. |

### 3.2 Salida de evaluación operativa (F2 y F3 · EV-010, EV-012)

Se calcula sobre la SOV `Creada` usando únicamente la información ya disponible en el sistema y se devuelve dentro de la respuesta estructurada del agente:

- **Evaluación de abastecimiento (`evaluacion_abastecimiento` · F2):**
  - Arreglo por producto con: `product_id` (`int`), `nombre` (`string`), `cantidad_solicitada` (`number`), `stock_libre` (`number`, referencial — **no constituye reserva**, RN-015), `compras_en_transito` (`number`, órdenes de compra confirmadas/programadas con llegada prevista `< fecha_entrega_requerida`; en MOCK etiquetadas `[SIM]`), `cantidad_faltante` (`number >= 0`) y `estado_linea` (`enum`: `"CUBIERTO_STOCK" | "CUBIERTO_TRANSITO" | "FALTANTE"`).
  - *Nota:* En modo MOCK/LIVE, la disponibilidad proyectada (`virtual_available`) es solo pronóstico.
- **Evaluación de despacho (`evaluacion_despacho` · F3):**
  - `peso_total_kg` (`number`), `camiones_operativos` (`array` de IDs/placas excluyendo unidades en mantenimiento), `viajes_estimados` (`integer`), `excede_capacidad_un_viaje` (`boolean`) y `estado_despacho` (`enum`: `"VIABLE_UN_VIAJE" | "EXCEDE_CAPACIDAD" | "SIN_FLOTA_OPERATIVA" | "NO_APLICA"`).
  - *Límite:* Estimar más de un viaje **no autoriza entregas parciales** (requiere revisión de **ALM** y, de corresponder, **GER** según RN-018) ni garantiza disponibilidad de ruta, agenda o conductor.

### 3.3 Aviso local a VEN (F4)

El agente no envía mensajes ni espera respuestas de abastecimiento o almacén; únicamente emite un aviso local dirigido a **VEN**:

| Campo | Tipo / Formato | Descripción |
|---|---|---|
| `aviso_ven` | `object` (en `AGENT_OUT_DIR`) | Notificación local con `sov_id`, `cotizacion_ref`, `resultado_evaluacion`, resumen de viabilidad (stock/abastecimiento programado/flota) y `timestamp`. Si queda en observación (`REQUIERE_REVISION`), indica que la coordinación y resolución se realizan fuera del agente. |

### 3.4 Recomendación consolidada (F5 · EV-014)

| Valor (`resultado_evaluacion`) | Condición determinista | Campos obligatorios de salida |
|---|---|---|
| `"FAVORABLE"` | Todo cubierto con stock en almacén o compras programadas en tránsito, despacho viable en 1 viaje (o `requiere_despacho == false`) y sin descuentos/crédito especial. | `motivos: []`, `nota: "Recomendación favorable no vinculante; requiere resolución humana"`. |
| `"REQUIERE_REVISION"` | Existe faltante (`FALTANTE`), carga que excede 1 viaje o sin flota operativa, o descuento `> 0 %` / crédito especial. La cotización/SOV queda **en observación**. | `motivos` (`array[string]` no vacío) + `responsable_sugerido` (`"VEN" \| "ALM" \| "CMP" \| "GER"`) para gestión externa al agente. |
| `"NO_EVALUABLE"` | Datos de Odoo no disponibles, campos/permisos faltantes o entrada inválida. El agente **no evalúa**. | `error_detalle` (`string`) + `alerta_a`: `"SIS"` (falla técnica/fuente) o `"VEN"` (entrada inválida). |

### 3.5 Escalamientos, vetos deterministas y bitácora (F6, F7 · RN-004, RN-006, EV-018)

- **Escalamientos (`escalamientos`):** Lista de registros con `escalamiento_id`, `regla` (ej. `"RN-004"` por descuento/crédito especial), `motivo`, `destinatario_rol` (`"GER" | "ALM" | "SIS"`), `estado: "PENDIENTE_DECISION_HUMANA"` y `timestamp`. **No equivale a aprobación humana.**
- **Bitácora auditable (`audit_log.jsonl`):** Archivo JSON Lines en `AGENT_OUT_DIR` con un registro por turno:

```json
{
  "timestamp": "2026-11-12T11:30:00-05:00",
  "session_id": "EJEMPLO",
  "input_prompt": "[SIM] Evaluar cotizacion S00042 para entrega 2026-11-15",
  "tools_invoked": ["generar_sov_desde_cotizacion", "consultar_catalogo_stock", "verificar_despacho_camion"],
  "odoo_latency_ms": 0,
  "decision_ven_propuesta": "ACEPTAR",
  "resultado_evaluacion": "FAVORABLE",
  "rule_triggered": ["RN-005"],
  "escalation_flag": false,
  "escalated_to": [],
  "output_response": "[SIM] SOV local creada; recomendacion FAVORABLE (no vinculante)"
}
```
*(En datos reales, `input_prompt` debe redactarse/minimizarse para evitar exposición de datos personales o sensibles).*

---

## 4. Fuentes

El agente opera bajo dos fuentes de datos explícitamente separadas según la variable `ODOO_MOCK_MODE`: **MOCK** (línea base reproducible con datos sintéticos `[SIM]`) y **LIVE** (consulta XML-RPC de solo lectura contra **Odoo 19 Community**). Ningún éxito en MOCK acredita integración real en LIVE.

### 4.1 Lista blanca de modelos y procedencia (MOCK vs. LIVE)

| Dato requerido | Modelo Odoo 19 (LIVE · solo lectura) | Fuente MOCK (`ODOO_MOCK_MODE=True`) | Estado respecto a versión base | Notas y verificación técnica |
|---|---|---|---|---|
| Cotización y sus líneas | `sale.order`, `sale.order.line` | Fixtures JSON `[SIM]` (`tests/fixtures/`) | **Nuevo (DEC-01)** | Lee cliente, líneas, cantidades, precios, término de pago, descuento y flete. |
| Productos, stock libre y peso | `product.product` | Catálogo sintético `[SIM]` | Se mantiene | Verifica `qty_available` / `virtual_available` (pronóstico) y `weight`. |
| Compras programadas en tránsito | Módulo Compras / Inventario (`purchase.order.line` o movimientos de entrada confirmados aún no recibidos) | Compras simuladas `[SIM]` con fecha prevista | **Nuevo (DEC-01)** | **Por verificar en instancia Odoo 19:** modelo/campo exacto de llegada prevista (`date_planned` / `scheduled_date`). |
| Camiones, estado y capacidad | `fleet.vehicle` (si módulo `fleet` está instalado) | JSON local `[SIM]` / `FLEET_CAPACITIES_KG_JSON` | Se mantiene (condicionado) | No asumir que `fleet.vehicle` existe ni que trae `capacity_kg` nativo; si falta, usar fuente local sin invocar el modelo ausente. |
| Cliente (solo nombre visible) | `res.partner` | Fixture `[SIM]` | Se mantiene | Solo lectura de nombre/dirección de entrega; no crea ni edita contactos. |

### 4.2 Verificación obligatoria en modo LIVE (Odoo 19)
- Antes de ejecutar `search_read`, el adaptador XML-RPC debe consultar `fields_get` sobre cada modelo habilitado para comprobar existencia del modelo, campos disponibles y permisos del usuario técnico.
- Si un modelo o campo requerido no existe o falla la conexión/permiso, el adaptador detiene la evaluación, retorna **`NO_EVALUABLE`** y alerta a **SIS**.
- **Capa LLM opcional:** Si se habilita (`LLM_ENABLED=True`), requiere `LLM_API_KEY` y `LLM_DATA_SHARING_ACK` explícito; nunca decide reglas ni reemplaza el motor determinista, y su uso no debe declararse si no fue ejecutado.

### 4.3 Políticas y definiciones pendientes explícitas
1. **Vigencia de cotización y política de créditos (`PEN-015`, `RN-002`):** Sin criterio cerrado en MIGAL; el agente no bloquea por fecha de vencimiento, pero sí escala a **GER** cualquier crédito especial.
2. **Representación de la SOV en Odoo (`PEN-016`, `INT-01`):** Alternativas A/B/C aún por validar en instancia; actualmente la SOV se guarda únicamente como JSON local.
3. **Evaluador y confirmador designados (`PEN-018`, `PEN-019`):** Roles pendientes de designación formal en `INT-01`; el agente no resuelve ni confirma.
4. **Límites entre condicionada y rechazada (`PEN-020`):** En PC3 se consolidan bajo **`REQUIERE_REVISION`** (cotización/SOV en observación) sin categoría `NO_VIABLE`.
5. **Estructura de `condicion_envio`:** Marcada como pendiente (`Condición de envío ?`) hasta definición funcional del equipo.

---

## 5. Herramientas

Todas las herramientas del agente son **de solo lectura en Odoo** (o escritura estrictamente local en `AGENT_OUT_DIR`). Las operaciones de escritura transaccional en Odoo (`create`, `write`, `action_confirm`, `button_validate`) están prohibidas en el adaptador.

### 5.1 Catálogo y contrato técnico de herramientas

| Herramienta | Propósito (DEC-01) | Entradas (JSON Schema resumido) | Salidas registradas | Límites deterministas |
|---|---|---|---|---|
| `generar_sov_desde_cotizacion`| Leer `sale.order` / `sale.order.line`, precargar propuesta en memoria y formalizar `sov_<id>.json` si VEN acepta. | `{ "cotizacion_ref": string\|int, "fecha_entrega_requerida": string(date), "accion_propuesta": "ACEPTAR"\|"CORREGIR"\|"DESCARTAR", "ajustes_propuesta"?: object, "usuario_invocador": string }` | `propuesta_sov` (memoria) o `sov_local` (`sov_<id>.json`) + evento de descarte/aceptación. | **Nunca** llama a `sale.order.create` ni `action_confirm`. |
| `consultar_catalogo_stock` | Consultar stock libre (`product.product`) y compras en tránsito con llegada `< fecha_entrega_requerida`. | `{ "lineas": [{ "product_id": int, "cantidad": number(>0) }], "fecha_entrega_requerida": string(date), "warehouse_id"?: int }` | Por producto: `stock_libre`, `compras_en_transito`, `cantidad_faltante`, `estado_linea`, peso y precio referencial. | No reserva inventario (`RN-015`). `virtual_available` es solo pronóstico. |
| `verificar_despacho_camion` | Calcular peso total, filtrar camiones operativos (excluyendo mantenimiento), estimar viajes y evaluar capacidad. | `{ "lineas": [{ "product_id": int, "cantidad": number, "peso_kg": number }], "requiere_despacho": boolean, "ubicacion_entrega"?: string }` | `peso_total_kg`, `camiones_operativos`, `viajes_estimados`, `excede_capacidad_un_viaje`, `estado_despacho`. | No asigna vehículo ni crea despachos. `>1` viaje no autoriza entrega parcial (`RN-018`). |
| `registrar_aviso_ven` | Emitir aviso local a **VEN** con el resultado consolidado (`FAVORABLE` o `REQUIERE_REVISION` en observación). | `{ "sov_id": string, "cotizacion_ref": string\|int, "resultado_evaluacion": string, "motivos": array[string] }` | Registro `aviso_ven` en `AGENT_OUT_DIR`. | No envía mensajes internos en Odoo ni espera respuestas de ALM/CMP. |
| `registrar_escalamiento` | Registrar bloqueo o excepción que requiere intervención humana (**GER**, **ALM**, **SIS**). | `{ "regla": string, "motivo": string, "destinatario_rol": "GER"\|"ALM"\|"SIS", "referencia": string }` | `escalamiento_id`, `regla`, `destinatario_rol`, `estado: "PENDIENTE_DECISION_HUMANA"`, `timestamp`. | No equivale a aprobación humana ni desbloquea operaciones. |

---

## 6. Reglas

El motor de reglas es **100 % determinista** (independiente de si la capa LLM está activa o no) y aplica las reglas de `catalogo-reglas.md`, `INT-01` y `DEC-01`.

### 6.1 Matriz de reglas deterministas y excepciones

| ID Regla / Excepción | Condición evaluada | Acción determinista del agente | Resultado asignado | Destinatario / Escalamiento |
|---|---|---|---|---|
| **RN-005 / EV-009** | Cotización válida + `fecha_entrega_requerida` válida + VEN acepta propuesta (`ACEPTAR`). | Formaliza `sov_<id>.json` local con referencia a `cotizacion_ref`. | Continúa a F2/F3 | VEN (local) |
| **RN-002** | `Fecha de Vencimiento` de cotización pasada o sin política fija. | **No bloquea** ni rechaza por vigencia (principio DEC-01). | Continúa evaluación | VEN |
| **RN-004 / EXC-002** | `Dscto > 0 %` o `Término de Pago` distinto de inmediato (crédito especial) o cambio de precio maestro. | **No aplica** descuento ni aprueba crédito; marca excepción. | `REQUIERE_REVISION` (en observación) | Escala a **GER** |
| **RN-015 / EXC-004** | `stock_libre + compras_en_transito < cantidad_solicitada` para al menos un producto. | Reporta faltante exacto por línea; no promete reserva ni entrega. | `REQUIERE_REVISION` (en observación) | Sugiere revisión **ALM / CMP** (fuera del agente) |
| **RN-018 / EXC-005** | `requiere_despacho == true` y (`peso_total_kg > capacidad_camion` o sin camiones operativos). | Excluye unidades en mantenimiento; calcula viajes orientativos sin autorizar entrega parcial. | `REQUIERE_REVISION` (en observación) | Escala/avisa **ALM** (y **GER** si requiere entrega parcial) |
| **RN-006 / EV-018 / CT-003** | No se permite confirmar al agente ni generar `sale.order`. | **Veto determinista inmediato:** impide confirmación y registra intento en bitácora. | Bloqueado (`confirmacion_permitida: false`) | Registra veto; requiere flujo humano autorizado |
| **Falla técnica / Entrada inválida** | Error de conexión Odoo, campo/modelo ausente en `fields_get`, permiso denegado o parámetro inválido. | Detiene evaluación de forma controlada; **nunca** marca como `FAVORABLE`. | `NO_EVALUABLE` | Alerta a **SIS** (falla técnica) o **VEN** (entrada) |
| **Condición favorable** | Todo cubierto (stock o compras en tránsito), 1 viaje (o sin despacho) y sin descuentos/crédito especial. | Emite recomendación positiva no vinculante y avisa a VEN. | `FAVORABLE` | **VEN** (resolución humana posterior) |

### 6.2 Casos de prueba obligatorios vinculados (`CP3-AI-0x`)
- **`CP3-AI-01` (Normal):** Stock suficiente y camión operativo -> `FAVORABLE`, subtotal y peso referenciales, **sin confirmación**.
- **`CP3-AI-02` (Borde):** Stock parcial o peso superior a capacidad -> `REQUIERE_REVISION`, reporta faltante/sobrecarga y escala a **ALM**.
- **`CP3-AI-03` (Escalamiento):** Descuento especial `10 %` -> veto determinista, escala a **GER**, no genera orden ni aplica descuento.

---

## 7. Permisos

Los permisos siguen el `modelo-autorizacion.md` bajo los principios de **mínimo privilegio**, **segregación de funciones** y **trazabilidad**. No se introduce ningún rol no confirmado (ej. `LOG`).

### 7.1 Matriz de permisos por rol sobre el agente

| Rol | Código | Permiso frente al agente | Permiso en Odoo 19 (contexto) | Restricción clave |
|---|---|---|---|---|
| **Atención y Ventas** | **VEN** | **Invoca** el agente; acepta, corrige o descarta la propuesta de SOV; recibe `aviso_ven`. | Gestiona CRM, clientes y cotizaciones; consulta stock. | No aplica descuentos autónomos (`0 %` autónomo, RN-004); no confirma sin evaluación. |
| **Gerencia** | **GER** | Recibe **escalamientos** de descuentos, créditos especiales y excepciones; **no** es reemplazado por el agente. | Supervisa y autoriza decisiones comerciales, compras y excepciones. | Única autoridad para autorizar descuentos, créditos y cancelaciones (`RN-004`, `RN-010`). |
| **Almacén y Despacho** | **ALM** | Recibe referencia/escalamiento externo cuando hay faltante o exceso de carga (`REQUIERE_REVISION`). | Opera inventario, recepciones y despachos; consulta pedidos. | El agente nunca reserva stock ni asigna vehículos en su nombre. |
| **Compras y Abastecimiento** | **CMP** | Su información de compras confirmadas en tránsito es **leída** por el agente; atiende faltantes fuera del agente. | Gestiona proveedores y prepara órdenes de compra. | Preparar compra (CMP) no equivale a confirmarla (GER). |
| **Administración del Sistema** | **SIS** | Administra `.env`, credenciales XML-RPC de solo lectura, modo `MOCK/LIVE` y atiende alertas `NO_EVALUABLE`. | Configura usuarios, grupos y parámetros técnicos (responsable inicial: **Brenda Mirano**). | Sus privilegios técnicos **no** otorgan autorización comercial ni financiera. |
| **Facturación y Contabilidad** | **FCO** | **Fuera de alcance** del agente en PC3. | Gestiona facturación, cobros, pagos y conciliación. | El agente no lee `account.move` ni interactúa con KeyFacil (`RN-009`). |

### 7.2 Combinación de roles en MIGAL y credencial técnica
- En MIGAL, los propietarios acumulan múltiples roles (Dueña: `GER, VEN, ALM, CMP, FCO`; Dueño: `GER, VEN, ALM, FCO`; Trabajador 1: `VEN, ALM`; Trabajador 2: `ALM`). Por ello, toda invocación exige `usuario_invocador` y deja rastro en `audit_log.jsonl`.
- En modo **LIVE**, la cuenta técnica configurada en `ODOO_USER` / `ODOO_PASSWORD` debe tener **permisos estrictos de solo lectura** sobre los modelos de la lista blanca (§4.1), nunca privilegios de administrador ni escritura transaccional.

---

## 8. Responsable humano

El principio rector de **DEC-01** e **INT-01** es que **el agente propone y recomienda; un humano siempre resuelve**. Ninguna salida del agente produce efectos jurídicos, comerciales, logísticos ni contables por sí sola.

| Momento del flujo | Decisión / Acción humana | Responsable designado | Notas de gobernanza |
|---|---|---|---|
| Invocación y validación de propuesta SOV (F1) | Aceptar, corregir o descartar la propuesta precargada. | **VEN** | La SOV solo se formaliza localmente si VEN ejecuta `ACEPTAR`. |
| Gestión ante observación de stock o compras en tránsito | Decidir reposición, compra, cambio de fecha o ajuste con el cliente (fuera del agente). | **VEN / ALM / CMP** | El agente solo informa lo ya disponible/programado en el sistema. |
| Revisión de despacho y entregas parciales | Validar capacidad real, ruta, conductor o autorizar entrega parcial (`RN-018`). | **ALM** (y **GER** si hay excepción) | El cálculo de viajes del agente es meramente orientativo. |
| Aprobación de descuentos, créditos o precios especiales | Autorizar o rechazar la excepción comercial (`RN-004`). | **GER** | Obligatorio antes de asumir cualquier compromiso. |
| Resolución final de la SOV (`EV-014`) | Aprobar, condicionar o rechazar la solicitud. | **Evaluador designado (`PEN-018`)** | Pendiente de designación formal en `INT-01`. |
| Confirmación de la orden de venta (`EV-018`) | Confirmar `sale.order` en Odoo solo tras evaluación aceptada. | **Confirmador designado (`PEN-019`)** | Bloqueado determinísticamente dentro del agente (`RN-006`). |
| Disponibilidad técnica, entorno y permisos | Verificar instancia Odoo 19, `fields_get`, credenciales y fallas `NO_EVALUABLE`. | **SIS** (Brenda Mirano) | Sin autoridad comercial. |

---

## 9. Escalamiento

Cuando una regla determinista detecta una excepción, bloqueo o falla técnica, el agente **detiene la vía favorable**, registra el escalamiento con `estado: "PENDIENTE_DECISION_HUMANA"` en `audit_log.jsonl` y deriva el caso al rol competente para su resolución **externa al agente**.

| Disparador de escalamiento | Regla / Código | Acción del agente | Rol destinatario | Resolución esperada (fuera del agente) |
|---|---|---|---|---|
| Descuento `> 0 %` o término de crédito especial | `RN-004`, `EXC-002` (F6) | No aplica el descuento/crédito; marca `REQUIERE_REVISION` (en observación) y registra escalamiento. | **GER** (vía **VEN**) | **GER** aprueba o rechaza la excepción; si cambia la cotización, **VEN** renegocia (`EV-07`, `RN-003`). |
| Stock libre + compras en tránsito insuficiente | `RN-015`, `EXC-004` (F2) | Reporta faltante por línea; marca `REQUIERE_REVISION` (en observación) y avisa a VEN. | **ALM / CMP** (coordinado por **VEN**) | Confirmar existencia física real, programar compra o renegociar fecha/cantidad con el cliente. |
| Carga excede 1 viaje o no hay camiones operativos | `RN-018`, `EXC-005` (F3) | Señala viajes estimados/sobrecarga; marca `REQUIERE_REVISION` (en observación) sin autorizar entrega parcial. | **ALM** (y **GER** si aplica excepción) | Validar logística real, dividir entregas con autorización o ajustar fecha de entrega. |
| Falla de conexión Odoo, campo/modelo ausente o permiso denegado | Control técnico `NO_EVALUABLE` | Detiene evaluación; **no** emite `FAVORABLE` ni `REQUIERE_REVISION`. | **SIS** | Diagnosticar instancia Odoo 19 / `.env` / `fields_get` o conmutar a modo `MOCK` documentado. |
| Parámetros de entrada faltantes o con formato inválido | Validación previa | Rechaza evaluación con `NO_EVALUABLE` y detalla campo inválido. | **VEN** | Corregir `cotizacion_ref` o `fecha_entrega_requerida` y reintentar invocación. |
