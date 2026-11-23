"""Lectura de la lista: con Gemini (foto o PDF) o desde texto pegado.

Gemini solo TRANSCRIBE el texto de cada línea y su cantidad: no recibe el catálogo
ni elige productos (regla 1 del plan migal_ocr). Se llama a la API REST de Gemini
con la biblioteca estándar, sin dependencias adicionales.
"""
import base64
import json
import logging
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_logger = logging.getLogger(__name__)

API = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
MODELOS_POR_DEFECTO = "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.6-flash"
CANTIDAD_MAXIMA = 10 ** 9

INSTRUCCIONES = (
    "Eres un transcriptor de documentos de una ferretería peruana. Lee la imagen o el PDF y transcribe cada "
    "línea de producto: el texto tal como aparece (con sus abreviaturas y medidas) y la cantidad pedida. Las "
    "notas pueden ser manuscritas, listas en papel o capturas de WhatsApp; las guías y facturas tienen columnas "
    "de cantidad, unidad y descripción. No corrijas ni completes nombres de productos (el símbolo de diámetro Ø "
    "o φ antes de una medida, como Ø 1/4, transcríbelo con ese símbolo), no inventes líneas y no incluyas "
    "precios, totales, fechas ni datos de personas. Si una cantidad no se lee con claridad, déjala en null. Si "
    "el documento no tiene líneas de productos legibles, responde legible = false y una lista vacía."
)
ESQUEMA = {
    "type": "OBJECT",
    "properties": {
        "legible": {"type": "BOOLEAN"},
        "lineas": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "textoCrudo": {"type": "STRING"},
                    "cantidadLeida": {"type": "NUMBER", "nullable": True},
                },
                "required": ["textoCrudo"],
            },
        },
    },
    "required": ["legible", "lineas"],
}


class LecturaError(RuntimeError):
    """No se pudo leer el documento (clave inválida, sin cuota, sin conexión, respuesta inválida)."""


def _cantidad(valor):
    try:
        cantidad = round(float(str(valor).replace(",", ".")), 3)
    except (TypeError, ValueError):
        return None
    return cantidad if 0 <= cantidad < CANTIDAD_MAXIMA else None


def leer_con_gemini(contenido, tipo_mime, api_key, modelos=MODELOS_POR_DEFECTO, timeout=90):
    """Devuelve (modelo_usado, [(texto, cantidad)]). Prueba los modelos en orden si uno no está disponible."""
    if not api_key:
        raise LecturaError("Falta la clave de la API de Gemini (Ajustes › Agente MIGAL).")
    cuerpo = json.dumps({
        "contents": [{"parts": [
            {"inline_data": {"mime_type": tipo_mime, "data": base64.b64encode(contenido).decode()}},
            {"text": INSTRUCCIONES},
        ]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": ESQUEMA},
    }).encode()
    ultimo = None
    lista = [m.strip() for m in (modelos or MODELOS_POR_DEFECTO).split(",") if m.strip()]
    for modelo in lista:
        try:
            req = Request(API % modelo, data=cuerpo, method="POST",
                          headers={"Content-Type": "application/json", "x-goog-api-key": api_key})
            with urlopen(req, timeout=timeout) as resp:
                datos = json.loads(resp.read().decode())
            texto = "".join(p.get("text", "") for p in datos["candidates"][0]["content"]["parts"])
            salida = json.loads(texto or "{}")
            lineas = []
            for linea in salida.get("lineas") or []:
                crudo = (linea.get("textoCrudo") or "").strip()
                if crudo:
                    lineas.append((crudo, _cantidad(linea.get("cantidadLeida"))))
            return modelo, lineas
        except HTTPError as exc:
            detalle = exc.read().decode(errors="ignore")[:300]
            ultimo = "Gemini respondió %s con el modelo %s: %s" % (exc.code, modelo, detalle)
            if exc.code in (400, 401, 403):
                break  # clave inválida o solicitud rechazada: otro modelo fallaría igual
            _logger.warning(ultimo)
        except (URLError, TimeoutError, OSError) as exc:
            ultimo = "Sin conexión con Gemini (%s)." % exc
            _logger.warning(ultimo)
        except (KeyError, IndexError, ValueError) as exc:
            ultimo = "Respuesta de Gemini no válida con el modelo %s (%s)." % (modelo, exc)
            _logger.warning(ultimo)
    raise LecturaError(ultimo or "No se pudo leer el documento con Gemini.")


_CANT_INICIO = re.compile(r"^\s*(?:[-•*]\s*)?(\d+(?:[.,]\d+)?)\s*(?:x\b|und\b|unid\b|u\b|\))?\s*(.+)$", re.I)
_UNIDADES_FINALES = (r"(?:unidades|unidad|unid|und|uds|u|kgs?|kilos?|m|mts?|metros?|bls|bolsas?|rollos?|pzas?|"
                     r"piezas?|cajas?|galones|galon|gln|latas?|millares?|docenas?|varillas?)\.?")
_CANT_FINAL = re.compile(r"^\s*(?:[-•*]\s*)?(.+?)\s*(?:[x:=\-–]\s*|\(\s*)(\d+(?:[.,]\d+)?)\s*(?:"
                         + _UNIDADES_FINALES + r"|\))?\s*\)?\s*$", re.I)


def leer_texto(texto):
    """Lista escrita o pegada: «10 bls cemento sol», «fierro 1/2 x 20», «- clavos 3" : 2 kg»."""
    lineas = []
    for fila in (texto or "").splitlines():
        fila = fila.strip()
        if not fila or len(fila) < 2:
            continue
        m = _CANT_INICIO.match(fila)
        # «1/2 fierro»: la fracción es medida, no cantidad.
        if m and not re.match(r"^\s*\d+\s*/", fila):
            lineas.append((m.group(2).strip(), _cantidad(m.group(1))))
            continue
        m = _CANT_FINAL.match(fila)
        if m and not re.search(r"\d\s*/\s*$", m.group(1)):
            lineas.append((m.group(1).strip(), _cantidad(m.group(2))))
            continue
        lineas.append((fila, None))
    return lineas
