# ERP-MIGAL · PC3 — Agente comercial O2C, configuración y pruebas

**Referencias:** [01 — Plan maestro](01-plan-maestro-pc3.md) · [02 — Distribución](02-distribucion-equipo-pc3.md) · [04 — Odoo/GitHub](04-colaboracion-odoo-github-pc3.md).
**Responsables por actividad:** Gabriel (A9, A11), Luis (A10, A8), Brenda (A7). **Implementación DEC-01 propuesta:** Luis Núñez, con revisión técnica de Gabriel Martínez; pendiente de confirmación del equipo.
**Alcance:** Agente Inteligente de Evaluación Comercial O2C y Continuidad de Atención de Ferre & Inversiones MIGAL.

> Este documento establece qué hay que verificar e integrar, **no certifica** una conexión a la instalación real de MIGAL ni una prueba de LLM remoto. Se conserva como línea base el paquete `ERP-Migal-PC3-Agente.zip` ya preparado, cuyas pruebas se ejecutaron en modo **MOCK**. La versión final debe revisarse de nuevo tras cualquier modificación.

## 1. Contrato de solución y escenario empresarial

**Escenario propuesto compartido con el informe:** un cliente solicita cemento, fierro y otros materiales; el agente consulta productos y disponibilidad, calcula un peso orientativo, identifica si existe restricción de stock o flota y devuelve una evaluación no vinculante. Si el cliente exige descuento, crédito o confirmación, el sistema **bloquea** la acción no autorizada y **escala** al rol humano apropiado.

**Flujo de referencia:** entrada → validación de entradas → consultas autorizadas / mock → reglas deterministas → respuesta → escalamiento cuando proceda → bitácora JSONL.

**Prohibiciones:** crear/confirmar `sale.order` en Odoo, realizar descuentos autónomos, emitir facturas, efectuar pagos, crear reservas, despachar, modificar stock o alterar proveedores. El borrador del MVP es **JSON local**, no un registro transaccional de Odoo. Una división de carga en viajes **no** implica permiso para entregas parciales: debe ser revisada por ALM y, de ser necesaria, por GER conforme a las decisiones vigentes.

### Acuerdos técnicos pendientes

- [ ] Ratificar DEC-01: Luis como implementador principal provisional, Gabriel como revisor, un suplente si se necesita apoyo y hora de versión candidata.
- [ ] Fijar versión exacta del código que usará Brenda y que se incluirá en el ZIP.
- [ ] Ratificar DEC-05: `MOCK` como modalidad base propuesta del equipo; `LIVE` solo si el jueves 12/11 a las 12:00 hay acceso autorizado y conexión Odoo verificada; declarar honestamente qué se probó.
- [ ] Definir una fuente de camiones y capacidades: `fleet.vehicle` verificado o JSON local `[SIM]` / autorizado.
- [ ] Acordar con el equipo si se activará LLM remoto; la rúbrica exige **Agente SIE**, no autoriza fingir un uso real de LLM.
- [ ] Verificar si las políticas de pago contra entrega/cliente nuevo son solo supuestos académicos o han sido aprobadas por GER.

## 2. Herramientas y contrato funcional (A9 — Gabriel)

| Tool | Entradas mínimas | Salida que debe quedar registrada | Límites |
|---|---|---|---|
| `consultar_catalogo_stock` | IDs de productos y cantidades positivas | Productos localizados, stock, faltantes, peso y precio **referencial** | No reserva; `virtual_available` es pronóstico |
| `verificar_despacho_camion` | Ítems y pesos/capacidades verificables | Camión considerado, disponibilidad declarada, viajes sugeridos y bloqueo | No asigna vehículo ni crea despachos |
| `crear_borrador_cotizacion` | Cliente, líneas, condiciones solicitadas | Referencia de borrador local o razón del veto | No usa `sale.order.create` |
| `registrar_escalamiento` | Motivo y destinatario | ID, regla, responsable, estado y timestamp | No equivale a aprobación humana |

