# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class SaleOrderRequestLine(models.Model):
    _name = "sale.order.request.line"
    _description = "Línea de Solicitud de orden de venta"

    request_id = fields.Many2one(
        comodel_name="sale.order.request",
        string="Solicitud",
        required=True,
        ondelete="cascade",
        copy=False,
    )
    sale_order_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Línea de cotización",
        required=True,
        readonly=True,
        help="Línea de la cotización de venta a la que corresponde esta línea de solicitud.",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Producto",
        required=True,
        readonly=True,
    )
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unidad de medida",
        required=True,
        readonly=True,
    )
    qty = fields.Float(
        string="Cantidad",
        required=True,
        default=1.0,
    )
    stock_qty = fields.Float(
        string="Stock disponible",
        compute="_compute_stock_qty",
        store=True,
        help="Cantidad disponible según la modalidad de entrega",
    )
    stock_sufficient = fields.Boolean(
        string="Stock suficiente",
        compute="_compute_stock_sufficient",
        store=True,
    )

    _sale_order_line_uniq_per_request = models.Constraint(
        "UNIQUE(request_id, sale_order_line_id)",
        "Una misma línea de cotización no puede aparecer dos veces en "
        "una misma solicitud de pedido.",
    )

    @api.constrains("request_id")
    def _check_company_consistency(self):
        """A3.3: Verifica que la compañía de la solicitud vinculada sea
        accesible por el usuario actual."""
        for line in self:
            if not line.request_id:
                continue
            user_company_ids = set(self.env.user.company_ids.ids)
            if line.request_id.company_id.id not in user_company_ids:
                raise UserError(
                    "No tiene acceso a la compañía de la solicitud vinculada (%s)."
                    % line.request_id.company_id.name
                )

    def check_access_rule(self, operation):
        """A3.3: Verificar que el usuario tenga acceso a la compañía del
        registro antes de permitir cualquier operación."""
        super(SaleOrderRequestLine, self).check_access_rule(operation)
        user_company_ids = set(self.env.user.company_ids.ids)
        if not user_company_ids:
            raise AccessError(
                "No tiene acceso a ninguna compañía."
            )
        for rec in self:
            if not rec.request_id:
                continue
            if rec.request_id.company_id.id not in user_company_ids:
                raise AccessError(
                    "No tiene acceso a la compañía de la solicitud vinculada (%s)."
                    % (rec.request_id.company_id.name or rec.request_id.company_id.id)
                )

    @api.constrains("sale_order_line_id", "product_id", "product_uom_id", "qty")
    def _check_sale_order_line_link(self):
        """Valida que la línea de solicitud corresponda a una línea de
        cotización válida y que la cantidad no subdeclare la comercial."""
        for line in self:
            if not line.sale_order_line_id:
                continue
            sol = line.sale_order_line_id

            # El producto de la línea de solicitud debe coincidir con el de la cotización.
            if line.product_id and line.product_id != sol.product_id:
                raise ValidationError(
                    "El producto de la línea de solicitud no coincide con el "
                    "producto de la línea de cotización vinculada."
                )

            # La unidad de medida debe coincidir.
            if line.product_uom_id and line.product_uom_id != sol.product_uom_id:
                raise ValidationError(
                    "La unidad de medida de la línea de solicitud no coincide "
                    "con la de la línea de cotización vinculada."
                )

            # La cantidad debe ser estrictamente positiva.
            if line.qty <= 0:
                raise ValidationError(
                    "La cantidad de la línea de solicitud debe ser mayor a cero."
                )

            # La cantidad no puede ser inferior a la cantidad comercial de la
            # línea de cotización (se compara en la misma unidad de medida).
            qty_sol = sol.product_uom_qty
            if sol.product_uom_id != line.product_uom_id:
                qty_sol = sol.product_uom_id._compute_quantity(
                    sol.product_uom_qty, line.product_uom_id
                )
            if line.qty < qty_sol:
                raise ValidationError(
                    "La cantidad declarada es inferior a la cantidad comercial "
                    "de la línea de cotización vinculada."
                )

    @api.depends("product_id", "qty", "request_id.delivery_mode")
    def _compute_stock_qty(self):
        for line in self:
            if not line.product_id:
                line.stock_qty = 0.0
                continue
            product = line.product_id
            # La disponibilidad proviene exclusivamente de los datos reales
            # de inventario (stock.quant). No se acepta ningún override por
            # contexto RPC: eso permitiría falsear el stock y saltarse la
            # aprobación de Abastecimiento/Transporte.
            if line.request_id.delivery_mode == "delivery":
                line.stock_qty = product.virtual_available
            else:
                line.stock_qty = product.free_qty

    @api.depends("stock_qty", "qty")
    def _compute_stock_sufficient(self):
        for line in self:
            line.stock_sufficient = line.stock_qty >= line.qty if line.product_id else False

    def _evaluate_stock(self):
        """Reevaluar el stock para esta línea."""
        self._compute_stock_qty()
        self._compute_stock_sufficient()
