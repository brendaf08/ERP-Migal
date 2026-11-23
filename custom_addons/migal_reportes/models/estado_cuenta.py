"""Acciones de impresión adicionales, sin alterar el reporte original de MIGAL."""
from odoo import models
from odoo.exceptions import UserError


class EstadoCuentaWizardReportes(models.TransientModel):
    _inherit = "migal.agente.estado.cuenta.wizard"

    def _migal_imprimir(self, xmlid):
        self.ensure_one()
        if not self.generado or not self.datos_json:
            raise UserError("Primero genere el estado de cuenta para imprimirlo.")
        # El acceso al asistente y la generación siguen protegidos por migal_agente.
        return self.env.ref(xmlid).report_action(self)

    def action_migal_vista_previa(self):
        self.ensure_one()
        if not self.generado or not self.datos_json:
            raise UserError("Primero genere el estado de cuenta para imprimirlo.")
        return self.env["migal.reportes.vista.previa"].abrir(
            self, "action_estado_cuenta_a4", "action_estado_cuenta_58",
            titulo="Estado de cuenta · %s" % self.partner_id.display_name)

    def action_imprimir_migal_a4(self):
        return self._migal_imprimir("migal_reportes.action_estado_cuenta_a4")

    def action_imprimir_migal_58(self):
        return self._migal_imprimir("migal_reportes.action_estado_cuenta_58")
