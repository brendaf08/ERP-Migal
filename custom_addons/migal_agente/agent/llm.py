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
    "Si el usuario nombra al cliente en vez de la referencia de la cotización, usa buscar_cotizaciones; "
    "si hay varias cotizaciones o varias versiones disponibles, enuméralas y pide que elija (una versión "
    "anterior sigue disponible hasta que vence, pero solo la más reciente se puede confirmar). "
    "Para ver el detalle de una cotización usa consultar_cotizacion.\n"
    "Los parámetros que no son obligatorios no se piden: por ejemplo, sin fecha la cobertura se evalúa para hoy "
    "y el estado de cuenta toma el mes en curso.\n"
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


# Varios modelos separados por coma, por orden de preferencia: si uno está saturado (503), sin cuota (429)
# o no existe (404), se usa el siguiente. El primero responde en 2-4 s con las herramientas del agente.
GEMINI_MODELO_POR_DEFECTO = "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.6-flash"
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
_CLAVES_ESQUEMA_GEMINI = {"type", "properties", "required", "description", "items", "enum", "nullable", "format"}


def _esquema_gemini(schema):
    """Subconjunto OpenAPI que acepta Gemini en las declaraciones de funciones."""
    if isinstance(schema, dict):
        limpio = {k: _esquema_gemini(v) for k, v in schema.items() if k in _CLAVES_ESQUEMA_GEMINI}
        if "properties" in schema:
            limpio["properties"] = {k: _esquema_gemini(v) for k, v in schema["properties"].items()}
        return limpio
    if isinstance(schema, list):
        return [_esquema_gemini(x) for x in schema]
    return schema


def _gemini_post(api_key, model, cuerpo, timeout=45):
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    req = Request(GEMINI_API % model, data=json.dumps(cuerpo).encode(), method="POST",
                  headers={"Content-Type": "application/json", "x-goog-api-key": api_key})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as exc:
        motivo = {400: "solicitud rechazada", 401: "clave inválida", 403: "clave sin permiso",
                  404: "modelo no disponible", 429: "límite de uso alcanzado"}.get(exc.code, "error %s" % exc.code)
        error = LLMUnavailable("Gemini: %s." % motivo)
        error.otro_modelo = exc.code in (404, 429) or exc.code >= 500
        raise error from exc
    except (URLError, TimeoutError, OSError) as exc:
        error = LLMUnavailable("Sin conexión con Gemini.")
        error.otro_modelo = isinstance(exc, TimeoutError)
        raise error from exc


def _gemini_post_con_respaldo(api_key, modelos, cuerpo, estado):
    """Prueba los modelos en orden; ``estado['modelo']`` recuerda el que respondió para el resto del turno."""
    candidatos = [estado["modelo"]] if estado.get("modelo") else modelos
    for posicion, modelo in enumerate(candidatos):
        try:
            datos = _gemini_post(api_key, modelo, cuerpo, timeout=30)
            estado["modelo"] = modelo
            return datos
        except LLMUnavailable as exc:
            if not getattr(exc, "otro_modelo", False) or posicion == len(candidatos) - 1:
                raise
            _logger.warning("Gemini: el modelo %s no está disponible (%s); se prueba el siguiente.", modelo, exc)
    raise LLMUnavailable("Sin modelos de Gemini configurados.")


def run_gemini(text, *, api_key, model, ejecutar_herramienta, history=None):
    """Mismo contrato que ``run`` usando la API de Gemini (function calling)."""
    if not api_key:
        raise LLMUnavailable("Falta la clave de Gemini.")
    modelos = [m.strip() for m in (model or GEMINI_MODELO_POR_DEFECTO).split(",") if m.strip()]
    estado = {}
    declaraciones = [{"name": s["name"], "description": s["description"],
                      "parameters": _esquema_gemini(s["input_schema"])} for s in contracts.llm_tool_specs()]
    contents = list(history or []) + [{"role": "user", "parts": [{"text": text}]}]
    llamadas = []
    for _round in range(MAX_TOOL_ROUNDS + 1):
        datos = _gemini_post_con_respaldo(api_key, modelos, {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": contents,
            "tools": [{"functionDeclarations": declaraciones}],
            "generationConfig": {"temperature": 0.2},
        }, estado)
        try:
            contenido = datos["candidates"][0]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMUnavailable("Gemini no devolvió respuesta.") from exc
        partes = contenido.get("parts") or []
        funciones = [p["functionCall"] for p in partes if "functionCall" in p]
        if not funciones or _round == MAX_TOOL_ROUNDS:
            return "\n".join(p.get("text", "") for p in partes if "text" in p).strip(), llamadas
        contents.append({"role": "model", "parts": partes})
        respuestas = []
        for llamada in funciones:
            args = llamada.get("args") if isinstance(llamada.get("args"), dict) else {}
            resultado = ejecutar_herramienta(llamada.get("name"), args)
            llamadas.append((llamada.get("name"), args, resultado))
            respuestas.append({"functionResponse": {
                "name": llamada.get("name"),
                "response": json.loads(json.dumps(resultado.get("para_llm", resultado), ensure_ascii=False,
                                                  default=str)),
            }})
        contents.append({"role": "user", "parts": respuestas})
    return "", llamadas


def run(text, *, api_key, model, ejecutar_herramienta, history=None, proveedor="anthropic"):
    """Ejecuta un turno con tool use.

    :param ejecutar_herramienta: callable(nombre, args) -> dict (resultado ya protegido).
    :param proveedor: «gemini» o «anthropic».
    :returns: (texto_final, llamadas) donde llamadas es una lista de (nombre, args, resultado).
    """
    if proveedor == "gemini":
        return run_gemini(text, api_key=api_key, model=model, ejecutar_herramienta=ejecutar_herramienta,
                          history=history)
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
