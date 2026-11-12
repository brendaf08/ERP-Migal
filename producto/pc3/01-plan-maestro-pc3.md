# ERP-MIGAL · PC3 — Plan maestro de ejecución

## 1. Cómo usar estos cuatro documentos

Este plan explica **el orden y las puertas de salida**. No es necesario crear un archivo de rúbrica, de informe ni de tablero independiente:

| Documento | Para qué sirve |
|---|---|
| **01 — Plan maestro** (este archivo) | Ordenar fases, prioridades, decisiones y entrega final. |
| [02 — Distribución del equipo](02-distribucion-equipo-pc3.md) | Saber qué hace cada uno, qué recibe, qué entrega y cómo comprobarlo; contiene el seguimiento del equipo. |
| [03 — Agente comercial](03-agente-comercial-pc3.md) | Especificación O2C, herramientas, controles, configuración, pruebas, bitácora, demo y **prompts B/C/E**. |
| [04 — Colaboración Odoo–GitHub](04-colaboracion-odoo-github-pc3.md) | Auditoría de código, workspace, Docker, datos, ramas/PR y **prompts A/D**. |

**Flujo práctico:** (1) revisar este plan → (2) confirmar encargados en 02 → (3) ejecutar fases consultando 03/04 → (4) marcar solo checklists con evidencia comprobable → (5) entregar y verificar los tres archivos oficiales.

### Alcance que NO debe cambiarse sin acuerdo

- Continuar las PC anteriores: **activos y mantenimiento**, **cadena de suministro parte I**, relación con **continuidad de servicio**, y agente de evaluación comercial **O2C**.
- Plataforma arquitectónica **Odoo 19 Community**; usar Python 3.12 y XML-RPC en consulta de solo lectura para el MVP. La instalación, datos y permisos locales necesitan comprobación.
- El agente **consulta, valida, recomienda, prepara borrador local y escala**; no confirma ventas, reserva stock, concede crédito/descuento, crea entregas, pagos o escrituras en Odoo.
- **GER** autoriza decisiones sensibles; **VEN** atiende y canaliza la solicitud; **ALM** evalúa almacén/despacho; **SIS** atiende configuración y accesos. No adoptar `LOG` como rol oficial sin actualizar el modelo.
- Distinguir evidencia **verificada**, **documentada**, **propuesta**, **no medida** y dato sintético **`[SIM]`**. No atribuir a Odoo un control que solo aparece en Markdown.
- Prioridad **P0:** cumplir y demostrar la PC3; **P1:** estabilizar instalación y repositorio; **P2:** mejoras posteriores (addon nativo, migraciones, automatización amplia).

## 2. Resultado y camino crítico

**Entregables obligatorios del docente (Grupo 1):**

| Entregable | Nombre oficial | Cómo se confirma |
|---|---|---|
| Informe PDF | `GE703_PC3_Informe_G1_Empresa.pdf` | Activos, mantenimiento, cinco variables de cadena, causa-efecto, decisión, fuentes, conclusiones, limitaciones y contribuciones. **No** requiere especificación técnica del agente dentro del informe. |
| Presentación PDF | `GE703_PC3_Presentacion_G1_Empresa.pdf` | Nueve láminas integradas, datos coherentes y demo en vivo con **caso normal + excepción prioritaria**. |
| Agente ZIP | `GE703_PC3_Agente_G1_Empresa.zip` | Código/exportación, configuración de ejemplo, datos de prueba, dependencias, guía, pruebas y reproducción desde carpeta limpia. |

El video `Video_Agente.mp4` corresponde al **respaldo de la actividad 7**, no reemplaza la demo en vivo. **Sin los tres entregables completos y subidos a tiempo, el grupo no podrá exponer.** La sesión reserva **10 minutos para presentación + demo**, **3 para preguntas** y **2 para retroalimentación**. El docente elige **dos expositores al azar**: los seis deben conocer todo.

```text
Activos (Diego) ──┬─► Cadena (César) ────┬─► Continuidad (Alejandro) ─► Informe
Mantenimiento ────┘                       └─► decisión y láminas 1–6
                                                 │
Escenario común ─► especificación (Gabriel) ─► IMPLEMENTACIÓN (Luis, propuesto)
                          └─────────────────────► pruebas/control (Luis)
                                                 └─► demo (Brenda) + láminas 7–9
Informe + Presentación + ZIP + ensayo ──────────────► revisión + aula virtual
```

### Decisiones transversales que el equipo debe cerrar

