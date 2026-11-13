# Declaración de uso de herramientas de inteligencia artificial

Este documento declara el uso de herramientas de inteligencia artificial (IA) en la elaboración de la documentación y el código de **ERP-MIGAL**, conforme a [CONTRIBUTING.md](../CONTRIBUTING.md), apartado 5. Distingue los usos comprobables en el historial del repositorio de los usos declarados por el equipo que no dejan evidencia en él.

La revisión y aprobación del contenido generado con apoyo de IA son responsabilidad del equipo. El uso de IA no convierte una propuesta en evidencia empresarial ni en una verificación técnica en Odoo.

## 1. Usos verificables en el repositorio

| Herramienta | Uso | Evidencia comprobable |
|---|---|---|
| OpenAI Codex | Elaboración de los cambios documentales de procesos y reglas, datos y trazabilidad, y casos de prueba. | Ramas `codex/b2-procesos-reglas`, `codex/b3-datos-trazabilidad` y `codex/b4-casos-prueba`, integradas mediante los PR #8, #9 y #10. |
| GitHub Copilot (revisor de PR) | Revisión automática de los Pull Requests. | Revisiones de `copilot-pull-request-reviewer[bot]` en los PR #5 al #19. |
| Herramientas LLM (ChatGPT / Claude) | Asistencia en la programación en Python, depuración de errores y generación de datos sintéticos (JSON) para el entorno de pruebas del Agente Comercial O2C. | Commits de implementación del agente comercial integrados en el PR #19. |

Los PRs registran además una aprobación humana antes de su integración en la rama principal.

## 2. Usos declarados sin evidencia en el repositorio

Las siguientes herramientas se utilizaron fuera del repositorio. Sus salidas no se incorporaron directamente mediante commits de la herramienta, por lo que el equipo declara su alcance.

| Herramienta | Uso declarado | Estado |
|---|---|---|
| Claude (Anthropic) | Búsqueda de información de referencia, estructuración de la arquitectura documental, análisis de alineamiento entre ramas y apoyo en la lógica de creación del agente comercial. | Declarado por el equipo de desarrollo. |
| ChatGPT (OpenAI) | Ordenamiento de ideas, refinamiento de la redacción técnica, validación de reglas de negocio y apoyo en la definición de los prompts del agente. | Declarado por el equipo de desarrollo. |
| Gemini (Google) | Revisión, reestructuración y análisis de las variables de la cadena de suministro, catálogo de activos, plan de mantenimiento y continuidad operativa para los entregables de la PC3. | Declarado por el equipo (Alejandro Flores, César Joaquín, Diego Pinedo). |

## 3. Uso en la elaboración de los primeros Pull Requests (PR #1 a #7)

Durante la elaboración y estructuración inicial del proyecto (PR #1 al #7), el equipo utilizó herramientas de IA (principalmente ChatGPT y Claude) como apoyo general para buscar información sobre estándares de arquitectura empresarial, ordenar las ideas iniciales, estructurar las tablas de decisiones (ADRs) y realizar correcciones ortográficas y de estilo. 

Todos los resultados generados fueron analizados, adaptados a la realidad operativa de la ferretería MIGAL y validados manualmente por los integrantes del equipo antes de su integración al repositorio.

## 4. Criterios aplicados y limitaciones

- Los hechos sobre MIGAL proceden de las fuentes registradas en [fuentes del negocio](fuentes-negocio.md), no de las herramientas de IA.
- Las herramientas de IA no ejecutaron pruebas en la instancia local de Odoo.
- Las salidas de IA se revisaron mediante Pull Requests antes de integrarse en `main`.
- Esta declaración se actualiza cuando se incorpora un nuevo uso relevante de IA.