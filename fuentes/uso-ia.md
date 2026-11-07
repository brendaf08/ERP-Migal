# Declaración de uso de herramientas de inteligencia artificial

Este documento declara el uso de herramientas de inteligencia artificial (IA) en la elaboración de la documentación de **ERP-MIGAL**, conforme a [CONTRIBUTING.md](../CONTRIBUTING.md), apartado 5. Distingue los usos comprobables en el historial del repositorio de los usos declarados por el equipo que no dejan evidencia en él.

La revisión y aprobación del contenido generado con apoyo de IA son responsabilidad del equipo. El uso de IA no convierte una propuesta en evidencia empresarial ni en una verificación técnica en Odoo.

## 1. Usos verificables en el repositorio

| Herramienta | Uso | Evidencia comprobable |
|---|---|---|
| OpenAI Codex | Elaboración de los cambios documentales de procesos y reglas, datos y trazabilidad, y casos de prueba. | Ramas `codex/b2-procesos-reglas`, `codex/b3-datos-trazabilidad` y `codex/b4-casos-prueba`, integradas mediante los PR #8, #9 y #10. |
| GitHub Copilot (revisor de PR) | Revisión automática de los Pull Requests. | Revisiones de `copilot-pull-request-reviewer[bot]` en los PR #5 a #10. |

Los PR #6 a #10 registran además una aprobación humana (`brendaf08`) antes de su integración.

## 2. Usos declarados sin evidencia en el repositorio

Las siguientes herramientas se utilizaron fuera del repositorio. Sus salidas no se incorporaron directamente mediante commits de la herramienta, por lo que su alcance debe confirmarlo el equipo.

| Herramienta | Uso declarado | Estado |
|---|---|---|
| Claude (Anthropic) | Auditorías de alineamiento entre ramas y de cobertura documental, especificación operativa de la consolidación de PR #3 y PR #4, y propuesta de los cambios correctivos de esta fase. No tuvo acceso de escritura al repositorio. | Declarado. Integrante responsable y fechas por confirmar. |
| ChatGPT (OpenAI) | Revisión y refinamiento de la especificación operativa de la consolidación. | Declarado por el equipo. Alcance por confirmar. |

## 3. Uso en la elaboración de los PR #1 a #7

El historial no permite determinar si se usó IA en los PR #1 a #7. El equipo debe completar este apartado indicando, para cada uno, si se utilizó alguna herramienta, con qué propósito y quién revisó el resultado.

## 4. Criterios aplicados y limitaciones

- Los hechos sobre MIGAL proceden de las fuentes registradas en [fuentes del negocio](fuentes-negocio.md), no de las herramientas de IA.
- Las herramientas de IA no ejecutaron pruebas en Odoo. Los casos de prueba permanecen **No ejecutados**.
- Las salidas de IA se revisaron mediante Pull Requests antes de integrarse en `main`.
- Esta declaración se actualiza cuando se incorpora un nuevo uso relevante de IA.
