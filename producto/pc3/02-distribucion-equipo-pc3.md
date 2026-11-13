# ERP-MIGAL · PC3 — Distribución del equipo y seguimiento

## 1. Asignaciones oficiales conservadas

| Integrante | Actividades | Resultado comprometido | Requiere de |
|---|---|---|---|
| **Diego Alonso Pinedo Aponte** | **A1, A2** | `activos.md`, `mantenimiento.md` | Contexto empresarial, datos de disponibilidad |
| **César Emmerson Joaquín Palomino** | **A3, A5** | `cadena_suministro.md`; láminas 1–4 | Diego, Alejandro |
| **Alejandro César Flores Marcos** | **A4, A6** | `continuidad_cadena.md`; láminas 5–6 | Diego, César |
| **Brenda Nicole Mirano Flores** | **A7** | Guion, demo real ejecutada, `Video_Agente.mp4`, verificación del ZIP | Implementador, Luis, Gabriel |
| **Luis Rodrigo Núñez Príncipe** | **A10, A8** | `configuracion.md`, 3 pruebas; láminas 7–9 | Implementador, Gabriel, Brenda |
| **Gabriel Gibson Martínez Arista** | **A9, A11** | `agente.md`, `guia_agente.md` | Implementador, Luis |

**Responsabilidades transversales propuestas (pendientes de confirmación del equipo).** No modifican la asignación oficial de las actividades A1–A11:

| Código | Necesidad | Titular / revisor (propuesto, por confirmar) |
|---|---|---|
| **DEC-01** | Programar e integrar agente comercial ejecutable | **Luis Núñez / Gabriel Martínez** |
| **DEC-02** | Unificar, revisar y exportar informe PDF | **Diego Pinedo** (cada uno redacta su parte) / Por confirmar |
| **DEC-03** | Montar, revisar y exportar presentación PDF | **Brenda Mirano** (cada uno hace sus láminas) / Por confirmar |
| **DEC-04** | Subir tres archivos al aula virtual y verificar recepción | **Diego Pinedo** / Validación con captura del envío |
| **DEC-05** | Fijar dataset, modalidad MOCK/LIVE, capacidades y fuentes | **MOCK oficial**; LIVE opcional si hay acceso a Odoo el jue 12 a las 12:00 |

> **Estado de DEC-05:** «MOCK oficial» significa modalidad base **propuesta para el equipo**; no es una disposición oficial del docente ni una prueba ya ejecutada. LIVE se considerará únicamente si se logra acceso autorizado y se verifica la conexión a Odoo a más tardar el jueves 12/11 a las 12:00. Si no, se presenta MOCK de manera explícita. Las capacidades y fuentes siguen requiriendo definición y procedencia.

## 2. Checklists individuales en secuencia

### Diego — A1: activos relevantes

**Hace:** tabla con ID, nombre, función operativa, proceso, criticidad y disponibilidad (MTBF, MTTR, % disponibilidad); debe justificar método, periodo y datos de origen. **Insumo:** [`contexto-empresa.md`](../../arquitectura/contexto-empresa.md), [`fuentes-negocio.md`](../../fuentes/fuentes-negocio.md). Dos camiones están documentados; montacargas y vehículo eléctrico requieren corroboración. **Salida:** `activos.md`, datos para Alejandro/César y el informe.

- [ ] Activos críticos identificados con **ID, función, proceso y criticidad justificada**.
- [ ] MTBF, MTTR y disponibilidad están calculados/definidos con unidad, periodo y fuente; donde no existen mediciones se indica **no medido** o `[SIM]`.
- [ ] La clasificación no presenta infraestructura sin corroboración como hecho confirmado.
- [ ] Tabla enviada a César/Alejandro y revisada para el informe.

### Diego — A2: mantenimiento por activo

**Hace:** por **cada ID** de A1, enfoque preventivo/predictivo/correctivo, frecuencia o disparador, intervención, responsable y vínculo con riesgo de continuidad. **Salida:** `mantenimiento.md`.

- [ ] Hay correspondencia **1:1** entre activos A1 y plan A2.
- [ ] Tipo, justificación, frecuencia/disparador y acción principal definidos.
- [ ] Se explica cómo la intervención influye en paradas, MTTR/servicio y qué es supuesto.
- [ ] El plan se entregó a Alejandro para su matriz causa-efecto.

