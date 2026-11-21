"""Control opcional del menú Imprimir: solo oculta enlaces, nunca elimina reportes."""

from odoo import api, models


class MigalAccionesVinculadas(models.Model):
    _inherit = "ir.actions.actions"

    @api.model
    def get_bindings(self, model_name):
        bindings = super().get_bindings(model_name)
        # Los informes fiscales de account.move se conservan: los PDFs MIGAL
        # todavía son vistas comerciales y no reemplazan los CPE de SUNAT.
        modelos = {"sale.order", "stock.picking", "account.payment"}
        if model_name not in modelos or not bindings.get("report"):
            return bindings
        activo = self.env["ir.config_parameter"].sudo().get_param(
            "migal_reportes.solo_migal", "True") in ("True", "true", "1")
        if not activo:
            return bindings
        reportes = bindings["report"]
        ids = [a["id"] for a in reportes if a.get("id")]
        referencias = self.env["ir.model.data"].sudo().search([
            ("module", "=", "migal_reportes"),
            ("model", "=", "ir.actions.report"),
            ("res_id", "in", ids),
        ])
        permitidos = set(referencias.mapped("res_id"))
        resultado = dict(bindings)
        resultado["report"] = [a for a in reportes if a.get("id") in permitidos]
        if not resultado["report"]:
            resultado.pop("report")
        return resultado
