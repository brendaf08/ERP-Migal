"""Logotipo de Ferre & Inversiones MIGAL como logo de la empresa (inicio de sesión, POS y documentos de Odoo)."""
import base64

from odoo import api, models
from odoo.tools.misc import file_open


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def _migal_aplicar_logo(self):
        with file_open("migal_reportes/static/img/logo_migal.png", "rb") as archivo:
            logo = base64.b64encode(archivo.read())
        self.search([]).write({"logo": logo})
