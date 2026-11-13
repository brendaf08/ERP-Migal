# -*- coding: utf-8 -*-
"""Regresión: escenario prioritario de compra futura no registrada.

Valida que Abastecimiento puede aprobar un faltante por abastecimiento futuro
aún no registrado en Compras, que F-2 aprueba automáticamente al completarse
las revisiones requeridas y que el vendedor puede aceptar posteriormente la
solicitud para generar la orden de venta, sin que el stock insuficiente
bloquee indebidamente el proceso, sin inventar existencias y sin crear
compra/recepción/entrega/factura automáticas.
"""

from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestEscenarioCompraFutura(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({
            "name": "PRUEBA - Cliente Compra Futura",
            "company_type": "company",
            "is_company": True,
        })
        cls.grp_sales = cls.env.ref("sale_order_request.group_sale_order_request_salesperson")
        cls.grp_supply = cls.env.ref("sale_order_request.group_sale_order_request_supply")
        cls.grp_transport = cls.env.ref("sale_order_request.group_sale_order_request_transport")
        cls.grp_user = cls.env.ref("base.group_user")
        cls.grp_sale = cls.env.ref("sales_team.group_sale_salesman")

        def _u(login, groups):
            return cls.env["res.users"].with_context(no_reset_password=True).create({
                "name": login,
                "login": login,
                "email": f"{login}@example.invalid",
                "password": "Test123!",
                "company_id": cls.company.id,
                "company_ids": [(6, 0, [cls.company.id])],
                "group_ids": [(6, 0, [g.id for g in groups])],
            })

        cls.user_sales = _u("vendedor_cf_test", [cls.grp_user, cls.grp_sale, cls.grp_sales])
        cls.user_supply = _u("abast_cf_test", [cls.grp_user, cls.grp_supply])
        cls.user_transport = _u("transp_cf_test", [cls.grp_user, cls.grp_transport])

        # Producto almacenable con stock físico limitado (5 m³)
        tmpl = cls.env["product.template"].create({
            "name": "PIEDRA CHANCADA CF TEST",
            "type": "consu",
            "is_storable": True,
            "sale_ok": True,
            "purchase_ok": True,
            "list_price": 100.0,
            "uom_id": cls.env.ref("uom.product_uom_cubic_meter").id,
        })
        cls.product = tmpl.product_variant_id
        location = cls.env.ref("stock.stock_location_stock")
        cls.env["stock.quant"].create({
            "product_id": cls.product.id,
            "location_id": location.id,
            "quantity": 5.0,
            "company_id": cls.company.id,
        })

    def _def(self, xmlid):
        return self.env.ref(f"sale_order_request.{xmlid}")

    def test_escenario_5_compra_futura_no_registrada(self):
        # 20 m³ solicitados, 5 m³ disponibles, faltante 15 m³, sin OC/recepción
        qty = 20.0
        product = self.product.with_company(self.company)
        self.assertLessEqual(product.free_qty, 5.0)
        self.assertFalse(self.env["purchase.order"].search([("partner_id", "!=", False), ("state", "not in", ("cancel",))]))

        env_sales = self.env(user=self.user_sales)
        so = env_sales["sale.order"].create({
            "partner_id": self.partner.id,
            "company_id": self.company.id,
            "user_id": self.user_sales.id,
            "sale_request_applicable": True,
            "client_order_ref": "PRUEBA CF-ESC5",
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": qty,
                "product_uom_id": self.product.uom_id.id,
                "price_unit": 100.0,
                "name": self.product.display_name,
            })],
        })
        so.action_mark_sale_request_subject()
        self.assertTrue(so.sale_request_subject)

        req = env_sales["sale.order.request"].create({
            "sale_order_id": so.id,
            "sale_order_revision_id": so.id,
            "delivery_mode": "delivery",
            "requester_id": self.user_sales.id,
            "line_ids": [(0, 0, {
                "sale_order_line_id": so.order_line[0].id,
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "qty": qty,
            })],
        })
        self.assertFalse(req.stock_sufficient)
        req.with_user(self.user_sales).action_request_validation()
        self.assertEqual(req.state, "pending_approval")

        def_abast = self._def("tier_def_sale_order_request_supply")
        def_trans = self._def("tier_def_sale_order_request_transport")
        review_a = req.review_ids.filtered(lambda r: r.definition_id.id == def_abast.id)
        review_t = req.review_ids.filtered(lambda r: r.definition_id.id == def_trans.id)
        self.assertEqual(len(review_a), 1)
        self.assertEqual(len(review_t), 1)

        # Abastecimiento aprueba (viable conseguir producto: compra futura no registrada)
        req.with_user(self.user_supply).validate_tier()
        req.with_user(self.user_transport).validate_tier()
        self.env.invalidate_all()
        req = env_sales["sale.order.request"].browse(req.id)
        self.assertEqual(req.validation_status, "validated")
        # F-2 automática al completar revisiones requeridas (sin action_approve manual)
        self.assertEqual(req.state, "approved")

        # Vendedor acepta manualmente pese a stock físico insuficiente
        req.with_user(self.user_sales).action_accept()
        self.assertEqual(req.state, "confirmed")
        so = self.env["sale.order"].browse(so.id)
        self.assertEqual(so.state, "sale")
        self.assertEqual(req.sale_order_id, so)

        # Sin órdenes de venta duplicadas
        dups = self.env["sale.order"].search([
            ("id", "!=", so.id),
            ("client_order_ref", "=", "PRUEBA CF-ESC5"),
            ("state", "!=", "cancel"),
        ])
        self.assertFalse(dups)

        # Sin compra/recepción/entrega/factura automáticas y sin stock inventado
        purchases = self.env["purchase.order"].search([("origin", "ilike", so.name)])
        self.assertFalse(purchases)
        self.assertFalse(so.invoice_ids)
        self.assertFalse(any(p.state == 'done' for p in so.picking_ids))
        self.assertEqual(self.product.with_company(self.company).qty_available, 5.0)
        quants = self.env["stock.quant"].search([
            ("product_id", "=", self.product.id),
            ("location_id.usage", "=", "internal"),
        ])
        self.assertEqual(sum(quants.mapped("quantity")), 5.0)
