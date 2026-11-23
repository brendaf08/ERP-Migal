"""Diagnóstico de disponibilidad en PDF y su acceso desde el asistente del Agente MIGAL."""
from odoo import api, models


class SaleOrderDiagnostico(models.Model):
    _inherit = "sale.order"

    def migal_diagnostico_cobertura(self, fecha=None):
        """Resultado de la herramienta de cobertura del agente (misma lógica que el chat y el asistente)."""
        self.ensure_one()
        return self.env["migal.agente.tool.cobertura"].evaluar(self.name, fecha_requerida=fecha or None)

    def action_migal_diagnostico_cobertura(self, fecha=None):
        self.ensure_one()
        return self.env["migal.reportes.vista.previa"].abrir(
            self, "action_diagnostico_cobertura", titulo="Disponibilidad · %s" % self.name,
            opciones={"fecha": fecha} if fecha else None)


class MigalAgenteDiagnostico(models.AbstractModel):
    _inherit = "migal.agente"

    def _widget_cobertura(self, order, params):
        res = super()._widget_cobertura(order, params)
        if res.get("ok"):
            res["documento"] = {
                "accion": "diagnostico_cobertura",
                "label": "Ver diagnóstico de disponibilidad",
                "icon": "fa-file-pdf-o",
                "params": {"fecha": params.get("fecha")} if params.get("fecha") else {},
            }
        return res

    def _widget_abrir(self, accion, record, params=None):
        if accion == "diagnostico_cobertura" and record._name == "sale.order":
            return record.action_migal_diagnostico_cobertura((params or {}).get("fecha"))
        return super()._widget_abrir(accion, record, params=params)
