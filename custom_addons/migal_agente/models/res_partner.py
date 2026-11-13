from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_migal_estado_cuenta(self):
        self.ensure_one()
        return self.env["migal.agente.estado.cuenta.wizard"].abrir(self.commercial_partner_id)
