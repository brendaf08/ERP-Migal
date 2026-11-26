import json
import logging
import uuid
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

HORAS_VIGENCIA = 24
# Sentinel no serializable por RPC/JSON: evita bypass público basado solo en contexto.
_INTERNAL_CREATE_SENTINEL = object()


class MigalAgenteEstadoCuentaPublicacion(models.Model):
    """Copia inmutable de un estado de cuenta revisado por FCO/GER para compartir con el cliente.

    - Se congela el contenido (lo que el cliente ve es exactamente lo revisado).
    - Se accede con un token aleatorio (UUID4) y caduca a las 24 horas.
    - Solo lectura interna: datos financieros congelados no editables por RPC.
    - Aislamiento por compañía (P3-01) y protección de escritura RPC (P3-P1).
    - P3-REV-01: creación interna validada contra usuario original antes de sudo.
    - P3-REV-02: write restringido incluso para superusuario; sin bypass genérico.
    """

    _name = "migal.agente.estado.cuenta.publicacion"
    _description = "Estado de cuenta compartido con el cliente"
    _order = "create_date desc"
    _rec_name = "partner_id"
    _check_company_auto = True

    token = fields.Char(required=True, readonly=True, index=True, copy=False, default=lambda s: str(uuid.uuid4()),
                        groups="base.group_system")
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True, readonly=True, ondelete="cascade",
                                 check_company=True)
    company_id = fields.Many2one(
        "res.company", string="Compañía", readonly=True, index=True,
        help="Compañía contable desde la que se generó el estado de cuenta. "
             "Es la fuente de aislamiento multi-compañía de la publicación.")
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
    ultima_vista = fields.Datetime(readonly=True)
    vigente = fields.Boolean(compute="_compute_vigente")

    @api.depends("expira", "activo")
    def _compute_vigente(self):
        ahora = fields.Datetime.now()
        for rec in self:
            rec.vigente = rec.activo and rec.expira > ahora

    @api.constrains("company_id", "partner_id")
    def _check_company_consistency(self):
        for rec in self:
            if not rec.company_id:
                # Registros históricos sin compañía: visibles solo para administración del sistema.
                continue
            if rec.partner_id.company_id and rec.partner_id.company_id != rec.company_id:
                raise UserError(
                    "La compañía de la publicación no coincide con la compañía del cliente."
                )

    def _check_company_access(self, company_id, user=None):
        user = user or self.env.user
        company = self.env["res.company"].browse(int(company_id)).exists()
        if not company:
            raise AccessError("No tiene acceso a la compañía de la publicación.")
        if user._is_superuser() or user._is_admin():
            # admin/superuser: acceso permitido si la compañía existe; la regla de registro y
            # el flujo de negocio siguen aplicando donde corresponda.
            return company
        allowed = self.env["res.users"].sudo().browse(user.id).company_ids.ids
        if company.id not in allowed:
            raise AccessError("No tiene acceso a la compañía de la publicación.")
        return company

    def _assert_create_vals(self, vals, user):
        company_id = vals.get("company_id") or (user.company_id.id if not user._is_superuser() else self.env.company.id)
        company = self._check_company_access(company_id, user=user)
        vals["company_id"] = company.id
        if "currency_id" not in vals:
            vals["currency_id"] = company.currency_id.id
        partner_id = vals.get("partner_id")
        if partner_id:
            partner = self.env["res.partner"].browse(partner_id).exists()
            if partner.company_id and partner.company_id.id != company.id:
                raise AccessError("El cliente no pertenece a la compañía de la publicación.")
        return vals

    @api.model
    def _create_validated(self, vals, user=None):
        """Creación interna controlada: valida compañía contra usuario original antes de sudo.

        No expone bypass por contexto RPC: el sentinel es un objeto Python no serializable.
        """
        user = self.env["res.users"].browse(user.id if isinstance(user, models.BaseModel) else int(user or self.env.uid)).exists()
        if not user:
            raise AccessError("Usuario no autorizado para crear la publicación.")
        vals = dict(vals)
        self._assert_create_vals(vals, user=user)
        rec = self.sudo().with_context(_migal_ec_internal_create=_INTERNAL_CREATE_SENTINEL).create(vals)
        return rec

    @api.model_create_multi
    def create(self, vals_list):
        internal = self.env.context.get("_migal_ec_internal_create") is _INTERNAL_CREATE_SENTINEL
        if internal:
            # Camino interno: ya validado por _create_validated. Aun así normalizamos campos
            # sensibles de consistencia para evitar uso incorrecto interno.
            clean = []
            for vals in vals_list:
                vals = dict(vals)
                company_id = vals.get("company_id")
                if not company_id:
                    raise AccessError("La publicación requiere compañía explícita.")
                company = self.env["res.company"].browse(int(company_id)).exists()
                if not company:
                    raise AccessError("Compañía inválida para la publicación.")
                vals["company_id"] = company.id
                if "currency_id" not in vals:
                    vals["currency_id"] = company.currency_id.id
                partner_id = vals.get("partner_id")
                if partner_id:
                    partner = self.env["res.partner"].browse(partner_id).exists()
                    if partner.company_id and partner.company_id.id != company.id:
                        raise AccessError("El cliente no pertenece a la compañía de la publicación.")
                clean.append(vals)
            records = super(MigalAgenteEstadoCuentaPublicacion, self.sudo()).create(clean)
            records._check_company_consistency()
            return records

        # Camino ORM/RPC/externo: siempre validar contra el usuario real del entorno.
        # No se permite bypass genérico por sudo/superuser: debe usarse _create_validated
        # con el usuario original validado antes de elevar privilegios.
        if self.env.su or self.env.is_superuser():
            raise AccessError(
                "La creación de publicaciones con privilegios elevados requiere la ruta interna "
                "validada con usuario original (_create_validated)."
            )
        user = self.env.user
        clean = []
        for vals in vals_list:
            vals = dict(vals)
            self._assert_create_vals(vals, user=user)
            clean.append(vals)
        records = super().create(clean)
        records._check_company_consistency()
        return records

    def write(self, vals):
        if not vals:
            return True
        keys = set(vals.keys())

        # P3-REV-02: campos financieros/de identidad nunca modificables por write genérico,
        # ni siquiera para superusuario. No hay bypass por contexto RPC.
        campos_protegidos = {
            "datos_json", "partner_id", "total_pendiente", "expira",
            "token", "user_id", "company_id",
        }
        if keys & campos_protegidos:
            no_permitidos = sorted(keys & campos_protegidos)
            raise AccessError(
                "No tiene permisos para modificar campos protegidos de la publicación: %s."
                % ", ".join(no_permitidos)
            )

        # Única operación permitida por write: revocación explícita activo=False.
        if keys != {"activo"}:
            no_permitidos = sorted(keys - {"activo"})
            raise AccessError(
                "No tiene permisos para modificar campos de la publicación: %s."
                % ", ".join(no_permitidos)
            )
        if vals.get("activo") is not False:
            raise AccessError("Solo se permite revocar una publicación (activo=False).")

        for rec in self:
            if not rec.company_id:
                # Registros históricos sin compañía: solo administración del sistema puede remediar.
                if not (self.env.is_superuser() or self.env.user.has_group("base.group_system")):
                    raise AccessError("La publicación no tiene compañía asignada; solicite revisión a SIS.")
                continue
            if not self.env.is_superuser():
                rec._check_company_access(rec.company_id.id, user=self.env.user)

        return super().write(vals)

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
        for rec in self:
            if rec.company_id and not self.env.is_superuser():
                rec._check_company_access(rec.company_id.id, user=self.env.user)
        self.write({"activo": False})

    def _registrar_vista(self, ip=None):
        """Incrementa vistas con deduplicación para reducir escrituras."""
        self.ensure_one()
        cutoff = fields.Datetime.now() - timedelta(minutes=5)
        now = fields.Datetime.now()
        self.env.cr.execute(
            """
            UPDATE migal_agente_estado_cuenta_publicacion
               SET vistas = COALESCE(vistas, 0) + 1,
                   ultima_vista = %s
             WHERE id = %s
               AND (ultima_vista IS NULL OR ultima_vista < %s)
            """,
            (now, self.id, cutoff),
        )

    @api.autovacuum
    def _gc_caducadas(self):
        """Borra las copias caducadas hace más de 30 días para minimizar los datos conservados."""
        self.sudo().search([("expira", "<", fields.Datetime.now() - timedelta(days=30))]).unlink()
