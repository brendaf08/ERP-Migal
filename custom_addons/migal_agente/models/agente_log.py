import base64
import json

from odoo import api, fields, models


class MigalAgenteLog(models.Model):
    """Bitácora del agente: un registro por turno (contrato de audit_log.jsonl de la PC3)."""

    _name = "migal.agente.log"
    _description = "Bitácora del Agente MIGAL"
    _order = "timestamp desc, id desc"
    _rec_name = "session_id"

    timestamp = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
    session_id = fields.Char(required=True, readonly=True, index=True)
    user_id = fields.Many2one("res.users", string="Usuario", default=lambda s: s.env.user, readonly=True)
    roles = fields.Char(string="Roles del usuario", readonly=True)
    canal = fields.Selection(
        [("chat", "Chat (Conversaciones)"), ("widget", "Asistente flotante"), ("boton", "Botón / asistente"),
         ("prueba", "Prueba automatizada")],
        default="chat", readonly=True,
    )
    modo = fields.Selection([("reglas", "Reglas deterministas"), ("llm", "LLM + reglas")],
                            default="reglas", readonly=True)
    input_prompt = fields.Text(string="Entrada", readonly=True)
    tools_invoked = fields.Text(string="Herramientas invocadas (JSON)", readonly=True)
    tools_resumen = fields.Char(string="Herramientas", compute="_compute_tools_resumen")
    odoo_latency_ms = fields.Float(string="Latencia Odoo (ms)", digits=(16, 1), readonly=True)
    rule_triggered = fields.Char(string="Reglas activadas", readonly=True)
    escalation_flag = fields.Boolean(string="Escalado", readonly=True)
    escalated_to = fields.Char(string="Escalado a", readonly=True)
    resultado = fields.Selection(
        [("ok", "Atendido"), ("bloqueado", "Bloqueado / vetado"), ("error", "Error controlado"),
         ("ayuda", "Ayuda / falta información")],
        readonly=True,
    )
    output_response = fields.Text(string="Respuesta", readonly=True)
    res_model = fields.Char(readonly=True)
    res_id = fields.Integer(readonly=True)

    @api.depends("tools_invoked")
    def _compute_tools_resumen(self):
        for rec in self:
            try:
                tools = json.loads(rec.tools_invoked or "[]")
            except ValueError:
                tools = []
            rec.tools_resumen = ", ".join(t.get("tool", "") for t in tools)

    def to_audit_dict(self):
        self.ensure_one()
        return {
            "timestamp": fields.Datetime.to_string(self.timestamp),
            "session_id": self.session_id,
            "user": self.user_id.login,
            "roles": (self.roles or "").split(",") if self.roles else [],
            "canal": self.canal,
            "modo": self.modo,
            "input_prompt": self.input_prompt or "",
            "tools_invoked": json.loads(self.tools_invoked or "[]"),
            "odoo_latency_ms": round(self.odoo_latency_ms, 1),
            "rule_triggered": [r for r in (self.rule_triggered or "").split(",") if r],
            "escalation_flag": self.escalation_flag,
            "escalated_to": [r for r in (self.escalated_to or "").split(",") if r],
            "resultado": self.resultado,
            "output_response": self.output_response or "",
        }

    def action_exportar_jsonl(self):
        """Descarga los registros seleccionados como audit_log.jsonl."""
        records = self or self.search([])
        content = "\n".join(json.dumps(r.to_audit_dict(), ensure_ascii=False) for r in records.sorted("timestamp"))
        attachment = self.env["ir.attachment"].create({
            "name": "audit_log.jsonl",
            "datas": base64.b64encode((content + "\n").encode("utf-8")),
            "mimetype": "application/jsonl",
            "res_model": self._name,
        })
        return {"type": "ir.actions.act_url", "url": "/web/content/%s?download=true" % attachment.id, "target": "self"}
