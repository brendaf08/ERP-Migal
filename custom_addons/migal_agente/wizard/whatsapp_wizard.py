from odoo import api, fields, models
from odoo.exceptions import UserError


class MigalAgenteWhatsappWizard(models.TransientModel):
    _name = "migal.agente.whatsapp.wizard"
    _description = "Agente MIGAL - Abrir cotización en WhatsApp"

    order_id = fields.Many2one("sale.order", required=True, readonly=True)
    habilitado = fields.Boolean(readonly=True)
    telefono = fields.Char(readonly=True)
    mensaje = fields.Text(string="Mensaje (editable)")
    enlace = fields.Char(string="Enlace", compute="_compute_enlace")
    resultado_html = fields.Html(readonly=True, sanitize=False)

    @api.depends("telefono", "mensaje")
    def _compute_enlace(self):
        tool = self.env["migal.agente.tool.whatsapp"]
        for wiz in self:
            wiz.enlace = tool.enlace_wa(wiz.telefono, wiz.mensaje) if wiz.habilitado and wiz.telefono else False

    @api.model
    def abrir(self, order):
        agente = self.env["migal.agente"]
        res = agente.ejecutar_desde_boton("preparar_whatsapp_cotizacion", {"cotizacion": order.name},
                                          descripcion="[botón] Abrir en WhatsApp %s" % order.name)
        datos = res.get("datos") or {}
        wiz = self.create({
            "order_id": order.id,
            "habilitado": res.get("ok", False),
            "telefono": datos.get("telefono"),
            "mensaje": datos.get("mensaje"),
            "resultado_html": agente.render_resultado(res),
        })
        return {
            "type": "ir.actions.act_window", "name": "Abrir en WhatsApp", "res_model": self._name,
            "res_id": wiz.id, "view_mode": "form", "target": "new",
        }

    def action_descargar_pdf(self):
        self.ensure_one()
        return self.env.ref("sale.action_report_saleorder").report_action(self.order_id)

    def action_registrar_envio(self):
        self.ensure_one()
        if not self.habilitado:
            raise UserError("El envío no está habilitado: revise los controles indicados.")
        agente = self.env["migal.agente"]
        traza = []
        res = agente.ejecutar_herramienta("registrar_envio_whatsapp", {"cotizacion": self.order_id.name}, traza=traza)
        # El mensaje editado por VEN se guarda en el registro de envío.
        if res.get("ok") and res["datos"].get("envio_id"):
            self.env["migal.agente.whatsapp.envio"].browse(res["datos"]["envio_id"]).sudo().mensaje = self.mensaje
        agente._registrar("[botón] Registrar envío WhatsApp %s" % self.order_id.name, "boton", "reglas", traza,
                          agente.render_resultado(res), resultado="ok" if res.get("ok") else "bloqueado",
                          reglas=res.get("reglas"), res_model="sale.order", res_id=self.order_id.id)
        if not res.get("ok"):
            raise UserError(res.get("mensaje"))
        return {
            "type": "ir.actions.client", "tag": "display_notification",
            "params": {"title": "Agente MIGAL", "message": res.get("mensaje"), "type": "success",
                       "next": {"type": "ir.actions.act_window_close"}},
        }