### César — A3: cadena de suministro parte I

**Hace:** flujo de abastecimiento de extremo a extremo, actores y RACI, además de cinco variables exigidas: **demanda, inventarios, capacidad, disponibilidad y nivel de servicio**. Puede apoyarse en [P2P](../../procesos/p2p/flujo.md), [O2C](../../procesos/o2c/flujo.md) e [inventario](../../procesos/inventario/flujo.md). **Salida:** `cadena_suministro.md`.

- [ ] Diagrama y actores identificados con RACI coherente con GER/VEN/ALM/CMP/FCO/SIS.
- [ ] Cinco variables documentadas con unidades, periodo y rangos/cálculos cuando corresponda.
- [ ] Valores reales/sintéticos diferenciados; stock actual/seguridad y métrica OTIF/fill rate definidos o limitación declarada.
- [ ] Cuello de botella y conexión con activos/escenario compartido verificados.

### César — A5: presentación de resultados

**Hace:** láminas **1–4** con los resultados de A1–A4, el cuello de botella y la **decisión principal**. **Salida:** bloque aprobado para presentación PDF.

- [ ] Activos/mantenimiento y cadena representados con gráficos o tablas legibles.
- [ ] Decisión principal explícita y apoyada en fuentes, datos o supuestos señalados.
- [ ] Cifras contrastadas con Diego/Alejandro y con el informe.
- [ ] Bloque comprimido para respetar los **10 minutos totales** de presentación **más demo**.

### Alejandro — A4: continuidad de la cadena

**Hace:** análisis **falla de activo → caída de disponibilidad → efecto en suministro/despacho → nivel de servicio → mitigación**, con problema, efectos y decisión; cuantitativo si hay datos, lógico cuando se justifique. **Insumos:** A1/A2 de Diego y A3 de César. **Salida:** `continuidad_cadena.md`.

- [ ] Escenario crítico elegido y parámetros alineados con los de Diego/César.
- [ ] Matriz causa-efecto explica tiempo de mantenimiento, indisponibilidad y servicio.
- [ ] Se explican problema, efectos, opciones y decisión principal sustentada.
- [ ] No se presentan políticas o porcentajes simulados como aprobados por MIGAL.

### Alejandro — A6: presentación de continuidad

**Hace:** láminas **5–6**, conectadas con A5 y con los incrementos previos; describen efecto de la decisión sobre la continuidad. **Salida:** bloque para presentación PDF.

- [ ] Secuencia problema → decisión → continuidad aparece visualmente.
- [ ] Cada decisión o mejora muestra valor operativo y sustento trazable.
- [ ] Datos y conceptos coinciden con A4, informe y láminas 1–4.
- [ ] Entregado al integrador DEC-03 para ensayo de tiempo.

### Gabriel — A9: especificación del agente

**Hace:** `agente.md` con **nueve apartados obligatorios**: **propósito, entradas, salidas, fuentes, herramientas, reglas, permisos, responsable humano y escalamiento**. Referencias: [reglas](../../procesos/catalogo-reglas.md), [seguridad](../../arquitectura/seguridad/modelo-autorizacion.md), [INT-01](../../arquitectura/integraciones/INT-01-CRM-ERP.md) y [Agente PC3](03-agente-comercial-pc3.md). **Salida:** contrato técnico que corresponda a la implementación.

- [ ] Nueve apartados completos, con tipos, formatos, permisos y herramientas reales.
- [ ] Reglas y excepciones respetan GER/VEN/ALM/SIS y bloqueos deterministas.
- [ ] Fuentes MOCK/LIVE y políticas pendientes explícitas, sin confundir Odoo 18 con 19.
- [ ] Especificación cotejada con código/fixtures por implementador y Luis.

### Gabriel — A11: manual, bitácora y recuperación

**Hace:** `guia_agente.md`, con instalación, ejecución, consulta de `audit_log.jsonl`, diagnóstico y recuperación seguros. **Salida:** manual reproducible por un tercero.

- [ ] Pasos verificables para instalar y correr MOCK; LIVE solo cuando esté configurado.
- [ ] Ejemplo **real de ejecución de prueba** del log; campos, errores y rutas explicados.
- [ ] Diagnóstico y recuperación de conexión, permisos, campo/modelo ausente y dependencia.
- [ ] Alguien distinto de Gabriel siguió la guía con la versión del ZIP.

