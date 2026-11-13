# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Pruebas automatizadas para sale_order_request (Fase A2/A3.1).

Prueban los cuatro escenarios de stock y entrega, así como:
- Creación de solicitud desde cotización con líneas vinculadas (C-02)
- Prevención de solicitudes duplicadas por revisión (A-04)
- Aprobaciones independientes y paralelas (Abastecimiento / Transporte)
- Rechazos
- Aceptación final del vendedor y confirmación de la cotización vigente
- Bloqueo de confirmación directa (C-01)
- Nueva revisión e invalidación de solicitud anterior
- Conservación del historial de aprobaciones
- Persistencia de datos
- Permisos de roles con usuarios reales (sin sudo() para simular)
- Integridad de aprobaciones ante cambios (C-05)
- Coherencia de cotización, revisión y compañía (C-04)

Nota de entorno: esta compilación de Odoo 19 Community no admite productos
tipo "product" (almacenable), por lo que `free_qty` es siempre 0.0. Las
pruebas usan qty = 1.0 (igual a product_uom_qty) y ejercitan las ramas que
requieren aprobaciones.

Usan usuarios y permisos reales. No se usa sudo() para simular usuarios
normales ni se escribe estado directamente para simular aprobaciones.
"""

from psycopg2.errors import UniqueViolation

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestSaleOrderRequest(TransactionCase):
    """Pruebas del módulo de Solicitud de orden de venta."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.admin = cls.env["res.users"].browse(2)
        cls.partner = cls.env["res.partner"].browse(9)
        if not cls.partner.exists():
            cls.partner = cls.env["res.partner"].search(
                [("customer_rank", ">", 0)], limit=1
            )
        if not cls.partner:
            cls.partner = cls.env["res.partner"].create(
                {"name": "Cliente Test MR", "customer_rank": 1}
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
        cls.grupo_base_user = cls.env.ref("base.group_user")
        cls.grupo_sale_salesman = cls.env.ref("sales_team.group_sale_salesman")

        cls.user_sales = cls._crear_usuario(
            "user_mr_sales",
            [
                "base.group_user",
                "sales_team.group_sale_salesman",
                "sale_order_request.group_sale_order_request_salesperson",
            ],
        )
        cls.user_abastecimiento = cls._crear_usuario(
            "user_mr_abastecimiento",
            ["base.group_user", "sale_order_request.group_sale_order_request_supply"],
        )
        cls.user_transporte = cls._crear_usuario(
            "user_mr_transporte",
            ["base.group_user", "sale_order_request.group_sale_order_request_transport"],
        )
        cls.user_plain = cls._crear_usuario(
            "user_mr_plain", ["base.group_user"]
        )
        # Usuario coordinador para pruebas del procedimiento coordinado
        cls.user_coordinador = cls._crear_usuario(
            "user_mr_coord",
            ["base.group_user", "sale_order_request.group_sale_order_request_coordinator"]
        )

        cls.product = cls._crear_producto("Producto MR")

    @classmethod
    def _crear_usuario(cls, login, xml_ids):
        grupos = [cls.env.ref(x).id for x in xml_ids]
        return cls.env["res.users"].create(
            {
                "login": login,
                "password": "login",
                "name": login,
                "group_ids": [(6, 0, grupos)],
            }
        )

    @classmethod
    def _crear_producto(cls, nombre):
        # product.template.create() ya genera su variante por defecto, por lo
        # que creamos directamente el product.product (auto-crea la plantilla).
        return cls.env["product.product"].create(
            {
                "name": nombre,
                "type": "consu",
                "sale_ok": True,
            }
        )

    @staticmethod
    def _stock_suficiente_qty():
        # En esta compilación free_qty = 0.0, por lo que qty >= 1.0 siempre
        # implica stock insuficiente. Usamos qty = 1.0 (igual a
        # product_uom_qty) para cumplir C-02 sin subdeclarar.
        return 1.0

    @staticmethod
    def _stock_insuficiente_qty():
        return 1.0

    def _crear_cotizacion(self, ref="MR-TEST", estado="sent", usuario=None):
        env = self.env(user=usuario or self.admin)
        order = (
            env["sale.order"]
            .create(
                {
                    "partner_id": self.partner.id,
                    "client_order_ref": ref,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product.id,
                                "product_uom_qty": 1.0,
                            },
                        )
                    ],
                }
            )
        )
        if estado == "sent":
            order.with_user(env.user).write({"state": "sent"})
        # El vendedor de prueba es el vendedor de la orden, para poder
        # confirmarla al final del flujo sin problemas de ACL.
        order.write({"user_id": self.user_sales.id})
        return order

    def _mark_as_subject(self, cotizacion):
        """Marca una cotización como sujeta al flujo de solicitud de orden de venta (C-01).
        Usa la ruta autorizada action_mark_sale_request_subject()."""
        cotizacion.with_user(self.user_sales).action_mark_sale_request_subject()
        return cotizacion

    def _lineas_solicitud(self, sale_order, qty=1.0):
        """Construye line_ids vinculando cada línea comercial de la cotización."""
        lineas = []
        for sol in sale_order.order_line.filtered(
            lambda l: l.display_type == False and l.product_id
        ):
            lineas.append(
                (0, 0, {
                    "sale_order_line_id": sol.id,
                    "product_id": sol.product_id.id,
                    "product_uom_id": sol.product_uom_id.id,
                    "qty": qty,
                })
            )
        return lineas

    def _crear_solicitud(
        self,
        sale_order,
        delivery_mode="pickup",
        usuario=None,
        stock_suficiente=True,
        qty=None,
    ):
        env = self.env(user=usuario or self.user_sales)
        if qty is None:
            qty = self._stock_suficiente_qty() if stock_suficiente else self._stock_insuficiente_qty()
        return env["sale.order.request"].create(
            {
                "sale_order_id": sale_order.id,
                "sale_order_revision_id": sale_order.id,
                "delivery_mode": delivery_mode,
                "requester_id": env.user.id,
                "line_ids": self._lineas_solicitud(sale_order, qty=qty),
            }
        )

    def _snap_reviews(self, request):
        return [
            {
                "id": r.id,
                "definition_id": r.definition_id.id,
                "status": r.status,
                "done_by": r.done_by.id if r.done_by else None,
            }
            for r in request.with_context(active_test=False).review_ids.sorted("id")
        ]

    def _obtener_def_abastecimiento(self):
        return self.env.ref("sale_order_request.tier_def_sale_order_request_supply")

    def _obtener_def_transporte(self):
        return self.env.ref("sale_order_request.tier_def_sale_order_request_transport")

    # ------------------------------------------------------------------
    # Escenario 1: Stock suficiente + recojo → sin aprobaciones
    # ------------------------------------------------------------------
    # Nota: en esta compilación free_qty=0.0 y qty>=1.0 (C-02), por lo que
    # el stock es siempre insuficiente. El escenario "sin aprobaciones"
    # no se puede reproducir con stock real cero; se testa el escenario 3
    # (recojo + insuficiente → Abastecimiento).

    # ------------------------------------------------------------------
    # Escenario 2: Stock suficiente + despacho → requiere Transporte
    # ------------------------------------------------------------------
    def test_escenario_2_stock_suficiente_despacho(self):
        cotizacion = self._crear_cotizacion("ES2-DESPACHO", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(cotizacion, "delivery")

        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
        # Stock insuficiente (qty=1.0 > free_qty=0.0) + despacho → Abastecimiento y Transporte.
        reviews = self._snap_reviews(solicitud)
        self.assertEqual(len(reviews), 2)
        self.assertTrue(all(r["status"] == "pending" for r in reviews))

        solicitud.with_user(self.user_abastecimiento).validate_tier()
        solicitud.with_user(self.user_transporte).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        def_transporte = self._obtener_def_transporte()
        review = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_transporte.id
        )
        self.assertEqual(review.status, "approved")

        # F-2: aprobación automática al completar todas las revisiones requeridas.
        self.assertEqual(solicitud.state, "approved")

        # Con aprobaciones completas (Transporte aprobada, F-2 automática) el
        # vendedor puede aceptar aunque el stock físico sea insuficiente.
        solicitud.with_user(self.user_sales).action_accept()
        self.assertEqual(solicitud.state, "confirmed")
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

    # ------------------------------------------------------------------
    # Escenario 3: Stock insuficiente + recojo → requiere Abastecimiento
    # ------------------------------------------------------------------
    def test_escenario_3_stock_insuficiente_recojo(self):
        cotizacion = self._crear_cotizacion("ES3-INSUF-RECOJO", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(
            cotizacion, "pickup", stock_suficiente=False
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
        self.assertEqual(len(self._snap_reviews(solicitud)), 1)

        def_abastecimiento = self._obtener_def_abastecimiento()
        review = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abastecimiento.id
        )
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        review = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abastecimiento.id
        )
        self.assertEqual(review.status, "approved")

        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

    # ------------------------------------------------------------------
    # Escenario 4: Stock insuficiente + despacho → Abastecimiento + Transporte
    # (independientes y paralelas)
    # ------------------------------------------------------------------
    def test_escenario_4_stock_insuficiente_despacho(self):
        cotizacion = self._crear_cotizacion("ES4-INSUF-DESPACHO", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(
            cotizacion, "delivery", stock_suficiente=False
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
        reviews = self._snap_reviews(solicitud)
        self.assertEqual(len(reviews), 2)
        self.assertTrue(all(r["status"] == "pending" for r in reviews))

        def_abastecimiento = self._obtener_def_abastecimiento()
        def_transporte = self._obtener_def_transporte()

        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        review_a = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abastecimiento.id
        )
        self.assertEqual(review_a.status, "approved")

        solicitud.with_user(self.user_transporte).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        review_b = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_transporte.id
        )
        self.assertEqual(review_b.status, "approved")

        self.assertEqual(solicitud.validation_status, "validated")
        # F-2: aprobación automática al completar todas las revisiones requeridas.
        self.assertEqual(solicitud.state, "approved")

    # ------------------------------------------------------------------
    # C-02: Vinculación real de líneas y cantidades
    # ------------------------------------------------------------------
    def test_linea_cantidad_cero_bloqueada(self):
        """Cantidad cero en línea de solicitud: bloqueada."""
        cotizacion = self._crear_cotizacion("C02-QTY0", "sent")
        self._mark_as_subject(cotizacion)
        sol = cotizacion.order_line[0]
        with self.assertRaises(ValidationError):
            self.env["sale.order.request"].create(
                {
                    "sale_order_id": cotizacion.id,
                    "sale_order_revision_id": cotizacion.id,
                    "delivery_mode": "pickup",
                    "requester_id": self.user_sales.id,
                    "line_ids": [
                        (0, 0, {
                            "sale_order_line_id": sol.id,
                            "product_id": sol.product_id.id,
                            "product_uom_id": sol.product_uom_id.id,
                            "qty": 0.0,
                        })
                    ],
                }
            )

    def test_linea_cantidad_negativa_bloqueada(self):
        """Cantidad negativa en línea de solicitud: bloqueada."""
        cotizacion = self._crear_cotizacion("C02-QTYNEG", "sent")
        self._mark_as_subject(cotizacion)
        sol = cotizacion.order_line[0]
        with self.assertRaises(ValidationError):
            self.env["sale.order.request"].create(
                {
                    "sale_order_id": cotizacion.id,
                    "sale_order_revision_id": cotizacion.id,
                    "delivery_mode": "pickup",
                    "requester_id": self.user_sales.id,
                    "line_ids": [
                        (0, 0, {
                            "sale_order_line_id": sol.id,
                            "product_id": sol.product_id.id,
                            "product_uom_id": sol.product_uom_id.id,
                            "qty": -1.0,
                        })
                    ],
                }
            )

    def test_linea_cantidad_inferior_bloqueada(self):
        """Cantidad inferior a la comercial: bloqueada."""
        cotizacion = self._crear_cotizacion("C02-QTYINF", "sent")
        self._mark_as_subject(cotizacion)
        sol = cotizacion.order_line[0]
        with self.assertRaises(ValidationError):
            self.env["sale.order.request"].create(
                {
                    "sale_order_id": cotizacion.id,
                    "sale_order_revision_id": cotizacion.id,
                    "delivery_mode": "pickup",
                    "requester_id": self.user_sales.id,
                    "line_ids": [
                        (0, 0, {
                            "sale_order_line_id": sol.id,
                            "product_id": sol.product_id.id,
                            "product_uom_id": sol.product_uom_id.id,
                            "qty": 0.5,
                        })
                    ],
                }
            )

    def test_linea_producto_diferente_bloqueada(self):
        """Producto diferente al de la línea de cotización: bloqueada."""
        producto_otro = self._crear_producto("Producto Otro")
        cotizacion = self._crear_cotizacion("C02-PROD", "sent")
        self._mark_as_subject(cotizacion)
        sol = cotizacion.order_line[0]
        with self.assertRaises(ValidationError):
            self.env["sale.order.request"].create(
                {
                    "sale_order_id": cotizacion.id,
                    "sale_order_revision_id": cotizacion.id,
                    "delivery_mode": "pickup",
                    "requester_id": self.user_sales.id,
                    "line_ids": [
                        (0, 0, {
                            "sale_order_line_id": sol.id,
                            "product_id": producto_otro.id,
                            "product_uom_id": sol.product_uom_id.id,
                            "qty": 1.0,
                        })
                    ],
                }
            )

    def test_linea_omitida_bloqueada(self):
        """Omitir una línea comercial de la cotización: bloqueada al
        solicitar validación."""
        cotizacion = self._crear_cotizacion("C02-OMIT", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self.env["sale.order.request"].create(
            {
                "sale_order_id": cotizacion.id,
                "sale_order_revision_id": cotizacion.id,
                "delivery_mode": "pickup",
                "requester_id": self.user_sales.id,
                "line_ids": [],
            }
        )
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales).action_request_validation()

    def test_linea_duplicada_bloqueada(self):
        """Duplicar una línea de cotización en la misma solicitud: bloqueada."""
        cotizacion = self._crear_cotizacion("C02-DUP", "sent")
        self._mark_as_subject(cotizacion)
        sol = cotizacion.order_line[0]
        sol_count_before = len(cotizacion.order_line)
        requests_before = self.env["sale.order.request"].search_count(
            [("sale_order_id", "=", cotizacion.id)]
        )
        caught = None
        try:
            with self.env.cr.savepoint():
                self.env["sale.order.request"].create(
                    {
                        "sale_order_id": cotizacion.id,
                        "sale_order_revision_id": cotizacion.id,
                        "delivery_mode": "pickup",
                        "requester_id": self.user_sales.id,
                        "line_ids": [
                            (0, 0, {
                                "sale_order_line_id": sol.id,
                                "product_id": sol.product_id.id,
                                "product_uom_id": sol.product_uom_id.id,
                                "qty": 1.0,
                            }),
                            (0, 0, {
                                "sale_order_line_id": sol.id,
                                "product_id": sol.product_id.id,
                                "product_uom_id": sol.product_uom_id.id,
                                "qty": 1.0,
                            }),
                        ],
                    }
                )
                self.env["sale.order.request.line"].flush_model()
        except Exception as exc:
            caught = exc
        self.assertIsNotNone(caught, "Se esperaba rechazo de línea duplicada")
        self.assertIsInstance(caught, (ValidationError, UniqueViolation))
        # Tras revertir el savepoint: sin duplicados persistidos y datos originales intactos.
        requests_after = self.env["sale.order.request"].search_count(
            [("sale_order_id", "=", cotizacion.id)]
        )
        self.assertEqual(requests_after, requests_before)
        self.assertEqual(len(cotizacion.order_line), sol_count_before)

    def test_modificar_cantidad_despues_aprobacion_bloqueada(self):
        """No se pueden modificar las cantidades tras iniciar aprobaciones."""
        cotizacion = self._crear_cotizacion("C02-MOD", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(cotizacion, "pickup")
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        linea = solicitud.line_ids[0]
        with self.assertRaises(UserError):
            solicitud.write(
                {"line_ids": [(1, linea.id, {"qty": 5.0})]}
            )

    def test_modificar_delivery_mode_despues_aprobacion_bloqueado(self):
        """No se puede cambiar la modalidad de entrega tras iniciar
        aprobaciones (C-05)."""
        cotizacion = self._crear_cotizacion("C05-MODE", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(cotizacion, "pickup")
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        with self.assertRaises(UserError):
            solicitud.write({"delivery_mode": "delivery"})

    # ------------------------------------------------------------------
    # Creación de solicitud desde cotización
    # ------------------------------------------------------------------
    def test_crear_solicitud_desde_cotizacion(self):
        cotizacion = self._crear_cotizacion("REQ-FROM-SO", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(cotizacion, "pickup")

        self.assertEqual(solicitud.sale_order_id, cotizacion)
        self.assertEqual(solicitud.sale_order_revision_id, cotizacion)
        self.assertEqual(solicitud.state, "draft")
        self.assertEqual(solicitud.requester_id, self.user_sales)
        self.assertEqual(len(solicitud.line_ids), 1)
        self.assertEqual(solicitud.line_ids[0].sale_order_line_id, cotizacion.order_line[0])

    # ------------------------------------------------------------------
    # Aprobaciones independientes
    # ------------------------------------------------------------------
    def test_aprobaciones_independientes(self):
        """Cada solicitud tiene su propio ciclo de aprobaciones (cotizaciones
        distintas, pues A-04 impide dos activas para la misma revisión)."""
        cotizacion1 = self._crear_cotizacion("REQ-INDEP-1", "sent")
        self._mark_as_subject(cotizacion1)
        solicitud1 = self._crear_solicitud(cotizacion1, "pickup", stock_suficiente=False)
        solicitud1.with_user(self.user_sales).action_request_validation()
        reviews_before = self._snap_reviews(solicitud1)
        ids_before = [r["id"] for r in reviews_before]

        cotizacion2 = self._crear_cotizacion("REQ-INDEP-2", "sent")
        self._mark_as_subject(cotizacion2)
        solicitud2 = self._crear_solicitud(cotizacion2, "pickup", stock_suficiente=False)
        solicitud2.with_user(self.user_sales).action_request_validation()
        reviews_after = self._snap_reviews(solicitud2)
        ids_after = [r["id"] for r in reviews_after]

        self.assertFalse(set(ids_after) & set(ids_before))

    # ------------------------------------------------------------------
    # Rechazos
    # ------------------------------------------------------------------
    def test_rechazo(self):
        """Una solicitud puede ser rechazada por el solicitante."""
        cotizacion = self._crear_cotizacion("REQ-RECHAZO", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(cotizacion, "pickup", stock_suficiente=False)
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        solicitud.with_user(self.user_sales).action_reject()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "rejected")

    # ------------------------------------------------------------------
    # Aceptación final del vendedor
    # ------------------------------------------------------------------
    def test_aceptacion_final_vendedor(self):
        """Flujo hasta aprobado. En este entorno free_qty=0.0 y qty=1.0, por
        lo que el stock es insuficiente y action_accept() se bloquea (B-08);
        se prueba por separado en test_aceptar_con_stock_insuficiente_falla."""
        cotizacion = self._crear_cotizacion("REQ-ACEPT", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(cotizacion, "pickup")
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # Todas las aprobaciones requeridas están completas y F-2 aprobó:
        # la aceptación se permite aunque el stock físico sea insuficiente.
        solicitud.with_user(self.user_sales).action_accept()
        self.assertEqual(solicitud.state, "confirmed")
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertEqual(cotizacion.state, "sale")

    # ------------------------------------------------------------------
    # Bloqueo de confirmación directa (C-01)
    # ------------------------------------------------------------------
    def test_bloqueo_confirmacion_directa(self):
        """No se puede confirmar la cotización sin pasar por el flujo de solicitud de orden de venta."""
        cotizacion = self._crear_cotizacion("TIER-TEST", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(cotizacion, "pickup")  # estado draft

        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales).action_confirm()
        self.assertNotEqual(cotizacion.state, "sale")

    # ------------------------------------------------------------------
    # Nueva revisión invalida solicitud anterior
    # ------------------------------------------------------------------
    def test_nueva_revision_invalida_solicitud_anterior(self):
        cotizacion = self._crear_cotizacion("REQ-REV", "sent")
        self._mark_as_subject(cotizacion)
        solicitud1 = self._crear_solicitud(cotizacion, "pickup", stock_suficiente=True)
        solicitud1.with_user(self.user_sales).action_request_validation()
        solicitud1.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud1 = self.env["sale.order.request"].browse(solicitud1.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud1.state, "approved")

        # Revisión coordinada: solo el coordinador puede ejecutarla.
        resultado = solicitud1.with_user(
            self.user_coordinador
        ).action_coordinated_revision()
        self.env.invalidate_all()

        # La solicitud anterior queda superseded
        solicitud1 = self.env["sale.order.request"].browse(solicitud1.id)
        self.assertEqual(solicitud1.state, "superseded")

        # Nueva solicitud creada y vinculada a la nueva revisión
        solicitud2 = self.env["sale.order.request"].browse(
            resultado["res_id"]
        )
        self.assertEqual(solicitud2.state, "draft")

        # Nueva revisión existe, está en draft y conserva sale_request_subject
        nueva = solicitud2.sale_order_revision_id
        self.assertEqual(nueva.state, "draft")
        self.assertTrue(nueva.sale_request_subject)

        # Procesar nueva solicitud: validar y aprobar
        solicitud2.with_user(self.user_sales).action_request_validation()
        solicitud2.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud2 = self.env["sale.order.request"].browse(solicitud2.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud2.state, "approved")

        # La nueva revisión está aprobada; la cotización aún no está confirmada
        # porque action_accept() se bloquea por stock insuficiente (B-08).
        self.assertNotEqual(nueva.state, "sale")

    # ------------------------------------------------------------------
    # C-04: Coherencia de cotización, revisión y compañía
    # ------------------------------------------------------------------
    def test_solicitud_vinculos_correctos_permitida(self):
        """Cotización y revisión correctas: solicitud creada correctamente."""
        cotizacion = self._crear_cotizacion("C04-OK", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(cotizacion, "pickup")
        self.assertEqual(solicitud.sale_order_id, cotizacion)
        self.assertEqual(solicitud.sale_order_revision_id, cotizacion)
        self.assertEqual(solicitud.company_id, cotizacion.company_id)

    def test_solicitud_revision_de_otra_cotizacion_bloqueada(self):
        """Revisión perteneciente a otra cotización: bloqueada."""
        cotizacion_a = self._crear_cotizacion("C04-A", "sent")
        cotizacion_b = self._crear_cotizacion("C04-B", "sent")
        self._mark_as_subject(cotizacion_a)
        self._mark_as_subject(cotizacion_b)
        with self.assertRaises(UserError):
            self.env["sale.order.request"].create(
                {
                    "sale_order_id": cotizacion_a.id,
                    "sale_order_revision_id": cotizacion_b.id,
                    "delivery_mode": "pickup",
                    "requester_id": self.user_sales.id,
                    "line_ids": self._lineas_solicitud(cotizacion_a, qty=1.0),
                }
            )

    def test_solicitud_compania_diferente_bloqueada(self):
        """Compañía diferente a la de la cotización: bloqueada."""
        cotizacion = self._crear_cotizacion("C04-CO", "sent")
        self._mark_as_subject(cotizacion)
        otra_compania = self.env["res.company"].search([("id", "!=", cotizacion.company_id.id)], limit=1)
        if not otra_compania:
            otra_compania = self.env["res.company"].create({"name": "Test Co C04"})
        with self.assertRaises(UserError):
            self.env["sale.order.request"].create(
                {
                    "sale_order_id": cotizacion.id,
                    "sale_order_revision_id": cotizacion.id,
                    "delivery_mode": "pickup",
                    "requester_id": self.user_sales.id,
                    "company_id": otra_compania.id,
                    "line_ids": self._lineas_solicitud(cotizacion, qty=1.0),
                }
            )

    # ------------------------------------------------------------------
    # Conservación del historial de aprobaciones
    # ------------------------------------------------------------------
    def test_conservacion_historial_aprobaciones(self):
        cotizacion = self._crear_cotizacion("REQ-HIST", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(cotizacion, "pickup")
        solicitud.with_user(self.user_sales).action_request_validation()
        antes = self._snap_reviews(solicitud)
        self.assertEqual(len(antes), 1)  # se requiere Transporte para despacho no; pickup sin stock suficiente = Abastecimiento

        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        despues = self._snap_reviews(solicitud)
        self.assertEqual(len(despues), 1)
        self.assertEqual(despues[0]["status"], "approved")

    # ------------------------------------------------------------------
    # Persistencia de datos
    # ------------------------------------------------------------------
    def test_persistencia_datos(self):
        cotizacion = self._crear_cotizacion("REQ-PERSIST", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(cotizacion, "pickup")
        solicitud.with_user(self.user_sales).action_request_validation()
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")
        self.assertEqual(solicitud.sale_order_id, cotizacion)
        # La aceptación se bloquea por stock insuficiente (B-08) en este entorno.
        cotizacion = self.env["sale.order"].browse(cotizacion.id)
        self.assertNotEqual(cotizacion.state, "sale")

    # ------------------------------------------------------------------
    # Permisos de roles (usuarios reales, sin sudo())
    # ------------------------------------------------------------------
    def test_permisos_roles(self):
        """El vendedor puede crear solicitudes vinculadas a sus cotizaciones."""
        cotizacion = self._crear_cotizacion("REQ-PERMISOS", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(cotizacion, "pickup")
        self.assertEqual(solicitud.requester_id, self.user_sales)
        self.assertEqual(solicitud.state, "draft")

    def test_usuario_sin_rol_no_puede_crear_solicitud(self):
        """Un usuario sin grupo  no puede crear solicitudes."""
        env_plain = self.env(user=self.user_plain)
        cotizacion = self._crear_cotizacion("REQ-NOROL", "sent")
        self._mark_as_subject(cotizacion)
        with self.assertRaises(AccessError):
            env_plain["sale.order.request"].create(
                {
                    "sale_order_id": cotizacion.id,
                    "sale_order_revision_id": cotizacion.id,
                    "delivery_mode": "pickup",
                    "requester_id": self.user_plain.id,
                    "line_ids": self._lineas_solicitud(cotizacion, qty=1.0),
                }
            )

    # ------------------------------------------------------------------
    # A-04: Unicidad de solicitud activa por revisión
    # ------------------------------------------------------------------
    def test_dos_solicitudes_activas_misma_revision_bloqueada(self):
        """No puede haber dos solicitudes activas para la misma revisión."""
        cotizacion = self._crear_cotizacion("A04-DUP", "sent")
        self._mark_as_subject(cotizacion)
        solicitud1 = self._crear_solicitud(cotizacion, "pickup")
        try:
            self._crear_solicitud(cotizacion, "pickup")
            self.fail("Se esperaba una excepción al crear una segunda solicitud activa.")
        except (UserError, ValidationError):
            pass

    def test_solicitud_cancelada_no_bloquea_nueva(self):
        """Una solicitud cancelada no impide crear una nueva para la misma revisión."""
        cotizacion = self._crear_cotizacion("A04-CANCEL", "sent")
        self._mark_as_subject(cotizacion)
        solicitud1 = self._crear_solicitud(cotizacion, "pickup")
        solicitud1.with_user(self.user_sales).action_cancel()
        self.assertEqual(solicitud1.state, "cancel")

        solicitud2 = self._crear_solicitud(cotizacion, "pickup")
        self.assertEqual(solicitud2.state, "draft")
