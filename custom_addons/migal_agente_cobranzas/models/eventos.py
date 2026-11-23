"""Eventos que emite el agente de cuentas por cobrar."""
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        agente = self.env["migal.agente.cobranzas"]
        for factura in res.filtered(lambda m: m.move_type in ("out_invoice", "out_refund") and m.state == "posted"):
            agente._emitir("EV-038", {"factura": factura.name, "cliente": factura.partner_id.display_name,
                                      "monto": factura.amount_total,
                                      "vencimiento": str(factura.invoice_date_due or "")})
        return res


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        res = super().action_post()
        agente = self.env["migal.agente.cobranzas"]
        for pago in self.filtered(lambda p: p.payment_type == "inbound" and p.partner_type == "customer"):
            agente._emitir("EV-043", {"pago": pago.name, "cliente": pago.partner_id.display_name, "monto": pago.amount})
        return res
