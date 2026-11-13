"""API del asistente flotante (avatar en la esquina inferior derecha).

El asistente no tiene lógica propia: llama a las mismas herramientas del agente
(contrato, permisos, guardarraíles, bitácora) y convierte sus resultados en una
secuencia de pasos que la interfaz muestra uno a uno.
"""
import json

from odoo import api, fields, models
from odoo.tools import format_amount

from ..agent import contracts, guardrails

ICONO_COBERTURA = {"stock": "ok", "reposicion": "aviso", "regla": "info", "faltante": "error",
                   "no_inventariable": "info"}
TEXTO_COBERTURA = {"stock": "con stock", "reposicion": "con reposición prevista", "regla": "regla habitual",
                   "faltante": "faltante", "no_inventariable": "no inventariable"}


def _paso(titulo, detalle="", tipo="ok"):
    return {"titulo": titulo, "detalle": detalle or "", "tipo": tipo}


class MigalAgenteWidget(models.AbstractModel):
    _inherit = "migal.agente"

    # ------------------------------------------------------------------
    # Contexto: qué puede hacer el asistente en la pantalla actual
    # ------------------------------------------------------------------
    @api.model
    def widget_contexto(self, res_model=False, res_id=False):
        roles = guardrails.user_roles(self.env.user, contracts.ROLE_GROUPS)
        ctx = {
            "usuario": self.env.user.name.split(" ")[0],
            "roles": roles,
            "modo": "LLM + reglas" if self._llm_config()["activo"] else "reglas",
            "titulo": "¿En qué te ayudo?",
            "subtitulo": "Abre una cotización o un cliente y te muestro lo que puedo hacer ahí.",
            "acciones": [],
            "registro": False,
        }
        record = self.env[res_model].browse(res_id).exists() if res_model in ("sale.order", "res.partner") and res_id else None
        if res_model == "sale.order" and record:
            ctx["registro"] = record.name
            lineas = record.order_line.filtered(lambda l: not l.display_type and l.product_id)
            if record.state in ("draft", "sent") and not lineas:
                ctx["titulo"] = "Cotización %s" % record.name
                ctx["subtitulo"] = "Agrega productos y guarda la cotización para que pueda revisarla."
            elif record.state in ("draft", "sent"):
                ctx["titulo"] = "Cotización %s" % record.name
                ctx["subtitulo"] = "%s · %s" % (record.partner_id.display_name,
                                                format_amount(self.env, record.amount_total, record.currency_id))
                ctx["pestanas"] = [
                    {"id": "enviar", "label": "Enviar cotización", "icon": "fa-paper-plane", "acciones": [
                        {"id": "procesar_cotizacion", "label": "Cliente a distancia: WhatsApp", "icon": "fa-whatsapp",
                         "descripcion": "Reviso controles, genero el PDF y el mensaje", "principal": True},
                        {"id": "qr", "label": "Cliente presencial: mostrar QR", "icon": "fa-qrcode",
                         "descripcion": "Escanea y ve la cotización en su celular", "principal": True},
                    ]},
                    {"id": "disponibilidad", "label": "Disponibilidad", "icon": "fa-cubes", "acciones": [
                        {"id": "cobertura", "label": "Cobertura preliminar", "icon": "fa-cubes",
                         "descripcion": "¿Alcanza el stock? ¿Desde cuándo se atiende todo?", "fecha": True,
                         "principal": True},
                    ]},
                ]
                ctx["acciones"] = [a for p in ctx["pestanas"] for a in p["acciones"]]
            else:
                ctx["solo_info"] = True
                ctx["titulo"] = "Pedido %s" % record.name
                ctx["subtitulo"] = "Ya no es una cotización abierta: su seguimiento va por la Solicitud de Orden de Venta."
        elif res_model == "res.partner" and record:
            partner = record.commercial_partner_id
            ctx["registro"] = partner.display_name
            ctx["titulo"] = partner.display_name
            ctx["subtitulo"] = partner.vat and "RUC/DNI %s" % partner.vat or "Cliente"
            permitido = any(r in ("FCO", "GER") for r in roles)
            ctx["acciones"] = [{
                "id": "estado_cuenta", "label": "Estado de cuenta", "icon": "fa-file-text-o",
                "descripcion": "Ventas y POS: saldo, antigüedad y PDF" if permitido else "Solo FCO o GER",
                "principal": True, "bloqueada": not permitido, "periodo": True,
            }, {
                "id": "estado_cuenta_compartir", "label": "Compartir con el cliente", "icon": "fa-share-alt",
                "descripcion": "QR o WhatsApp · copia de solo lectura 24 h" if permitido else "Solo FCO o GER",
                "bloqueada": not permitido, "periodo": True,
            }]
        return ctx

    # ------------------------------------------------------------------
    # Ejecución de acciones: devuelve pasos para animar
    # ------------------------------------------------------------------
    @api.model
    def widget_ejecutar(self, accion, res_model=False, res_id=False, params=None):
        params = params or {}
        metodo = {
            "procesar_cotizacion": self._widget_procesar_cotizacion,
            "cobertura": self._widget_cobertura,
            "whatsapp": self._widget_whatsapp,
            "registrar_envio": self._widget_registrar_envio,
            "qr": self._widget_qr,
            "estado_cuenta_compartir": self._widget_compartir_estado,
            "registrar_envio_estado": self._widget_registrar_envio_estado,
            "estado_cuenta": self._widget_estado_cuenta,
        }.get(accion)
        if not metodo:
            return {"ok": False, "pasos": [_paso("Acción no reconocida", accion, "error")], "final": "No reconozco esa acción."}
        record = self.env[res_model].browse(res_id).exists() if res_model and res_id else None
        if not record:
            return {"ok": False, "pasos": [_paso("No encuentro el registro", "Guarda el documento e inténtalo de nuevo.", "error")],
                    "final": "Necesito un documento guardado para trabajar."}
        return metodo(record, params)

    def _ejecutar(self, nombre, args, descripcion):
        traza = []
        res = self.ejecutar_herramienta(nombre, args, traza=traza)
        estado = "ok" if res.get("ok") else ("bloqueado" if res.get("estado") in ("bloqueado", "sin_permiso") else "error")
        self._registrar(descripcion, "widget", "reglas", traza, self.render_resultado(res), resultado=estado,
                        reglas=res.get("reglas"), escalar=res.get("escalar_a"),
                        res_model=res.get("res_model"), res_id=res.get("res_id"))
        return res

    @staticmethod
    def _pasos_controles(res):
        return [_paso(c["control"], c["detalle"], "ok" if c["ok"] else "error") for c in res.get("controles") or []]

    def _pasos_cobertura(self, res):
        d = res.get("datos") or {}
        fecha_txt = lambda iso: "%s/%s/%s" % (iso[8:10], iso[5:7], iso[:4]) if iso else ""
        pasos = [_paso("Revisando stock en %s para el %s" % (d.get("almacen") or "tienda", fecha_txt(d.get("fecha_requerida"))),
                       "Fecha %s · descuento lo ya comprometido en otras ventas y sumo las reposiciones previstas"
                       % d.get("origen_fecha", ""), "info")]
        for l in d.get("lineas", []):
            pasos.append(_paso(
                "%s · %g %s → %s" % (l["producto"], l["cantidad"], l["uom"], TEXTO_COBERTURA.get(l["estado"], l["estado"])),
                l["detalle"] + ((" Próximas llegadas: %s." % l["llegadas"]) if l.get("llegadas") and l["estado"] == "faltante" else ""),
                ICONO_COBERTURA.get(l["estado"], "info")))
        if d.get("fecha_atencion"):
            pasos.append(_paso("Fecha estimada para atender todo: %s" % fecha_txt(d["fecha_atencion"]),
                               "Estimación con stock, reposiciones previstas y regla habitual; no es una entrega garantizada.",
                               "ok" if d["fecha_atencion"] <= d.get("fecha_requerida", "") else "aviso"))
        return pasos

    # --- Cotización -------------------------------------------------------
    def _widget_procesar_cotizacion(self, order, params):
        pasos = [_paso("Leyendo la cotización %s" % order.name,
                       "%s · %s producto(s) · %s" % (order.partner_id.display_name,
                                                     len(order.order_line.filtered(lambda l: not l.display_type)),
                                                     format_amount(self.env, order.amount_total, order.currency_id)), "info")]
        wa = self._ejecutar("preparar_whatsapp_cotizacion", {"cotizacion": order.name},
                            "[asistente] Procesar cotización %s (controles y WhatsApp)" % order.name)
        pasos += self._pasos_controles(wa)
        cob = {}
        if params.get("incluir_disponibilidad"):
            cob = self._ejecutar("evaluar_cobertura_preliminar", {"cotizacion": order.name},
                                 "[asistente] Enviar cotización %s (disponibilidad)" % order.name)
            if cob.get("ok"):
                pasos.append(_paso("Agregando la disponibilidad al mensaje", cob["mensaje"],
                                   "ok" if cob["estado"] in ("cubierta", "cubierta_condicionada") else "aviso"))
        resultado = {"ok": bool(wa.get("ok")), "pasos": pasos, "pdf_url": "/report/pdf/sale.report_saleorder/%s" % order.id,
                     "pdf_nombre": "Cotización %s.pdf" % order.name}
        pasos.append(_paso("Generando el PDF de la cotización", "Listo para descargar y adjuntar en WhatsApp.", "ok"))
        if wa.get("ok"):
            pasos.append(_paso("Redactando el mensaje para %s" % order.partner_id.display_name,
                               "Puedes editarlo antes de abrir WhatsApp.", "ok"))
            resultado.update(self._datos_whatsapp(order, wa))
            frase = self._frase_disponibilidad(cob)
            if frase:
                m = resultado["whatsapp"]["mensaje"]
                corte = m.rfind(" Quedo atento")
                resultado["whatsapp"]["mensaje"] = (m[:corte] + " " + frase + m[corte:]) if corte > 0 else m + " " + frase
            resultado["final"] = "Todo listo: abre WhatsApp, adjunta el PDF y envía. Luego confirma el envío aquí."
        else:
            resultado["final"] = "No puedo preparar el envío todavía: %s" % wa.get("mensaje")
        resultado["avisos"] = (wa.get("avisos") or []) + (cob.get("avisos") or [])
        return resultado

    @staticmethod
    def _frase_disponibilidad(cob):
        """Frase breve y no vinculante sobre disponibilidad para añadir al mensaje de la cotización."""
        if not cob.get("ok"):
            return ""
        d = cob["datos"]
        fd = lambda iso: "%s/%s/%s" % (iso[8:10], iso[5:7], iso[:4])
        if cob["estado"] in ("cubierta", "cubierta_condicionada"):
            return "Según nuestro stock y reposiciones previstas, podríamos atender su pedido completo para el %s." % fd(
                d["fecha_requerida"])
        if d.get("fecha_atencion"):
            return "Según nuestras reposiciones previstas, podríamos atender su pedido completo desde el %s (fecha estimada)." % fd(
                d["fecha_atencion"])
        return "Algunos productos requieren confirmar su abastecimiento; le daremos la fecha al aceptar la cotización."

    def _widget_cobertura(self, order, params):
        args = {"cotizacion": order.name}
        if params.get("fecha"):
            args["fecha_requerida"] = params["fecha"]
        cob = self._ejecutar("evaluar_cobertura_preliminar", args, "[asistente] Cobertura %s" % order.name)
        pasos = self._pasos_controles(cob)
        res = {"ok": bool(cob.get("ok")), "pasos": pasos, "final": cob.get("mensaje"), "avisos": cob.get("avisos") or []}
        if cob.get("ok"):
            pasos += self._pasos_cobertura(cob)
            mensaje = cob["datos"].get("mensaje_cliente")
            if mensaje:
                from .tool_whatsapp import E164_RE, normalizar_telefono
                tel = normalizar_telefono(order.partner_id.phone)
                res["sugerencia"] = {"mensaje": mensaje, "telefono": tel if E164_RE.match(tel) else ""}
        return res

    def _widget_whatsapp(self, order, params):
        wa = self._ejecutar("preparar_whatsapp_cotizacion", {"cotizacion": order.name}, "[asistente] WhatsApp %s" % order.name)
        pasos = self._pasos_controles(wa)
        res = {"ok": bool(wa.get("ok")), "pasos": pasos, "final": wa.get("mensaje"), "avisos": wa.get("avisos") or [],
               "pdf_url": "/report/pdf/sale.report_saleorder/%s" % order.id, "pdf_nombre": "Cotización %s.pdf" % order.name}
        if wa.get("ok"):
            pasos.append(_paso("Redactando el mensaje", "Puedes editarlo antes de abrir WhatsApp.", "ok"))
            res.update(self._datos_whatsapp(order, wa))
        return res

    def _widget_qr(self, order, params):
        pasos = [_paso("Leyendo la cotización %s" % order.name,
                       "%s · %s" % (order.partner_id.display_name,
                                    format_amount(self.env, order.amount_total, order.currency_id)), "info")]
        res = self._ejecutar("generar_qr_cotizacion", {"cotizacion": order.name}, "[asistente] QR presencial %s" % order.name)
        pasos += self._pasos_controles(res)
        resultado = {"ok": bool(res.get("ok")), "pasos": pasos, "final": res.get("mensaje"),
                     "avisos": res.get("avisos") or []}
        if res.get("ok"):
            d = res["datos"]
            pasos.append(_paso("Generando el código QR", "Apunta a la versión digital de solo lectura.", "ok"))
            resultado["qr"] = {"imagen": "data:image/png;base64,%s" % d["qr_png_base64"], "url": d["url"],
                               "cotizacion": order.name, "cliente": d["cliente"], "accesible": d["accesible"],
                               "total": format_amount(self.env, order.amount_total, order.currency_id)}
            resultado["pdf_url"] = "/report/pdf/sale.report_saleorder/%s" % order.id
            resultado["pdf_nombre"] = "Cotización %s.pdf" % order.name
        return resultado

    @staticmethod
    def _datos_whatsapp(order, wa):
        d = wa.get("datos") or {}
        return {"whatsapp": {"telefono": d.get("telefono"), "mensaje": d.get("mensaje"), "cotizacion": order.name}}

    def _widget_registrar_envio(self, order, params):
        res = self._ejecutar("registrar_envio_whatsapp", {"cotizacion": order.name},
                             "[asistente] Registrar envío WhatsApp %s" % order.name)
        if res.get("ok") and params.get("mensaje") and res["datos"].get("envio_id"):
            self.env["migal.agente.whatsapp.envio"].browse(res["datos"]["envio_id"]).sudo().mensaje = params["mensaje"]
        paso = _paso("Registrando el envío en Odoo", res.get("mensaje"), "ok" if res.get("ok") else "error")
        return {"ok": bool(res.get("ok")), "pasos": [paso], "final": res.get("mensaje"), "registrado": bool(res.get("ok"))}

    # --- Cliente ----------------------------------------------------------
    def _widget_estado_cuenta(self, partner, params):
        partner = partner.commercial_partner_id
        hoy = fields.Date.context_today(self)
        args = {
            "cliente": partner.vat or partner.ref or partner.name,
            "fecha_desde": params.get("fecha_desde") or fields.Date.to_string(hoy.replace(day=1)),
            "fecha_hasta": params.get("fecha_hasta") or fields.Date.to_string(hoy),
        }
        res = self._ejecutar("generar_estado_cuenta", args, "[asistente] Estado de cuenta %s" % partner.display_name)
        if not res.get("ok"):
            return {"ok": False, "pasos": [_paso("Generando el estado de cuenta", res.get("mensaje"), "error")],
                    "final": res.get("mensaje")}
        d = res["datos"]
        s = d["simbolo"]
        money = lambda v: "%s %s" % (s, "{:,.2f}".format(v or 0.0))
        pasos = [
            _paso("Buscando a %s en la contabilidad" % d["cliente"], "Período %s al %s" % (d["fecha_desde"], d["fecha_hasta"]), "info"),
            _paso("Saldo anterior al período: %s" % money(d["saldo_anterior"]), "Apuntes publicados antes del %s" % d["fecha_desde"], "ok"),
            _paso("%s movimiento(s) en el período" % len(d["movimientos"]),
                  "Saldo al cierre del período: %s" % money(d["saldo_periodo"]), "ok"),
        ]
        for doc in d["documentos_pendientes"]:
            pasos.append(_paso("%s %s · pendiente %s" % (doc.get("tipo_cliente", ""), doc["documento"], money(doc["pendiente"])),
                               "%s · %s" % (doc.get("plazo", ""), doc.get("estado_plazo", "")),
                               "error" if doc.get("excedido") else ("info" if doc.get("con_plazo") else "aviso")))
        if d["pagos_sin_aplicar"]:
            pasos.append(_paso("Abono a cuenta de %s aún no aplicado" % money(d["total_sin_aplicar"]),
                               "Ya está descontado del total. FCO debe aplicarlo a un documento.", "aviso"))
        for info in d["informativo"]:
            pasos.append(_paso("Aparte (no suma): %s %s" % (info["origen"], info["documento"]), info["nota"], "info"))
        wiz = self.env["migal.agente.estado.cuenta.wizard"].create({
            "partner_id": partner.id,
            "fecha_desde": d["fecha_desde"], "fecha_hasta": d["fecha_hasta"],
            "datos_json": json.dumps(d, ensure_ascii=False, default=str), "generado": True,
        })
        pasos.append(_paso("Generando el PDF para el cliente", "Listo para descargar y compartir.", "ok"))
        return {
            "ok": True, "pasos": pasos,
            "final": "Total pendiente: %s%s." % (money(d["total_pendiente"]),
                                                 (" · plazo excedido %s" % money(d["total_vencido"])) if d["total_vencido"] else ""),
            "pdf_url": "/report/pdf/migal_agente.report_estado_cuenta/%s" % wiz.id,
            "pdf_nombre": "Estado de cuenta - %s.pdf" % d["cliente"],
            "avisos": res.get("avisos") or [],
            "puede_compartir": True,
            "periodo": {"fecha_desde": d["fecha_desde"], "fecha_hasta": d["fecha_hasta"]},
        }

    def _widget_compartir_estado(self, partner, params):
        partner = partner.commercial_partner_id
        hoy = fields.Date.context_today(self)
        args = {
            "cliente": partner.vat or partner.ref or partner.name,
            "fecha_desde": params.get("fecha_desde") or fields.Date.to_string(hoy.replace(day=1)),
            "fecha_hasta": params.get("fecha_hasta") or fields.Date.to_string(hoy),
        }
        pasos = [_paso("Recalculando el estado de cuenta de %s" % partner.display_name,
                       "Período %s al %s, con los datos contables de este momento" % (args["fecha_desde"], args["fecha_hasta"]),
                       "info")]
        res = self._ejecutar("compartir_estado_cuenta", args, "[asistente] Compartir estado de cuenta %s" % partner.display_name)
        pasos += self._pasos_controles(res)
        if not res.get("ok"):
            return {"ok": False, "pasos": pasos, "final": res.get("mensaje")}
        d = res["datos"]
        pasos.append(_paso("Generando el código QR", "Apunta a la copia de solo lectura (vence %s)." % d["expira"], "ok"))
        resultado = {
            "ok": True, "pasos": pasos, "final": res["mensaje"], "avisos": res.get("avisos") or [],
            "qr": {"imagen": "data:image/png;base64,%s" % d["qr_png_base64"], "url": d["url"],
                   "cotizacion": "Estado de cuenta", "titulo": "Estado de cuenta", "cliente": d["cliente"],
                   "accesible": d["accesible"], "total": "Pendiente %s %s" % (d["simbolo"], "{:,.2f}".format(d["total_pendiente"]))},
            "pdf_url": d["pdf_url"], "pdf_nombre": "Estado de cuenta - %s.pdf" % d["cliente"],
        }
        if d["telefono"]:
            pasos.append(_paso("Redactando el mensaje de WhatsApp", "Resumen del saldo; puedes editarlo.", "ok"))
            resultado["whatsapp"] = {"telefono": d["telefono"], "mensaje": d["mensaje"], "cotizacion": d["cliente"],
                                     "accion_registro": "registrar_envio_estado"}
        return resultado

    def _widget_registrar_envio_estado(self, partner, params):
        partner = partner.commercial_partner_id
        permitido, _roles = guardrails.check_permission(self.env.user, contracts.TOOLS["compartir_estado_cuenta"],
                                                         contracts.ROLE_GROUPS)
        if not permitido:
            return {"ok": False, "final": "Solo FCO o GER pueden compartir estados de cuenta.",
                    "pasos": [_paso("Registrando el envío", "Acción no permitida para su rol.", "error")]}
        nota = "Agente MIGAL: %s compartió por WhatsApp el estado de cuenta con %s." % (self.env.user.name, partner.display_name)
        partner.sudo().message_post(body=nota, author_id=self.env.user.partner_id.id,
                                    message_type="comment", subtype_xmlid="mail.mt_note")
        self._registrar("[asistente] Registrar envío de estado de cuenta %s" % partner.display_name, "widget", "reglas",
                        [{"tool": "registrar_envio_estado", "arguments": {"cliente": partner.display_name}, "source": "odoo_orm",
                          "ok": True}], nota, resultado="ok", res_model="res.partner", res_id=partner.id)
        return {"ok": True, "registrado": True, "final": "Envío registrado en el historial del cliente.",
                "pasos": [_paso("Registrando el envío en el historial del cliente", nota, "ok")]}

    # ------------------------------------------------------------------
    # Texto libre desde el panel
    # ------------------------------------------------------------------
    @api.model
    def widget_mensaje(self, texto, res_model=False, res_id=False):
        texto = (texto or "").strip()
        if res_model == "sale.order" and res_id:
            order = self.env["sale.order"].browse(res_id).exists()
            from ..agent import intent
            nombre, args = intent.parse(texto)
            if order and "cotizacion" in contracts.TOOLS.get(nombre, {}).get("input_schema", {}).get("properties", {}) \
                    and not args.get("cotizacion"):
                texto = "%s %s" % (texto, order.name)
        html, log = self.procesar_mensaje(texto, canal="widget", session_id="widget-%s" % self.env.uid)
        return {"html": str(html), "resultado": log.resultado}
