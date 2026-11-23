# Guía del equipo: agentes MIGAL

Cómo construir cada agente en paralelo, con la misma arquitectura, sin pisarnos y gastando pocos créditos de IA. Las reglas que deben seguir los asistentes de código están en [AGENTS.md](../../AGENTS.md).

## 1. Quién hace qué

| Agente | Responsable | Ficha | Herramienta de IA | Revisa el PR |
|---|---|---|---|---|
| Orquestador y núcleo | Luis | [ADR-007](../../arquitectura/decisiones/ADR-007-arquitectura-multiagente.md) | Codex, Claude Code, Gemini | Aprobación final |
| Ventas | Brenda | [ventas.md](ventas.md) | Codex | Alejandro |
| Marketing | Brenda | [marketing.md](marketing.md) | Codex | Alejandro |
| Cadena de suministro | Alejandro | [suministro.md](suministro.md) | Google AI Pro | Brenda |
| Cuentas por pagar | Diego | [pagos.md](pagos.md) | Claude Code | Gabriel |
| Cuentas por cobrar | Gabriel | [cobranzas.md](cobranzas.md) | Google AI Pro | Diego |
| Contabilidad | César | [contabilidad.md](contabilidad.md) | Gratuitas (Gemini CLI, Copilot Student, OpenCode) | Luis |

Cada agente ya tiene un módulo instalado con al menos una herramienta real, sus pruebas, los eventos conectados y los contratos del catálogo. Nadie parte de cero ni espera a otro: si el agente que te responde todavía no implementa una consulta, el orquestador devuelve la respuesta de ejemplo del contrato marcada como simulada.

## 2. Primer día

1. Actualiza `main` y aplica los módulos a tu base:
   ```powershell
   git checkout main; git pull
   powershell -ExecutionPolicy Bypass -File .\infra\odoo\actualizar.ps1
   powershell -ExecutionPolicy Bypass -File .\infra\odoo\cargar_datos_demo.ps1
   ```
2. Crea tu rama: `git checkout -b feat/agente-<codigo>`.
3. Abre Odoo, entra al chat del agente y prueba las frases de tu ficha. Revisa en **Agente MIGAL → Bitácora** que la llamada quedó registrada con tu agente.
4. Lee tu ficha y el proceso de tu área en `procesos/`.
5. Para usar el chat con Gemini, cada uno crea su propia clave gratuita en Google AI Studio y la pega en **Ajustes → Agente MIGAL**. Google AI Pro no incluye clave de API. La clave nunca va al código ni al repositorio.

## 3. Ciclo de trabajo por herramienta

1. Elige la siguiente tarea de la sección 2 de tu ficha.
2. Pide a tu asistente de código **una sola herramienta por vez**, citando la ficha y AGENTS.md (prompt sugerido abajo).
3. Revisa el código: que solo toque tu módulo, que use `self._consultar` para otros agentes y que no confirme, pague ni envíe nada.
4. Agrega o ajusta la prueba y corre la batería (comando en AGENTS.md).
5. Prueba la frase en el chat y el botón del asistente si corresponde.
6. Commit pequeño: `feat(agente-<codigo>): agregar <herramienta>`.

Prompt sugerido:

> Lee AGENTS.md y producto/agentes/<codigo>.md. Implementa solo la herramienta «<nombre>» en custom_addons/migal_agente_<codigo>/models/agente.py siguiendo el patrón de las herramientas existentes, con su prueba en tests/test_<codigo>.py y una frase en _reconocer. No modifiques otros módulos.

## 4. Ahorrar créditos de IA

- Abre el asistente **dentro de tu módulo** y nómbrale solo los archivos necesarios; no le pidas leer todo el repositorio.
- Una tarea pequeña por conversación; empieza una nueva al terminar cada herramienta.
- Pide primero el plan en tres líneas y después el código.
- Corre tú las pruebas en Docker y pégale solo el error, no el registro completo.
- Gratis: Gemini CLI con cuenta personal, GitHub Copilot con el Student Developer Pack (correo UNI) y OpenCode con modelos gratuitos.
- Declara la herramienta usada en [uso de IA](../../fuentes/uso-ia.md).

## 5. Reglas de oro

1. Tu agente vive solo en `custom_addons/migal_agente_<codigo>`. Cambios al núcleo o al catálogo: pídelos a Luis.
2. Los agentes leen, calculan, proponen y preparan borradores. Nunca confirman, aprueban, pagan, dan descuentos ni envían en masa.
3. Entre agentes solo con contratos del catálogo (`_consultar`, `_emitir`).
4. Datos de prueba con «[PRUEBA]». Claves solo en Ajustes. Nada de `.env`, respaldos ni fotos reales en GitHub.
5. PR con las cuatro secciones de CONTRIBUTING y sin declarar pruebas no realizadas.

## 6. Cambios a un contrato

Agregar un campo opcional a la salida se puede en cualquier momento. Cambiar o quitar algo, o crear un contrato nuevo, requiere: proponerlo en el grupo, acuerdo del agente que lo consume y que Luis actualice `catalogo.py` e [INT-02](../../arquitectura/integraciones/INT-02-contratos-agentes.md) subiendo la versión.

## 7. Calendario

| Fecha | Hito |
|---|---|
| Lun 23/11 | Base publicada y fusionada en `main` |
| Mar 24/11 | Cada uno con su rama y su primera herramienta nueva |
| Mié 25/11 | Reunión de 30 min: contratos versión 1 cerrados |
| Mié 25 – sáb 28 | Desarrollo; las consultas pendientes responden simuladas |
| Dom 29/11 | Consultas reales entre agentes (sin simulador) |
| Lun 30/11 | Pruebas de flujos completos y correcciones |
| Mar 1/12 | Congelamiento al mediodía; demos y PR fusionados en la noche |

## 8. Terminado significa

- Las herramientas de la ficha implementadas o justificadas como pendientes.
- Pruebas propias y del núcleo en verde.
- Las consultas que ofreces devuelven las claves de `ejemplo_salida`; ya no aparece «simulada» para ellas.
- Ficha actualizada con lo que quedó y lo que falta.
- PR revisado por tu pareja y aprobado por Luis.