**Modelos que pueden ser relevantes (sujetos a instalación, campos y permisos):** `product.product`, `res.partner`, `account.move`, `fleet.vehicle` y `sale.order` para **consulta**. El adaptador debe usar `fields_get` para comprobar campos antes de `search_read`; **no asumir** que `fleet.vehicle` está instalado ni que contiene `capacity_kg` nativo. Si no está `fleet`, la configuración debe admitir una fuente local sin hacer llamadas al modelo ausente, una vez adaptado y probado el código.

**Roles de autoridad:** `GER` autoriza condiciones sensibles; `VEN` recibe/gestiona solicitudes comerciales; `ALM` verifica despacho y condiciones logísticas; `SIS` gestiona accesos y fallas técnicas. No introducir `LOG` como rol confirmado.

### Checklist A9 — Especificación (`agente.md`)

- [ ] Nueve apartados completos; entradas/salidas tipadas, fuentes con procedencia y herramientas JSON Schema.
- [ ] Reglas, permisos, responsables GER/VEN/ALM/SIS y escalamiento definidos con referencias.
- [ ] Límites de lectura, condiciones sensibles y datos MOCK/LIVE explícitos.
- [ ] Gabriel y el implementador comprobaron que el documento coincide con el código final.

### Prompt B — Alinear modelos y campos antes de programar (solo diagnóstico)

**Cuándo:** después de auditar Odoo y antes de editar el agente.


```text
Actúa como Arquitecto de Integraciones Odoo 19 y Backend Python 3.12.

Workspace: ERP-MIGAL.

Disponemos de:
- Documentación y arquitectura empresarial.
- Código o addons de Odoo 19.
- Agente comercial Python con motor determinista.
- Conexión XML-RPC de solo lectura.

OBJETIVO:
Determinar si las consultas del agente corresponden a los modelos, campos, permisos y datos realmente disponibles en la instancia de Odoo.

ACTIVIDADES:

1. Revisar los documentos vigentes del repositorio.
2. Identificar modelos y campos usados por el agente.
3. Contrastar los campos con los addons y, si existe acceso autorizado a Odoo, mediante `fields_get`.
4. Verificar la disponibilidad de `product.product`, `res.partner`, `account.move`, `sale.order` y `fleet.vehicle` según los módulos instalados.
5. Revisar las herramientas disponibles en el agente.
6. Identificar incompatibilidades, riesgos y supuestos.
7. Proponer cambios mínimos que mantengan los dos modos: MOCK y LIVE.
8. Conservar intactas las reglas de autorización de GER y los controles deterministas.

No modificar archivos todavía.

No consultar datos empresariales reales innecesarios ni mostrar credenciales.

ENTREGABLE:
Matriz de compatibilidad Odoo–Agente, con campos verificados, ausentes, propuestos y ajustes necesarios.
```

- [ ] Se obtuvo una matriz de campos y permisos verificados, supuestos o ausentes.
- [ ] Se sabe si usar Odoo Flota o la fuente local; sin confundir MOCK con LIVE.

## 3. Motor determinista y gobernanza (A8 — Luis)

| Situación | Resultado exigido | Responsable / estado |
|---|---|---|
| Descuento solicitado > 0 % | No aplicar; registrar regla RN-004; canalizar con VEN y escalar a GER | GER autoriza; regla de PC3 conservadora |
| Crédito nuevo, saldo vencido o condiciones inciertas | No dar por aprobado; pedir verificación y escalar política comercial | GER; la regla de pago contra entrega exige corroboración |
| Confirmación de orden sin evaluación interna aceptada | Vetar confirmación; no crear venta | RN-005/006; autorización por definir en INT-01 |
| Stock insuficiente o incierto | No prometer despacho/reserva | ALM; RN-015 |
| Camión no operativo o capacidad insuficiente | Excluir o calcular alternativas no vinculantes; escalar | ALM |
| Falta de fuente/permiso/servicio | Fallar de forma controlada; reportar datos no verificables | SIS/ALM/GER según causa |

**No afirmar que un estado de Flota garantiza disponibilidad de ruta, agenda o conductor.** El estado de vehículo, capacidad configurada, carga y agenda real son dimensiones distintas.

### Checklist A8 — Bloque 3 (láminas 7–9)

