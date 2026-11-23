"""Orquestador del Agente MIGAL.

Flujo por turno (igual en chat y botones):

    entrada -> guardarraíles (vetos) -> interpretación (REGLAS o LLM)
            -> herramienta [contrato JSON Schema + permiso por rol]
            -> respuesta -> escalamiento cuando procede -> bitácora
"""
import json
import logging
import re
import time
import uuid

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from ..agent import contracts, guardrails, intent, llm

_logger = logging.getLogger(__name__)

TOOL_IMPL = {
    "buscar_cotizaciones": ("migal.agente.tool.cotizacion", "buscar"),
    "consultar_cotizacion": ("migal.agente.tool.cotizacion", "consultar"),
    "preparar_whatsapp_cotizacion": ("migal.agente.tool.whatsapp", "preparar"),
    "registrar_envio_whatsapp": ("migal.agente.tool.whatsapp", "registrar"),
    "generar_qr_cotizacion": ("migal.agente.tool.whatsapp", "qr"),
    "evaluar_cobertura_preliminar": ("migal.agente.tool.cobertura", "evaluar"),
    "generar_estado_cuenta": ("migal.agente.tool.estado.cuenta", "generar"),
    "compartir_estado_cuenta": ("migal.agente.tool.estado.cuenta", "compartir"),
}

ESTADO_ICONO = {
    "stock": "🟢", "reposicion": "🟡", "regla": "🔵", "faltante": "🔴", "no_inventariable": "⚪",
}


# Pregunta que acompaña a la lista de opciones según la acción pedida.
PREGUNTA = {
    "consultar_cotizacion": "¿Cuál desea ver?",
    "preparar_whatsapp_cotizacion": "¿Cuál desea enviar por WhatsApp?",
    "registrar_envio_whatsapp": "¿Cuál registro como enviada?",
    "generar_qr_cotizacion": "¿De cuál genero el código QR?",
    "evaluar_cobertura_preliminar": "¿De cuál evalúo la cobertura?",
}
ORDINALES = {"primera": 1, "primero": 1, "segunda": 2, "segundo": 2, "tercera": 3, "tercero": 3,
             "cuarta": 4, "cuarto": 4, "quinta": 5, "quinto": 5, "sexta": 6, "septima": 7, "octava": 8}
REF_VERSION_RE = re.compile(r"-\d+$")


def _money(value, symbol="S/"):
    return "%s %s" % (symbol, "{:,.2f}".format(value or 0.0))


