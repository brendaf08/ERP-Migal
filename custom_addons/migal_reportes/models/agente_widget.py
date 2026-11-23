"""Ofrece los dos nuevos PDFs en el avatar flotante del Agente MIGAL."""
from odoo import models


class AgenteWidgetReportes(models.AbstractModel):
    _inherit = "migal.agente"

    def _widget_estado_cuenta(self, partner, params):
        resultado = super()._widget_estado_cuenta(partner, params)
        if resultado.get("ok") and resultado.get("pdf_url"):
            # La herramienta original ya generó el wizard y verificó permisos.
            original = resultado["pdf_url"]
            prefijo = "/report/pdf/migal_agente.report_estado_cuenta/"
            if original.startswith(prefijo):
                identificador = original[len(prefijo):]
                if identificador.isdigit():
                    resultado["pdf_url"] = "/report/pdf/migal_reportes.report_estado_cuenta_a4/%s" % identificador
                    resultado["pdf_ticket_url"] = "/report/pdf/migal_reportes.report_estado_cuenta_58/%s" % identificador
                    resultado["pdf_nombre"] = "MIGAL Estado de cuenta A4.pdf"
                    resultado["pdf_ticket_nombre"] = "MIGAL Estado de cuenta ticket 58mm.pdf"
        return resultado
