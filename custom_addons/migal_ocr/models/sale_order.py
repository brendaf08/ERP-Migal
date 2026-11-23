from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_migal_escanear_lista(self):
        """Abre «Escanear lista» en una ventana sobre la cotización."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Escanear lista · %s") % self.name,
            "res_model": "migal.ocr.documento",
            "view_mode": "form",
            "views": [(self.env.ref("migal_ocr.view_migal_ocr_documento_dialogo").id, "form")],
            "target": "new",
            "context": {
                "default_order_id": self.id,
                "default_partner_id": self.partner_id.id,
                "migal_ocr_dialogo": True,
                "dialog_size": "extra-large",
            },
        }
