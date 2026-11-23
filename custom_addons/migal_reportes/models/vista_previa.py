"""Vista previa común de impresión: muestra el PDF real (A4 o ticket 58 mm) antes de descargarlo."""
import json
from urllib.parse import quote

from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MigalReportesVistaPrevia(models.TransientModel):
    _name = "migal.reportes.vista.previa"
    _description = "Vista previa de impresión MIGAL"

    titulo = fields.Char(readonly=True)
    res_model = fields.Char(required=True, readonly=True)
    res_id = fields.Integer(required=True, readonly=True)
    accion_a4 = fields.Char(required=True, readonly=True)
    accion_58 = fields.Char(readonly=True)
    tiene_ticket = fields.Boolean(compute="_compute_vista")
    opciones_json = fields.Char(readonly=True, help="Datos del reporte (por ejemplo la fecha evaluada).")
    formato = fields.Selection([("a4", "A4"), ("58", "Ticket 58 mm")], required=True, default="a4")
    vista = fields.Html(compute="_compute_vista", sanitize=False)

    def _registro(self):
        self.ensure_one()
        record = self.env[self.res_model].browse(self.res_id).exists()
        if not record:
            raise UserError(_("El documento ya no existe o no tiene acceso a él."))
        record.check_access("read")
        return record

    def _accion(self):
        self.ensure_one()
        xmlid = self.accion_58 if self.formato == "58" and self.accion_58 else self.accion_a4
        return self.env.ref("migal_reportes.%s" % xmlid)

    @api.depends("formato", "res_model", "res_id", "accion_a4", "accion_58", "opciones_json")
    def _compute_vista(self):
        for wiz in self:
            wiz.tiene_ticket = bool(wiz.accion_58)
            if not (wiz.res_model and wiz.res_id and wiz.accion_a4):
                wiz.vista = False
                continue
            reporte = wiz._accion()
            consulta = ("?options=%s" % quote(wiz.opciones_json)) if wiz.opciones_json else ""
            src = "/report/pdf/%s/%s%s#toolbar=1&navpanes=0&view=FitH" % (reporte.report_name, wiz.res_id, consulta)
            ancho = "100%" if wiz.formato == "a4" else "420px"
            wiz.vista = Markup(
                "<div style='display:flex;justify-content:center;background:#525659;border-radius:6px;"
                "padding:8px'><iframe src='%s' title='Vista previa' style='width:%s;max-width:100%%;"
                "height:70vh;border:0;background:#fff'></iframe></div>") % (src, ancho)

    def action_descargar(self):
        self.ensure_one()
        datos = json.loads(self.opciones_json) if self.opciones_json else None
        accion = self._accion().report_action(self._registro(), data=datos)
        accion["close_on_report_download"] = True
        return accion

    @api.model
    def abrir(self, record, accion_a4, accion_58=None, titulo=None, formato="a4", opciones=None):
        record.ensure_one()
        record.check_access("read")
        wiz = self.create({
            "titulo": titulo or record.display_name,
            "res_model": record._name,
            "res_id": record.id,
            "accion_a4": accion_a4,
            "accion_58": accion_58 or False,
            "formato": formato if accion_58 else "a4",
            "opciones_json": json.dumps(opciones) if opciones else False,
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Imprimir · %s") % wiz.titulo,
            "res_model": self._name,
            "res_id": wiz.id,
            "view_mode": "form",
            "views": [(self.env.ref("migal_reportes.view_migal_vista_previa").id, "form")],
            "target": "new",
            "context": {"dialog_size": "extra-large"},
        }