### Luis — A10: configuración y pruebas

**Hace:** `configuracion.md`, requisitos, versiones/dependencias, plantilla de variables y **mínimo tres casos ejecutados** (normal, borde, escalamiento). Los antiguos `CP-01..CP-04` del repositorio son antecedentes, no sustituyen las pruebas PC3. **Salida:** entorno repetible y matriz esperado/observado.

- [ ] Python, entorno, dependencias, `.env.example`, modos MOCK/LIVE y comandos documentados.
- [ ] `CP3-AI-01` normal, `CP3-AI-02` borde y `CP3-AI-03` escalamiento **ejecutados y registrados**.
- [ ] Para cada caso: datos, esperado, observado, fecha, versión, modo, evidencia y responsable.
- [ ] ZIP extraído en carpeta limpia y bitácoras/escalamientos comprobados con Brenda.

### Luis — A8: gobernanza, límites y próximos pasos

**Hace:** láminas **7–9** explicando reglas, controles, trazabilidad, escalamiento humano, límites actuales y próximos pasos. **Salida:** bloque alineado con pruebas reales.

- [ ] Reglas y controles mostrados son los **implementados**, no solo planeados.
- [ ] Hay trazabilidad visible: entrada → herramientas → regla → decisión → log.
- [ ] Se representa cuándo intervienen GER/VEN/ALM/SIS y quién decide.
- [ ] Límites y evolución futura explicados sin atribuir capacidades LIVE/LLM no demostradas.

### Brenda — A7: demo en vivo y video backup

**Hace:** reproducir **caso normal + excepción prioritaria** con entradas exactas, mostrar respuesta, reglas y bitácora; ensayar entorno y grabar `Video_Agente.mp4` como contingencia. **Salida:** demo ensayada y paquete verificado con implementador, Gabriel y Luis.

- [ ] Versión del agente, entorno, comandos y guion con prompts/inputs definidos.
- [ ] Demo de principio a fin ejecutada y cronometrada (normal + excepción), sin confundir MOCK/LIVE.
- [ ] `Video_Agente.mp4` grabado, abierto y consistente con el ZIP final.
- [ ] Instalación del ZIP en otra carpeta comprobada; sin secretos ni pasos ocultos.

## 3. Dependencias e integración transversal

| Primero debe existir | Para que pueda continuar | Responsable que entrega |
|---|---|---|
| A1 + A2 (activos y mantenimiento) | A3/A4 y síntesis de A5 | Diego |
| A3 (cinco variables, RACI) | A4 y coherencia de A5/A6 | César |
| A4 (escenario causa-efecto) | Decisión final, informe, A5/A6 y escenario demo | Alejandro |
| DEC-01 (código/agente) y A9 | A10, A11 y A7 | Implementador designado + Gabriel |
| A10 (pruebas, logs) | A7 y A8 finales | Luis |
| A1–A4 + fuentes | Informe académico integrado | Integrador DEC-02 |
| A5 + A6 + A8 | Presentación PDF final | Integrador DEC-03 |
| Informe + Presentación + Agente ZIP | Entrega en aula virtual | DEC-04 (sube y verifica) |

### Checklist corto de integración del informe (sin `.md` separado)

- [ ] DEC-02 recibió A1–A4; integró **contexto, problema, objetivos, alcance y continuidad con PC anteriores**.
- [ ] Incluyó resultados, conclusión/decisión, limitaciones, contribuciones de los seis y uso de IA validado humanamente.
- [ ] Verificó fuentes, unidades, periodos, datos `[SIM]`, gráficos y contradicciones.
- [ ] Exportó y **abrió** `GE703_PC3_Informe_G1_Empresa.pdf` para revisión cruzada.

### Checklist corto de presentación y defensa (sin `.md` separado)

- [ ] DEC-03 integró láminas 1–9 y resolvió cifras/roles incoherentes.
- [ ] **Todos los seis** conocen datos, decisión, agente, reglas, mock/live y límites; nadie depende del autor de un bloque.
- [ ] Se ensayó con **dos integrantes escogidos al azar** y se verificó máximo **10 min presentación + demo**; **3 min preguntas**, **2 min retroalimentación**.
- [ ] Video de Brenda permanece respaldo; no sustituye demostración en vivo.

