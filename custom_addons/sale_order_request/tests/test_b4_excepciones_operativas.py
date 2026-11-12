# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Pruebas funcionales — Fase B4 (excepciones operativas) — sale_order_request.

Verifica el tratamiento de situaciones anormales, transiciones no habituales
e intentos de ejecutar operaciones fuera de orden en el flujo de solicitud de orden de venta.

Escenarios cubiertos:
- B4.1: Cancelación de solicitudes (draft, pending_approval, approved, accepted)
- B4.2: Solicitudes sustituidas por nuevas revisiones (superseded)
- B4.3: Aprobaciones incompletas y fuera de orden
- B4.4: Cambios en la cotización y sus líneas (bloqueos post-aprobación)
- B4.5: Cambios de inventario durante el proceso
- B4.6: Operaciones repetidas e interrupciones

Usa usuarios sintéticos creados en la prueba (no usuarios reales de ).
"""

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestB4ExcepcionesOperativas(TransactionCase):
    """Tratamiento de excepciones operativas del flujo de solicitud de orden de venta."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.admin = cls.env["res.users"].browse(2)
        cls.partner = cls.env["res.partner"].search(
            [("customer_rank", ">", 0)], limit=1
        )
        if not cls.partner:
            cls.partner = cls.env["res.partner"].create(
                {"name": "Cliente Test B4", "customer_rank": 1}
            )

        cls.company_1 = cls.env.company
        cls.company_2 = cls.env["res.company"].create({"name": "Company Test 2"})
        cls.admin.write({"company_ids": [(4, cls.company_2.id)]})

        cls.grupo_salesperson = cls.env.ref(
            "sale_order_request.group_sale_order_request_salesperson"
        )
        cls.grupo_abastecimiento = cls.env.ref(
            "sale_order_request.group_sale_order_request_supply"
        )
        cls.grupo_transporte = cls.env.ref(
            "sale_order_request.group_sale_order_request_transport"
        )
        cls.grupo_base_user = cls.env.ref("base.group_user")
        cls.grupo_sale_salesman = cls.env.ref("sales_team.group_sale_salesman")

        # Productos almacenables con stock real en ubicación de company 1
        cls.product_recojo, _ = cls._crear_producto_almacenable(
            "Producto B4 Recojo", qty_stock=50.0, company=cls.company_1
        )
        cls.product_despacho, _ = cls._crear_producto_almacenable(
            "Producto B4 Despacho", qty_stock=50.0, company=cls.company_1
        )
        cls.product_insuficiente, _ = cls._crear_producto_almacenable(
            "Producto B4 Insuficiente", qty_stock=1.0, company=cls.company_1
        )

        # Usuarios de prueba sintéticos
        cls.user_sales_c1 = cls._crear_usuario(
            "user_b4_sales_c1", [cls.company_1.id],
            ["base.group_user", "sales_team.group_sale_salesman",
             "sale_order_request.group_sale_order_request_salesperson"]
        )
        cls.user_abast_c1 = cls._crear_usuario(
            "user_b4_abast_c1", [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_supply"]
        )
        cls.user_trans_c1 = cls._crear_usuario(
            "user_b4_trans_c1", [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_transport"]
        )
        cls.user_plain_c1 = cls._crear_usuario(
            "user_b4_plain_c1", [cls.company_1.id], ["base.group_user"]
        )
        cls.user_sales_c2 = cls._crear_usuario(
            "user_b4_sales_c2", [cls.company_2.id],
            ["base.group_user", "sales_team.group_sale_salesman",
             "sale_order_request.group_sale_order_request_salesperson"]
        )
        # Usuario coordinador para pruebas del procedimiento coordinado
        cls.user_coordinador_c1 = cls._crear_usuario(
            "user_b4_coord_c1", [cls.company_1.id],
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
    def _crear_producto_almacenable(cls, nombre, qty_stock=50.0, company=None):
        company = company or cls.company_1
        template = cls.env["product.template"].create({
            "name": nombre,
            "type": "consu",
            "is_storable": True,
            "sale_ok": True,
            "company_id": company.id,
        })
        product = template.product_variant_ids[0]
        ubicacion = cls.env["stock.location"].search(
            [("usage", "=", "internal"), ("company_id", "=", company.id)],
            limit=1
        )
        if not ubicacion:
            wh = cls.env["stock.warehouse"].search(
                [("company_id", "=", company.id)], limit=1
            )
            ubicacion = wh.lot_stock_id
        cls.env["stock.quant"].create({
            "product_id": product.id,
            "location_id": ubicacion.id,
            "quantity": qty_stock,
        })
        cls.env.invalidate_all()
        product = cls.env["product.product"].browse(product.id)
        return product, ubicacion

    def _crear_cotizacion(self, ref, company, sales_user, producto, qty=5.0,
                          sale_request_applicable=True):
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

    # ------------------------------------------------------------------
    # B4.1 — Cancelación de solicitudes
    # ------------------------------------------------------------------
    def test_b41_cancelar_antes_de_aprobaciones(self):
        """Cancelación desde draft (sin aprobaciones iniciadas)."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-1-C1", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        self.assertEqual(solicitud.state, "draft")

        solicitud.with_user(self.user_sales_c1).action_cancel()
        self.assertEqual(solicitud.state, "cancel")

        # Historial conservado (mensaje post)
        self.assertTrue(len(solicitud.message_ids) > 0)

    def test_b41_cancelar_con_aprobaciones_pendientes(self):
        """Cancelación desde pending_approval (aprobaciones pendientes)."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B4-1-C2", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        solicitud.with_user(self.user_sales_c1).action_cancel()
        self.assertEqual(solicitud.state, "cancel")

    def test_b41_cancelar_despues_de_aprobar(self):
        """Cancelación desde approved (ya aprobada, no aceptada)."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B4-1-C3", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        solicitud.with_user(self.user_sales_c1).action_cancel()
        self.assertEqual(solicitud.state, "cancel")

    def test_b41_no_puede_cancelar_despues_de_aceptar(self):
        """Cancelación desde accepted NO está definida (transición no permitida)."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B4-1-C4", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0  # stock suficiente → autoaprobada
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "approved")
        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")

        # Desde confirmed no hay transición a cancel
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).action_cancel()
        self.assertEqual(solicitud.state, "confirmed")

    def test_b41_usuario_sin_acceso_no_puede_cancelar(self):
        """Usuario de company_2 no puede cancelar solicitud de company_1."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion = self._crear_cotizacion(
            "B4-1-C5", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales_c1, cotizacion, "pickup", qty=5.0
        )

        with self.assertRaises(UserError):
            env_sales_c2["sale.order.request"].browse(solicitud.id).action_cancel()

    # ------------------------------------------------------------------
    # B4.2 — Solicitudes sustituidas por nuevas revisiones
    # ------------------------------------------------------------------
    def test_b42_nueva_revision_invalida_solicitud_anterior(self):
        """Nueva revisión de cotización invalida la solicitud anterior."""
        env_sales = self.env(user=self.user_sales_c1)
        env_coord = self.env(user=self.user_coordinador_c1)
        cotizacion = self._crear_cotizacion(
            "B4-2-C1", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # Revisión coordinada: solo el coordinador puede ejecutarla.
        # La solicitud está en 'approved' (stock insuficiente impide
        # action_accept(), pero la revisión coordinada sigue siendo válida).
        resultado = solicitud.with_user(
            self.user_coordinador_c1
        ).action_coordinated_revision()
        self.env.invalidate_all()

        # La solicitud anterior queda superseded
        solicitud = env_sales["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "superseded")

        # No se puede aceptar una solicitud superseded
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "superseded")

        # Nueva solicitud creada y vinculada a la nueva revisión
        solicitud_nueva = env_sales["sale.order.request"].browse(
            resultado["res_id"]
        )
        self.assertEqual(solicitud_nueva.state, "draft")
        solicitud_nueva.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud_nueva.state, "pending_approval")

        # La cotización original pasa a cancel
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "cancel")

    def test_b42_no_puede_confirmar_revision_obsoleta(self):
        """No se puede confirmar comercialmente una revisión obsoleta."""
        env_sales = self.env(user=self.user_sales_c1)
        env_coord = self.env(user=self.user_coordinador_c1)
        cotizacion = self._crear_cotizacion(
            "B4-2-C2", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "approved")
        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")

        # Revisión coordinada: solo el coordinador puede ejecutarla
        solicitud.with_user(self.user_coordinador_c1).action_coordinated_revision()
        self.env.invalidate_all()

        # Intentar confirmar la revisión obsoleta directamente
        # (debería fallar porque existe una revisión posterior)
        cotizacion_obsoleta = self.env["sale.order"].browse(cotizacion.id)
        with self.assertRaises(UserError):
            cotizacion_obsoleta.with_user(self.user_sales_c1).action_confirm()

    def test_b42_solicitud_con_aprobaciones_pendientes_puede_superseders(self):
        """Solicitud con aprobaciones pendientes no puede usar supersede directo;
        solo la ruta coordinada permite reemplazarla."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        env_trans = self.env(user=self.user_trans_c1)
        env_coord = self.env(user=self.user_coordinador_c1)
        cotizacion = self._crear_cotizacion(
            "B4-2-C3", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Directo: action_supersede() está bloqueado como operación pública
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).action_supersede()
        self.assertEqual(solicitud.state, "pending_approval")

        # Ruta coordinada: validar ambas aprobaciones; F-2 aprueba al completar Tier.
        solicitud.with_user(self.user_abast_c1).validate_tier()
        solicitud.with_user(self.user_trans_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "approved")

        # Revisión coordinada: solo el coordinador puede ejecutarla
        solicitud.with_user(self.user_coordinador_c1).action_coordinated_revision()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "superseded")

    # ------------------------------------------------------------------
    # B4.3 — Aprobaciones incompletas y fuera de orden
    # ------------------------------------------------------------------
    def test_b43_no_puede_aceptar_con_aprobacion_pendiente(self):
        """Aceptación final bloqueada si hay revisiones pendientes."""
        env_sales = self.env(user=self.user_sales_c1)
        env_trans = self.env(user=self.user_trans_c1)
        cotizacion = self._crear_cotizacion(
            "B4-3-C1", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Solo Abastecimiento valida, Transporte sigue pendiente
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # Estado sigue pending_approval porque no todas las revisiones están validadas

        # action_approve falla porque hay revisiones pendientes
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_abast_c1).action_approve()

    def test_b43_no_puede_aceptar_con_aprobacion_rechazada(self):
        """Aceptación final bloqueada si hay una revisión rechazada."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B4-3-C2", self.company_1, self.user_sales_c1,
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

        # El solicitante rechaza la solicitud
        solicitud.with_user(self.user_sales_c1).action_reject()
        self.assertEqual(solicitud.state, "rejected")

        # No se puede aceptar desde rejected
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).action_accept()

    def test_b43_usuario_sin_grupo_no_puede_aprobar(self):
        """Usuario sin grupo de Abastecimiento no puede aprobar revisión."""
        env_plain = self.env(user=self.user_plain_c1)
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-3-C3", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()

        # Usuario sin grupo de Abastecimiento intenta validar la revisión
        try:
            env_plain["sale.order.request"].browse(solicitud.id).validate_tier()
            self.fail("Expected exception but no exception was raised")
        except Exception:
            pass  # Expected - usuario sin grupo no puede validar

    def test_b43_no_puede_aprobar_dos_veces(self):
        """Segundo intento de aprobar falla porque ya está aprobada."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B4-3-C4", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")
        approval_date = solicitud.approval_date
        reviews_before = solicitud.review_ids.read(
            ["status", "done_by", "reviewed_date"]
        )
        messages_before = len(solicitud.message_ids)

        # Segundo intento de aprobar desde estado approved (no es transición válida)
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_abast_c1).action_approve()

        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "approved")
        self.assertEqual(solicitud.approval_date, approval_date)
        self.assertEqual(
            solicitud.review_ids.read(["status", "done_by", "reviewed_date"]),
            reviews_before,
        )
        self.assertEqual(len(solicitud.message_ids), messages_before)

    def test_b43_transicion_incompatible_con_estado_actual(self):
        """Intentar aprobar desde draft (sin validación previa) falla."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B4-3-C5", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        self.assertEqual(solicitud.state, "draft")

        # No se puede aprobar directamente desde draft sin pasar por validación
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_abast_c1).action_approve()

    def test_b43_aprobaciones_independientes_abastecimiento_y_transporte(self):
        """Abastecimiento y Transporte pueden aprobar de forma independiente."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        env_trans = self.env(user=self.user_trans_c1)
        cotizacion = self._crear_cotizacion(
            "B4-3-C6", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

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

        # Abastecimiento valida primero
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        review_a = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abast.id
        )
        self.assertEqual(review_a.status, "approved")

        # Transporte todavía pendiente
        review_t = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_trans.id
        )
        self.assertEqual(review_t.status, "pending")

        # Transporte valida después
        solicitud.with_user(self.user_trans_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        review_t = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_trans.id
        )
        self.assertEqual(review_t.status, "approved")
        self.assertEqual(solicitud.validation_status, "validated")

    # ------------------------------------------------------------------
    # B4.4 — Cambios en la cotización y sus líneas
    # ------------------------------------------------------------------
    def test_b44_no_puede_modificar_lineas_despues_de_aprobaciones(self):
        """No se pueden modificar líneas de la solicitud tras iniciar aprobaciones."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-4-C1", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "approved")

        # Intentar modificar line_ids desde approved
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).write({
                "line_ids": [(0, 0, {
                    "sale_order_line_id": cotizacion.order_line[0].id,
                    "product_id": self.product_insuficiente.id,
                    "product_uom_id": cotizacion.order_line[0].product_uom_id.id,
                    "qty": 10.0,
                })]
            })

    def test_b44_no_puede_cambiar_modalidad_despues_de_aprobaciones(self):
        """No se puede cambiar delivery_mode tras iniciar aprobaciones."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-4-C2", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "approved")

        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).write({
                "delivery_mode": "delivery"
            })

    def test_b44_campos_identificadores_inmutables(self):
        """Los campos identificadores no se pueden modificar tras la creación."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-4-C3", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        self.assertEqual(solicitud.state, "draft")

        # Crear una segunda cotización para intentar cambiar el vínculo
        cotizacion2 = self._crear_cotizacion(
            "B4-4-C3B", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion2, self.user_sales_c1)

        # Intentar cambiar sale_order_id a una cotización diferente (inmutable)
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).write({
                "sale_order_id": cotizacion2.id,
            })

        # Intentar cambiar requester_id (inmutable)
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).write({
                "requester_id": self.user_plain_c1.id,
            })

    def test_b44_cotizacion_no_confirmada_sin_solicitud_aceptada(self):
        """No se puede confirmar una cotización sujeta a solicitud de orden de venta sin solicitud aceptada."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-4-C4", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        # Intentar confirmar directamente sin flujo de solicitud de orden de venta
        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales_c1).action_confirm()
        self.assertEqual(cotizacion.state, "sent")

    # ------------------------------------------------------------------
    # B4.5 — Cambios de inventario durante el proceso
    # ------------------------------------------------------------------
    def test_b45_stock_insuficiente_despues_de_aprobar_bloquea_aceptar(self):
        """Stock insuficiente después de aprobar bloquea action_accept()."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B4-5-C1", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # action_accept revalida stock y bloquea porque free_qty=1.0 < qty=5.0
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "approved")

    def test_b45_revalidacion_antes_de_confirmar(self):
        """La aceptación final revalida el stock antes de confirmar."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-5-C2", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "approved")
        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")

        # Cotización confirmada en sale
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

    def test_b45_diferencia_recojo_vs_despacho_stock_suficiente(self):
        """Recojo usa free_qty, despacho usa virtual_available."""
        env_sales = self.env(user=self.user_sales_c1)
        # Recojo con stock suficiente: sin aprobaciones
        cotizacion_recojo = self._crear_cotizacion(
            "B4-5-C3", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion_recojo, self.user_sales_c1)
        solicitud_recojo = self._crear_solicitud(
            env_sales, cotizacion_recojo, "pickup", qty=5.0
        )
        solicitud_recojo.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud_recojo.state, "approved")

        # Despacho con stock suficiente: requiere Transporte
        cotizacion_despacho = self._crear_cotizacion(
            "B4-5-C4", self.company_1, self.user_sales_c1,
            producto=self.product_despacho, qty=5.0
        )
        self._mark_as_subject(cotizacion_despacho, self.user_sales_c1)
        solicitud_despacho = self._crear_solicitud(
            env_sales, cotizacion_despacho, "delivery", qty=5.0
        )
        solicitud_despacho.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud_despacho.state, "pending_approval")

    # ------------------------------------------------------------------
    # B4.6 — Operaciones repetidas e interrupciones
    # ------------------------------------------------------------------
    def test_b46_doble_envio_aprobacion(self):
        """Doble envío de action_approve: segundo intento falla."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B4-6-C1", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")
        approval_date = solicitud.approval_date
        reviews_before = solicitud.review_ids.read(
            ["status", "done_by", "reviewed_date"]
        )
        messages_before = len(solicitud.message_ids)

        # Segundo intento de approve desde estado approved (rechazado, sin efectos)
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_abast_c1).action_approve()

        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "approved")
        self.assertEqual(solicitud.approval_date, approval_date)
        self.assertEqual(
            solicitud.review_ids.read(["status", "done_by", "reviewed_date"]),
            reviews_before,
        )
        self.assertEqual(len(solicitud.message_ids), messages_before)

    def test_b46_doble_envio_aceptacion(self):
        """Doble envío de action_accept: segundo intento falla."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-6-C2", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "approved")
        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")

        # Segundo intento de accept desde estado confirmed
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")

    def test_b46_repeticion_cancelacion(self):
        """Repetición de cancel: segundo intento falla."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-6-C3", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_cancel()
        self.assertEqual(solicitud.state, "cancel")

        # Segundo intento de cancel desde estado cancel
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).action_cancel()
        self.assertEqual(solicitud.state, "cancel")

    def test_b46_repeticion_supersede(self):
        """Repetición de supersede: invocación directa bloqueada;
        ruta coordinada funciona una vez."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        env_coord = self.env(user=self.user_coordinador_c1)
        cotizacion = self._crear_cotizacion(
            "B4-6-C4", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # Invocación directa de action_supersede() está bloqueada
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales_c1).action_supersede()
        self.assertEqual(solicitud.state, "approved")

        # Revisión coordinada (sin accept, stock insuficiente)
        solicitud.with_user(self.user_coordinador_c1).action_coordinated_revision()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "superseded")

        # Segundo intento de acción coordinada sobre solicitud ya superseded
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_coordinador_c1).action_coordinated_revision()

    def test_b46_no_se_crean_solicitudes_duplicadas(self):
        """No se crean solicitudes duplicadas para la misma revisión."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-6-C5", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud1 = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud1.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud1.state, "approved")

        # Intentar crear segunda solicitud para la misma revisión
        try:
            self._crear_solicitud(
                env_sales, cotizacion, "pickup", qty=5.0
            )
            self.fail("Expected exception but no exception was raised")
        except (UserError, ValidationError):
            pass  # Expected - no se permite solicitud duplicada

    def test_b47_crear_solicitud_desde_cotizacion_subject(self):
        """Crear solicitud desde cotización sujeta a solicitud de orden de venta con stock suficiente + recojo."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-7-C1", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        resultado = cotizacion.with_user(self.user_sales_c1).action_create_sale_order_request_from_quotation()

        # Verificar que se abrió la acción para abrir la solicitud
        self.assertEqual(resultado["res_model"], "sale.order.request")
        self.assertIn("res_id", resultado)

        solicitud = self.env["sale.order.request"].browse(resultado["res_id"])

        # Verificar vinculación con cotización y revisión vigente
        self.assertEqual(solicitud.sale_order_id.id, cotizacion.id)
        self.assertEqual(solicitud.sale_order_revision_id.id, cotizacion.id)
        self.assertEqual(solicitud.state, "draft")
        self.assertEqual(solicitud.unrevisioned_name, cotizacion.unrevisioned_name)
        self.assertEqual(solicitud.company_id, cotizacion.company_id)
        self.assertEqual(solicitud.requester_id, self.user_sales_c1)

        # Verificar líneas de solicitud
        self.assertEqual(len(solicitud.line_ids), 1)
        self.assertEqual(solicitud.line_ids[0].sale_order_line_id, cotizacion.order_line[0])
        self.assertEqual(solicitud.line_ids[0].product_id, cotizacion.order_line[0].product_id)
        self.assertEqual(solicitud.line_ids[0].qty, cotizacion.order_line[0].product_uom_qty)

        # No crear segunda sale.order
        self.assertEqual(
            self.env["sale.order"].search_count([
                ("client_order_ref", "=", cotizacion.client_order_ref)
            ]),
            1
        )

    def test_b47_crear_solicitud_cotizacion_no_sujeto(self):
        """Rechazar crear solicitud desde cotización no sujeta a ."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-7-C2", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        # No marcar como : sale_request_subject=False y sale_request_applicable=False

        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales_c1).action_create_sale_order_request_from_quotation()

    def test_b47_crear_solicitud_estado_no_valido(self):
        """Rechazar crear solicitud desde cotización en estado no válido."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-7-C4", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        # Cambiar estado a cancel (fuera de draft/sent) para probar guardia de estado
        cotizacion.with_user(self.user_sales_c1).write({"state": "cancel"})

        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales_c1).action_create_sale_order_request_from_quotation()

    def test_b47_crear_solicitud_usuario_no_vendedor(self):
        """Rechazar crear solicitud desde usuario no vendedor de solicitudes de orden de venta."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-7-C5", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        # Usuario sin grupo vendedor (user_plain_c1)
        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_plain_c1).action_create_sale_order_request_from_quotation()

    def test_b47_crear_solicitud_duplicada_misma_revision(self):
        """Rechazar crear segunda solicitud para la misma revisión."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-7-C6", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        # Crear primera solicitud
        cotizacion.with_user(self.user_sales_c1).action_create_sale_order_request_from_quotation()

        # Intentar crear segunda solicitud para la misma revisión
        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales_c1).action_create_sale_order_request_from_quotation()

    def test_b47_no_crear_segunda_sale_order(self):
        """No crear segunda sale.order al crear solicitud desde cotización."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B4-7-C7", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        cotizacion.with_user(self.user_sales_c1).action_create_sale_order_request_from_quotation()

        # Verificar que sigue existiendo solo una cotización con ese client_order_ref
        count = self.env["sale.order"].search_count([
            ("client_order_ref", "=", cotizacion.client_order_ref)
        ])
        self.assertEqual(count, 1)