| Código | Decisión | Propuesta actual | Estado |
|---|---|---|---|
| **DEC-01** | Implementador del **código ejecutable** y revisión | **Luis Núñez / Gabriel Martínez** | Por confirmar |
| **DEC-02** | Integración y revisión del **informe PDF** | **Diego Pinedo** integra las partes de todos / revisor por confirmar | Por confirmar |
| **DEC-03** | Integración y revisión de las **nueve láminas** | **Brenda Mirano** integra las láminas de todos / revisor por confirmar | Por confirmar |
| **DEC-04** | Subida de los **tres entregables** y evidencia de recepción | **Diego Pinedo** / captura de envío | Por confirmar |
| **DEC-05** | Dataset, modo de demo y fuentes de stock/flota | **MOCK oficial propuesto para el equipo**; LIVE opcional si hay acceso autorizado a Odoo el **jueves 12/11 a las 12:00** | Modalidad propuesta; fuentes y capacidades por fijar |

> Las actividades de cada integrante **no** deben redistribuirse tácitamente. Estas cinco decisiones son responsabilidades **transversales adicionales**.

## 3. Fases de ejecución (con checklist breve)

### Fase 0 — Acordar alcance y responsables · P0

**Entradas:** repartición interna, rúbrica oficial, rama `main`, código Odoo del compañero, agente Python inicial.
**Resultado:** escenario y responsables, sin suposiciones sobre avances.

- [ ] Ratificar o ajustar los titulares/revisores propuestos en DEC-01 a DEC-04, y registrar quién puede relevar a Luis si necesita apoyo en el código.
- [ ] Fijar **un solo escenario**: pedido de materiales → consulta de stock → capacidad/despacho → respuesta y escalamiento cuando proceda.
- [ ] Ratificar DEC-05: MOCK como modalidad base del equipo; evaluar LIVE solo con acceso y consultas verificadas hasta el jueves 12/11 a las 12:00; etiquetar los datos `[SIM]` y documentar capacidades/fuentes.
- [ ] Designar lugar de integración y revisión en GitHub; comunicarlo a los seis.

**Se cierra cuando:** escenario, fuentes, modo y responsables están acordados. **Siguiente paso:** Fase 1.

### Fase 1 — Auditoría del Odoo modificado · P0 acotada

**Guía y prompt A:** [04 — Auditoría Odoo–GitHub](04-colaboracion-odoo-github-pc3.md). **No mover ni borrar** addons o núcleo automáticamente.

- [ ] Recibir código y determinar revisión/versión exacta de Odoo.
- [ ] Identificar módulos propios/terceros/nativos, diferencias con el core, dependencias y accesos.
- [ ] Elaborar `REPORTE_AUDITORIA_MIGAL.md` con hallazgos comprobados y riesgos.
- [ ] Marcar lo que exige verificación en instancia; si no hay acceso, dejarlo como bloqueo y continuar `MOCK` sin falsear resultados.

**Se cierra cuando:** sabemos qué es código propio, qué puede integrarse y qué aún no se ha verificado. **Siguiente paso:** Fase 2.

### Fase 2 — Preparar GitHub, workspace y entorno mínimo · P0 / P1

**Guía, publicación PowerShell y prompt D:** [04 — Colaboración](04-colaboracion-odoo-github-pc3.md). Publicar primero los cuatro Markdown mediante PR, sin crear un segundo repositorio final; la auditoría de Odoo puede continuar en paralelo.

- [ ] Publicar estos **cuatro** `.md` en `producto/pc3/` desde `docs/pc3-coordinacion`, comprobar enlaces y abrir PR para revisión; preservar `arquitectura/`, `procesos/`, `datos/`, `fuentes/`, `producto/` y `pruebas/`.
- [ ] Organizar `producto/pc3/` (estos cuatro MD), `producto/agente-comercial/` (código), `infra/odoo/` y `custom_addons/` solo si auditados.
- [ ] Versionar fixtures sintéticos y `.env.example`; excluir claves, backups, filestore y logs sensibles.
- [ ] Validar Docker/instancia que exista, no reinstalar ni sobrescribir bases operativas innecesariamente.

**Se cierra cuando:** el equipo puede encontrar el código, la configuración y las instrucciones sin perder el trabajo previo. **Siguiente paso:** fases 3 y 4 en paralelo.

### Fase 3 — Completar análisis e integrar informe · P0

**Contenido:** Diego A1–2, César A3, Alejandro A4; **Diego propuesto como integrador DEC-02**, con revisión por confirmar. Cada integrante redacta su parte.

- [ ] Consolidar `activos.md`, `mantenimiento.md`, `cadena_suministro.md` y `continuidad_cadena.md` con cálculos, periodos, fuentes y supuestos.
- [ ] Incorporar contexto, problema/objetivos, continuidad con PC anteriores, resultados, **decisión principal** y conclusiones.
- [ ] Revisar fuentes, etiquetas `[SIM]`, limitaciones, contribuciones de los seis y declaración de uso de IA/validación humana.
- [ ] Revisar cifras y diagramas cruzadamente; exportar y **abrir** `GE703_PC3_Informe_G1_Empresa.pdf`.

**Se cierra cuando:** informe legible, completo y consistente; **no** es necesario añadirle el manual técnico del agente. **Siguiente paso:** integración de láminas (Fase 6).