## 4. Seguimiento compacto (llenar solo con evidencia)

| Frente | Responsable | Estado | Evidencia o bloqueo | Próximo paso |
|---|---|---|---|---|
| A1–A2 activos/mantenimiento | Diego | Pendiente de comprobar | — | Verificar tablas con fuentes |
| A3 y A5 cadena/láminas 1–4 | César | Pendiente de comprobar | — | Integrar A1/A2 |
| A4 y A6 continuidad/láminas 5–6 | Alejandro | Pendiente de comprobar | — | Cerrar escenario y decisión |
| A9 y A11 especificación/manual | Gabriel | Pendiente de comprobar | — | Alinear con código ejecutable |
| A10 y A8 pruebas/gobernanza | Luis | Pendiente de comprobar | — | Ejecutar CP3-AI-01/02/03 |
| A7 demo/video | Brenda | Pendiente de comprobar | — | Ensayar con candidato ZIP |
| Código del agente (**DEC-01**) | Luis (propuesto) / Gabriel (revisor propuesto) | Propuesta por confirmar | — | Ratificar responsable y comprobar versión MOCK |
| Informe PDF (**DEC-02**) | Diego (propuesto) / revisor por confirmar | Propuesta por confirmar | — | Recibir partes individuales y acordar revisor |
| Presentación PDF (**DEC-03**) | Brenda (propuesta) / revisor por confirmar | Propuesta por confirmar | — | Recibir láminas individuales y acordar revisor |
| Subida/confirmación (**DEC-04**) | Diego (propuesto) | Propuesta por confirmar | — | Ratificar subida y captura de recepción |
| Dataset y modalidad (**DEC-05**) | Equipo; responsable de datos por confirmar | MOCK propuesto / LIVE condicionado | — | Validar fuentes y decidir LIVE antes del jue. 12, 12:00 |

**Regla de actualización:** para marcar una casilla y cambiar el estado a **Validada**, enlazar al archivo/commit, salida de prueba o evidencia del entregable. Las ausencias de evidencia son «pendiente de verificar», no automáticamente «incumplido».

## 5. Rutas propuestas de trabajo (sin alterar la estructura ya existente)

```text
ERP-Migal/
├── procesos/
│   ├── activos_mantenimiento/activos.md         # A1
│   ├── activos_mantenimiento/mantenimiento.md   # A2
│   ├── continuidad/continuidad_cadena.md        # A4
│   └── cadena_suministro.md                     # A3
├── producto/
│   ├── pc3/                                      # Estos 4 Markdown
│   └── agente-comercial/
│       ├── agente.md                            # A9
│       ├── configuracion.md                     # A10
│       ├── guia_agente.md                       # A11
│       └── ...                                  # Código, fixtures, README
├── pruebas/pc3/                                 # Evidencias de 3 casos
└── infra/odoo/                                  # Solo infraestructura aprobada
```

Las rutas propuestas deben acordarse antes de crear archivos para evitar duplicar contenido; los PDF y ZIP finales siguen el nombre oficial de la rúbrica.

## 6. Checklist final de entrega (equipo completo)

- [ ] **Informe:** `GE703_PC3_Informe_G1_Empresa.pdf` completo y revisado.
- [ ] **Presentación:** `GE703_PC3_Presentacion_G1_Empresa.pdf` con nueve láminas coherentes.
- [ ] **Agente:** `GE703_PC3_Agente_G1_Empresa.zip` reproducible y tres casos ejecutados/documentados.
- [ ] **Demo:** normal + excepción ensayados, auditoría visible y video backup abierto.
- [ ] **Rúbrica transversal:** fuentes/ética/contribuciones, permisos, límites y los seis preparados para defensa.
- [ ] **Entrega oficial:** los **tres** adjuntos subidos al aula virtual **antes del viernes 13/11/2026 a las 17:00**; Diego (DEC-04 propuesto) y otro integrante comprobaron la recepción mediante captura.

**Fuentes documentales del repositorio:** [`README.md`](../../README.md), [`CONTRIBUTING.md`](../../CONTRIBUTING.md), [`modelo de autorización`](../../arquitectura/seguridad/modelo-autorizacion.md), [`módulos Odoo 19`](../../arquitectura/modulos-y-dependencias.md). La repartición de 11 actividades y la rúbrica oficial prevalecen sobre este plan cuando corresponda.
