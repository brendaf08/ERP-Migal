"""Eventos que emite el agente de cadena de suministro."""
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()
        agente = self.env["migal.agente.suministro"]
        for picking in self.filtered(lambda p: p.picking_type_code == "incoming" and p.state == "done"):
            agente._emitir("EV-027", {
                "recepcion": picking.name,
                "orden_compra": picking.purchase_id.name or picking.origin or "",
                "proveedor": picking.partner_id.display_name or "",
                "lineas": [{"producto": m.product_id.display_name, "recibido": m.quantity} for m in picking.move_ids],
            })
        return res
