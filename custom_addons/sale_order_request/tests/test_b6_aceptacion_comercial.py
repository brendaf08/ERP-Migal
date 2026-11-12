# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Pruebas de aceptación comercial — Fase B6 — sale_order_request.

Ejecuta los escenarios B5-T1 a B5-T5 definidos en los entregables B5-E6.
Estos escenarios validan el comportamiento del addon dentro del contexto de
cotizaciones comerciales completas de Odoo 19.

No repite las pruebas técnicas de B3 y B4. Valida la integración comercial.

Resultados: PASS / FAIL / BLOCKED / NOT RUN.
"""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestB6AceptacionComercial(TransactionCase):
    """Pruebas de aceptación comercial para Fase B6."""

    # ------------------------------------------------------------------
    # setUpClass — crear datos sintéticos dentro de la prueba
    # ------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.admin = cls.env["res.users"].browse(2)
        cls.company_1 = cls.env.company
        cls.company_2 = cls.env["res.company"].create({"name": "Company Test 2"})
        cls.admin.write({"company_ids": [(4, cls.company_2.id)]})
        cls.partner = cls.env["res.partner"].search(
            [("customer_rank", ">", 0)], limit=1
        )
        if not cls.partner:
            cls.partner = cls.env["res.partner"].create({
                "name": "Cliente B6 Sintetico",
                "customer_rank": 1,
                "company_id": cls.company_1.id,
            })

        cls.grupo_salesperson = cls.env.ref(
            "sale_order_request.group_sale_order_request_salesperson"
        )
        cls.grupo_abastecimiento = cls.env.ref(
            "sale_order_request.group_sale_order_request_supply"
        )
        cls.grupo_transporte = cls.env.ref(
            "sale_order_request.group_sale_order_request_transport"
        )

        # Almacén y ubicación de company 1
        cls.warehouse_c1 = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_1.id)], limit=1
        )
        if not cls.warehouse_c1:
            cls.warehouse_c1 = cls.env["stock.warehouse"].create({
                "name": "Almacén B6 C1",
                "code": "WHB6",
                "company_id": cls.company_1.id,
            })
        cls.loc_c1 = cls.warehouse_c1.lot_stock_id

        # Crear productos con stock real en company 1
        cls.product_suficiente, _ = cls._crear_producto_stock(
            "Producto B6 Suficiente", qty_stock=50.0, company=cls.company_1
        )
        cls.product_insuficiente, _ = cls._crear_producto_stock(
            "Producto B6 Insuficiente", qty_stock=1.0, company=cls.company_1
        )

        # Usuarios sintéticos
        cls.user_sales_c1 = cls._crear_usuario(
            "user_b6_sales_c1", [cls.company_1.id],
            ["base.group_user", "sales_team.group_sale_salesman",
             "sale_order_request.group_sale_order_request_salesperson"]
        )
        cls.user_abast_c1 = cls._crear_usuario(
            "user_b6_abast_c1", [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_supply"]
        )
        cls.user_trans_c1 = cls._crear_usuario(
            "user_b6_trans_c1", [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_transport"]
        )
        cls.user_sales_c2 = cls._crear_usuario(
            "user_b6_sales_c2", [cls.company_2.id],
            ["base.group_user", "sales_team.group_sale_salesman",
             "sale_order_request.group_sale_order_request_salesperson"]
        )
        # Usuario coordinador para pruebas del procedimiento coordinado
        cls.user_coordinador_c1 = cls._crear_usuario(
            "user_b6_coord_c1", [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_coordinator"]
        )

    @classmethod
    def _crear_usuario(cls, login, company_ids, xml_ids):
        grupos = [cls.env.ref(x).id for x in xml_ids]
        return cls.env["res.users"].create({
            "login": login,
            "password": "login",
            "name": login,
            "company_id": company_ids[0],
            "company_ids": [(6, 0, company_ids)],
            "group_ids": [(6, 0, grupos)],
        })

    @classmethod
    def _crear_producto_stock(cls, nombre, qty_stock=50.0, company=None):
        company = company or cls.company_1
        template = cls.env["product.template"].create({
            "name": nombre,
            "type": "consu",
            "is_storable": True,
            "sale_ok": True,
            "company_id": company.id,
        })
        product = template.product_variant_ids[0]
        cls.env["stock.quant"].create({
            "product_id": product.id,
            "location_id": cls.loc_c1.id,
            "quantity": qty_stock,
        })
        cls.env.invalidate_all()
        product = cls.env["product.product"].browse(product.id)
        return product, cls.loc_c1

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _crear_cotizacion(self, ref, company, sales_user, producto, qty=5.0):
        env = self.env(user=self.admin)
        order = env["sale.order"].with_company(company).create({
            "partner_id": self.partner.id,
            "client_order_ref": ref,
            "company_id": company.id,
            "user_id": sales_user.id,
            "order_line": [
                (0, 0, {
                    "product_id": producto.id,
                    "product_uom_qty": qty,
                })
            ],
        })
        order.with_user(sales_user).action_mark_sale_request_subject()
        order.with_user(env.user).write({"state": "sent"})
        return order

    def _mark_as_subject(self, cotizacion, usuario):
        if not cotizacion.sale_request_subject:
            cotizacion.with_user(usuario).action_mark_sale_request_subject()
        return cotizacion

    def _crear_solicitud(self, env, sale_order, delivery_mode="pickup", qty=5.0,
                         company_id=None):
        vals = {
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
        }
        if company_id is not None:
            vals["company_id"] = company_id
        return env["sale.order.request"].create(vals)

    def _obtener_def_abastecimiento(self):
        return self.env.ref("sale_order_request.tier_def_sale_order_request_supply")

    def _obtener_def_transporte(self):
        return self.env.ref("sale_order_request.tier_def_sale_order_request_transport")

    def _resultado(self, nombre, estado, detalle=""):
        print(f"\n[{estado}] {nombre}")
        if detalle:
            print(f"  {detalle}")

    # ------------------------------------------------------------------
    # B5-T1 — Stock suficiente + recojo → sin aprobaciones → sale
    # ------------------------------------------------------------------
    def test_b6_t1_stock_suficiente_recojo_sin_aprobaciones(self):
        """Cotización sujeta a solicitud de orden de venta, stock suficiente, recojo → sin aprobaciones → sale."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B6-T1", self.company_1, self.user_sales_c1,
            producto=self.product_suficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )

        # Precondición: stock suficiente
        self.assertTrue(solicitud.line_ids[0].stock_sufficient,
                        "Stock suficiente: qty=5.0 <= free_qty=50.0")

        # Solicitar validación → aprobado directamente (sin revisiones de Tier)
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "approved",
                         "Stock suficiente + recojo → aprobado directamente")
        self.assertEqual(len(solicitud.review_ids), 0,
                         "No debe haber revisiones de Tier")

        # Aceptación final por el vendedor
        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")

        # Cotización en sale
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

        # No segunda sale.order
        ordenes_dup = self.env["sale.order"].search([
            ("unrevisioned_name", "=", cotizacion.unrevisioned_name),
            ("id", "!=", cotizacion.id),
        ])
        self.assertEqual(len(ordenes_dup), 0,
                         "No se debe crear segunda sale.order")

        self._resultado("B5-T1", "PASS",
                        "Cotización confirmada en sale, sin aprobaciones, sin duplicados")

    # ------------------------------------------------------------------
    # B5-T2 — Stock insuficiente + despacho → Abastecimiento + Transporte → accept bloqueado
    # ------------------------------------------------------------------
    def test_b6_t2_stock_insuficiente_despacho_abastecimiento_transporte(self):
        """Cotización sujeta a solicitud de orden de venta, stock insuficiente, despacho → Abastecimiento + Transporte → accept bloqueado."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        env_trans = self.env(user=self.user_trans_c1)
        cotizacion = self._crear_cotizacion(
            "B6-T2", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )

        # Precondición: stock insuficiente
        self.assertFalse(solicitud.line_ids[0].stock_sufficient,
                         "Stock insuficiente: qty=5.0 > free_qty=1.0")

        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Ambas revisiones creadas
        def_abast = self._obtener_def_abastecimiento()
        def_trans = self._obtener_def_transporte()
        review_a = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abast.id
        )
        review_t = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_trans.id
        )
        self.assertEqual(len(review_a), 1)
        self.assertEqual(len(review_t), 1)

        # Abastecimiento y Transporte validan y aprueban
        solicitud.with_user(self.user_abast_c1).validate_tier()
        solicitud.with_user(self.user_trans_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        review_a = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abast.id
        )
        review_t = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_trans.id
        )
        self.assertEqual(review_a.status, "approved")
        self.assertEqual(review_t.status, "approved")
        self.assertEqual(solicitud.validation_status, "validated")

        # F-2: aprobación automática al completar todas las revisiones requeridas.
        self.assertEqual(solicitud.state, "approved")

        # Aceptación final bloqueada por stock insuficiente (revalidación)
        try:
            solicitud.with_user(self.user_sales_c1).action_accept()
            self.fail("action_accept() debería haber fallado por stock insuficiente")
        except UserError:
            pass  # Esperado

        self.assertEqual(solicitud.state, "approved")
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sent")

        self._resultado("B5-T2", "PASS",
                        "Aprobaciones registradas, accept bloqueado por stock, cotización en sent")

    # ------------------------------------------------------------------
    # B5-T3 — Nueva revisión → solicitud anterior superseded → nueva solicitud con Transporte
    # ------------------------------------------------------------------
    def test_b6_t3_nueva_revision_sustituye_solicitud(self):
        """Nueva revisión de cotización → solicitud anterior superseded → nueva solicitud con aprobación propia."""
        env_sales = self.env(user=self.user_sales_c1)
        env_trans = self.env(user=self.user_trans_c1)
        env_coord = self.env(user=self.user_coordinador_c1)
        cotizacion = self._crear_cotizacion(
            "B6-T3", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        solicitud.with_user(self.user_abast_c1).validate_tier()
        solicitud.with_user(self.user_trans_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar todas las revisiones requeridas.
        self.assertEqual(solicitud.state, "approved")

        # Revisión coordinada: solo el coordinador puede ejecutarla
        # (stock insuficiente impide action_accept(), pero la revisión
        # coordinada sigue siendo válida desde 'approved')
        resultado = solicitud.with_user(
            self.user_coordinador_c1
        ).action_coordinated_revision()
        self.env.invalidate_all()

        # La solicitud anterior queda superseded
        solicitud = env_sales["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "superseded")

        # Nueva solicitud creada y vinculada a la nueva revisión
        solicitud_nueva = env_sales["sale.order.request"].browse(
            resultado["res_id"]
        )
        self.assertEqual(solicitud_nueva.state, "draft")

        # Nueva solicitud para la revisión nueva, con despacho (requiere Transporte)
        solicitud_nueva.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud_nueva.state, "pending_approval")

        # Validar Transporte en la nueva solicitud
        solicitud_nueva.with_user(self.user_trans_c1).validate_tier()
        self.env.invalidate_all()
        solicitud_nueva = self.env["sale.order.request"].browse(solicitud_nueva.id)
        def_trans = self._obtener_def_transporte()
        review_t = solicitud_nueva.review_ids.filtered(
            lambda r: r.definition_id.id == def_trans.id
        )
        self.assertEqual(review_t.status, "approved",
                         "Transporte validó su revisión en la nueva solicitud")
        # La nueva solicitud requiere sus propias aprobaciones (estado pendiente)
        self.assertEqual(solicitud_nueva.state, "pending_approval",
                         "Nueva solicitud requiere aprobación propia")

        # Cotización original pasa a cancel
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "cancel")

        # Nueva revisión está en draft y conserva sale_request_subject
        nueva = solicitud_nueva.sale_order_revision_id
        self.assertEqual(nueva.state, "draft")
        self.assertTrue(nueva.sale_request_subject)

        self._resultado("B5-T3", "PASS",
                        "Solicitud anterior superseded, nueva solicitud independiente con Transporte")

    # ------------------------------------------------------------------
    # B5-T4 — Usuario de compañía 2 intenta aprobar solicitud de compañía 1
    # ------------------------------------------------------------------
    def test_b6_t4_aislamiento_multiempresa(self):
        """Operación entre empresas rechazada: usuario de C2 no puede operar
        una solicitud de C1.

        Se intenta una operación de aprobación desde compañía 2 sobre una
        solicitud de compañía 1. La operación debe ser rechazada y la solicitud
        debe permanecer sin cambios, sin atribuir el rechazo a un mecanismo
        específico no demostrable estáticamente.
        """
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion = self._crear_cotizacion(
            "B6-T4", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales_c1, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        # Recojo + stock insuficiente: requiere Abastecimiento y queda pendiente.
        self.assertEqual(solicitud.state, "pending_approval")
        reviews_before = solicitud.review_ids.read(["status", "done_by", "reviewed_date"])

        # Precondición: solicitud pertenece a company_1
        self.assertEqual(solicitud.company_id.id, self.company_1.id)
        # Precondición: user_sales_c2 solo pertenece a company_2
        self.assertEqual(self.user_sales_c2.company_id.id, self.company_2.id)
        self.assertNotIn(self.company_1.id, self.user_sales_c2.company_ids.ids)

        estado_antes = solicitud.state
        approval_date_antes = solicitud.approval_date

        # Intento de operación de aprobación desde compañía 2 sobre solicitud de compañía 1.
        # Se verifica rechazo y ausencia de cambios sin atribuir la causa a un
        # mecanismo específico (control de acceso/registro o control de compañía).
        try:
            env_sales_c2["sale.order.request"].browse(solicitud.id).with_user(
                self.user_sales_c2
            ).action_approve()
            self.fail(
                "La operación desde compañía 2 sobre solicitud de compañía 1 debió ser rechazada."
            )
        except (AccessError, UserError):
            pass

        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, estado_antes)
        self.assertEqual(solicitud.state, "pending_approval")
        self.assertEqual(solicitud.approval_date, approval_date_antes)
        self.assertEqual(
            solicitud.review_ids.read(["status", "done_by", "reviewed_date"]),
            reviews_before,
        )

        self._resultado("B5-T4", "PASS",
                        "Operación entre empresas rechazada desde C2 sobre solicitud de C1, sin modificaciones")

    # ------------------------------------------------------------------
    # B5-T5 — Solicitud rechazada → cotización no llega a sale
    # ------------------------------------------------------------------
    def test_b6_t5_solicitud_rechazada_bloquea_confirmacion(self):
        """Solicitud rechazada → cotización permanece en sent, no llega a sale."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B6-T5", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Abastecimiento valida la revisión
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        def_abast = self._obtener_def_abastecimiento()
        review_abast = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abast.id
        )
        self.assertEqual(review_abast.status, "approved")

        # El solicitante rechaza la solicitud
        solicitud.with_user(self.user_sales_c1).action_reject()
        self.assertEqual(solicitud.state, "rejected")

        # Intentar confirmar la cotización directamente → debe fallar
        try:
            cotizacion.with_user(self.user_sales_c1).action_confirm()
            self.fail("action_confirm() debería haber fallado")
        except UserError:
            pass  # Esperado

        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sent")

        self._resultado("B5-T5", "PASS",
                        "Solicitud rechazada, cotización en sent, confirmación bloqueada")
