"""Capa LLM OPCIONAL del Agente MIGAL (desactivada por defecto).

Rol del LLM: interpretar lenguaje libre y redactar la respuesta. NO decide:
- Los guardarraíles se evalúan antes de llamar al LLM.
- Cada herramienta que el LLM solicita pasa por la misma validación de contrato,
  control de permisos por rol y guardarraíles que en modo REGLAS
  (callback ``ejecutar_herramienta`` del orquestador).
- Si el SDK no está instalado, falta la API key, no hay consentimiento de
  transferencia de datos o el servicio falla, el orquestador vuelve al modo REGLAS.

Requiere el paquete ``anthropic`` (pip install anthropic) solo si se activa.
"""
import json
import logging

from . import contracts

_logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-5-5"
MAX_TOOL_ROUNDS = 3

SYSTEM_PROMPT = (
    "Eres el Agente MIGAL, asistente interno de Ferre & Inversiones MIGAL (ferretería, Perú) "
    "dentro de Odoo 19. Atiendes a vendedores (VEN), facturación y cobranzas (FCO) y gerencia (GER).\n"
    "Puedes: preparar el envío de una cotización por WhatsApp, registrar un envío confirmado, "
    "evaluar la cobertura preliminar de stock de una cotización y generar el estado de cuenta de un "
    "cliente. Usa siempre una herramienta para obtener datos; nunca inventes cifras, stock, saldos, "
    "fechas ni teléfonos.\n"
    "Los resultados de las herramientas son la única fuente de verdad. Si una herramienta devuelve "
    "un bloqueo, un error o falta de permiso, explícalo tal cual sin intentar rodearlo.\n"
    "Nunca prometas descuentos, crédito, reservas, entregas garantizadas ni confirmaciones de venta: "
    "esas decisiones son de Gerencia o del flujo de aprobación. Si te lo piden, indica que se escala.\n"
    "Si falta un dato obligatorio (por ejemplo la referencia de la cotización o el cliente), pídelo.\n"
    "Responde en español, breve y claro, en texto plano (sin tablas markdown): el sistema ya "
    "muestra el detalle de cada herramienta debajo de tu respuesta."
)


class LLMUnavailable(RuntimeError):
    pass


def _block_to_dict(block):
    if hasattr(block, "model_dump"):
        return block.model_dump(exclude_none=True)
    return dict(block)


def run(text, *, api_key, model, ejecutar_herramienta, history=None):
    """Ejecuta un turno con tool use.

    :param ejecutar_herramienta: callable(nombre, args) -> dict (resultado ya protegido).
    :returns: (texto_final, llamadas) donde llamadas es una lista de (nombre, args, resultado).
    """
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise LLMUnavailable("El paquete 'anthropic' no está instalado.") from exc
    if not api_key:
        raise LLMUnavailable("Falta la API key del LLM.")

    client = anthropic.Anthropic(api_key=api_key, timeout=45.0, max_retries=1)
    tools = [dict(spec, strict=True) for spec in contracts.llm_tool_specs()]
    messages = list(history or []) + [{"role": "user", "content": text}]
    llamadas = []

    for _round in range(MAX_TOOL_ROUNDS + 1):
        try:
            response = client.beta.messages.create(
                model=model or DEFAULT_MODEL,
                max_tokens=4000,
                system=SYSTEM_PROMPT,
                tools=tools,
                tool_choice={"type": "auto"},
                output_config={"effort": "low"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                messages=messages,
            )
        except anthropic.AuthenticationError as exc:
            raise LLMUnavailable("API key del LLM inválida.") from exc
        except anthropic.RateLimitError as exc:
            raise LLMUnavailable("Límite de uso del LLM alcanzado.") from exc
        except anthropic.APIStatusError as exc:
            raise LLMUnavailable("Error del servicio LLM (%s)." % exc.status_code) from exc
        except anthropic.APIConnectionError as exc:
            raise LLMUnavailable("Sin conexión con el servicio LLM.") from exc

        if response.stop_reason == "refusal":
            raise LLMUnavailable("El LLM declinó la solicitud.")

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if response.stop_reason != "tool_use" or not tool_uses:
            texto = "\n".join(b.text for b in response.content if b.type == "text").strip()
            return texto, llamadas

        if _round == MAX_TOOL_ROUNDS:
            break

        messages.append({"role": "assistant", "content": [_block_to_dict(b) for b in response.content]})
        results = []
        for block in tool_uses:
            args = block.input if isinstance(block.input, dict) else {}
            resultado = ejecutar_herramienta(block.name, args)
            llamadas.append((block.name, args, resultado))
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(resultado.get("para_llm", resultado), ensure_ascii=False, default=str)[:12000],
                "is_error": not resultado.get("ok", False),
            })
        messages.append({"role": "user", "content": results})

    return "", llamadas