### Fase 4 — Implementar/alinear agente comercial · P0

**Guía y prompts B/C:** [03 — Agente comercial](03-agente-comercial-pc3.md). Gabriel A9/11; Luis A10/8; Brenda A7; **Luis como implementador provisional DEC-01 y Gabriel como revisor propuesto**, pendientes de ratificación.

- [ ] Alinear contrato de herramientas, reglas, roles y fuentes con el código actual.
- [ ] Verificar, cuando exista instancia autorizada, conexión XML-RPC, modelos/campos con `fields_get` y permisos; no asumir `fleet.vehicle`.
- [ ] Conservar modo `MOCK` reproducible y prohibir escritura en Odoo; vetar descuento/confirmación/crédito no autorizado.
- [ ] Generar bitácora/escalamientos y adaptar `agente.md`, `configuracion.md`, `guia_agente.md` a lo **implementado**.

**Se cierra cuando:** el agente ejecuta consultas/evaluaciones en el modo declarado y conserva controles; no basta un diagrama. **Siguiente paso:** Fase 5.

### Fase 5 — Pruebas, demostración y ensayo · P0

**Guía y prompt E:** [03 — Agente comercial](03-agente-comercial-pc3.md).

- [ ] Ejecutar `CP3-AI-01` normal, `CP3-AI-02` borde y `CP3-AI-03` escalamiento; consignar **esperado vs. observado**.
- [ ] Verificar bitácora JSONL, reglas activadas, responsable de escalamiento, fecha, modo y versión del código.
- [ ] Reproducir el paquete desde carpeta limpia; ensayar **caso normal + excepción** con Brenda y grabar video de respaldo.
- [ ] Ensayar presentación + demo dentro de **10 minutos**; elegir **dos personas aleatorias** en el simulacro.

**Se cierra cuando:** pruebas efectivamente ejecutadas con evidencia, entorno reproducible y demo cronometrada. **Siguiente paso:** Fase 6.

### Fase 6 — Integrar, congelar y subir · P0

- [ ] Integrar láminas: **César 1–4**, **Alejandro 5–6**, **Luis 7–9**; comprobar concordancia con informe y salida del agente.
- [ ] Exportar presentación PDF y empaquetar ZIP con código, datos de prueba, configuración, manual y pruebas; sin secretos.
- [ ] Revisar en **otra carpeta** los tres archivos finales, incluidos nombres exactos, páginas, ejecución y legibilidad.
- [ ] Subir **los tres** al aula virtual **antes de 13/11/2026 17:00**; que un segundo integrante compruebe que se adjuntaron correctamente.

**Se cierra cuando:** se verificó la subida del informe, la presentación y el ZIP. **Fase posterior:** defensa del 14/11; luego mejoras P2.

## 4. Orden práctico inmediato y prioridades

| Cuándo | Prioridad real | Evidencia mínima |
|---|---|---|
| **Mié. 11/11, cierre del día** | Publicar los cuatro Markdown para revisión y ratificar DEC-01 a DEC-05; escenario, Odoo y A1–4 en paralelo | PR de `docs/pc3-coordinacion` y acuerdos en [02](02-distribucion-equipo-pc3.md) |
| **Jue. 12/11** | F3 (informe) + F4 (agente) en paralelo; F5 (pruebas y ensayo) | PDFs candidatos, ZIP candidato y bitácora reproducible |
| **Vie. 13/11 antes de 17:00** | Revisión final F6, subir tres entregables y confirmar | Archivos y constancia de subida |
| **Sáb. 14/11** | Exposición con dos seleccionados al azar | Demo en vivo y defensa de decisiones |

**No bloquear la PC3 por reestructuraciones P1/P2.** Una demo `MOCK` verdaderamente ejecutable y declarada es mejor que afirmar falsamente una integración `LIVE`. Sin embargo, no sustituye la evidencia de Odoo real si el equipo declara que la tiene.

## 5. Checklist de cierre del plan

- [ ] Las 11 actividades tienen entregables, revisores y evidencia en [02](02-distribucion-equipo-pc3.md).
- [ ] El informe incluye resultados, fuentes, ética, contribuciones y continuidad con PC anteriores.
- [ ] El agente/ZIP y sus pruebas coinciden; se demuestra caso normal + excepción en vivo.
- [ ] Los seis dominan proceso, decisión, datos, permisos, demo y límites.
- [ ] Los tres archivos oficiales se encuentran cargados y verificados antes del plazo.

**Referencias:** repartición interna de 11 actividades; `GE703_PC3_Instrucciones_y_Rubrica_Agente_SIE.pdf`; [`README`](../../README.md), [`CONTRIBUTING`](../../CONTRIBUTING.md), [`modelo de autorización`](../../arquitectura/seguridad/modelo-autorizacion.md) del repositorio. Mantener prioridad de requisitos oficiales sobre cronogramas internos.
