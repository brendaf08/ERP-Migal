"""Eventos que emite el agente de ventas."""
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super().action_confirm()
        agente = self.env["migal.agente.ventas"]
        for orden in self.filtered(lambda o: o.state == "sale"):
            agente._emitir("EV-018", {
                "orden": orden.name, "cliente": orden.partner_id.display_name, "monto": orden.amount_total,
                "lineas": [{"producto": l.product_id.display_name, "cantidad": l.product_uom_qty}
                           for l in orden.order_line if l.product_id],
            })
        return res
