from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    migal_whatsapp_envio_ids = fields.One2many("migal.agente.whatsapp.envio", "order_id",
                                               string="Envíos por WhatsApp")
    migal_whatsapp_envio_count = fields.Integer(compute="_compute_migal_whatsapp_envio_count")

    def _compute_migal_whatsapp_envio_count(self):
        for order in self:
            order.migal_whatsapp_envio_count = len(order.migal_whatsapp_envio_ids)

    def action_migal_whatsapp(self):
        self.ensure_one()
        return self.env["migal.agente.whatsapp.wizard"].abrir(self)

    def action_migal_cobertura(self):
        self.ensure_one()
        return self.env["migal.agente.cobertura.wizard"].abrir(self)

    def action_migal_ver_envios(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Envíos por WhatsApp",
            "res_model": "migal.agente.whatsapp.envio",
            "view_mode": "list,form",
            "domain": [("order_id", "=", self.id)],
        }
