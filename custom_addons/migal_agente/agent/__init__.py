"""Núcleo del Agente MIGAL independiente de la interfaz.

- ``contracts``: contrato de herramientas (JSON Schema), roles y permisos.
- ``guardrails``: reglas deterministas que vetan acciones no autorizadas.
- ``intent``: intérprete determinista de solicitudes en lenguaje natural.
- ``llm``: adaptador opcional de LLM (solo interpreta y redacta).
"""
from . import contracts
from . import guardrails
from . import intent
from . import llm
