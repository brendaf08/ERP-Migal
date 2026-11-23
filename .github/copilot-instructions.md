# Instrucciones para GitHub Copilot

Antes de proponer o escribir código en este repositorio, lee `AGENTS.md` (raíz) y la ficha del agente en el que se trabaja, `producto/agentes/<area>.md`. Esas son las instrucciones completas; este archivo solo resume lo obligatorio.

- Proyecto: ERP de Ferre & Inversiones MIGAL sobre Odoo 19 Community en Docker. Orquestador en `custom_addons/migal_agente`; cada agente en `custom_addons/migal_agente_<codigo>` (ventas, marketing, suministro, cobranzas, pagos, contabilidad).
- Trabaja solo en el módulo del agente. No edites `migal_agente` (núcleo), `agent/catalogo.py` ni el módulo de otro integrante.
- Para pedir datos a otro agente usa `self._consultar("<contrato>", args)`; para avisar, `self._emitir("EV-xxx", datos)` (solo el dueño del evento). Nunca importes el modelo de otro agente.
- Cada herramienta se declara en `_herramientas()` con `description`, `input_schema` (`additionalProperties: False`), `roles` (VEN, ALM, CMP, FCO, GER, SIS), `reglas` y `metodo`, y devuelve `self._resultado(ok, estado, titulo, mensaje, datos=...)`.
- Los agentes leen, calculan y proponen: nunca confirman, aprueban, pagan, dan descuentos o crédito, ajustan inventario ni envían mensajes masivos. Sin `sudo()` salvo justificación.
- Nada de secretos ni datos reales: sin `.env`, claves de API, respaldos, filestore ni fotos reales. Datos de prueba con el prefijo «[PRUEBA]».
- Cada herramienta nueva lleva pruebas en `tests/` (herramienta, permiso por rol y frase de chat) y no debe llamar a Gemini.
- Commits `tipo(agente-<codigo>): descripcion`; PR a `main` con Objetivo, Cambios realizados, Validación y evidencia, Impactos y pendientes.
