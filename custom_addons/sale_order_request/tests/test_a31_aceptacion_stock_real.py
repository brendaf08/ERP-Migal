# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Prueba funcional completa: aceptación final con producto almacenable y
stock real en PRUEBAS.

Valida el flujo completo de Solicitud de orden de venta con:
- Producto almacenable (type='consu', is_storable=True)
- Stock real registrado vía stock.quant
- Identificación automática de cotización sujeta a solicitud de orden de venta (sale_request_applicable=True)
- Flujo completo hasta action_accept() y confirmación de cotización
- Ausencia de creación de segundo sale.order
- Escenario de stock insuficiente con conformidad aprobada (abastecimiento futuro) y revalidación
"""

from odoo.exceptions import UserError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestA31AceptacionStockReal(TransactionCase):
    """Flujo funcional completo con producto almacenable y stock real."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.admin = cls.env["res.users"].browse(2)
        # Admin necesita group_sale_order_request_salesperson para marcar cotizaciones
        # como  en los helpers de prueba.
        cls.admin.write({
            "group_ids": [(4, cls.env.ref(
                "sale_order_request.group_sale_order_request_salesperson").id)]
        })
        cls.partner = cls.env["res.partner"].search(
            [("customer_rank", ">", 0)], limit=1
        )
        if not cls.partner:
            cls.partner = cls.env["res.partner"].create(
                {"name": "Cliente Test A31", "customer_rank": 1}
            )

        cls.grupo_salesperson = cls.env.ref(
            "sale_order_request.group_sale_order_request_salesperson"
        )
        cls.grupo_abastecimiento = cls.env.ref(
            "sale_order_request.group_sale_order_request_supply"
        )
        cls.grupo_transporte = cls.env.ref(
            "sale_order_request.group_sale_order_request_transport"
        )
        cls.grupo_sale_salesman = cls.env.ref("sales_team.group_sale_salesman")

        cls.user_sales = cls.env["res.users"].create({
            "login": "user_a31_sales",
            "password": "login",
            "name": "user_a31_sales",
            "group_ids": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("sales_team.group_sale_salesman").id,
                cls.env.ref("sale_order_request.group_sale_order_request_salesperson").id,
            ])],
        })
        cls.user_abastecimiento = cls.env["res.users"].create({
            "login": "user_a31_abastecimiento",
            "password": "login",
            "name": "user_a31_abastecimiento",
            "group_ids": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("sale_order_request.group_sale_order_request_supply").id,
            ])],
        })
        cls.user_transporte = cls.env["res.users"].create({
            "login": "user_a31_transporte",
            "password": "login",
            "name": "user_a31_transporte",
            "group_ids": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("sale_order_request.group_sale_order_request_transport").id,
            ])],
        })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _crear_producto_almacenable(self, nombre, qty_stock=50.0):
        """Crea un producto almacenable (consu + is_storable) y registra
        stock real vía stock.quant en ubicación interna."""
        template = self.env["product.template"].create({
            "name": nombre,
            "type": "consu",
            "is_storable": True,
            "sale_ok": True,
        })
        product = template.product_variant_ids[0]
        # Ubicación interna
        ubicacion = self.env["stock.location"].search(
            [("usage", "=", "internal")], limit=1
        )
        self.env["stock.quant"].create({
            "product_id": product.id,
            "location_id": ubicacion.id,
            "quantity": qty_stock,
        })
        # Forzar recomputo de campos de stock
        self.env.invalidate_all()
        product = self.env["product.product"].browse(product.id)
        # Acceder a free_qty para disparar el compute
        _ = product.free_qty
        self.assertGreater(
            product.free_qty, 0,
            f"free_qty debe ser > 0 para {nombre}, obtuvo {product.free_qty}"
        )
        return product, ubicacion

    def _crear_cotizacion(self, ref, sale_request_applicable=True, producto=None, usuario=None):
        if producto is None:
            if getattr(self, 'product', None) is not None:
                producto = self.product
            else:
                producto, _ = self._crear_producto_almacenable(
                    f"Producto {ref}", qty_stock=50.0
                )
        self.product = producto
        env = self.env(user=usuario or self.admin)
        order = env["sale.order"].create({
            "partner_id": self.partner.id,
            "client_order_ref": ref,
            "order_line": [
                (0, 0, {
                    "product_id": producto.id,
                    "product_uom_qty": 5.0,
                })
            ],
        })
        if sale_request_applicable:
            # Marcar como  vía ruta autorizada (action_mark_sale_request_subject).
            # Se ejecuta como admin para tener acceso de escritura a la cotización;
            # el método verifica internamente que el usuario tenga
            # group_sale_order_request_salesperson.
            order.with_user(self.admin).action_mark_sale_request_subject()
            # Verificar identificación
            self.assertTrue(order.sale_request_applicable)
            self.assertTrue(order.sale_request_subject)
        order.with_user(env.user).write({"state": "sent"})
        order.write({"user_id": self.user_sales.id})
        return order

    def _crear_solicitud(self, env, sale_order, delivery_mode="pickup", qty=5.0):
        return env["sale.order.request"].create({
            "sale_order_id": sale_order.id,
            "sale_order_revision_id": sale_order.id,
            "delivery_mode": delivery_mode,
            "requester_id": env.user.id,
            "line_ids": [(0, 0, {
                "sale_order_line_id": sale_order.order_line[0].id,
                "product_id": sale_order.order_line[0].product_id.id,
                "product_uom_id": sale_order.order_line[0].product_uom_id.id,
                "qty": qty,
            })],
        })

    # ------------------------------------------------------------------
    # Prueba 1: Flujo completo con stock suficiente (recojo)
    # ------------------------------------------------------------------
    def test_flujo_completo_stock_suficiente_recojo(self):
        """1. Crear cotización sujeta a solicitud de orden de venta → 2. Identificación automática →
        3. Crear solicitud vinculada → 4. Stock suficiente →
        5. Aprobaciones (ninguna para recojo+stock suficiente) →
        6. action_accept() → 7. Confirmación de cotización →
        8. No segundo sale.order."""
        producto, _ = self._crear_producto_almacenable(
            "Producto Stock Real Recojo", qty_stock=50.0
        )
        self.product = producto

        cotizacion = self._crear_cotizacion("A31-FULL-RECOJO", sale_request_applicable=True)
        # Verificar identificación automática (Punto 2)
        self.assertTrue(cotizacion.sale_request_applicable)
        self.assertTrue(cotizacion.sale_request_subject)

        # 3. Crear solicitud vinculada
        env_sales = self.env(user=self.user_sales)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        self.assertEqual(solicitud.sale_order_id, cotizacion)
        self.assertEqual(solicitud.sale_order_revision_id, cotizacion)
        self.assertEqual(len(solicitud.line_ids), 1)
        self.assertEqual(solicitud.line_ids[0].sale_order_line_id, cotizacion.order_line[0])

        # 4. Verificar disponibilidad suficiente (5 <= 50)
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "approved", "Stock suficiente → autoaprobación")

        # 5. No hay revisiones pendientes (autoaprobación)
        pending = solicitud.review_ids.filtered(
            lambda r: r.status in ("waiting", "pending")
        )
        self.assertEqual(len(pending), 0)

        # 6. action_accept()
        solicitud.with_user(self.user_sales).action_accept()
        self.assertEqual(solicitud.state, "confirmed")

        # 7. Confirmación de cotización correspondiente
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

        # 8. No segundo sale.order
        ordenes_dup = self.env["sale.order"].search([
            ("unrevisioned_name", "=", cotizacion.unrevisioned_name),
            ("id", "!=", cotizacion.id),
        ])
        self.assertEqual(len(ordenes_dup), 0, "No debe crearse un segundo sale.order")

    # ------------------------------------------------------------------
    # Prueba 2: Stock insuficiente con conformidad aprobada (abastecimiento futuro)
    # ------------------------------------------------------------------
    def test_stock_insuficiente_con_conformidad_permite_aceptacion(self):
        """Producto con stock insuficiente: si Abastecimiento aprueba (conformidad
        de abastecimiento futuro) y F-2 aprueba automáticamente al completar las
        revisiones requeridas, el vendedor puede aceptar y confirmar la cotización
        sin inventar existencias ni crear compras/recepciones/entregas/facturas."""
        producto, _ = self._crear_producto_almacenable(
            "Producto Stock Bajo", qty_stock=2.0
        )
        self.product = producto

        cotizacion = self._crear_cotizacion("A31-STOCK-BAJO", sale_request_applicable=True)
        env_sales = self.env(user=self.user_sales)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )

        # Stock insuficiente (2 < 5) → requiere Abastecimiento
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Abastecimiento valida; F-2 aprueba automáticamente al completar Tier.
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "approved")

        # action_accept() revalida stock pero no bloquea: conformidad vigente.
        solicitud.with_user(self.user_sales).action_accept()
        self.assertEqual(solicitud.state, "confirmed")
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")
        # Sin inventar stock ni crear documentos automáticos (compra/recepción/factura)
        self.assertEqual(producto.qty_available, 2.0)
        self.assertFalse(self.env["purchase.order"].search([("origin", "ilike", cotizacion.name)]))
        self.assertFalse(cotizacion.invoice_ids)
        # No confirmar entregas automáticamente
        self.assertFalse(any(p.state == 'done' for p in cotizacion.picking_ids))

    # ------------------------------------------------------------------
    # Prueba 3: Cotización no  confirma normalmente
    # ------------------------------------------------------------------
    def test_cotizacion_no_subject_confirma_normalmente(self):
        """Una cotización no sujeta a  confirma sin solicitud."""
        env_admin = self.env(user=self.admin)
        cotizacion = self._crear_cotizacion(
            "A31-NO-", sale_request_applicable=False, usuario=self.admin
        )
        self.assertFalse(cotizacion.sale_request_applicable)
        self.assertFalse(cotizacion.sale_request_subject)

        cotizacion.with_user(self.admin).action_confirm()
        self.assertEqual(cotizacion.state, "sale")

    # ------------------------------------------------------------------
    # Prueba 4: Cotización sujeta a solicitud de orden de venta sin solicitud aceptada no confirma
    # ------------------------------------------------------------------
    def test_cotizacion_subject_sin_solicitud_no_confirma(self):
        """Cotización sujeta a solicitud de orden de venta sin solicitud aceptada: confirmación bloqueada."""
        producto, _ = self._crear_producto_almacenable(
            "Producto Sin Solicitud", qty_stock=50.0
        )
        self.product = producto

        cotizacion = self._crear_cotizacion("A31-SIN-REQ", sale_request_applicable=True)
        self.assertTrue(cotizacion.sale_request_subject)

        # Intentar confirmar sin solicitud
        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales).action_confirm()
        self.assertNotEqual(cotizacion.state, "sale")

    # ------------------------------------------------------------------
    # Prueba 5: Despacho requiere Transporte
    # ------------------------------------------------------------------
    def test_flujo_despacho_requiere_transporte(self):
        """Modalidad despacho con stock insuficiente requiere Transporte."""
        producto, _ = self._crear_producto_almacenable(
            "Producto Despacho", qty_stock=2.0
        )
        self.product = producto

        cotizacion = self._crear_cotizacion("A31-DESPACHO", sale_request_applicable=True)
        env_sales = self.env(user=self.user_sales)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )

        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
        # Dos revisiones: Abastecimiento + Transporte
        self.assertEqual(len(solicitud.review_ids), 2)

        # Ambos revisores validan sus revisiones Tier
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        solicitud.with_user(self.user_transporte).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.validation_status, "validated")

        # Al completar todas las revisiones requeridas, F-2 aprueba automáticamente.
        self.assertEqual(solicitud.state, "approved")

        # Aceptación permitida con aprobaciones completas pese a stock insuficiente
        solicitud.with_user(self.user_sales).action_accept()
        self.assertEqual(solicitud.state, "confirmed")
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")
        self.assertEqual(producto.qty_available, 2.0)
        self.assertFalse(self.env["purchase.order"].search([("origin", "ilike", cotizacion.name)]))
        self.assertFalse(cotizacion.invoice_ids)
        self.assertFalse(any(p.state == 'done' for p in cotizacion.picking_ids))