class MigalAgente(models.AbstractModel):
    _name = "migal.agente"
    _description = "Agente MIGAL - orquestador"

    # ------------------------------------------------------------------
    # Configuración
    # ------------------------------------------------------------------
    @api.model
    def _param(self, key, default=False):
        return self.env["ir.config_parameter"].sudo().get_param("migal_agente.%s" % key, default)

    @api.model
    def _llm_config(self):
        enabled = self._param("llm_enabled") in ("True", "1", True)
        ack = self._param("llm_data_ack") in ("True", "1", True)
        proveedor = self._param("llm_proveedor") or "gemini"
        modelo = (self._param("llm_model") or "").strip()
        if proveedor == "gemini" and not modelo.startswith("gemini"):
            modelo = llm.GEMINI_MODELO_POR_DEFECTO
        elif proveedor != "gemini" and (not modelo or modelo.startswith("gemini")):
            modelo = llm.DEFAULT_MODEL
        return {
            "activo": enabled and ack and bool(self._param("llm_api_key")),
            "api_key": self._param("llm_api_key"),
            "model": modelo,
            "proveedor": proveedor,
        }

    @api.model
    def agente_partner(self):
        return self.env.ref("migal_agente.partner_agente_migal")

    # ------------------------------------------------------------------
    # Ejecución protegida de herramientas
    # ------------------------------------------------------------------
    @api.model
    def ejecutar_herramienta(self, nombre, args, *, traza=None):
        """Valida contrato y permisos, ejecuta y registra la llamada en ``traza``."""
        traza = traza if traza is not None else []
        entrada = {"tool": nombre, "arguments": args, "source": "odoo_orm"}
        t0 = time.perf_counter()
        try:
            spec = contracts.TOOLS.get(nombre)
            if not spec:
                raise contracts.ToolInputError("Herramienta no autorizada: %s" % nombre)
            limpio = contracts.validate_args(nombre, args)
            permitido, roles = guardrails.check_permission(self.env.user, spec, contracts.ROLE_GROUPS)
            if not permitido:
                resultado = self.env["migal.agente.tool.base"]._resultado(
                    False, "sin_permiso", "Acción no permitida para su rol",
                    "Su usuario (roles: %s) no está autorizado para «%s». Roles autorizados: %s." % (
                        ", ".join(roles) or "ninguno", nombre.replace("_", " "), ", ".join(spec["roles"])),
                    reglas=["AUT-ROL"], datos={"roles_usuario": roles, "roles_requeridos": spec["roles"]})
            else:
                model_name, method = TOOL_IMPL[nombre]
                resultado = getattr(self.env[model_name], method)(**limpio)
        except contracts.ToolInputError as exc:
            resultado = self.env["migal.agente.tool.base"]._resultado(
                False, "entrada_invalida", "Datos incompletos o inválidos", str(exc))
        except (UserError, AccessError, ValidationError) as exc:
            resultado = self.env["migal.agente.tool.base"]._resultado(
                False, "error", "No se pudo completar la consulta", exc.args[0] if exc.args else str(exc))
        except Exception:  # noqa: BLE001 - el agente falla de forma controlada
            _logger.exception("Error inesperado en la herramienta %s", nombre)
            resultado = self.env["migal.agente.tool.base"]._resultado(
                False, "error", "Error interno", "Ocurrió un error inesperado; se registró para revisión (SIS).",
                escalar_a=["SIS"])
        entrada["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        entrada["ok"] = resultado.get("ok")
        entrada["estado"] = resultado.get("estado")
        traza.append(entrada)
        resultado["para_llm"] = {k: resultado[k] for k in
                                 ("ok", "estado", "titulo", "mensaje", "datos", "controles", "avisos", "escalar_a")}
        if "qr_png_base64" in (resultado.get("datos") or {}):
            resultado["para_llm"]["datos"] = {k: v for k, v in resultado["datos"].items() if k != "qr_png_base64"}
        return resultado

    # ------------------------------------------------------------------
    # Punto de entrada: chat
    # ------------------------------------------------------------------
    @api.model
    def procesar_mensaje(self, texto, *, canal="chat", session_id=None):
        """Atiende un mensaje y devuelve (html_respuesta, log)."""
        session_id = session_id or uuid.uuid4().hex[:12]
        traza = []
        vetos = guardrails.check_request(texto)
        if vetos:
            html = self._render_vetos(vetos)
            log = self._registrar(texto, canal, "reglas", traza, html, resultado="bloqueado",
                                  reglas=[v["regla"] for v in vetos],
                                  escalar=sorted({v["escalar_a"] for v in vetos}), session_id=session_id)
            return html, log

        # Respuesta a una lista de opciones mostrada en el turno anterior («2», «S00637-01»...).
        seleccion = self.env["migal.agente.seleccion"]._pendiente(session_id)
        if seleccion:
            opcion = self._interpretar_eleccion(texto, seleccion)
            if opcion:
                return self._continuar_seleccion(texto, canal, session_id, seleccion, opcion)
            seleccion.unlink()  # otro pedido: la lista anterior se descarta

        cfg = self._llm_config()
        modo = "reglas"
        resultados = []
        texto_llm = ""
        aviso_llm = None
        if cfg["activo"]:
            modo = "llm"
            try:
                texto_llm, llamadas = llm.run(
                    texto, api_key=cfg["api_key"], model=cfg["model"], proveedor=cfg["proveedor"],
                    ejecutar_herramienta=lambda n, a: self.ejecutar_herramienta(n, a, traza=traza))
                resultados = [r for (_n, _a, r) in llamadas]
            except llm.LLMUnavailable as exc:
                # Se atiende igual con el intérprete propio; el detalle queda en el registro del servidor.
                _logger.warning("Agente MIGAL: servicio de IA no disponible (%s)", exc)
                modo = "reglas"

        nombre = None
        if modo == "reglas":
            nombre, args = intent.parse(texto)
            if nombre == "ayuda":
                html = self._render_ayuda(aviso_llm)
                log = self._registrar(texto, canal, modo, traza, html, resultado="ayuda", session_id=session_id)
                return html, log
            cliente = args.pop("_cliente", None)
            previo = []
            if "cotizacion" in contracts.TOOLS[nombre]["input_schema"]["properties"]:
                if not args.get("cotizacion") and cliente:
                    return self._resolver_por_cliente(texto, canal, session_id, nombre, args, cliente)
                if not args.get("cotizacion"):
                    # «ya la envié», «el QR de esa»: la cotización con la que se venía trabajando.
                    anterior = self._cotizacion_en_contexto(session_id)
                    if anterior:
                        args["cotizacion"] = anterior
                        previo.append(Markup("<p><small>Sobre la cotización <b>%s</b>.</small></p>") % anterior)
                elif not previo:
                    resp = self._preguntar_version_si_ambigua(texto, canal, session_id, nombre, args)
                    if resp:
                        return resp
            faltan = [r for r in contracts.TOOLS[nombre]["input_schema"]["required"] if not args.get(r)]
            if faltan:
                html = self._render_falta_dato(nombre, faltan)
                log = self._registrar(texto, canal, modo, traza, html, resultado="ayuda", session_id=session_id)
                return html, log
            resultado = self.ejecutar_herramienta(nombre, args, traza=traza)
            if resultado.get("estado") == "ambiguo" and (resultado.get("datos") or {}).get("candidatos_ids"):
                return self._pedir_cliente(texto, canal, session_id, nombre, args, resultado, traza)
            if previo:
                return self._responder(texto, canal, modo, session_id, traza, [resultado], previo=previo)
            resultados = [resultado]

        if modo == "llm":
            # El LLM no recuerda el turno anterior: si listó varias cotizaciones, la respuesta
            # «2» se resuelve aquí (por defecto, mostrando su detalle).
            busqueda = next((r for r in resultados if len((r.get("datos") or {}).get("opciones") or []) > 1), None)
            if busqueda:
                self.env["migal.agente.seleccion"]._guardar(
                    session_id, "consultar_cotizacion", {}, "cotizacion",
                    self._opciones_compactas(busqueda["datos"]["opciones"]))
        return self._responder(texto, canal, modo, session_id, traza, resultados,
                               texto_llm=texto_llm, aviso_llm=aviso_llm)

    def _responder(self, texto, canal, modo, session_id, traza, resultados, *, texto_llm="", aviso_llm=None,
                   previo=None):
        """Compone el HTML de los resultados y registra la bitácora."""
        partes = list(previo or [])
        if aviso_llm:
            partes.append(Markup("<p><i>%s</i></p>") % aviso_llm)
        if texto_llm:
            partes.append(self._texto_ia_a_html(texto_llm))
            if resultados:
                partes.append(Markup("<p><small><i>Detalle:</i></small></p>"))
        for res in resultados:
            partes.append(self.render_resultado(res))
        if not partes:
            partes.append(self._render_ayuda())
        html = Markup("").join(partes)

        estado = "ok"
        if resultados and not all(r.get("ok") for r in resultados):
            estado = "bloqueado" if any(r.get("estado") in ("bloqueado", "sin_permiso") for r in resultados) else "error"
        reglas = sorted({c for r in resultados for c in r.get("reglas", [])})
        escalar = sorted({c for r in resultados for c in r.get("escalar_a", [])})
        principal = next((r for r in resultados if r.get("res_model")), {})
        log = self._registrar(texto, canal, modo, traza, html, resultado=estado, reglas=reglas, escalar=escalar,
                              session_id=session_id, res_model=principal.get("res_model"),
                              res_id=principal.get("res_id"))
        return html, log

    # ------------------------------------------------------------------
    # Cotizaciones por cliente y elección de versión
    # ------------------------------------------------------------------
    @staticmethod
    def _opciones_compactas(opciones):
        return [{"n": o["n"], "ref": o["ref"], "order_id": o["order_id"], "base": o.get("base", ""),
                 "revision_number": o.get("revision_number", 0)} for o in opciones]

    def _resolver_por_cliente(self, texto, canal, session_id, nombre, args, cliente):
        traza = []
        busqueda = self.ejecutar_herramienta("buscar_cotizaciones", {"cliente": cliente}, traza=traza)
        opciones = (busqueda.get("datos") or {}).get("opciones") or []
        if not busqueda.get("ok") or not opciones:
            previo = [self.render_resultado(busqueda)]
            if busqueda.get("estado") == "sin_resultados":
                previo.append(Markup("<p><small>Puede indicar la referencia (por ejemplo S00573) o el nombre "
                                     "completo o RUC/DNI del cliente.</small></p>"))
            html = Markup("").join(previo)
            estado = "bloqueado" if busqueda.get("estado") == "sin_permiso" else "ayuda"
            log = self._registrar(texto, canal, "reglas", traza, html, resultado=estado, session_id=session_id)
            return html, log
        if len(opciones) == 1:
            fam = opciones[0]
            if len(fam["versiones"]) > 1:
                return self._pedir_version(texto, canal, session_id, nombre, args, fam, traza=traza)
            args = dict(args, cotizacion=fam["ref"])
            previo = [Markup("<p><small>🔎 %s tiene una sola cotización abierta: <b>%s</b>.</small></p>") % (
                fam["cliente"], fam["ref"])]
            return self._responder(texto, canal, "reglas", session_id, traza,
                                   [self.ejecutar_herramienta(nombre, args, traza=traza)], previo=previo)
        self.env["migal.agente.seleccion"]._guardar(
            session_id, nombre, args, "cotizacion", self._opciones_compactas(opciones))
        html = self._render_opciones(busqueda["datos"], PREGUNTA.get(nombre, "¿Cuál desea?"))
        log = self._registrar(texto, canal, "reglas", traza, html, resultado="ayuda", session_id=session_id)
        return html, log

    def _cotizacion_en_contexto(self, session_id, minutos=60):
        """Última cotización trabajada en esta conversación (para «ya la envié», «el QR de esa»)."""
        log = self.env["migal.agente.log"].sudo().search([
            ("session_id", "=", session_id),
            ("user_id", "=", self.env.uid),
            ("res_model", "=", "sale.order"),
            ("res_id", ">", 0),
            ("create_date", ">=", fields.Datetime.subtract(fields.Datetime.now(), minutes=minutos)),
        ], order="id desc", limit=1)
        if not log:
            return None
        order = self.env["sale.order"].with_context(active_test=False).search([("id", "=", log.res_id)])
        return order.name if order else None

    def _pedir_cliente(self, texto, canal, session_id, nombre, args, resultado, traza):
        """Varios clientes coinciden (estado de cuenta): lista para elegir."""
        partners = self.env["res.partner"].browse(resultado["datos"]["candidatos_ids"]).exists()
        opciones = [{"n": n, "ref": p.display_name, "partner_id": p.id, "order_id": 0, "base": "",
                     "revision_number": 0, "doc": p.vat or ""} for n, p in enumerate(partners, 1)]
        self.env["migal.agente.seleccion"]._guardar(session_id, nombre, args, "cliente", opciones)
        items = Markup("").join(
            Markup("<li><b>%s.</b> %s%s</li>") % (o["n"], o["ref"], (" · %s" % o["doc"]) if o["doc"] else "")
            for o in opciones)
        html = Markup(
            "<p>👥 Hay <b>%s clientes</b> que coinciden con «%s». ¿De cuál se trata?</p>"
            "<ul style='list-style:none;padding-left:4px'>%s</ul>"
            "<p><small>Responda con el número o con el nombre.</small></p>") % (
            len(opciones), resultado["datos"].get("cliente", ""), items)
        log = self._registrar(texto, canal, "reglas", traza, html, resultado="ayuda", session_id=session_id)
        return html, log

    def _preguntar_version_si_ambigua(self, texto, canal, session_id, nombre, args):
        """«S00637» sin número de versión y con varias versiones disponibles: preguntar cuál."""
        ref = args["cotizacion"].strip().upper()
        if REF_VERSION_RE.search(ref):
            return None
        order = self.env["sale.order"].search([("name", "=", ref)], limit=1)
        if not order:
            return None
        fam = self.env["migal.agente.tool.cotizacion"].datos_familia(order)
        if len(fam["versiones"]) <= 1:
            return None
        return self._pedir_version(texto, canal, session_id, nombre, args, fam)

    def _pedir_version(self, texto, canal, session_id, nombre, args, fam, traza=None):
        opciones = [dict(v, n=n, base=fam["base"]) for n, v in enumerate(fam["versiones"], 1)]
        self.env["migal.agente.seleccion"]._guardar(
            session_id, nombre, args, "version", self._opciones_compactas(opciones))
        html = self._render_versiones(fam, opciones, PREGUNTA.get(nombre, "¿Cuál desea?"))
        log = self._registrar(texto, canal, "reglas", traza or [], html, resultado="ayuda", session_id=session_id)
        return html, log

    def _interpretar_eleccion(self, texto, seleccion):
        """Devuelve la opción elegida o None si el mensaje es otro pedido."""
        norm = guardrails.normalize(texto).strip(" .!?¿¡")
        opciones = seleccion.opciones
        if not opciones or len(norm.split()) > 7:
            return None
        if seleccion.etapa == "cliente" and not re.fullmatch(r"\D*\d{1,2}\D*", norm):
            palabras = [w for w in re.split(r"[^a-z0-9]+", norm) if len(w) > 2 and w not in ("el", "la", "de", "del")]
            coinciden = [o for o in opciones if palabras and all(w in guardrails.normalize(o["ref"]) for w in palabras)]
            if len(coinciden) == 1:
                return coinciden[0]
        ref = intent._order(norm)
        if ref:
            for o in opciones:
                if o["ref"].upper() == ref or (seleccion.etapa == "cotizacion" and o["base"].upper() == ref):
                    return o
            return None
        # «versión 1», «v2», «la -01»: número de versión (no de la lista).
        m = re.search(r"\b(?:version|v)\s*-?0*(\d{1,3})\b|(?:^|\s)-0*(\d{1,3})\b", norm)
        if m:
            numero = int(m.group(1) or m.group(2))
            return next((o for o in opciones if o.get("revision_number") == numero), None)
        if seleccion.etapa == "version":
            if re.search(r"\b(mas reciente|ultima version|la ultima|la nueva|mas nueva|actual|vigente)\b", norm):
                return max(opciones, key=lambda o: o.get("revision_number", 0))
            if re.search(r"\b(original|primera version|version inicial)\b", norm):
                return min(opciones, key=lambda o: o.get("revision_number", 0))
            if re.search(r"\banterior\b", norm) and len(opciones) > 1:
                return sorted(opciones, key=lambda o: o.get("revision_number", 0))[-2]
        m = re.fullmatch(r"(?:(?:la|el|opcion|numero|nro|n|#|quiero|ver|elijo|escojo|dame|es|esa|con)\s*)*"
                         r"(\d{1,2})\s*[).]?(?:\s+(?:por favor|porfa|gracias))?", norm)
        if m:
            numero = int(m.group(1))
            return next((o for o in opciones if o["n"] == numero), None)
        palabras = norm.split()
        for palabra, numero in ORDINALES.items():
            if palabra in palabras:
                return next((o for o in opciones if o["n"] == numero), None)
        if re.search(r"\bultim[ao]\b", norm):
            return opciones[-1]
        return None

    def _continuar_seleccion(self, texto, canal, session_id, seleccion, opcion):
        nombre, args, etapa = seleccion.herramienta, seleccion.args, seleccion.etapa
        seleccion.unlink()
        if etapa == "cliente":
            partner = self.env["res.partner"].search([("id", "=", opcion["partner_id"])])
            if not partner:
                html = Markup("<p>⚠️ Ya no tengo acceso a ese cliente. Vuelva a consultarlo.</p>")
                log = self._registrar(texto, canal, "reglas", [], html, resultado="error", session_id=session_id)
                return html, log
            args = dict(args, cliente=partner.vat or partner.name)
            traza = []
            return self._responder(texto, canal, "reglas", session_id, traza,
                                   [self.ejecutar_herramienta(nombre, args, traza=traza)])
        order = self.env["sale.order"].with_context(active_test=False).search([("id", "=", opcion["order_id"])])
        if not order:
            html = Markup("<p>⚠️ Ya no tengo acceso a la cotización %s. Vuelva a consultarla.</p>") % opcion["ref"]
            log = self._registrar(texto, canal, "reglas", [], html, resultado="error", session_id=session_id)
            return html, log
        if etapa == "cotizacion":
            fam = self.env["migal.agente.tool.cotizacion"].datos_familia(order)
            if len(fam["versiones"]) > 1:
                return self._pedir_version(texto, canal, session_id, nombre, args, fam)
        args = dict(args, cotizacion=order.name)
        traza = []
        return self._responder(texto, canal, "reglas", session_id, traza,
                               [self.ejecutar_herramienta(nombre, args, traza=traza)])

    # ------------------------------------------------------------------
    # Punto de entrada: botones y asistentes
    # ------------------------------------------------------------------
    @api.model
    def ejecutar_desde_boton(self, nombre, args, descripcion=None):
        traza = []
        resultado = self.ejecutar_herramienta(nombre, args, traza=traza)
        estado = "ok" if resultado.get("ok") else (
            "bloqueado" if resultado.get("estado") in ("bloqueado", "sin_permiso") else "error")
        self._registrar(descripcion or "[botón] %s %s" % (nombre, json.dumps(args, ensure_ascii=False)),
                        "boton", "reglas", traza, self.render_resultado(resultado), resultado=estado,
                        reglas=resultado.get("reglas"), escalar=resultado.get("escalar_a"),
                        res_model=resultado.get("res_model"), res_id=resultado.get("res_id"))
        return resultado

    # ------------------------------------------------------------------
    # Bitácora y escalamiento
    # ------------------------------------------------------------------
    def _registrar(self, texto, canal, modo, traza, html, *, resultado, reglas=None, escalar=None,
                   session_id=None, res_model=None, res_id=None):
        reglas = list(reglas or [])
        escalar = list(escalar or [])
        roles = guardrails.user_roles(self.env.user, contracts.ROLE_GROUPS)
        log = self.env["migal.agente.log"].sudo().create({
            "session_id": session_id or uuid.uuid4().hex[:12],
            "user_id": self.env.user.id,
            "roles": ",".join(roles),
            "canal": canal,
            "modo": modo,
            "input_prompt": (texto or "")[:3000],
            "tools_invoked": json.dumps(traza, ensure_ascii=False, default=str),
            "odoo_latency_ms": sum(t.get("latency_ms", 0.0) for t in traza),
            "rule_triggered": ",".join(reglas),
            "escalation_flag": bool(escalar),
            "escalated_to": ",".join(escalar),
            "resultado": resultado,
            "output_response": self._html_a_texto(html)[:4000],
            "res_model": res_model or False,
            "res_id": res_id or 0,
        })
        if escalar and res_model and res_id:
            record = self.env[res_model].sudo().browse(res_id).exists()
            if record and hasattr(record, "message_post"):
                record.message_post(
                    body=Markup("Agente MIGAL: escalamiento a <b>%s</b> (reglas %s) solicitado por %s.") % (
                        ", ".join(escalar), ", ".join(reglas) or "-", self.env.user.name),
                    author_id=self.agente_partner().id, message_type="comment", subtype_xmlid="mail.mt_note")
        return log

    @staticmethod
    def _html_a_texto(html):
        import re
        text = re.sub(r"<br\s*/?>|</p>|</tr>|</li>", "\n", str(html))
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"[ \t]+", " ", text).strip()

    # ------------------------------------------------------------------
    # Presentación (HTML seguro para Conversaciones)
    # ------------------------------------------------------------------
    @staticmethod
    def _texto_ia_a_html(texto):
        """Texto de la IA a HTML seguro: escapa todo y solo interpreta **negrita** y los saltos de línea."""
        seguro = str(escape(texto.strip()))
        seguro = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", seguro)
        seguro = re.sub(r"(?m)^\s*[*\-]\s+", "• ", seguro)
        return Markup("<p>%s</p>" % seguro.replace("\n", "<br/>"))

    def _render_ayuda(self, aviso=None):
        partes = []
        if aviso:
            partes.append(Markup("<p><i>%s</i></p>") % aviso)
        partes.append(Markup(
            "<p>Hola, soy el <b>Agente MIGAL</b>. Escríbame como le resulte cómodo, por ejemplo:</p><ul>"
            "<li>📄 <b>Ver una cotización</b>: «cotización de Luis» o «S00573». Si hay varias, le muestro la "
            "lista y usted elige («1», «la segunda» o «la más reciente»).</li>"
            "<li>📲 <b>Enviar por WhatsApp</b>: «mándale la cotización a Luis por WhatsApp». Cuando la envíe, "
            "dígame «ya la envié».</li>"
            "<li>🔳 <b>QR para el cliente</b>: «qr de la cotización de Luis» para que la vea en su celular.</li>"
            "<li>📦 <b>Stock de una cotización</b>: «¿hay stock para la cotización de Luis?» o "
            "«cobertura S00573 para el 20/11».</li>"
            "<li>💰 <b>Estado de cuenta y pagos</b>: «cuánto debe Luis», «historial de pagos de Luis» o "
            "«estado de cuenta de Luis de octubre».</li>"
            "<li>📷 <b>Lista de productos del cliente</b>: en la cotización pulse «Escanear lista», suba la foto o "
            "pegue el texto y le propongo cada producto con su % de coincidencia.</li>"
            "</ul>"))
        return Markup("").join(partes)

    def _render_falta_dato(self, nombre, faltan):
        ejemplos = {
            "cotizacion": "la referencia de la cotización (por ejemplo S00573) o el cliente "
                          "(por ejemplo «cotización de Luis»)",
            "cliente": "el cliente (nombre o RUC/DNI)",
        }
        return Markup("<p>Para <b>%s</b> necesito %s.</p>") % (
            nombre.replace("_", " "), ", ".join(ejemplos.get(f, f) for f in faltan))

    def _render_vetos(self, vetos):
        filas = Markup("").join(
            Markup("<li><b>%s</b>: %s → escalado a <b>%s</b>.</li>") % (v["regla"], v["motivo"], v["escalar_a"])
            for v in vetos)
        return Markup(
            "<p>⛔ <b>Solicitud bloqueada por los controles del agente.</b></p><ul>%s</ul>"
            "<p>No se realizó ningún cambio en Odoo. Puede informar al cliente que la condición está en "
            "revisión.</p>") % filas

    def render_resultado(self, res):
        icono = "✅" if res.get("ok") else (
            "🔒" if res.get("estado") == "sin_permiso" else "🔎" if res.get("estado") == "sin_resultados" else "⚠️")
        partes = [Markup("<p>%s <b>%s</b><br/>%s</p>") % (icono, res.get("titulo", ""), res.get("mensaje", ""))]
        controles = res.get("controles") or []
        if controles:
            partes.append(Markup("<ul>%s</ul>") % Markup("").join(
                Markup("<li>%s %s: %s</li>") % ("✔" if c["ok"] else "✖", c["control"], c["detalle"])
                for c in controles))
        datos = res.get("datos") or {}
        if res.get("ok"):
            renderer = {
                "preparar_whatsapp": self._render_whatsapp,
                "cobertura": self._render_cobertura,
                "estado_cuenta": self._render_estado_cuenta,
            }
            if "qr_png_base64" in datos:
                partes.append(Markup(
                    "<p><img src='data:image/png;base64,%s' alt='QR' style='width:180px;height:180px'/><br/>"
                    "<small><a href='%s' target='_blank' rel='noopener'>Abrir la versión digital</a></small></p>")
                    % (datos["qr_png_base64"], datos["url"]))
            elif "enlace_whatsapp" in datos:
                partes.append(renderer["preparar_whatsapp"](datos))
            elif "lineas" in datos:
                partes.append(renderer["cobertura"](datos))
            elif "movimientos" in datos:
                partes.append(renderer["estado_cuenta"](datos))
            elif datos.get("detalle_cotizacion"):
                partes.append(self._render_cotizacion(datos))
            elif datos.get("opciones"):
                partes.append(self._render_opciones(datos, ""))
        for aviso in res.get("avisos") or []:
            partes.append(Markup("<p><small>ℹ️ %s</small></p>") % aviso)
        if res.get("escalar_a"):
            partes.append(Markup("<p><small>Escalado a: %s</small></p>") % ", ".join(res["escalar_a"]))
        return Markup("").join(partes)

    def _render_whatsapp(self, d):
        return Markup(
            "<p><a href='%s' target='_blank' rel='noopener'>📲 Abrir chat de WhatsApp con %s</a></p>"
            "<blockquote>%s</blockquote>"
            "<p><small>Adjunte el PDF de la cotización antes de enviar. Luego escriba «registrar envío %s».</small></p>"
        ) % (d["enlace_whatsapp"], d["telefono"], d["mensaje"], d["cotizacion"])

    def _render_cobertura(self, d):
        def fd(iso):
            return "%s/%s" % (iso[8:10], iso[5:7]) if iso else "—"

        filas = Markup("").join(
            Markup("<tr><td>%s %s</td><td style='text-align:right'>%s %s</td><td style='text-align:right'>%s</td>"
                   "<td style='text-align:right'>%s</td><td style='text-align:right'>%s</td><td>%s</td>"
                   "<td style='text-align:center'>%s</td></tr>") % (
                ESTADO_ICONO.get(l["estado"], ""), l["producto"], "{:g}".format(l["cantidad"]), l["uom"],
                "{:g}".format(l["disponible"]) + (" (%g comp.)" % l["comprometido"] if l.get("comprometido") else ""),
                "{:g}".format(l["reposicion"]), "{:g}".format(l["faltante"]), l["detalle"], fd(l.get("fecha_posible")))
            for l in d["lineas"])
        html = Markup(
            "<p><small>Almacén: %s · Fecha evaluada: %s (%s)</small></p>"
            "<table class='table table-sm table-bordered'><thead><tr><th>Producto</th><th>Pide</th>"
            "<th>Libre</th><th>Llega a tiempo</th><th>Falta</th><th>Resultado</th><th>Se cubre</th></tr></thead>"
            "<tbody>%s</tbody></table>"
            "<p><small>🟢 stock · 🟡 reposición prevista · 🔵 regla habitual · 🔴 faltante · «Libre» descuenta lo "
            "comprometido en otras ventas</small></p>") % (
            d["almacen"], d["fecha_requerida"], d["origen_fecha"], filas)
        if d.get("fecha_atencion"):
            html += Markup("<p>📅 <b>Fecha estimada para atender todo: %s</b> (no garantizada)</p>") % (
                "%s/%s/%s" % (d["fecha_atencion"][8:10], d["fecha_atencion"][5:7], d["fecha_atencion"][:4]))
        if d.get("mensaje_cliente"):
            html += Markup("<p><small><b>Mensaje sugerido para el cliente:</b></small></p><blockquote>%s</blockquote>") % (
                d["mensaje_cliente"])
        return html

    def _render_estado_cuenta(self, d):
        s = d["simbolo"]

        def signo(v):
            return ("+ " if v > 0 else "− ") + _money(abs(v), s)

        mov = Markup("").join(
            Markup("<tr><td>%s</td><td>%s</td><td>%s</td><td style='text-align:right%s'>%s</td></tr>") % (
                m.get("fecha_txt") or m["fecha"], m["documento"], m.get("tipo_cliente") or m["tipo"],
                ";color:#198754" if m.get("importe", 0) < 0 else "", signo(m.get("importe", 0)))
            for m in d["movimientos"]) or Markup("<tr><td colspan='4'><i>Sin movimientos en el período.</i></td></tr>")
        antig = Markup("").join(
            Markup("<li>%s %s · %s · <span style='%s'>%s</span>: <b>%s</b></li>") % (
                x.get("tipo_cliente", ""), x["documento"], x.get("plazo", ""),
                "color:#c0392b;font-weight:bold" if x.get("excedido") else "", x.get("estado_plazo", ""),
                _money(x["pendiente"], s))
            for x in d["documentos_pendientes"])
        info = Markup("").join(
            Markup("<li>%s %s: %s. <i>%s</i></li>") % (i["origen"], i["documento"], _money(i["importe"], s), i["nota"])
            for i in d["informativo"])
        html = Markup(
            "<table class='table table-sm table-bordered'><thead><tr><th>Fecha</th><th>Documento</th><th>Tipo</th>"
            "<th style='text-align:right'>Saldo</th></tr></thead><tbody>"
            "<tr><td>%s</td><td colspan='2'><b>Saldo anterior</b></td><td style='text-align:right'><b>%s</b></td></tr>%s"
            "<tr><td>%s</td><td colspan='2'><b>Saldo al cierre</b></td><td style='text-align:right'><b>%s</b></td></tr>"
            "</tbody></table>") % (
            d.get("fecha_desde_txt") or d["fecha_desde"], _money(d["saldo_anterior"], s), mov,
            d.get("fecha_hasta_txt") or d["fecha_hasta"], _money(d["saldo_periodo"], s))
        if antig:
            html += Markup("<p><b>Antigüedad de la deuda</b></p><ul>%s</ul>") % antig
        html += Markup("<p>💰 <b>Total pendiente: %s</b>%s</p>") % (
            _money(d["total_pendiente"], s),
            Markup(" · <span style='color:#c0392b'>plazo excedido %s</span>") % _money(d["total_vencido"], s)
            if d["total_vencido"] else "")
        if d.get("total_sin_aplicar"):
            html += Markup("<p><small>Incluye un abono a cuenta de %s aún no aplicado a un documento.</small></p>") % (
                _money(d["total_sin_aplicar"], s))
        if info:
            html += Markup("<p><small><b>Informativo (no suma al saldo):</b></small></p><ul><small>%s</small></ul>") % info
        return html

    def _li_version(self, n, v, mostrar_version=False):
        etiqueta = ""
        if mostrar_version:
            etiqueta = Markup(" · versión %s%s") % (
                v["revision_number"], Markup(" <b>(más reciente)</b>") if v["es_ultima"] else " (anterior)")
        if v["vencida"]:
            vig = Markup(" · <span style='color:#c0392b'>venció el %s</span>") % v["vigencia"]
        else:
            vig = (Markup(" · vigente hasta %s") % v["vigencia"]) if v["vigencia"] else ""
        extra = v.get("extra") or ""
        return Markup("<li><b>%s.</b> <b>%s</b>%s · %s · <b>%s</b>%s · %s<br/><small>%s</small>%s</li>") % (
            n, v["ref"], etiqueta, v["fecha"], _money(v["total"], v["simbolo"]), vig, v["estado"],
            v["productos"] or "Sin productos", extra)

    def _render_opciones(self, d, pregunta):
        grupos = {}
        for o in d["opciones"]:
            grupos.setdefault(o["cliente"], []).append(o)
        partes = [Markup("<p>🔎 Encontré <b>%s cotizaciones abiertas</b> que coinciden con «%s». %s</p>") % (
            len(d["opciones"]), d["cliente_buscado"], pregunta)]
        for cliente, opciones in grupos.items():
            items = []
            for o in opciones:
                v = dict(o["versiones"][0])
                if len(o["versiones"]) > 1:
                    v["extra"] = Markup("<br/><small>📑 %s versiones disponibles</small>") % len(o["versiones"])
                items.append(self._li_version(o["n"], v))
            partes.append(Markup("<p><b>👤 %s</b></p><ul style='list-style:none;padding-left:4px'>%s</ul>") % (
                cliente, Markup("").join(items)))
        partes.append(Markup("<p><small>Responda con el número (por ejemplo «1») o la referencia.</small></p>"))
        return Markup("").join(partes)

    def _render_versiones(self, fam, opciones, pregunta):
        items = Markup("").join(self._li_version(o["n"], o, mostrar_version=True) for o in opciones)
        return Markup(
            "<p>📑 La cotización <b>%s</b> de %s tiene <b>%s versiones disponibles</b>. %s</p>"
            "<ul style='list-style:none;padding-left:4px'>%s</ul>"
            "<p><small>Responda con el número de la lista, «la más reciente», «versión 1» o la referencia. "
            "Una versión anterior sigue disponible hasta que vence.</small></p>") % (
            fam["base"], fam["cliente"], len(opciones), pregunta, items)

    def _render_cotizacion(self, d):
        s = d["simbolo"]
        filas = Markup("").join(
            Markup("<tr><td>%s</td><td style='text-align:right'>%s %s</td><td style='text-align:right'>%s</td>"
                   "<td style='text-align:right'>%s</td><td style='text-align:right'>%s</td></tr>") % (
                l["producto"], "{:g}".format(l["cantidad"]), l["uom"], _money(l["precio"], s),
                ("%g%%" % l["descuento"]) if l["descuento"] else "—", _money(l["subtotal"], s))
            for l in d["lineas_cotizacion"]) or Markup("<tr><td colspan='5'><i>Sin productos.</i></td></tr>")
        if d["vencida"]:
            vig = Markup("<span style='color:#c0392b'>venció el %s</span>") % d["vigencia"]
        else:
            vig = ("vigente hasta %s" % d["vigencia"]) if d["vigencia"] else "sin fecha de vencimiento"
        html = Markup(
            "<p>👤 %s%s · Vendedor: %s<br/>📅 Fecha: %s · %s</p>"
            "<table class='table table-sm table-bordered'><thead><tr><th>Producto</th><th>Cantidad</th>"
            "<th>Precio</th><th>Desc.</th><th>Subtotal</th></tr></thead><tbody>%s</tbody></table>"
            "<p>Base imponible %s · Impuestos %s · <b>Total %s</b></p>") % (
            d["cliente"], (" (%s)" % d["documento"]) if d["documento"] else "", d["vendedor"] or "—", d["fecha"],
            vig, filas, _money(d["base_imponible"], s), _money(d["impuestos"], s), _money(d["total"], s))
        otras = [v for v in d["versiones"] if v["ref"] != d["cotizacion"]]
        if otras:
            html += Markup("<p><small>📑 Otras versiones disponibles: %s</small></p>") % Markup(", ").join(
                Markup("<b>%s</b> (%s%s)") % (v["ref"], _money(v["total"], v["simbolo"]),
                                               ", más reciente" if v["es_ultima"] else "")
                for v in otras)
        html += Markup("<p><a href='%s' target='_blank'>Abrir %s en Ventas</a></p>") % (d["url"], d["cotizacion"])
        if d["disponible"] and not d["vencida"]:
            html += Markup("<p><small>Puede pedirme: «whatsapp %s», «qr %s» o «cobertura %s».</small></p>") % (
                d["cotizacion"], d["cotizacion"], d["cotizacion"])
        return html

    # ------------------------------------------------------------------
    # Acción de menú: abrir el chat con el agente
    # ------------------------------------------------------------------
    @api.model
    def action_abrir_chat(self):
        partner = self.agente_partner()
        channel = self.env["discuss.channel"]._get_or_create_chat([partner.id])
        if not channel.message_ids:
            channel.sudo().message_post(author_id=partner.id, body=self._render_ayuda(),
                                        message_type="comment", subtype_xmlid="mail.mt_comment")
        return {
            "type": "ir.actions.client",
            "tag": "mail.action_discuss",
            "params": {"active_id": "discuss.channel_%s" % channel.id},
        }
