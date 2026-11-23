"""Control de acceso en la generación directa de estados de cuenta.

La autorización debe comprobarse también al solicitar /report/pdf/... de forma
manual; no basta con ocultar botones en la interfaz.
"""
from odoo import api, models
from odoo.exceptions import AccessError, UserError


def _estado_cuenta_values(env, docids):
    autorizado = (
        env.user.has_group("account.group_account_invoice")
        or env.user.has_group("sales_team.group_sale_manager")
    )
    if not autorizado:
        raise AccessError("Solo Facturación/Cobranzas o Gerencia pueden imprimir estados de cuenta.")
    docs = env["migal.agente.estado.cuenta.wizard"].browse(docids).exists()
    if not docs or len(docs) != len(set(docids)):
        raise UserError("No se encontró el estado de cuenta solicitado.")
    if any(not doc.generado or not doc.datos_json for doc in docs):
        raise UserError("Genere primero el estado de cuenta.")
    return {
        "doc_ids": docs.ids,
        "doc_model": "migal.agente.estado.cuenta.wizard",
        "docs": docs,
    }


class ReportEstadoCuentaMigalA4(models.AbstractModel):
    _name = "report.migal_reportes.report_estado_cuenta_a4"
    _description = "MIGAL - Reporte estado de cuenta A4"

    @api.model
    def _get_report_values(self, docids, data=None):
        return _estado_cuenta_values(self.env, docids)


class ReportEstadoCuentaMigalTicket(models.AbstractModel):
    _name = "report.migal_reportes.report_estado_cuenta_58"
    _description = "MIGAL - Reporte estado de cuenta ticket 58 mm"

    @api.model
    def _get_report_values(self, docids, data=None):
        return _estado_cuenta_values(self.env, docids)
