"""Elección pendiente del chat del Agente MIGAL.

Cuando una solicitud coincide con varias cotizaciones (o con varias versiones de
una misma cotización) el agente muestra una lista numerada y guarda aquí qué iba
a hacer. El siguiente mensaje del usuario («2», «la segunda», «S00637-01»,
«versión 1», «la más reciente»...) completa la acción. Cualquier otro mensaje
descarta la elección. Solo se accede con sudo desde el orquestador.
"""
import json
from datetime import timedelta

from odoo import api, fields, models

VIGENCIA_MINUTOS = 30


class MigalAgenteSeleccion(models.Model):
    _name = "migal.agente.seleccion"
    _description = "Agente MIGAL - elección pendiente en el chat"
    _order = "id desc"

    session_id = fields.Char(required=True, index=True)
    user_id = fields.Many2one("res.users", required=True, ondelete="cascade", index=True)
    herramienta = fields.Char(required=True)
    args_json = fields.Text(default="{}")
    etapa = fields.Selection([("cotizacion", "Cotización"), ("version", "Versión"), ("cliente", "Cliente")],
                             required=True)
    opciones_json = fields.Text(default="[]")
    expira = fields.Datetime(required=True)

    @property
    def args(self):
        return json.loads(self.args_json or "{}")

    @property
    def opciones(self):
        return json.loads(self.opciones_json or "[]")

    @api.model
    def _pendiente(self, session_id):
        return self.sudo().search([
            ("session_id", "=", session_id),
            ("user_id", "=", self.env.uid),
            ("expira", ">", fields.Datetime.now()),
        ], limit=1)

    @api.model
    def _guardar(self, session_id, herramienta, args, etapa, opciones):
        self._descartar(session_id)
        return self.sudo().create({
            "session_id": session_id,
            "user_id": self.env.uid,
            "herramienta": herramienta,
            "args_json": json.dumps(args, ensure_ascii=False),
            "etapa": etapa,
            "opciones_json": json.dumps(opciones, ensure_ascii=False),
            "expira": fields.Datetime.now() + timedelta(minutes=VIGENCIA_MINUTOS),
        })

    @api.model
    def _descartar(self, session_id):
        self.sudo().search([("session_id", "=", session_id), ("user_id", "=", self.env.uid)]).unlink()

    @api.model
    def _limpiar(self):
        self.sudo().search([("expira", "<", fields.Datetime.now() - timedelta(days=1))]).unlink()
