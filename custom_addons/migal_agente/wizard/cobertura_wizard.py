from odoo import api, fields, models


class MigalAgenteCoberturaWizard(models.TransientModel):
    _name = "migal.agente.cobertura.wizard"
    _description = "Agente MIGAL - Cobertura preliminar"

    order_id = fields.Many2one("sale.order", required=True, readonly=True)
    fecha_requerida = fields.Date(string="Fecha requerida por el cliente")
    resultado_html = fields.Html(readonly=True, sanitize=False)

    @api.model
    def abrir(self, order):
        wiz = self.create({"order_id": order.id})
        wiz.action_evaluar()
        return {
            "type": "ir.actions.act_window", "name": "Cobertura preliminar", "res_model": self._name,
            "res_id": wiz.id, "view_mode": "form", "target": "new",
        }

    def action_evaluar(self):
        self.ensure_one()
        args = {"cotizacion": self.order_id.name}
        if self.fecha_requerida:
            args["fecha_requerida"] = fields.Date.to_string(self.fecha_requerida)
        agente = self.env["migal.agente"]
        res = agente.ejecutar_desde_boton("evaluar_cobertura_preliminar", args,
                                          descripcion="[botón] Cobertura preliminar %s" % self.order_id.name)
        self.resultado_html = agente.render_resultado(res)
        return {
            "type": "ir.actions.act_window", "name": "Cobertura preliminar", "res_model": self._name,
            "res_id": self.id, "view_mode": "form", "target": "new",
        }
