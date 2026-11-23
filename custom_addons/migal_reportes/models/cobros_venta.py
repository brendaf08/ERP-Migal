"""Cobros contabilizados, comprobantes externos y seguimiento de la venta."""

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


_ESTADOS_EMISION = [
    ("order", "Orden de venta"),
    ("receipt_pending", "Boleta pendiente"),
    ("invoice_pending", "Factura pendiente"),
    ("receipt", "Boleta emitida"),
    ("invoice", "Factura emitida"),
]


_TIPOS_EMISION_PREVISTA = [
    ("invoice_pending", "Factura"),
    ("receipt_pending", "Boleta"),
    ("order", "Sin comprobante"),
]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    migal_comprobante_externo = fields.Selection(
        _ESTADOS_EMISION,
        string="Estado de emisión",
        copy=False,
        readonly=True,
        tracking=True,
    )
    # Las vistas almacenadas de 1.20 todavía pueden referenciar este campo
    # hasta que Odoo cargue la nueva vista del formulario.
    migal_tipo_emision_previsto = fields.Selection(
        _TIPOS_EMISION_PREVISTA,
        string="Comprobante previsto",
        compute="_compute_migal_tipo_emision_compat",
    )
    migal_codigo_comprobante = fields.Char(
        string="Referencia de Key Fácil", copy=False, readonly=True, tracking=True, size=100
    )
    migal_fecha_comprobante = fields.Date(
        string="Fecha de emisión", copy=False, readonly=True, tracking=True
    )
    migal_cobro_ids = fields.One2many(
        "account.payment", "migal_orden_cobro_id", string="Cobros de la orden",
        groups="account.group_account_invoice",
    )
    migal_ultimo_cobro = fields.Datetime(copy=False, readonly=True)
    migal_cobrado = fields.Monetary(
        string="Cobrado", currency_field="currency_id",
        compute="_compute_migal_cobro", compute_sudo=True,
    )
    migal_saldo_cobro = fields.Monetary(
        string="Saldo pendiente", currency_field="currency_id",
        compute="_compute_migal_cobro", compute_sudo=True,
    )
    migal_estado_cobro = fields.Selection(
        [("pending", "Pendiente"), ("partial", "Pago parcial"), ("paid", "Pagada")],
        string="Estado de cobro", compute="_compute_migal_cobro", compute_sudo=True,
    )
    migal_resumen_cotizacion_id = fields.Many2one(
        "sale.order", string="Cotización", compute="_compute_migal_resumen_venta"
    )
    migal_resumen_estado_solicitud = fields.Selection(
        related="migal_solicitud_id.state",
        string="Estado de la solicitud",
        depends=["migal_solicitud_id"],
        compute_sudo=False,
    )
    migal_resumen_orden_id = fields.Many2one(
        "sale.order", string="Orden de venta", compute="_compute_migal_resumen_venta"
    )
    migal_resumen_despacho_ids = fields.Many2many(
        "stock.picking", string="Despachos", compute="_compute_migal_resumen_venta"
    )

    @api.depends("migal_comprobante_externo")
    def _compute_migal_tipo_emision_compat(self):
        tipos_emitidos = {"invoice": "invoice_pending", "receipt": "receipt_pending"}
        for order in self:
            estado = order.migal_comprobante_externo
            order.migal_tipo_emision_previsto = tipos_emitidos.get(estado, estado)

    def action_confirm(self):
        self.check_access("write")
        sin_eleccion = self.filtered(
            lambda order: order.state in ("draft", "sent") and not order.migal_comprobante_externo
        )
        if sin_eleccion:
            sin_eleccion.write({"migal_comprobante_externo": "order"})
        return super().action_confirm()

    @api.constrains("migal_comprobante_externo", "migal_codigo_comprobante", "migal_fecha_comprobante")
    def _check_migal_comprobante_externo(self):
        for order in self:
            if order.migal_comprobante_externo in ("invoice", "receipt"):
                if not (order.migal_codigo_comprobante or "").strip():
                    raise ValidationError(_("El número o código del comprobante es obligatorio."))
            elif order.migal_codigo_comprobante or order.migal_fecha_comprobante:
                raise ValidationError(_("Solo los comprobantes emitidos pueden tener número o fecha."))

    @api.depends(
        "amount_total", "currency_id", "migal_cobro_ids.amount", "migal_cobro_ids.date",
        "migal_cobro_ids.currency_id", "migal_cobro_ids.state", "migal_cobro_ids.move_id.state",
        "migal_cobro_ids.move_id.reversal_move_ids.state",
    )
    def _compute_migal_cobro(self):
        for order in self:
            payments = order.migal_cobro_ids.filtered(
                lambda pay: pay.state in ("in_process", "paid")
                and pay.move_id.state == "posted"
                and not any(move.state == "posted" for move in pay.move_id.reversal_move_ids)
            )
            currency = order.currency_id
            paid = sum(
                pay.currency_id._convert(pay.amount, currency, order.company_id, pay.date)
                for pay in payments
            )
            balance = max(order.amount_total - paid, 0)
            order.migal_cobrado = currency.round(paid) if currency else paid
            order.migal_saldo_cobro = currency.round(balance) if currency else balance
            if not currency or currency.is_zero(paid):
                order.migal_estado_cobro = "pending"
            elif currency.is_zero(balance):
                order.migal_estado_cobro = "paid"
            else:
                order.migal_estado_cobro = "partial"

    @api.depends("state", "current_revision_id", "current_revision_id.state",
                 "picking_ids", "current_revision_id.picking_ids", "migal_solicitud_id")
    def _compute_migal_resumen_venta(self):
        for order in self:
            current = order.current_revision_id or order
            order.migal_resumen_cotizacion_id = order.migal_solicitud_id.sale_order_id or order
            order.migal_resumen_orden_id = current if current.state == "sale" else False
            order.migal_resumen_despacho_ids = current.picking_ids.filtered(
                lambda picking: picking.picking_type_code == "outgoing"
                or picking.location_dest_id.usage == "customer"
            )

    def action_migal_registrar_cobro(self):
        self.ensure_one()
        self._migal_validar_registro_cobro()
        return {
            "type": "ir.actions.act_window",
            "name": _("Registrar cobro"),
            "res_model": "migal.venta.cobro.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_order_id": self.id,
                "default_amount": self.migal_saldo_cobro,
            },
        }

    def _migal_validar_registro_cobro(self):
        self.ensure_one()
        self.check_access("write")
        if not self.env.user.has_group("account.group_account_invoice"):
            raise AccessError(_("Necesitas permisos de facturación para registrar cobros."))
        if self.state != "sale" or self.current_revision_id:
            raise UserError(_("Registra el cobro desde la orden de venta confirmada y vigente."))
        if any(invoice.state == "posted" and invoice.move_type == "out_invoice" for invoice in self.invoice_ids):
            raise UserError(_("Esta orden ya tiene factura contabilizada en Odoo. Registra el cobro desde esa factura."))
        if self.currency_id.is_zero(self.migal_saldo_cobro):
            raise UserError(_("La orden no tiene saldo pendiente."))

    def action_migal_ver_cobros(self):
        self.ensure_one()
        self.check_access("read")
        self.env["account.payment"].check_access("read")
        customer = self.partner_id.commercial_partner_id
        if not customer:
            raise UserError(_("Selecciona un cliente para consultar sus pagos."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Pagos de %s", customer.display_name),
            "res_model": "account.payment",
            "views": [(False, "list"), (False, "form")],
            "domain": [
                ("partner_id.commercial_partner_id", "=", customer.id),
                ("company_id", "=", self.company_id.id),
                ("partner_type", "=", "customer"),
                ("payment_type", "=", "inbound"),
            ],
            "context": {"create": False},
            "target": "current",
        }

    def action_migal_registrar_comprobante(self):
        self.ensure_one()
        self.check_access("write")
        if self.state != "sale" or self.current_revision_id:
            raise UserError(_("Actualiza la emisión desde la orden confirmada y vigente."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Emisión en Key Fácil"),
            "res_model": "migal.venta.comprobante.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_order_id": self.id,
                "default_status": self.migal_comprobante_externo,
                "default_code": self.migal_codigo_comprobante,
            },
        }


class AccountPayment(models.Model):
    _inherit = "account.payment"

    migal_orden_cobro_id = fields.Many2one(
        "sale.order", string="Orden de venta MIGAL", copy=False, readonly=True,
        index="btree_not_null", ondelete="restrict", check_company=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get("migal_orden_cobro_id") for vals in vals_list):
            raise AccessError(_("Vincula el cobro desde la orden de venta."))
        return super().create(vals_list)

    def write(self, vals):
        if "migal_orden_cobro_id" in vals:
            raise AccessError(_("El vínculo del cobro se registra desde la orden de venta."))
        return super().write(vals)

    def _migal_vincular_cobro(self, order):
        self.ensure_one()
        return super().write({"migal_orden_cobro_id": order.id})


class MigalVentaCobroWizard(models.TransientModel):
    _name = "migal.venta.cobro.wizard"
    _description = "Registrar un cobro contabilizado desde una orden"

    order_id = fields.Many2one("sale.order", required=True, readonly=True)
    company_id = fields.Many2one(related="order_id.company_id")
    currency_id = fields.Many2one(related="order_id.currency_id")
    amount = fields.Monetary(string="Monto recibido", required=True)
    date = fields.Date(string="Fecha", required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one(
        "account.journal", string="Diario", required=True,
        domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]",
    )
    valid_method_ids = fields.Many2many(
        "account.payment.method.line", compute="_compute_valid_method_ids",
    )
    payment_method_line_id = fields.Many2one(
        "account.payment.method.line", string="Método de cobro", required=True,
        domain="[('id', 'in', valid_method_ids), ('payment_account_id', '!=', False)]",
    )
    reference = fields.Char(string="Referencia del abono", size=100)
    payment_id = fields.Many2one("account.payment", readonly=True)

    @api.depends("journal_id.inbound_payment_method_line_ids.payment_account_id")
    def _compute_valid_method_ids(self):
        for wizard in self:
            wizard.valid_method_ids = wizard.journal_id.inbound_payment_method_line_ids.filtered("payment_account_id")

    @api.onchange("journal_id")
    def _onchange_migal_cobro_journal(self):
        self.payment_method_line_id = self.valid_method_ids[:1]

    def action_registrar(self):
        self.ensure_one()
        self.check_access("write")
        order = self.order_id.with_company(self.company_id)
        order.check_access("write")
        if not self.env.user.has_group("account.group_account_invoice"):
            raise AccessError(_("Necesitas permisos de facturación para registrar cobros."))
        if self.payment_id:
            return {"type": "ir.actions.act_window_close"}

        with self.env.cr.savepoint():
            # Serializa altas de cobros de la misma orden y permite el reintento transaccional de Odoo.
            order.write({"migal_ultimo_cobro": fields.Datetime.now()})
            order.invalidate_recordset(["migal_cobrado", "migal_saldo_cobro", "migal_cobro_ids"])
            self.invalidate_recordset(["payment_id"])
            if self.payment_id:
                return {"type": "ir.actions.act_window_close"}
            order._migal_validar_registro_cobro()
            currency = order.currency_id
            amount = currency.round(self.amount)
            if currency.compare_amounts(amount, 0) <= 0:
                raise UserError(_("Ingresa un monto mayor a cero."))
            comparison = currency.compare_amounts(amount, order.migal_saldo_cobro)
            if comparison > 0:
                raise UserError(_("El cobro supera el saldo pendiente de la orden."))
            if self.date > fields.Date.context_today(self):
                raise UserError(_("La fecha del cobro no puede ser futura."))
            journal = self.journal_id
            method = self.payment_method_line_id
            if journal.company_id != order.company_id or journal.type not in ("bank", "cash"):
                raise UserError(_("Elige un diario de banco o caja de la misma compañía."))
            if journal.currency_id and journal.currency_id != currency:
                raise UserError(_("La moneda del diario debe coincidir con la moneda de la orden."))
            if method not in journal.inbound_payment_method_line_ids or not method.payment_account_id:
                raise UserError(_("Configura una cuenta de cobros pendientes en el método de entrada del diario."))
            memo = " | ".join(value for value in (order.name, (self.reference or "").strip()) if value)
            payment = self.env["account.payment"].with_company(order.company_id).create({
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": order.partner_invoice_id.commercial_partner_id.id,
                "journal_id": journal.id,
                "payment_method_line_id": method.id,
                "currency_id": currency.id,
                "amount": amount,
                "date": self.date,
                "memo": memo,
            })
            payment.action_post()
            if payment.move_id.state != "posted":
                raise UserError(_("Odoo no contabilizó el cobro. Verifica la configuración del diario."))
            payment._migal_vincular_cobro(order)
            self.payment_id = payment
        return {"type": "ir.actions.act_window_close"}


class MigalVentaComprobanteWizard(models.TransientModel):
    _name = "migal.venta.comprobante.wizard"
    _description = "Registrar el comprobante externo de una orden"

    order_id = fields.Many2one("sale.order", required=True, readonly=True)
    status = fields.Selection(_ESTADOS_EMISION, string="Estado de emisión", required=True, default="order")
    code = fields.Char(string="Referencia de Key Fácil", size=100)

    def action_registrar(self):
        self.ensure_one()
        self.check_access("write")
        order = self.order_id
        order.check_access("write")
        if order.state != "sale" or order.current_revision_id:
            raise UserError(_("Registra el comprobante desde la orden confirmada y vigente."))
        issued = self.status in ("invoice", "receipt")
        code = (self.code or "").strip() if issued else False
        values = {
            "migal_comprobante_externo": self.status,
            "migal_codigo_comprobante": code,
        }
        if self.status != order.migal_comprobante_externo or code != order.migal_codigo_comprobante:
            values["migal_fecha_comprobante"] = False
        order.write(values)
        return {"type": "ir.actions.act_window_close"}


class MigalConfirmarSolicitudWizard(models.TransientModel):
    _name = "migal.venta.confirmar.solicitud.wizard"
    _description = "Confirmar una solicitud con el comprobante previsto"

    request_id = fields.Many2one("sale.order.request", required=True, readonly=True, ondelete="cascade")
    tipo_emision = fields.Selection(
        _TIPOS_EMISION_PREVISTA, string="Comprobante", required=True, default="order",
    )

    def action_confirmar(self):
        self.ensure_one()
        self.check_access("write")
        request = self.request_id
        request.check_access("write")
        request._migal_validar_apertura_confirmacion()
        order = request.sale_order_revision_id
        order.check_access("write")
        if order.migal_comprobante_externo in ("invoice", "receipt"):
            raise UserError(_("Esta cotización ya tiene un comprobante emitido registrado."))

        # La elección y la confirmación se guardan en la misma transacción.
        with self.env.cr.savepoint():
            order.write({"migal_comprobante_externo": self.tipo_emision})
            result = request.action_accept()
        return result or {"type": "ir.actions.act_window_close"}
