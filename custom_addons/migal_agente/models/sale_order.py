import logging

from markupsafe import Markup

from odoo import api, fields, models
from odoo.tools import format_date

_logger = logging.getLogger(__name__)

ESTADOS_ABIERTOS = ("draft", "sent")

# Contexto técnico para cerrar versiones sin que Tier Validation borre su historial
# de aprobaciones (ver sale_revision_tier_compat) ni bloquee la escritura.
CTX_CIERRE_VERSION = {"skip_validation_check": True, "preserve_tier_reviews_on_revision": True}


class SaleOrder(models.Model):
    _inherit = "sale.order"

    migal_whatsapp_envio_ids = fields.One2many("migal.agente.whatsapp.envio", "order_id",
                                               string="Envíos por WhatsApp")
    migal_whatsapp_envio_count = fields.Integer(compute="_compute_migal_whatsapp_envio_count")

    def _compute_migal_whatsapp_envio_count(self):
        for order in self:
            order.migal_whatsapp_envio_count = len(order.migal_whatsapp_envio_ids)

    def action_migal_whatsapp(self):
        self.ensure_one()
        return self.env["migal.agente.whatsapp.wizard"].abrir(self)

    def action_migal_cobertura(self):
        self.ensure_one()
        return self.env["migal.agente.cobertura.wizard"].abrir(self)

    def action_migal_ver_envios(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Envíos por WhatsApp",
            "res_model": "migal.agente.whatsapp.envio",
            "view_mode": "list,form",
            "domain": [("order_id", "=", self.id)],
        }

    # ------------------------------------------------------------------
    # Versiones de cotización: la anterior sigue vigente hasta su vencimiento
    # ------------------------------------------------------------------
    # OCA sale_order_revision cancela y archiva la versión anterior en cuanto se
    # crea una nueva. En MIGAL, durante la negociación el cliente puede volver a
    # una propuesta anterior, así que esa versión:
    #   * sigue abierta (borrador/enviada) y visible mientras su vigencia no venza;
    #   * se puede consultar, enviar por WhatsApp/QR y evaluar su cobertura;
    #   * NO se puede confirmar: sale_order_request exige confirmar la versión más
    #     reciente (para aceptar la propuesta anterior se crea una versión nueva a
    #     partir de ella);
    #   * se cierra (cancelada y archivada, como hacía OCA) cuando vence su plazo
    #     (cron diario) o cuando se confirma otra versión de la misma cotización.
    # Sin fecha de vigencia no hay plazo que esperar: se aplica el cierre inmediato de OCA.

    def _migal_familia(self):
        """Todas las versiones de esta cotización (incluidas archivadas)."""
        self.ensure_one()
        return self.sudo().with_context(active_test=False).search([
            ("unrevisioned_name", "=", self.unrevisioned_name or self.name),
            ("company_id", "=", self.company_id.id),
        ])

    def _migal_sigue_vigente(self):
        self.ensure_one()
        hoy = fields.Date.context_today(self)
        return bool(self.state in ESTADOS_ABIERTOS and self.validity_date and self.validity_date >= hoy)

    def _prepare_revision_data(self, new_revision):
        vals = super()._prepare_revision_data(new_revision)
        if self._migal_sigue_vigente():
            vals.pop("state", None)
            vals.pop("active", None)
        return vals

    def _get_new_rev_data(self, new_rev_number):
        # Al crear una versión desde una versión anterior, se numera después de la
        # más alta de la familia (evita choques con el índice único de OCA).
        new_rev_number = self.env.context.get("migal_revision_number") or new_rev_number
        vals = super()._get_new_rev_data(new_rev_number)
        # current_revision_id se copia (copy=True): partiendo de una versión anterior, la
        # nueva heredaría el enlace a la que era la más reciente.
        vals["current_revision_id"] = False
        return vals

    def copy_revision_with_context(self):
        self.ensure_one()
        familia = self._migal_familia() - self
        mayor = max(familia.mapped("revision_number") + [self.revision_number])
        rec = self.with_context(migal_revision_number=mayor + 1) if mayor > self.revision_number else self
        new_revision = super(SaleOrder, rec).copy_revision_with_context()
        # Todas las versiones de la familia apuntan a la más reciente (OCA solo
        # actualiza las que apuntaban a la versión de origen).
        rezagadas = (familia - new_revision).filtered(lambda o: o.current_revision_id != new_revision)
        if rezagadas:
            rezagadas.with_context(**CTX_CIERRE_VERSION).write({"current_revision_id": new_revision.id})
        return new_revision

    def _migal_cerrar_version(self, motivo):
        """Cancela y archiva versiones anteriores (mismo efecto que el cierre de OCA)."""
        for order in self:
            order.sudo().with_context(**CTX_CIERRE_VERSION).write({"state": "cancel", "active": False})
            order.sudo().message_post(body=motivo, message_type="comment", subtype_xmlid="mail.mt_note")

    def action_confirm(self):
        res = super().action_confirm()
        for order in self.filtered(lambda o: o.state == "sale"):
            otras = (order._migal_familia() - order).filtered(
                lambda o: o.active and o.state in ESTADOS_ABIERTOS)
            otras._migal_cerrar_version(
                Markup("Versión cerrada: se confirmó la versión <b>%s</b> de esta cotización.") % order.name)
        return res

    @api.model
    def _cron_migal_vencer_versiones(self):
        """Cierra las versiones anteriores cuya vigencia ya venció."""
        hoy = fields.Date.context_today(self)
        vencidas = self.sudo().search([
            ("current_revision_id", "!=", False),
            ("state", "in", ESTADOS_ABIERTOS),
            ("validity_date", "<", hoy),
        ])
        for order in vencidas:
            order._migal_cerrar_version(Markup(
                "Versión anterior cerrada: su vigencia venció el %s. La versión más reciente es <b>%s</b>.") % (
                format_date(self.env, order.validity_date), order.current_revision_id.name))
        if vencidas:
            _logger.info("Agente MIGAL: %s versiones anteriores vencidas cerradas.", len(vencidas))
        self.env["migal.agente.seleccion"].sudo()._limpiar()
        return len(vencidas)