- [ ] Lámina 7 muestra reglas y controles realmente ejecutados.
- [ ] Lámina 8 representa entrada → tools → reglas → resultado → `audit_log.jsonl`, con escalamiento humano.
- [ ] Lámina 9 declara límites y próximos pasos sin atribuir funcionalidades no comprobadas.
- [ ] Las capturas corresponden a la misma versión/fixtures del ZIP.

## 4. Entorno y configuración (A10 — Luis)

**Stack definido:** Windows 11, Python 3.12, bibliotecas estándar (`xmlrpc.client`, `json`, `unittest`, etc.), Odoo 19 Community local/Docker **cuando exista instancia autorizada**. La capa LLM es opcional; requiere consentimiento/condiciones de uso cuando se conecte a servicios externos.

| Variable | Uso | Estado |
|---|---|---|
| `ODOO_MOCK_MODE=True/False` | Seleccionar backend offline o XML-RPC | Definida en paquete inicial |
| `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD` | Conexión a Odoo, solo con secretos locales | Validar contra instancia |
| `ODOO_WAREHOUSE_ID` | Contexto de almacén para stock | ID real por verificar |
| `FLEET_TRUCK_IDS` | Vehículos autorizados a consulta | IDs reales o fuente local por verificar |
| `FLEET_OPERATIONAL_STATE_IDS` | Estados considerados operativos | Política/IDs por verificar |
| `FLEET_CAPACITIES_KG_JSON` | Capacidades por camión | Fuente/autorización por verificar |
| `AGENT_OUT_DIR` | Auditoría y borradores | Definido |
| `LLM_ENABLED`, `LLM_API_KEY`, `LLM_DATA_SHARING_ACK` | Capa opcional de LLM | No probar/afirmar sin ejecución |

**Advertencia:** `.env.example` es plantilla, no archivo que el proyecto cargue necesariamente de forma automática. Probar los comandos reales de arranque en PowerShell. La integración **LIVE** necesita permisos verificados; si un modelo/campo no existe, se documenta bloqueo, no éxito.

### Checklist A10 — Instalación y requisitos

- [ ] Python/OS/dependencias, `.env.example`, comandos y modos MOCK/LIVE documentados.
- [ ] MOCK ejecuta sin Odoo; LIVE solo se declara probado con conexión/campos/permisos comprobados.
- [ ] Instalación repetida en carpeta limpia y commit de referencia identificado.
- [ ] ZIP sin contraseñas, datos no autorizados o salidas privadas.

### Prompt C — Implementación quirúrgica (después de B)

**Cuándo:** con matriz de compatibilidad revisada y responsable DEC-01 designado.


```text
Actúa como Ingeniero Backend Python 3.12 especializado en Odoo 19 y agentes LLM.

Utiliza la matriz de compatibilidad previamente validada.

OBJETIVO:
Aplicar exclusivamente los cambios técnicos necesarios para ejecutar el agente comercial de MIGAL.

CONDICIONES:
- Mantener arquitectura modular.
- Mantener XML-RPC en modo solo lectura.
- No confirmar ventas, compras, créditos, descuentos ni despachos.
- Mantener gobernanza mediante reglas deterministas.
- Conservar funcionamiento en modo mock.
- Utilizar solo modelos y campos verificados.
- Evitar dependencias adicionales salvo necesidad justificada.

TAREAS:

1. Proponer los archivos a modificar.
2. Implementar los ajustes mínimos.
3. Añadir pruebas de regresión.
4. Ejecutar las pruebas unitarias.
5. Registrar resultados y limitaciones.
6. Mostrar las diferencias realizadas.
7. Actualizar configuración e instrucciones de uso cuando corresponda.

No incluir credenciales ni datos sensibles en los commits.

No modificar el núcleo Odoo.

No hacer push ni fusionar cambios sin revisión.

CRITERIO DE ACEPTACIÓN:
El agente ejecuta los tres casos de la PC3, produce bitácoras auditables y bloquea las operaciones restringidas.
```

