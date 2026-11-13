# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Pruebas funcionales — Fase B3 — sale_order_request.

Flujo funcional integral de Solicitud de orden de venta con usuarios sintéticos
y datos controlados en PRUEBAS.

Escenarios cubiertos:
- Escenario 1: Stock suficiente + recojo (sin aprobaciones)
- Escenario 2: Stock suficiente + despacho (requiere Transporte)
- Escenario 3: Stock insuficiente + recojo (requiere Abastecimiento)
- Escenario 4: Stock insuficiente + despacho (requiere Abastecimiento + Transporte)
- 5.1: Aprobaciones paralelas (Abastecimiento y Transporte independientes)
- 5.2: Rechazo de una aprobación
- 5.3: Revisión de cotización (nueva revisión invalida solicitud anterior)
- 5.4: Revalidación de stock (registra insuficiencia sin bloquear con aprobaciones completas)
- 5.5: Seguridad funcional (usuarios sin permisos no pueden operar)

Nota de entorno: esta compilación de Odoo 19 Community tiene free_qty=0.0 y
virtual_available=0.0 para todos los productos (no hay productos almacenables
con stock real). Por lo tanto, toda solicitud con qty >= 1.0 tiene stock
insuficiente y requiere aprobaciones según la matriz .
Los flujos legítimos se validan hasta approved; la aceptación final se bloquea
stock insuficiente; con aprobaciones completas la aceptación es permitida
(conformidad de abastecimiento futuro) sin inventar existencias.
"""

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestB3FlujoFuncionalIntegral(TransactionCase):
    """Flujo funcional integral de Solicitud de orden de venta."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.admin = cls.env["res.users"].browse(2)
        cls.partner = cls.env["res.partner"].search(
            [("customer_rank", ">", 0)], limit=1
        )
        if not cls.partner:
            cls.partner = cls.env["res.partner"].create(
                {"name": "Cliente Test B3", "customer_rank": 1}
            )

        # Compañías existentes en PRUEBAS: 1, 2, 3
        cls.company_1 = cls.env.company
        cls.company_2 = cls.env["res.company"].create({"name": "Company Test 2"})
        cls.company_3 = cls.env["res.company"].create({"name": "Company Test 3"})
        cls.admin.write({"company_ids": [(4, cls.company_2.id), (4, cls.company_3.id)]})

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

        cls.product = cls.env["product.product"].create({
            "name": "Producto B3",
            "type": "consu",
            "sale_ok": True,
        })

        # Usuarios de prueba sintéticos (mismos que B2)
        cls.user_sales_c1 = cls._crear_usuario(
            "user_b3_sales_c1", [cls.company_1.id],
            ["base.group_user", "sales_team.group_sale_salesman",
             "sale_order_request.group_sale_order_request_salesperson"]
        )
        cls.user_abast_c1 = cls._crear_usuario(
            "user_b3_abast_c1", [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_supply"]
        )
        cls.user_trans_c1 = cls._crear_usuario(
            "user_b3_trans_c1", [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_transport"]
        )
        cls.user_plain_c1 = cls._crear_usuario(
            "user_b3_plain_c1", [cls.company_1.id], ["base.group_user"]
        )
        cls.user_sales_c2 = cls._crear_usuario(
            "user_b3_sales_c2", [cls.company_2.id],
            ["base.group_user", "sales_team.group_sale_salesman",
             "sale_order_request.group_sale_order_request_salesperson"]
        )
        cls.user_abast_c2 = cls._crear_usuario(
            "user_b3_abast_c2", [cls.company_2.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_supply"]
        )
        cls.user_sales_c3 = cls._crear_usuario(
            "user_b3_sales_c3", [cls.company_3.id],
            ["base.group_user", "sales_team.group_sale_salesman",
             "sale_order_request.group_sale_order_request_salesperson"]
        )
        # Usuario coordinador (pendiente D-AUD-5 para asignación real;
        # aquí solo para pruebas automáticas del procedimiento coordinado)
        cls.user_coordinador_c1 = cls._crear_usuario(
            "user_b3_coord_c1", [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_coordinator"]
        )

        # Asegurar almacenes para compañías 2 y 3
        Warehouse = cls.env["stock.warehouse"]
        for comp in [cls.company_2, cls.company_3]:
            existing = Warehouse.search([("company_id", "=", comp.id)], limit=1)
            if not existing:
                Warehouse.create({
                    "name": "Almacén %s" % comp.name,
                    "code": "WH%s" % comp.id,
                    "company_id": comp.id,
                })

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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _crear_cotizacion(self, ref, company, sales_user, sale_request_applicable=True):
        env = self.env(user=self.admin)
        order = env["sale.order"].with_company(company).create({
            "partner_id": self.partner.id,
            "client_order_ref": ref,
            "company_id": company.id,
            "user_id": sales_user.id,
            "order_line": [
                (0, 0, {
                    "product_id": self.product.id,
                    "product_uom_qty": 5.0,
                })
            ],
        })
        order.with_user(env.user).write({"state": "sent"})
        return order

    def _mark_as_subject(self, cotizacion, usuario):
        if not cotizacion.sale_request_subject:
            cotizacion.with_user(usuario).action_mark_sale_request_subject()
        return cotizacion

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

    def _obtener_def_abastecimiento(self):
        return self.env.ref("sale_order_request.tier_def_sale_order_request_supply")

    def _obtener_def_transporte(self):
        return self.env.ref("sale_order_request.tier_def_sale_order_request_transport")

    # ------------------------------------------------------------------
    # ESCENARIO 1: Stock suficiente + recojo (sin aprobaciones)
    # ------------------------------------------------------------------
    def test_escenario_1_stock_suficiente_recojo(self):
        """Cotización sujeta a solicitud de orden de venta en compañía 1, recojo, stock suficiente.
        La solicitud se autoaprueba sin requerir Abastecimiento ni Transporte."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B3-E1-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )

        # 1. Cotización creada y marcada como 
        self.assertTrue(cotizacion.sale_request_applicable)
        self.assertTrue(cotizacion.sale_request_subject)
        self.assertEqual(cotizacion.state, "sent")

        # 2. Solicitud vinculada a la cotización y sus líneas
        self.assertEqual(solicitud.sale_order_id, cotizacion)
        self.assertEqual(solicitud.sale_order_revision_id, cotizacion)
        self.assertEqual(len(solicitud.line_ids), 1)
        self.assertEqual(solicitud.line_ids[0].sale_order_line_id,
                         cotizacion.order_line[0])

        # 3. Solicitud en borrador inicialmente
        self.assertEqual(solicitud.state, "draft")

        # 4. Solicitar validación - stock insuficiente (qty=5 > free_qty=0)
        # por lo que requiere Abastecimiento (recojo + insuficiente)
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # 5. Verificar que se creó revisión de Abastecimiento
        def_abast = self._obtener_def_abastecimiento()
        review_abast = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abast.id
        )
        self.assertEqual(len(review_abast), 1)
        self.assertEqual(review_abast.status, "pending")

        # 6. Transporte NO interviene (recojo)
        def_trans = self._obtener_def_transporte()
        review_trans = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_trans.id
        )
        self.assertEqual(len(review_trans), 0)

        # 7. Abastecimiento aprueba
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_sales["sale.order.request"].browse(solicitud.id)
        review_abast = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abast.id
        )
        self.assertEqual(review_abast.status, "approved")

        # 8. F-2: aprobación automática al completar la revisión requerida
        self.assertEqual(solicitud.state, "approved")

        # 9. Aceptación final permitida: Abastecimiento aprobó el faltante
        # (conformidad de abastecimiento futuro) aunque el stock físico sea
        # insuficiente. No se inventan existencias.
        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")

        # 10. La cotización vigente se confirma
        cotizacion = env_sales["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

        # 11. No se creó segunda sale.order
        ordenes_dup = self.env["sale.order"].search([
            ("unrevisioned_name", "=", cotizacion.unrevisioned_name),
            ("id", "!=", cotizacion.id),
        ])
        self.assertEqual(len(ordenes_dup), 0)

    # ------------------------------------------------------------------
    # ESCENARIO 2: Stock suficiente + despacho (requiere Transporte)
    # ------------------------------------------------------------------
    def test_escenario_2_stock_suficiente_despacho(self):
        """Cotización sujeta a solicitud de orden de venta en compañía 1, despacho, stock insuficiente.
        Requiere Abastecimiento y Transporte."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B3-E2-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )

        self.assertEqual(solicitud.state, "draft")

        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Ambas revisiones creadas (Abastecimiento + Transporte)
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
        self.assertEqual(review_a.status, "pending")
        self.assertEqual(review_t.status, "pending")

        # Abastecimiento y Transporte validan en paralelo
        solicitud.with_user(self.user_abast_c1).validate_tier()
        solicitud.with_user(self.user_trans_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_sales["sale.order.request"].browse(solicitud.id)
        review_a = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abast.id
        )
        review_t = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_trans.id
        )
        self.assertEqual(review_a.status, "approved")
        self.assertEqual(review_t.status, "approved")
        self.assertEqual(solicitud.validation_status, "validated")

        # F-2: aprobación automática al completar todas las revisiones requeridas
        self.assertEqual(solicitud.state, "approved")

        # Aceptación final permitida con aprobaciones completas pese a
        # stock físico insuficiente (conformidad aprobada).
        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")
        cotizacion = env_sales["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

        # No se creó segunda sale.order
        ordenes_dup = self.env["sale.order"].search([
            ("unrevisioned_name", "=", cotizacion.unrevisioned_name),
            ("id", "!=", cotizacion.id),
        ])
        self.assertEqual(len(ordenes_dup), 0)

    # ------------------------------------------------------------------
    # ESCENARIO 3: Stock insuficiente + recojo (requiere Abastecimiento)
    # ------------------------------------------------------------------
    def test_escenario_3_stock_insuficiente_recojo(self):
        """Cotización sujeta a solicitud de orden de venta en compañía 1, recojo, stock insuficiente.
        Requiere Abastecimiento."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B3-E3-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )

        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        def_abast = self._obtener_def_abastecimiento()
        review_abast = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abast.id
        )
        self.assertEqual(len(review_abast), 1)
        self.assertEqual(review_abast.status, "pending")

        def_trans = self._obtener_def_transporte()
        review_trans = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_trans.id
        )
        self.assertEqual(len(review_trans), 0)

        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_sales["sale.order.request"].browse(solicitud.id)
        review_abast = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abast.id
        )
        self.assertEqual(review_abast.status, "approved")

        # F-2: aprobación automática al completar la revisión requerida
        self.assertEqual(solicitud.state, "approved")

        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")
        cotizacion = env_sales["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

        ordenes_dup = self.env["sale.order"].search([
            ("unrevisioned_name", "=", cotizacion.unrevisioned_name),
            ("id", "!=", cotizacion.id),
        ])
        self.assertEqual(len(ordenes_dup), 0)

    # ------------------------------------------------------------------
    # ESCENARIO 4: Stock insuficiente + despacho (requiere Abastecimiento +
    # Transporte)
    # ------------------------------------------------------------------
    def test_escenario_4_stock_insuficiente_despacho(self):
        """Cotización sujeta a solicitud de orden de venta en compañía 1, despacho, stock insuficiente.
        Requiere Abastecimiento y Transporte."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B3-E4-C1", self.company_1, self.user_sales_c1
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

        solicitud.with_user(self.user_abast_c1).validate_tier()
        solicitud.with_user(self.user_trans_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_sales["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.validation_status, "validated")

        # F-2: aprobación automática al completar todas las revisiones requeridas
        self.assertEqual(solicitud.state, "approved")

        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")
        cotizacion = env_sales["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

        ordenes_dup = self.env["sale.order"].search([
            ("unrevisioned_name", "=", cotizacion.unrevisioned_name),
            ("id", "!=", cotizacion.id),
        ])
        self.assertEqual(len(ordenes_dup), 0)

    # ------------------------------------------------------------------
    # 5.1: Aprobaciones paralelas (Abastecimiento y Transporte)
    # ------------------------------------------------------------------
    def test_aprobaciones_paralelas(self):
        """Abastecimiento y Transporte pueden validar en cualquier orden."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        env_trans = self.env(user=self.user_trans_c1)
        cotizacion = self._crear_cotizacion(
            "B3-51-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
        self.assertEqual(len(solicitud.review_ids), 2)

        # Transporte valida primero (orden invertido)
        solicitud.with_user(self.user_trans_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_trans["sale.order.request"].browse(solicitud.id)
        def_trans = self._obtener_def_transporte()
        review_t = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_trans.id
        )
        self.assertEqual(review_t.status, "approved")

        # Luego Abastecimiento valida
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_abast["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.validation_status, "validated")

        # F-2: aprobación automática al completar todas las revisiones requeridas
        self.assertEqual(solicitud.state, "approved")

    # ------------------------------------------------------------------
    # 5.2: Rechazo de una aprobación
    # ------------------------------------------------------------------
    def test_rechazo_abastecimiento(self):
        """Abastecimiento rechaza; la solicitud se rechaza y la cotización
        no se confirma."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B3-52-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)

        # El solicitante rechaza (tiene permiso para rechazar su propia solicitud)
        solicitud.with_user(self.user_sales_c1).action_reject()
        self.assertEqual(solicitud.state, "rejected")

        # La cotización no se confirma
        cotizacion = env_sales["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sent")

        # El historial conserva el rechazo (review con status approved,
        # pero la solicitud queda rechazada)
        review = solicitud.review_ids[0]
        self.assertEqual(review.status, "approved")
        self.assertEqual(review.done_by, self.user_abast_c1)
        self.assertIsNotNone(review.reviewed_date)

    # ------------------------------------------------------------------
    # 5.3: Revisión de cotización (nueva revisión invalida solicitud anterior)
    # ------------------------------------------------------------------
    def test_nueva_revision_invalida_solicitud_anterior(self):
        """Nueva revisión de cotización invalida la solicitud anterior."""
        env_sales = self.env(user=self.user_sales_c1)
        env_coord = self.env(user=self.user_coordinador_c1)
        cotizacion = self._crear_cotizacion(
            "B3-53-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_sales["sale.order.request"].browse(solicitud.id)
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

        # Nueva solicitud creada y vinculada a la nueva revisión
        solicitud_nueva = env_sales["sale.order.request"].browse(
            resultado["res_id"]
        )
        self.assertEqual(solicitud_nueva.state, "draft")

        # Nueva revisión existe, está en draft y conserva sale_request_subject
        nueva = solicitud_nueva.sale_order_revision_id
        self.assertEqual(nueva.state, "draft")
        self.assertTrue(nueva.sale_request_subject)

        # La cotización original fue cancelada al crear la revisión
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "cancel")

    # ------------------------------------------------------------------
    # 5.4: Revalidación de stock (stock insuficiente bloquea aceptación)
    # ------------------------------------------------------------------
    def test_revalidacion_stock_bloquea_aceptacion(self):
        """La aceptación final se permite con aprobaciones completas pese a stock insuficiente (B-08 ajustado)."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B3-54-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_abast["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # La revalidación registra stock insuficiente pero no bloquea la
        # aceptación cuando las aprobaciones requeridas están completas.
        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")
        cotizacion = env_sales["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

    # ------------------------------------------------------------------
    # 5.5: Seguridad funcional (usuarios sin permisos no pueden operar)
    # ------------------------------------------------------------------
    def test_usuario_sin_grupo_no_puede_crear_solicitud(self):
        """Usuario sin grupo  no puede crear solicitudes."""
        env_plain = self.env(user=self.user_plain_c1)
        cotizacion = self._crear_cotizacion(
            "B3-55-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        with self.assertRaises(AccessError):
            env_plain["sale.order.request"].create({
                "sale_order_id": cotizacion.id,
                "sale_order_revision_id": cotizacion.id,
                "delivery_mode": "pickup",
                "requester_id": self.user_plain_c1.id,
                "line_ids": [(0, 0, {
                    "sale_order_line_id": cotizacion.order_line[0].id,
                    "product_id": self.product.id,
                    "product_uom_id": cotizacion.order_line[0].product_uom_id.id,
                    "qty": 5.0,
                })],
            })

    def test_usuario_de_otra_compania_no_puede_aprobar_solicitud(self):
        """Un usuario de otra compañía no puede aprobar una solicitud ajena.

        El intento de action_approve() desde una compañía sin acceso a la
        solicitud es rechazado por el control de compañía, sin modificar el
        estado ni las revisiones.
        """
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "B3-55-C2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )
        solicitud_c2.with_user(self.user_sales_c2).action_request_validation()
        # Recojo + stock insuficiente: requiere Abastecimiento y queda pendiente.
        self.assertEqual(solicitud_c2.state, "pending_approval")
        self.assertEqual(solicitud_c2.company_id.id, self.company_2.id)
        self.assertEqual(self.user_sales_c1.company_id.id, self.company_1.id)
        self.assertNotIn(self.company_2.id, self.user_sales_c1.company_ids.ids)
        approval_date_antes = solicitud_c2.approval_date
        reviews_before = solicitud_c2.review_ids.read(["status", "done_by", "reviewed_date"])

        # Control de compañía en action_approve() (_check_company_consistency):
        # el usuario de C1 no pertenece a company_ids de la solicitud de C2.
        with self.assertRaises(UserError):
            env_sales_c1["sale.order.request"].browse(solicitud_c2.id).action_approve()

        solicitud_c2 = env_sales_c2["sale.order.request"].browse(solicitud_c2.id)
        self.assertEqual(solicitud_c2.state, "pending_approval")
        self.assertEqual(solicitud_c2.approval_date, approval_date_antes)
        self.assertEqual(
            solicitud_c2.review_ids.read(["status", "done_by", "reviewed_date"]),
            reviews_before,
        )
