# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Pruebas funcionales — Fase B3 (stock real) — sale_order_request.

Verifica los cuatro escenarios de la matriz de aprobaciones con productos
almacenables y stock real mediante stock.quant en PRUEBAS.

Diagnóstico clave: free_qty es company-dependiente. stock.quant.company_id se
deriva de stock.location.company_id. Por tanto, se debe crear el quant en una
ubicación cuya compañía coincida con el contexto de empresa usado al consultar
free_qty.

Escenarios cubiertos:
- Escenario 1: Stock suficiente + recojo → sin aprobaciones, aceptación directa
- Escenario 2: Stock suficiente + despacho → solo Transporte, aceptación directa
- Escenario 3: Stock insuficiente + recojo → Abastecimiento, aceptación bloqueada
- Escenario 4: Stock insuficiente + despacho → Abastecimiento + Transporte, aceptación bloqueada
- 5.2: Rechazo de Abastecimiento y Transporte
- 5.3: Nueva revisión invalida solicitud anterior
- 5.4: Revalidación de stock no bloquea con aprobaciones completas
- 5.5: Seguridad funcional (sin grupo, empresa diferente)

Nota: En esta compilación Odoo 19 Community, los productos tipo consu con
is_storable=True permiten registrar stock.quant. free_qty es > 0 solo cuando
el quant.company_id coincide con el company_ctx de la consulta.
"""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestB3FlujoFuncionalStockReal(TransactionCase):
    """Flujo funcional integral de Solicitud de orden de venta con stock real."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.admin = cls.env["res.users"].browse(2)
        cls.partner = cls.env["res.partner"].search(
            [("customer_rank", ">", 0)], limit=1
        )
        if not cls.partner:
            cls.partner = cls.env["res.partner"].create(
                {"name": "Cliente Test B3SR", "customer_rank": 1}
            )

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

        # Crear productos almacenables con stock real en ubicación de company 1
        cls.product_recojo, _ = cls._crear_producto_almacenable(
            "Producto B3 Recojo", qty_stock=50.0, company=cls.company_1
        )
        cls.product_despacho, _ = cls._crear_producto_almacenable(
            "Producto B3 Despacho", qty_stock=50.0, company=cls.company_1
        )
        cls.product_insuficiente, _ = cls._crear_producto_almacenable(
            "Producto B3 Insuficiente", qty_stock=1.0, company=cls.company_1
        )

        # Usuarios de prueba sintéticos
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
        # Usuario coordinador para pruebas del procedimiento coordinado
        cls.user_coordinador_c1 = cls._crear_usuario(
            "user_b3_coord_c1", [cls.company_1.id],
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
        """Crea un producto almacenable (consu + is_storable) y registra
        stock real vía stock.quant en ubicación interna de la compañía dada.

        IMPORTANTE: stock.quant.company_id se deriva de location.company_id,
        no se puede forzar en el create. Debe usarse una ubicación cuya
        company_id coincida con la compañía del producto para que free_qty
        sea visible desde el contexto de esa compañía.
        """
        company = company or cls.company_1
        template = cls.env["product.template"].create({
            "name": nombre,
            "type": "consu",
            "is_storable": True,
            "sale_ok": True,
            "company_id": company.id,
        })
        product = template.product_variant_ids[0]
        # Ubicación interna de la misma compañía
        ubicacion = cls.env["stock.location"].search(
            [("usage", "=", "internal"), ("company_id", "=", company.id)],
            limit=1
        )
        if not ubicacion:
            # Fallback: usar el lote de stock del almacén de la compañía
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
    # ESCENARIO 1: Stock suficiente + recojo → sin aprobaciones
    # ------------------------------------------------------------------
    def test_escenario_1_stock_suficiente_rejo(self):
        """Cotización sujeta a solicitud de orden de venta, recojo, stock suficiente → sin aprobaciones,
        aceptación final, cotización confirmada en sale."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B3-E1-C1", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )

        # Verificar identificaciones
        self.assertTrue(cotizacion.sale_request_applicable)
        self.assertTrue(cotizacion.sale_request_subject)
        self.assertEqual(solicitud.sale_order_id, cotizacion)
        self.assertEqual(solicitud.sale_order_revision_id, cotizacion)
        self.assertEqual(len(solicitud.line_ids), 1)
        self.assertEqual(solicitud.line_ids[0].sale_order_line_id,
                         cotizacion.order_line[0])
        self.assertEqual(solicitud.state, "draft")
        self.assertTrue(solicitud.line_ids[0].stock_sufficient,
                        "Stock suficiente: qty=5.0 <= free_qty=50.0")

        # Solicitar validación: stock suficiente + recojo → sin aprobaciones
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "approved",
                         "Stock suficiente + recojo → sin aprobaciones")

        # Verificación: no hay revisiones de Tier
        self.assertEqual(len(solicitud.review_ids), 0)

        # Aceptación final por el vendedor
        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")

        # Cotización confirmada y en estado sale
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

        # No se creó segunda sale.order
        ordenes_dup = self.env["sale.order"].search([
            ("unrevisioned_name", "=", cotizacion.unrevisioned_name),
            ("id", "!=", cotizacion.id),
        ])
        self.assertEqual(len(ordenes_dup), 0,
                         "No se debe crear una segunda sale.order")

    # ------------------------------------------------------------------
    # ESCENARIO 2: Stock suficiente + despacho → solo Transporte
    # ------------------------------------------------------------------
    def test_escenario_2_stock_suficiente_despacho(self):
        """Cotización sujeta a solicitud de orden de venta, despacho, stock suficiente → solo Transporte."""
        env_sales = self.env(user=self.user_sales_c1)
        env_trans = self.env(user=self.user_trans_c1)
        cotizacion = self._crear_cotizacion(
            "B3-E2-C1", self.company_1, self.user_sales_c1,
            producto=self.product_despacho, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )

        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Solo Transporte interviene (despacho + stock suficiente)
        def_trans = self._obtener_def_transporte()
        review_t = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_trans.id
        )
        self.assertEqual(len(review_t), 1)
        self.assertEqual(review_t.status, "pending")

        def_abast = self._obtener_def_abastecimiento()
        review_a = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abast.id
        )
        self.assertEqual(len(review_a), 0)

        # Transporte valida y aprueba
        solicitud.with_user(self.user_trans_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_trans["sale.order.request"].browse(solicitud.id)
        review_t = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_trans.id
        )
        self.assertEqual(review_t.status, "approved")

        # F-2: aprobación automática al completar la revisión requerida (solo Transporte).
        self.assertEqual(solicitud.state, "approved")

        # Aceptación final por el vendedor
        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")

        # Cotización confirmada y en estado sale
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

        # No se creó segunda sale.order
        ordenes_dup = self.env["sale.order"].search([
            ("unrevisioned_name", "=", cotizacion.unrevisioned_name),
            ("id", "!=", cotizacion.id),
        ])
        self.assertEqual(len(ordenes_dup), 0,
                         "No se debe crear una segunda sale.order")

    # ------------------------------------------------------------------
    # ESCENARIO 3: Stock insuficiente + recojo → Abastecimiento
    # ------------------------------------------------------------------
    def test_escenario_3_stock_insuficiente_rejo(self):
        """Cotización sujeta a solicitud de orden de venta, recojo, stock insuficiente → Abastecimiento."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B3-E3-C1", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)

        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )

        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Solo Abastecimiento interviene (rejo + insuficiente)
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

        # Abastecimiento valida y aprueba
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_sales["sale.order.request"].browse(solicitud.id)
        review_abast = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abast.id
        )
        self.assertEqual(review_abast.status, "approved")

        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # Aceptación final permitida con aprobaciones completas pese a stock insuficiente
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
    # ESCENARIO 4: Stock insuficiente + despacho → Abastecimiento + Transporte
    # ------------------------------------------------------------------
    def test_escenario_4_stock_insuficiente_despacho(self):
        """Cotización sujeta a solicitud de orden de venta, despacho, stock insuficiente → Abastecimiento +
        Transporte."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        env_trans = self.env(user=self.user_trans_c1)
        cotizacion = self._crear_cotizacion(
            "B3-E4-C1", self.company_1, self.user_sales_c1,
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
        self.assertEqual(review_a.status, "pending")
        self.assertEqual(review_t.status, "pending")

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

        # F-2: aprobación automática al completar todas las revisiones requeridas.
        self.assertEqual(solicitud.state, "approved")

        # Aceptación final permitida con aprobaciones completas pese a stock insuficiente
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
    # 5.2: Rechazo de Abastecimiento y Transporte
    # ------------------------------------------------------------------
    def test_rechazo_abastecimiento(self):
        """Abastecimiento rechaza; la solicitud se rechaza y la cotización
        no se confirma."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B3-52-C1", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_abast["sale.order.request"].browse(solicitud.id)

        solicitud.with_user(self.user_sales_c1).action_reject()
        self.assertEqual(solicitud.state, "rejected")

        cotizacion = env_sales["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sent")

        review = solicitud.review_ids[0]
        self.assertEqual(review.status, "approved")
        self.assertEqual(review.done_by, self.user_abast_c1)
        self.assertIsNotNone(review.reviewed_date)

    def test_rechazo_transporte(self):
        """Transporte rechaza; la solicitud se rechaza y la cotización
        no se confirma."""
        env_sales = self.env(user=self.user_sales_c1)
        env_trans = self.env(user=self.user_trans_c1)
        cotizacion = self._crear_cotizacion(
            "B3-52-C2", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        solicitud.with_user(self.user_trans_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_trans["sale.order.request"].browse(solicitud.id)

        solicitud.with_user(self.user_sales_c1).action_reject()
        self.assertEqual(solicitud.state, "rejected")

        cotizacion = env_sales["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sent")

        review = solicitud.review_ids[0]
        self.assertEqual(review.status, "approved")
        self.assertEqual(review.done_by, self.user_trans_c1)
        self.assertIsNotNone(review.reviewed_date)

    # ------------------------------------------------------------------
    # 5.3: Nueva revisión invalida solicitud anterior
    # ------------------------------------------------------------------
    def test_nueva_revision_invalida_solicitud_anterior(self):
        # Usar producto con stock insuficiente para obtener el flujo
        # pending_approval → approved → confirmed (necesario para revisión
        # coordinada)
        env_sales = self.env(user=self.user_sales_c1)
        env_coord = self.env(user=self.user_coordinador_c1)
        cotizacion = self._crear_cotizacion(
            "B3-53-C1", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
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
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # Revisión coordinada: solo el coordinador puede ejecutarla.
        # La solicitud está en 'approved' (con aprobaciones completas;
        # action_accept() es posible con aprobaciones completas; la revisión coordinada sigue siendo válida).
        resultado = solicitud.with_user(
            self.user_coordinador_c1
        ).action_coordinated_revision()
        self.env.invalidate_all()

        # La solicitud anterior queda superseded
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
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
    # 5.4: Revalidación de stock
    # ------------------------------------------------------------------
    def test_revalidacion_stock_bloquea_aceptacion(self):
        """Stock insuficiente no bloquea action_accept() con aprobaciones completas."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B3-54-C1", self.company_1, self.user_sales_c1,
            producto=self.product_insuficiente, qty=5.0
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

        solicitud.with_user(self.user_sales_c1).action_accept()
        self.assertEqual(solicitud.state, "confirmed")
        cotizacion = env_sales["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

    # ------------------------------------------------------------------
    # 5.5: Seguridad funcional
    # ------------------------------------------------------------------
    def test_usuario_sin_grupo_no_puede_crear_solicitud(self):
        """Usuario sin grupo  no puede crear solicitudes."""
        env_plain = self.env(user=self.user_plain_c1)
        cotizacion = self._crear_cotizacion(
            "B3-55-C1", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
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
                    "product_id": self.product_recojo.id,
                    "product_uom_id": cotizacion.order_line[0].product_uom_id.id,
                    "qty": 5.0,
                })],
            })

    def test_vendedor_no_puede_acceder_solicitud_ajena(self):
        """Vendedor de c2 no puede acceder a solicitud de c1 (empresa diferente).

        Comprueba el aislamiento de acceso multiempresa mediante lectura: un
        usuario sin acceso a la compañía de la solicitud no puede leerla.
        """
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)

        cotizacion_c1 = self._crear_cotizacion(
            "B3-55-C1", self.company_1, self.user_sales_c1,
            producto=self.product_recojo, qty=5.0
        )
        self._mark_as_subject(cotizacion_c1, self.user_sales_c1)
        solicitud_c1 = self._crear_solicitud(
            env_sales_c1, cotizacion_c1, "pickup", qty=5.0
        )
        solicitud_c1.with_user(self.user_sales_c1).action_request_validation()
        # Recojo + stock suficiente (product_recojo): ruta sin Tier / F-2 aprueba.
        self.assertEqual(solicitud_c1.state, "approved")

        # Precondición: solicitud pertenece a company_1
        self.assertEqual(solicitud_c1.company_id.id, self.company_1.id)

        # Precondición: user_sales_c2 solo pertenece a company_2
        self.assertEqual(self.user_sales_c2.company_id.id, self.company_2.id)
        self.assertNotIn(self.company_1.id, self.user_sales_c2.company_ids.ids)

        # Aislamiento entre compañías: usuario de c2 no puede acceder a solicitud de c1.
        with self.assertRaises(AccessError):
            env_sales_c2["sale.order.request"].browse(solicitud_c1.id).check_access("read")
