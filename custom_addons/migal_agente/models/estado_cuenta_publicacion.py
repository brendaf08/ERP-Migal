import json
import uuid
from datetime import timedelta

from odoo import api, fields, models

HORAS_VIGENCIA = 24


class MigalAgenteEstadoCuentaPublicacion(models.Model):
    """Copia inmutable de un estado de cuenta revisado por FCO/GER para compartir con el cliente.

    - Se congela el contenido (lo que el cliente ve es exactamente lo revisado).
    - Se accede con un token aleatorio (UUID4) y caduca a las 24 horas.
    - Solo lectura: la ruta pública entrega el PDF y nada más.
    """

    _name = "migal.agente.estado.cuenta.publicacion"
    _description = "Estado de cuenta compartido con el cliente"
    _order = "create_date desc"
    _rec_name = "partner_id"

    token = fields.Char(required=True, readonly=True, index=True, copy=False, default=lambda s: str(uuid.uuid4()),
                        groups="base.group_system")
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True, readonly=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", string="Compartido por", default=lambda s: s.env.user, readonly=True)
    fecha_desde = fields.Date(readonly=True)
    fecha_hasta = fields.Date(readonly=True)
    total_pendiente = fields.Monetary(readonly=True, currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda s: s.env.company.currency_id, readonly=True)
    datos_json = fields.Text(readonly=True)
    expira = fields.Datetime(required=True, readonly=True,
                             default=lambda s: fields.Datetime.now() + timedelta(hours=HORAS_VIGENCIA))
    activo = fields.Boolean(default=True, help="Desmarcar para revocar el enlace antes de que caduque.")
    vistas = fields.Integer(readonly=True)
    vigente = fields.Boolean(compute="_compute_vigente")

    @api.depends("expira", "activo")
    def _compute_vigente(self):
        ahora = fields.Datetime.now()
        for rec in self:
            rec.vigente = rec.activo and rec.expira > ahora

    def get_datos(self):
        self.ensure_one()
        return json.loads(self.datos_json or "{}")

    @api.model
    def _buscar_vigente(self, token):
        if not token or len(token) != 36:
            return self.browse()
        rec = self.sudo().search([("token", "=", token), ("activo", "=", True),
                                  ("expira", ">", fields.Datetime.now())], limit=1)
        return rec

    def action_revocar(self):
        self.write({"activo": False})

    @api.autovacuum
    def _gc_caducadas(self):
        """Borra las copias caducadas hace más de 30 días (minimiza datos conservados)."""
        self.sudo().search([("expira", "<", fields.Datetime.now() - timedelta(days=30))]).unlink()
