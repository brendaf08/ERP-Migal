"""Accesos al flujo de solicitudes desde la cotización."""
from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    migal_solicitud_id = fields.Many2one(
        "sale.order.request", compute="_compute_migal_solicitud"
    )
    migal_solicitud_activa = fields.Boolean(compute="_compute_migal_solicitud")

    migal_solicitudes_revision_ids = fields.One2many(
        "sale.order.request", "sale_order_revision_id", string="Solicitudes de la revisión"
    )

    @api.depends(
        "current_revision_id",
        "company_id",
        "migal_solicitudes_revision_ids.state",
        "migal_solicitudes_revision_ids.company_id",
        "current_revision_id.migal_solicitudes_revision_ids.state",
        "current_revision_id.migal_solicitudes_revision_ids.company_id",
    )
    @api.depends_context("uid", "company")
    def _compute_migal_solicitud(self):
        Request = self.env["sale.order.request"]
        for order in self:
            revision = order.current_revision_id or order
            domain = [
                ("sale_order_revision_id", "=", revision.id),
                ("company_id", "=", order.company_id.id),
            ]
            order.migal_solicitud_id = False
            order.migal_solicitud_activa = False
            if not revision.id:
                continue
            active = Request.search(
                domain + [("state", "not in", ("cancel", "superseded", "confirmed"))],
                order="id desc",
                limit=1,
            )
            order.migal_solicitud_activa = bool(active)
            order.migal_solicitud_id = active or Request.search(domain, order="id desc", limit=1)

    def action_migal_crear_solicitud(self):
        self.ensure_one()
        self.check_access("read")
        if self.state not in ("draft", "sent"):
            raise UserError(_("Solo se puede crear una solicitud desde una cotización."))
        if not self.sale_request_subject:
            self.action_mark_sale_request_subject()
        return self.action_create_sale_order_request_from_quotation()

    def action_migal_abrir_solicitud(self):
        self.ensure_one()
        self.check_access("read")
        request = self.migal_solicitud_id
        if not request:
            return self.env["ir.actions.actions"]._for_xml_id(
                "sale_order_request.action_sale_order_request"
            )
        request.check_access("read")
        return {
            "type": "ir.actions.act_window",
            "name": _("Solicitud"),
            "res_model": request._name,
            "res_id": request.id,
            "views": [(self.env.ref("sale_order_request.view_sale_order_request_form").id, "form")],
            "target": "current",
        }

    def _migal_abrir_documento_venta(self, nombre, cotizacion=False):
        self.ensure_one()
        self.check_access("read")
        return {
            "type": "ir.actions.act_window",
            "name": nombre,
            "res_model": "sale.order",
            "res_id": self.id,
            "views": [(self.env.ref("sale.view_order_form").id, "form")],
            "context": {"migal_ver_como_cotizacion": cotizacion},
            "target": "current",
        }

    def action_migal_ir_cotizacion(self):
        self.ensure_one()
        self.check_access("read")
        quotation = self.migal_solicitud_id.sale_order_id or self
        return quotation._migal_abrir_documento_venta(_("Cotización"), cotizacion=True)

    def action_migal_ir_orden(self):
        self.ensure_one()
        self.check_access("read")
        order = self.current_revision_id or self
        if order.state == "sale":
            return order._migal_abrir_documento_venta(_("Orden de venta"))
        return self.env["ir.actions.actions"]._for_xml_id(
            "migal_reportes.action_migal_ordenes_confirmadas"
        )


class SaleOrderRequest(models.Model):
    _inherit = "sale.order.request"

    def _migal_validar_apertura_confirmacion(self):
        self.ensure_one()
        if self.state != "approved":
            raise UserError(_("La solicitud debe estar aprobada para confirmar la venta."))
        if self.requester_id != self.env.user:
            raise UserError(_("Solo el vendedor solicitante puede confirmar esta venta."))

    def action_migal_elegir_comprobante(self):
        self.ensure_one()
        self.check_access("write")
        self._migal_validar_apertura_confirmacion()
        return {
            "type": "ir.actions.act_window",
            "name": _("Aceptar y confirmar"),
            "res_model": "migal.venta.confirmar.solicitud.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_request_id": self.id, "default_tipo_emision": "order"},
        }

    def action_migal_ir_cotizacion(self):
        self.ensure_one()
        self.check_access("read")
        return self.sale_order_id._migal_abrir_documento_venta(
            _("Cotización"), cotizacion=True
        )

    def action_migal_ir_orden(self):
        self.ensure_one()
        self.check_access("read")
        return self.sale_order_revision_id.action_migal_ir_orden()

    def _add_tier_validation_label(self, node, params):
        if "o_migal_solicitud" not in node.getparent().get("class", "").split():
            return super()._add_tier_validation_label(node, params)
        return etree.fromstring(
            self.env["ir.qweb"]._render("migal_reportes.solicitud_aviso_aprobacion", params)
        )

    def _add_tier_validation_reviews(self, node, params):
        reviews = super()._add_tier_validation_reviews(node, params)
        if "o_migal_solicitud" not in node.getparent().get("class", "").split():
            return reviews
        details = etree.Element("details", {"class": "mt-3", "invisible": "not review_ids"})
        etree.SubElement(details, "summary").text = _("Detalle de aprobaciones")
        details.append(reviews)
        return details