- [ ] Cambios mínimos revisados en rama; no escrituras en Odoo ni secretos.
- [ ] Pruebas unitarias y modo MOCK preservados; especificación y código consistentes.

## 5. Plan de pruebas del agente (A10 — Luis)

**Convención diferenciada:** `CP3-AI-01` a `CP3-AI-03` para evitar confundirlos con `pruebas/CP-01` a `CP-04` de las PC anteriores, que permanecen como documentación antecedente.

| Código | Entrada sintética / condición | Resultado esperado | Evidencia |
|---|---|---|---|
| `CP3-AI-01` — normal | Pedido con stock suficiente y camión operable según dataset | Evaluación informativa favorable, subtotal y peso, **sin confirmación** | Consola + log + resultado esperado/observado |
| `CP3-AI-02` — borde | Stock parcial o peso por encima de capacidad | Reportar faltante/sobrecarga, sugerir revisión, **escalar ALM** | Respuesta + regla + log |
| `CP3-AI-03` — escalamiento | Descuento especial 10 % o confirmación sin evaluación | Veto, escalar a GER, no generar orden ni aplicar descuentos | Respuesta + log + escalamiento |

El paquete inicial contiene fixtures con nombres `CP-01.json`, `CP-02.json`, `CP-03.json` y pruebas offline. Mantener dichos nombres físicos si el script los necesita; **la convención documental** `CP3-AI-0x` evita colisiones en el repositorio. Los resultados preliminares offline **no** equivalen a resultados después de integrar addons/Odoo ni a ejecuciones en el equipo del docente.

### Checklist de resultados y evidencia

- [ ] CP3-AI-01/02/03 ejecutados con datos, precondiciones, esperado, observado y estado.
- [ ] Cada resultado conserva fecha, operador, versión, modo y evidencia.
- [ ] Se revisaron bitácora JSONL, reglas activadas y registro de escalamiento.
- [ ] Otro integrante reprodujo los casos desde el ZIP; fallos/bloqueos no se reportaron como aprobados.

## 6. Bitácora y confidencialidad (A11 — Gabriel; A8/A10 — Luis)

**Contrato mínimo por turno** de `audit_log.jsonl`:

```json
{
  "timestamp": "2026-11-11T00:00:00-05:00",
  "session_id": "PC3-EJEMPLO",
  "input_prompt": "[SIM] Solicito material con entrega",
  "tools_invoked": [],
  "odoo_latency_ms": 0,
  "rule_triggered": [],
  "escalation_flag": false,
  "escalated_to": [],
  "output_response": "[SIM] Evaluación informativa, sin confirmar pedido"
}
```

> Ejemplo ilustrativo de **estructura**, no evidencia de una corrida. Las bitácoras reales deben generarse ejecutando el programa y resguardarse con datos sintéticos. Con datos reales, minimizar/redactar `input_prompt`, establecer permisos de acceso y retención.

### Checklist A11 — Guía (`guia_agente.md`)

- [ ] Instalación, ejecución MOCK/LIVE, comandos y salidas de ejemplo revisados.
- [ ] Esquema JSONL más **log real de prueba**, sin datos sensibles.
- [ ] Diagnóstico y recuperación de conexión, permisos, campos ausentes y LLM documentados.
- [ ] Guía seguida por una persona distinta al autor.

## 7. Mini-guion de demostración y defensa (A7 Brenda + A8 Luis)

No crear un documento de demo independiente. **Exigencia oficial:** caso normal y excepción prioritaria **en vivo**; máximo **10:00** minutos para **presentación + demo**. Dos expositores elegidos al azar; los seis practican. Propuesta de tiempos: **2:00** resultados (láminas 1–4), **1:30** continuidad (5–6), **4:00** demo normal+excepción, **2:00** gobernanza (7–9) y **0:30** transición. El video es solo respaldo.

**Guion MOCK de modalidad base** (ejecutarlo desde el ZIP final; no acredita integración real a Odoo; `LIVE` queda como opción condicionada):

```powershell
python --version
$env:ODOO_MOCK_MODE="True"
$env:LLM_ENABLED="False"
python -m unittest discover -s tests -v
python -m migal_pc3.cli --case tests/fixtures/CP-01.json
python -m migal_pc3.cli --case tests/fixtures/CP-03.json
```

