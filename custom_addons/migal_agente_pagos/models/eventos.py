"""Eventos que emite el agente de cuentas por pagar."""
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        agente = self.env["migal.agente.pagos"]
        for factura in res.filtered(lambda m: m.move_type in ("in_invoice", "in_refund") and m.state == "posted"):
            ordenes = factura.invoice_line_ids.purchase_line_id.order_id
            agente._emitir("EV-040", {"factura": factura.name, "proveedor": factura.partner_id.display_name,
                                      "monto": factura.amount_total, "orden_compra": ", ".join(ordenes.mapped("name"))})
        return res


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        res = super().action_post()
        agente = self.env["migal.agente.pagos"]
        for pago in self.filtered(lambda p: p.payment_type == "outbound" and p.partner_type == "supplier"):
            agente._emitir("EV-055", {"pago": pago.name, "proveedor": pago.partner_id.display_name, "monto": pago.amount})
        return res
