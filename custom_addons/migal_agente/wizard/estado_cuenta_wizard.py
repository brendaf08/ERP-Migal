import json
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import UserError


class MigalAgenteEstadoCuentaWizard(models.TransientModel):
    _name = "migal.agente.estado.cuenta.wizard"
    _description = "Agente MIGAL - Estado de cuenta"

    partner_id = fields.Many2one("res.partner", string="Cliente", required=True)
    fecha_desde = fields.Date(required=True, default=lambda s: date.today().replace(day=1))
    fecha_hasta = fields.Date(required=True, default=fields.Date.context_today)
    resultado_html = fields.Html(readonly=True, sanitize=False)
    datos_json = fields.Text(readonly=True)
    generado = fields.Boolean(readonly=True)

    @api.model
    def abrir(self, partner):
        wiz = self.create({"partner_id": partner.id})
        wiz.action_generar()
        return wiz._accion()

    def _accion(self):
        return {
            "type": "ir.actions.act_window", "name": "Estado de cuenta", "res_model": self._name,
            "res_id": self.id, "view_mode": "form", "target": "new",
        }

    def _cliente_ref(self):
        p = self.partner_id.commercial_partner_id
        return p.vat or p.ref or p.name

    def action_generar(self):
        self.ensure_one()
        agente = self.env["migal.agente"]
        args = {
            "cliente": self._cliente_ref(),
            "fecha_desde": fields.Date.to_string(self.fecha_desde),
            "fecha_hasta": fields.Date.to_string(self.fecha_hasta),
        }
        res = agente.ejecutar_desde_boton("generar_estado_cuenta", args,
                                          descripcion="[botón] Estado de cuenta %s" % self.partner_id.display_name)
        self.write({
            "resultado_html": agente.render_resultado(res),
            "datos_json": json.dumps(res.get("datos") or {}, ensure_ascii=False, default=str) if res.get("ok") else False,
            "generado": bool(res.get("ok")),
        })
        return self._accion()

    def get_datos(self):
        self.ensure_one()
        return json.loads(self.datos_json or "{}")

    def action_imprimir(self):
        self.ensure_one()
        if not self.generado:
            raise UserError("Primero genere el estado de cuenta (requiere rol FCO o GER).")
        return self.env.ref("migal_agente.action_report_estado_cuenta").report_action(self)