- [ ] Brenda y otro integrante reprodujeron caso normal y excepción prioritaria, con bitácora visible.
- [ ] Se midió la duración de toda la presentación + demo (≤10 min).
- [ ] Los seis saben explicar y ejecutar la demo; se eligieron dos al azar en ensayo.
- [ ] Existe video abierto y probado como contingencia; la versión coincide con el ZIP.

### Prompt E — Verificación de la versión candidata

**Cuándo:** antes de congelar el ZIP, obtener resultados observados y ensayar con Brenda.


```text
Actúa como Ingeniero de Pruebas y Reproducibilidad de Python 3.12 para ERP-MIGAL PC3.

OBJETIVO: verificar la versión candidata del Agente SIE que se va a entregar y exponer, sin modificar los registros reales de Odoo.

1. Lee las actividades 7, 8, 9, 10 y 11, el plan maestro PC3 y la rúbrica oficial.
2. Verifica el modo seleccionado: MOCK, LIVE o LLM remoto; no infieras éxito de los que no se ejecuten.
3. Ejecuta o guía la ejecución de los casos CP3-AI-01, CP3-AI-02 y CP3-AI-03, consignando entrada, esperado, observado, fecha, operador, entorno y versión.
4. Verifica que la bitácora registre herramientas, reglas, escalamiento y respuesta por turno.
5. Reproduce la instalación desde una carpeta limpia usando solo archivos del paquete y prerequisitos declarados.
6. Verifica que ningún archivo de entrega contenga secretos, contraseñas, base empresarial ni datos personales no autorizados.
7. Construye el guion de demo de máximo cuatro minutos: caso normal y excepción prioritaria; deja video como respaldo, no sustituto.
8. Comprueba coherencia con las láminas 7–9 y con el escenario de mantenimiento/cadena de suministro.
9. Devuelve reporte de fallos, limitaciones, evidencias y criterio de aceptación, sin afirmar aprobaciones que no ocurrieron.

NO subas archivos al aula virtual, no hagas push y no modifiques core Odoo sin una instrucción explícita posterior.
```

- [ ] CP3-AI-01/02/03 realmente ejecutados con resultados esperados/observados.
- [ ] ZIP reproducido en carpeta nueva, sin secretos y con demo ensayada.

## 8. Empaquetado y definición de terminado del agente

**Nombre oficial:** `GE703_PC3_Agente_G1_Empresa.zip`. Debe incluir código/exportación, configuración, fixtures, dependencias, guía, licencia cuando corresponda y acceso seguro. Debe abrir en una carpeta limpia y ejecutar la demo reproducible.

- [ ] El ZIP incluye fuente, configuración de ejemplo, mock, contrato tools, tests, `agente.md`, `configuracion.md`, `guia_agente.md` y README.
- [ ] README especifica `python -m unittest discover -s tests -v` y comandos exactos de demo, comprobados.
- [ ] Se excluyeron claves, respaldos reales, datos personales, directorios `.venv` y archivos de salida privados.
- [ ] Se verificaron permisos de archivos y rutas relativas para Windows.
- [ ] Se comparó la versión del ZIP con la demo que mostrará Brenda.
- [ ] Se documentaron pendientes técnicos sin prometer integraciones ausentes.
- [ ] Revisión por Luis (pruebas), Gabriel (guía), Brenda (demo) e implementador principal.

## 9. Fuentes base

- [Catálogo de reglas](../../procesos/catalogo-reglas.md) y [modelo de autorización](../../arquitectura/seguridad/modelo-autorizacion.md).
- [INT-01 CRM–ERP](../../arquitectura/integraciones/INT-01-CRM-ERP.md) y [módulos y dependencias](../../arquitectura/modulos-y-dependencias.md).
- [Registro de pendientes](../../producto/registro-pendientes.md): PEN-015, PEN-016, PEN-018–020, entre otros.
- Antecedente `docs/agente_flujos`: útil para comparación, no para imponer Odoo 18 ni políticas no corroboradas.
