"""Orquestador del Agente MIGAL.

Flujo por turno (igual en chat y botones):

    entrada -> guardarraíles (vetos) -> interpretación (REGLAS o LLM)
            -> herramienta [contrato JSON Schema + permiso por rol]
            -> respuesta -> escalamiento cuando procede -> bitácora
"""
import json
import logging
import time
import uuid

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from ..agent import contracts, guardrails, intent, llm

_logger = logging.getLogger(__name__)

TOOL_IMPL = {
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
        return {
            "activo": enabled and ack and bool(self._param("llm_api_key")),
            "api_key": self._param("llm_api_key"),
            "model": self._param("llm_model") or llm.DEFAULT_MODEL,
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

        cfg = self._llm_config()
        modo = "reglas"
        resultados = []
        texto_llm = ""
        aviso_llm = None
        if cfg["activo"]:
            modo = "llm"
            try:
                texto_llm, llamadas = llm.run(
                    texto, api_key=cfg["api_key"], model=cfg["model"],
                    ejecutar_herramienta=lambda n, a: self.ejecutar_herramienta(n, a, traza=traza))
                resultados = [r for (_n, _a, r) in llamadas]
            except llm.LLMUnavailable as exc:
                aviso_llm = "LLM no disponible (%s). Respondí con el modo de reglas." % exc
                modo = "reglas"

        nombre = None
        if modo == "reglas":
            nombre, args = intent.parse(texto)
            if nombre == "ayuda":
                html = self._render_ayuda(aviso_llm)
                log = self._registrar(texto, canal, modo, traza, html, resultado="ayuda", session_id=session_id)
                return html, log
            faltan = [r for r in contracts.TOOLS[nombre]["input_schema"]["required"] if not args.get(r)]
            if faltan:
                html = self._render_falta_dato(nombre, faltan)
                log = self._registrar(texto, canal, modo, traza, html, resultado="ayuda", session_id=session_id)
                return html, log
            resultados = [self.ejecutar_herramienta(nombre, args, traza=traza)]

        partes = []
        if aviso_llm:
            partes.append(Markup("<p><i>%s</i></p>") % aviso_llm)
        if texto_llm:
            partes.append(Markup("<p>%s</p>") % texto_llm)
            if resultados:
                partes.append(Markup("<p><small><i>Detalle verificado por las herramientas del agente:</i></small></p>"))
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
    def _render_ayuda(self, aviso=None):
        cfg = self._llm_config()
        modo = "LLM + reglas" if cfg["activo"] else "reglas deterministas"
        partes = []
        if aviso:
            partes.append(Markup("<p><i>%s</i></p>") % aviso)
        partes.append(Markup(
            "<p>Hola, soy el <b>Agente MIGAL</b> (modo: %s). Puedo ayudarle con:</p><ul>"
            "<li><b>WhatsApp</b>: «whatsapp S00573» prepara el enlace y el mensaje; «registrar envío S00573» "
            "deja constancia cuando ya lo envió.</li>"
            "<li><b>Cliente presencial</b>: «qr S00573» muestra un código QR para que vea la cotización en su celular.</li>"
            "<li><b>Cobertura preliminar</b>: «cobertura S00573» o «cobertura S00573 para el 20/11/2026».</li>"
            "<li><b>Estado de cuenta</b> (FCO/GER): «estado de cuenta de Cliente Prueba del 01/10/2026 al 13/11/2026».</li>"
            "</ul><p><small>No confirmo ventas, no reservo stock, no aplico descuentos ni otorgo crédito: "
            "esas decisiones se escalan a Gerencia.</small></p>") % modo)
        return Markup("").join(partes)

    def _render_falta_dato(self, nombre, faltan):
        ejemplos = {
            "cotizacion": "la referencia de la cotización (por ejemplo S00573)",
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
        icono = "✅" if res.get("ok") else ("🔒" if res.get("estado") == "sin_permiso" else "⚠️")
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
