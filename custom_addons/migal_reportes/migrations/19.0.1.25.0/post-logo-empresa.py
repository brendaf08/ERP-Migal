from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Bases que ya tenían migal_reportes: aplica el logotipo MIGAL como logo de la empresa."""
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["res.company"]._migal_aplicar_logo()
