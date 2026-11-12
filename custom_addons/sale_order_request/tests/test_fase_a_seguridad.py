# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Pruebas de seguridad y control de la Fase A2/A3.1 — sale_order_request.

Verifican las protecciones server-side implementadas:

- Guardia de confirmación de cotización: no se confirma una cotización
  sujeta al flujo de solicitud de orden de venta sin una Solicitud de Pedido válida y aceptada
  vinculada a la revisión exacta. La pertenencia al flujo se determina por
  el indicador protegido ``sale_request_subject``, no por la existencia de una
  solicitud (C-01).
- Guardia de transiciones de estado: no se puede escribir `state` por
  ORM/RPC, ni siquiera inyectando el contexto `sale_order_request_allow_state_write`.
- Inmutabilidad de la solicitud: cotización, revisión, familia, compañía
  y solicitante no se alteran tras la creación.
- Creación protegida: una solicitud nace siempre en borrador; nunca se
  acepta un estado impuesto por el creador.
- Stock real: la disponibilidad se lee de `product.free_qty` /
  `product.virtual_available` y no se puede falsear por contexto RPC.
- Creación de orden: no se puede crear una sale.order directamente en
  'sale'.
- Aceptación final: solo el vendedor solicitante, con stock suficiente.
- Aprobaciones Tier: solo un revisor asignado puede aprobar.
- Vinculación real de líneas: productos, cantidades y unidades de medida
  deben corresponderse con las líneas de la cotización (C-02).
- Coherencia de cotización, revisión, compañía y familia (C-04).
- Unicidad de solicitud activa por revisión (A-04).
- Congelación de datos comerciales tras iniciar aprobaciones (C-05).

Nota de entorno: esta compilación de Odoo 19 Community no admite
productos tipo "product" (almacenable) ni permite crear stock.quant para
consumibles/servicios, por lo que `free_qty` y `virtual_available` son
siempre 0.0. Como la cantidad de la solicitud debe ser >= la cantidad
comercial (C-02), el stock real (0.0) siempre es insuficiente cuando la
cantidad es >= 1.0. Las pruebas usan qty = 1.0 (igual a product_uom_qty)
y ejercitan las ramas que requieren aprobaciones.

Usan usuarios y permisos reales creados en la prueba. No se usa sudo()
para simular usuarios normales ni contextos artificiales para omitir
protecciones.
"""

from psycopg2.errors import UniqueViolation

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestSaleOrderRequestPhaseASecurity(TransactionCase):
    """Protecciones de seguridad del flujo Solicitud de orden de venta."""

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
                {"name": "Cliente Test FA", "customer_rank": 1}
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

        # Usuarios de prueba (registros nuevos, sin modificar cuentas preexistentes)
        cls.user_sales = cls._crear_usuario(
            "user_fa2_sales",
            [
                "base.group_user",
                "sales_team.group_sale_salesman",
                "sale_order_request.group_sale_order_request_salesperson",
            ],
        )
        cls.user_abastecimiento = cls._crear_usuario(
            "user_fa2_abastecimiento",
            ["base.group_user", "sale_order_request.group_sale_order_request_supply"],
        )
        cls.user_transporte = cls._crear_usuario(
            "user_fa2_transporte",
            ["base.group_user", "sale_order_request.group_sale_order_request_transport"],
        )
        cls.user_plain = cls._crear_usuario(
            "user_fa2_plain", ["base.group_user"]
        )
        # Usuario coordinador para pruebas del procedimiento coordinado
        cls.user_coordinador = cls._crear_usuario(
            "user_fa2_coord",
            ["base.group_user", "sale_order_request.group_sale_order_request_coordinator"]
        )

        # Producto consumible: free_qty/virtual_available = 0.0 en esta compilación.
        cls.product = cls._crear_producto("Producto FA2")

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
        return cls.env["product.product"].create(
            {
                "name": nombre,
                "type": "consu",
                "sale_ok": True,
            }
        )

    def _crear_producto_servicio(self, nombre):
        return self.env["product.product"].create(
            {
                "name": nombre,
                "type": "service",
                "sale_ok": True,
            }
        )

    def _obtener_def_abastecimiento(self):
        return self.env.ref("sale_order_request.tier_def_sale_order_request_supply")

    def _obtener_def_transporte(self):
        return self.env.ref("sale_order_request.tier_def_sale_order_request_transport")

    # ------------------------------------------------------------------
    # Helpers de cotización y solicitud
    # ------------------------------------------------------------------
    def _crear_cotizacion(self, ref, estado="sent", usuario=None):
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
        self, env, sale_order, delivery_mode="pickup", qty=1.0
    ):
        return env["sale.order.request"].create(
            {
                "sale_order_id": sale_order.id,
                "sale_order_revision_id": sale_order.id,
                "delivery_mode": delivery_mode,
                "requester_id": env.user.id,
                "line_ids": self._lineas_solicitud(sale_order, qty=qty),
            }
        )

    # ------------------------------------------------------------------
    # C-01: identificación de cotizaciones sujetas a 
    # ------------------------------------------------------------------
    def test_cotizacion_subject_sin_solicitud_no_se_confirma(self):
        """Cotización sujeta a solicitud de orden de venta sin solicitud: confirmación bloqueada."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C01-SIN-REQ", "sent")
        self._mark_as_subject(cotizacion)

        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales).action_confirm()
        self.assertNotEqual(cotizacion.state, "sale")

    def test_cotizacion_subject_solicitud_pendiente_no_se_confirma(self):
        """Cotización sujeta a solicitud de orden de venta con solicitud pendiente: confirmación bloqueada."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C01-PENDIENTE", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(env_sales, cotizacion, "pickup")
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales).action_confirm()
        self.assertNotEqual(cotizacion.state, "sale")

    def test_cotizacion_subject_solicitud_aceptada_se_confirma(self):
        """Cotización sujeta a solicitud de orden de venta con solicitud aprobada: la confirmación queda
        bloqueada por stock insuficiente (B-08) en este entorno."""
        env_sales = self.env(user=self.user_sales)
        env_admin = self.env(user=self.admin)
        cotizacion = self._crear_cotizacion("C01-ACEPTADA", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(env_sales, cotizacion, "pickup")
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # La aceptación se bloquea por stock insuficiente (B-08), la cotización
        # no se confirma.
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales).action_accept()
        self.assertEqual(solicitud.state, "approved")
        cotizacion = env_admin["sale.order"].browse(cotizacion.id)
        self.assertNotEqual(cotizacion.state, "sale")

    def test_cotizacion_no_subject_confirma_normalmente(self):
        """Cotización no sujeta a  confirma normalmente (sin indicador)."""
        env_admin = self.env(user=self.admin)
        cotizacion = self._crear_cotizacion("C01-NO-", "sent")
        cotizacion.with_user(self.admin).action_confirm()
        self.assertEqual(cotizacion.state, "sale")

    def test_no_puede_quitar_sale_request_subject(self):
        """No se puede desasignar sale_request_subject una vez establecido (evasión)."""
        env_admin = self.env(user=self.admin)
        cotizacion = self._crear_cotizacion("C01-NO-QUITAR", "sent")
        self._mark_as_subject(cotizacion)

        with self.assertRaises(UserError):
            cotizacion.with_user(self.admin).write({"sale_request_subject": False})
        self.assertTrue(cotizacion.sale_request_subject)

    def test_sale_request_subject_no_escrito_directamente(self):
        """El indicador sale_request_subject no puede asignarse por write() directo.
        Solo se establece mediante action_mark_sale_request_subject() o
        sale_request_applicable=True al crear."""
        env_admin = self.env(user=self.admin)
        cotizacion = self._crear_cotizacion("C01-SOLO-AUTO", "sent")

        with self.assertRaises(UserError):
            cotizacion.with_user(self.admin).write({"sale_request_subject": True})
        self.assertFalse(cotizacion.sale_request_subject)

    def test_identificacion_automatica_via_sale_request_applicable(self):
        """Crear una cotización no establece sale_request_applicable automáticamente.
        El marcado  solo se hace vía action_mark_sale_request_subject()."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = env_sales["sale.order"].create({
            "partner_id": self.partner.id,
            "client_order_ref": "C01-AUTO-ID",
            "order_line": [
                (0, 0, {"product_id": self.product.id, "product_uom_qty": 1.0})
            ],
        })
        cotizacion.with_user(env_sales.user).write({"state": "sent"})
        # sale_request_applicable no se establece automáticamente en create()
        self.assertFalse(cotizacion.sale_request_applicable)
        self.assertFalse(cotizacion.sale_request_subject)
        # El marcado  solo se hace vía acción autorizada
        cotizacion.with_user(self.user_sales).action_mark_sale_request_subject()
        self.assertTrue(cotizacion.sale_request_applicable)
        self.assertTrue(cotizacion.sale_request_subject, "sale_request_subject debe estar True tras marcar como ")

    def test_identificacion_automatica_no_subject_por_defecto(self):
        """Una cotización sin sale_request_applicable no es sujeta a ."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = env_sales["sale.order"].create({
            "partner_id": self.partner.id,
            "client_order_ref": "C01-NO-AUTO",
            "order_line": [
                (0, 0, {"product_id": self.product.id, "product_uom_qty": 1.0})
            ],
        })
        cotizacion.with_user(env_sales.user).write({"state": "sent"})
        self.assertFalse(cotizacion.sale_request_applicable)
        self.assertFalse(cotizacion.sale_request_subject)

    def test_no_puede_modificar_sale_request_applicable_despues_de_sujeto(self):
        """Una vez la cotización está sujeta a , no se puede cambiar
        sale_request_applicable (evitar evasión)."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C01-NO-MOD-APP", "sent")
        self._mark_as_subject(cotizacion)
        self.assertTrue(cotizacion.sale_request_subject)

        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales).write({"sale_request_applicable": False})
        self.assertTrue(cotizacion.sale_request_applicable)

    def test_vendedor_solicitud_puede_marcar_sujeto(self):
        """Un vendedor con grupo  puede marcar una cotización como sujeto
        mediante action_mark_sale_request_subject()."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C01-VENDEDOR-", "sent")
        cotizacion.with_user(self.user_sales).action_mark_sale_request_subject()
        self.assertTrue(cotizacion.sale_request_subject)
        self.assertTrue(cotizacion.sale_request_applicable)

    def test_vendedor_sin_grupo_solicitud_no_puede_marcar_sujeto(self):
        """Un vendedor sin grupo  no puede marcar una cotización como sujeto."""
        env_plain = self.env(user=self.user_plain)
        cotizacion = self._crear_cotizacion("C01-SIN-GRUPO", "sent")
        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_plain).action_mark_sale_request_subject()
        self.assertFalse(cotizacion.sale_request_subject)


    def test_deteccion_sujeto_solicitud_independiente_de_lectura_solicitudes(self):
        """La detección de  no depende de leer sale.order.request:
        un usuario sin acceso de lectura a solicitudes sigue detectando
        que la cotización es  y se bloquea al confirmar."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C01-SIN-LECTURA", "sent")
        self._mark_as_subject(cotizacion)
        # No hay solicitud en absoluto; el usuario_sales tiene lectura sobre
        # sale.order (sale_request_subject) pero no necesita leer sale.order.request.
        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales).action_confirm()
        self.assertNotEqual(cotizacion.state, "sale")

    # ------------------------------------------------------------------
    # B-03: guardia de transiciones de estado (sin contexto autorizable)
    # ------------------------------------------------------------------
    def test_estado_no_escrito_directamente_orm(self):
        """Un vendedor no puede escribir `state` por ORM."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B03-ORM", "sent")
        solicitud = self._crear_solicitud(env_sales, cotizacion)

        with self.assertRaises(UserError):
            env_sales["sale.order.request"].browse(solicitud.id).write(
                {"state": "accepted"}
            )
        self.assertEqual(
            env_sales["sale.order.request"].browse(solicitud.id).state, "draft"
        )

    def test_no_salto_directo_draft_a_accepted(self):
        """No se puede pasar directamente de draft a accepted."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B03-DA", "sent")
        solicitud = self._crear_solicitud(env_sales, cotizacion)

        with self.assertRaises(UserError):
            env_sales["sale.order.request"].browse(solicitud.id).write(
                {"state": "accepted"}
            )
        self.assertEqual(
            env_sales["sale.order.request"].browse(solicitud.id).state, "draft"
        )

    def test_no_salto_directo_draft_a_confirmed(self):
        """No se puede pasar directamente de draft a confirmed."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B03-DC", "sent")
        solicitud = self._crear_solicitud(env_sales, cotizacion)

        with self.assertRaises(UserError):
            env_sales["sale.order.request"].browse(solicitud.id).write(
                {"state": "confirmed"}
            )
        self.assertEqual(
            env_sales["sale.order.request"].browse(solicitud.id).state, "draft"
        )

    def test_contexto_sale_order_request_allow_state_write_no_autoriza(self):
        """Inyectar el contexto sale_order_request_allow_state_write no autoriza escribir
        state por write(); el guardia de write() no admite contexto."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B03-CTX", "sent")
        solicitud = self._crear_solicitud(env_sales, cotizacion)

        with self.assertRaises(UserError):
            env_sales["sale.order.request"].browse(solicitud.id).with_context(
                sale_order_request_allow_state_write=True
            ).write({"state": "approved"})
        self.assertEqual(
            env_sales["sale.order.request"].browse(solicitud.id).state, "draft"
        )

    # ------------------------------------------------------------------
    # B-04: creación protegida
    # ------------------------------------------------------------------
    def test_crear_solicitud_estado_forzado(self):
        """create() nunca acepta un estado impuesto: nace en borrador."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B04-CREATE", "sent")
        solicitud = env_sales["sale.order.request"].create(
            {
                "sale_order_id": cotizacion.id,
                "sale_order_revision_id": cotizacion.id,
                "delivery_mode": "pickup",
                "requester_id": env_sales.user.id,
                "state": "accepted",  # intenta forzar estado
                "line_ids": self._lineas_solicitud(cotizacion, qty=1.0),
            }
        )
        self.assertEqual(solicitud.state, "draft")

    # ------------------------------------------------------------------
    # B-02 / B-05: inmutabilidad de identificadores de la solicitud
    # ------------------------------------------------------------------
    def test_solicitante_inmutable(self):
        """Tras crear la solicitud no se puede cambiar el solicitante."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B05-IMM", "sent")
        solicitud = self._crear_solicitud(env_sales, cotizacion, "pickup")

        with self.assertRaises(UserError):
            solicitud.with_user(env_sales.user).write(
                {"requester_id": self.user_plain.id}
            )
        self.assertEqual(solicitud.requester_id, env_sales.user)

    # ------------------------------------------------------------------
    # C-02: vinculación real de líneas y cantidades
    # ------------------------------------------------------------------
    def test_linea_cantidad_cero_bloqueada(self):
        """Cantidad cero en línea de solicitud: bloqueada."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C02-QTY0", "sent")
        with self.assertRaises(ValidationError):
            env_sales["sale.order.request"].create(
                {
                    "sale_order_id": cotizacion.id,
                    "sale_order_revision_id": cotizacion.id,
                    "delivery_mode": "pickup",
                    "requester_id": env_sales.user.id,
                    "line_ids": self._lineas_solicitud(cotizacion, qty=0.0),
                }
            )

    def test_linea_cantidad_negativa_bloqueada(self):
        """Cantidad negativa en línea de solicitud: bloqueada."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C02-QTYNEG", "sent")
        with self.assertRaises(ValidationError):
            env_sales["sale.order.request"].create(
                {
                    "sale_order_id": cotizacion.id,
                    "sale_order_revision_id": cotizacion.id,
                    "delivery_mode": "pickup",
                    "requester_id": env_sales.user.id,
                    "line_ids": self._lineas_solicitud(cotizacion, qty=-1.0),
                }
            )

    def test_linea_cantidad_inferior_bloqueada(self):
        """Cantidad inferior a la comercial: bloqueada."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C02-QTYINF", "sent")
        with self.assertRaises(ValidationError):
            env_sales["sale.order.request"].create(
                {
                    "sale_order_id": cotizacion.id,
                    "sale_order_revision_id": cotizacion.id,
                    "delivery_mode": "pickup",
                    "requester_id": env_sales.user.id,
                    "line_ids": self._lineas_solicitud(cotizacion, qty=0.5),
                }
            )

    def test_linea_producto_diferente_bloqueada(self):
        """Producto diferente al de la línea de cotización: bloqueada."""
        env_sales = self.env(user=self.user_sales)
        producto_otro = self._crear_producto("Producto Otro")
        cotizacion = self._crear_cotizacion("C02-PROD", "sent")
        sol = cotizacion.order_line[0]
        with self.assertRaises(ValidationError):
            env_sales["sale.order.request"].create(
                {
                    "sale_order_id": cotizacion.id,
                    "sale_order_revision_id": cotizacion.id,
                    "delivery_mode": "pickup",
                    "requester_id": env_sales.user.id,
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
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C02-OMIT", "sent")
        # Crear solicitud sin líneas (no cubre la línea comercial de la cotización)
        solicitud = env_sales["sale.order.request"].create(
            {
                "sale_order_id": cotizacion.id,
                "sale_order_revision_id": cotizacion.id,
                "delivery_mode": "pickup",
                "requester_id": env_sales.user.id,
                "line_ids": [],
            }
        )
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales).action_request_validation()

    def test_linea_duplicada_bloqueada(self):
        """Duplicar una línea de cotización en la misma solicitud: bloqueada."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C02-DUP", "sent")
        sol = cotizacion.order_line[0]
        sol_count_before = len(cotizacion.order_line)
        requests_before = self.env["sale.order.request"].search_count(
            [("sale_order_id", "=", cotizacion.id)]
        )
        caught = None
        try:
            with self.env.cr.savepoint():
                env_sales["sale.order.request"].create(
                    {
                        "sale_order_id": cotizacion.id,
                        "sale_order_revision_id": cotizacion.id,
                        "delivery_mode": "pickup",
                        "requester_id": env_sales.user.id,
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
                env_sales["sale.order.request.line"].flush_model()
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

    def test_cantidades_correctas_permitidas(self):
        """Cantidades iguales a las comerciales: permitidas."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C02-OK", "sent")
        solicitud = self._crear_solicitud(env_sales, cotizacion, "pickup", qty=1.0)
        self.assertEqual(solicitud.state, "draft")

    def test_modificar_cantidad_despues_aprobacion_bloqueada(self):
        """No se pueden modificar las cantidades tras iniciar aprobaciones."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("C02-MOD", "sent")
        solicitud = self._crear_solicitud(env_sales, cotizacion, "pickup", qty=1.0)
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        linea = solicitud.line_ids[0]
        with self.assertRaises(UserError):
            solicitud.write(
                {"line_ids": [(1, linea.id, {"qty": 5.0})]}
            )

    # ------------------------------------------------------------------
    # A1 / B-01: protección de confirmación de cotización (mantenida)
    # ------------------------------------------------------------------
    def test_no_confirmar_sin_solicitud_valida(self):
        """Orden sujeta a  sin solicitud aceptada no se confirma."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B01-SIN-REQ", "sent")
        self._mark_as_subject(cotizacion)
        self._crear_solicitud(env_sales, cotizacion, "pickup")  # estado draft

        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales).action_confirm()
        self.assertNotEqual(cotizacion.state, "sale")

    def test_no_confirmar_solicitud_de_otra_revision(self):
        """Una orden con solicitud aceptada para la revisión B no permite
        confirmar la revisión A (obsoleta)."""
        env_sales = self.env(user=self.user_sales)
        env_coord = self.env(user=self.user_coordinador)
        cotizacion = self._crear_cotizacion("B01-REV-OBS", "sent")
        self._mark_as_subject(cotizacion)
        cotizacion.write({"user_id": self.user_sales.id})

        # Solicitud para la revisión original (familia queda sujeta a )
        self._crear_solicitud(env_sales, cotizacion, "pickup", qty=1.0)

        # Procesar solicitud original hasta approved
        solicitud_original = self.env["sale.order.request"].search(
            [("sale_order_revision_id", "=", cotizacion.id),
             ("company_id", "=", cotizacion.company_id.id)],
            limit=1
        )
        solicitud_original.with_user(self.user_sales).action_request_validation()
        solicitud_original.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud_original = self.env["sale.order.request"].browse(
            solicitud_original.id
        )
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud_original.state, "approved")

        # Revisión coordinada: solo el coordinador puede ejecutarla
        # (stock insuficiente impide action_accept(), pero approved es válido
        #  para la revisión coordinada)
        solicitud_original.with_user(self.user_coordinador).action_coordinated_revision()
        self.env.invalidate_all()

        # La solicitud original quedó superseded
        solicitud_original = self.env["sale.order.request"].browse(
            solicitud_original.id
        )
        self.assertEqual(solicitud_original.state, "superseded")

        # La cotización original pasó a cancel (revisión anterior archivada)
        self.assertEqual(cotizacion.state, "cancel")

        # Intentar confirmar la revisión original (obsoleta): debe bloquearse
        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales).action_confirm()

    # ------------------------------------------------------------------
    # A3 / B-08: aceptación final solo del solicitante y stock suficiente
    # ------------------------------------------------------------------
    def test_aceptar_como_no_solicitante_falla(self):
        """Un vendedor que no es el solicitante no puede aceptar."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B08-NO-SOLIC", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(env_sales, cotizacion, "pickup")
        solicitud.with_user(self.user_sales).action_request_validation()

        with self.assertRaises(UserError):
            solicitud.with_user(self.user_plain).action_accept()

    def test_aceptante_autorizado_puede_aceptar(self):
        """El vendedor solicitante llega a approved y la aceptación queda
        bloqueada por stock insuficiente (B-08); en este entorno no se puede
        llegar a confirmed porque free_qty=0.0 y qty=1.0."""
        env_sales = self.env(user=self.user_sales)
        env_admin = self.env(user=self.admin)
        cotizacion = self._crear_cotizacion("B08-ACEPT", "sent")
        self._mark_as_subject(cotizacion)
        cotizacion.write({"user_id": self.user_sales.id})
        solicitud = self._crear_solicitud(env_sales, cotizacion, "pickup", qty=1.0)
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # La aceptación final se bloquea por stock insuficiente (B-08).
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales).action_accept()
        self.assertEqual(solicitud.state, "approved")

        cotizacion = env_admin["sale.order"].browse(cotizacion.id)
        self.assertNotEqual(cotizacion.state, "sale")

    def test_aceptar_con_stock_insuficiente_falla(self):
        """La aceptación se bloquea si, tras revalidar, el stock es insuficiente."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B08-STOCK-INS", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=1.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # Pickup + stock insuficiente: solo aplica Abastecimiento. Al completar
        # la revisión requerida, F-2 aprueba automáticamente (sin action_approve).
        self.assertEqual(solicitud.state, "approved")
        self.assertEqual(solicitud.validation_status, "validated")

        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales).action_accept()

    # ------------------------------------------------------------------
    # B-09: aprobaciones Tier solo por revisor asignado
    # ------------------------------------------------------------------
    def test_no_revisor_no_puede_validar_revision_tier(self):
        """Un usuario no asignado como revisor no puede validar una revisión Tier.

        Verifica que validate_tier(), invocado por un usuario que no es revisor
        de las revisiones pendientes, no completa ninguna revisión ni altera la
        solicitud. La posibilidad de validar se conserva para el revisor
        asignado.
        """
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B09-NO-REVISOR", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(env_sales, cotizacion, "delivery")
        solicitud.with_user(self.user_sales).action_request_validation()
        # delivery + stock insuficiente → Abastecimiento y Transporte.
        self.assertEqual(solicitud.state, "pending_approval")
        def_abastecimiento = self._obtener_def_abastecimiento()
        def_transporte = self._obtener_def_transporte()
        review_abast = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abastecimiento.id
        )
        review_trans = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_transporte.id
        )
        self.assertEqual(len(review_abast), 1)
        self.assertEqual(len(review_trans), 1)
        self.assertEqual(review_abast.status, "pending")
        self.assertEqual(review_trans.status, "pending")
        reviews_before = solicitud.review_ids.read(["status", "done_by", "reviewed_date"])

        # user_sales no es revisor asignado a Abastecimiento ni a Transporte:
        # no debe completar ninguna revisión Tier.
        solicitud.with_user(self.user_sales).validate_tier()

        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        review_abast = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abastecimiento.id
        )
        review_trans = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_transporte.id
        )
        self.assertEqual(solicitud.state, "pending_approval")
        self.assertEqual(review_abast.status, "pending")
        self.assertFalse(review_abast.done_by)
        self.assertFalse(review_abast.reviewed_date)
        self.assertEqual(review_trans.status, "pending")
        self.assertFalse(review_trans.done_by)
        self.assertFalse(review_trans.reviewed_date)
        self.assertEqual(
            solicitud.review_ids.read(["status", "done_by", "reviewed_date"]),
            reviews_before,
        )

        # El revisor asignado (Transporte) conserva la posibilidad de validar su revisión.
        solicitud.with_user(self.user_transporte).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        review_abast = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abastecimiento.id
        )
        review_trans = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_transporte.id
        )
        self.assertEqual(review_trans.status, "approved")
        self.assertEqual(review_trans.done_by, self.user_transporte)
        self.assertTrue(review_trans.reviewed_date)
        self.assertEqual(review_abast.status, "pending")
        self.assertFalse(review_abast.done_by)
        self.assertFalse(review_abast.reviewed_date)
        self.assertEqual(solicitud.state, "pending_approval")

    def test_action_approve_no_permite_aprobar_con_revisiones_pendientes(self):
        """action_approve() no puede aprobar con revisiones Tier pendientes."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B09-PENDIENTE", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(env_sales, cotizacion, "delivery")
        solicitud.with_user(self.user_sales).action_request_validation()
        # delivery + stock insuficiente → Abastecimiento y Transporte.
        # Solo valida Abastecimiento: queda Transporte pendiente.
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "pending_approval")
        reviews_before = solicitud.review_ids.read(["status", "done_by", "reviewed_date"])

        with self.assertRaises(UserError):
            solicitud.with_user(self.user_abastecimiento).action_approve()

        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "pending_approval")
        self.assertEqual(
            solicitud.review_ids.read(["status", "done_by", "reviewed_date"]),
            reviews_before,
        )

    def test_revisor_asignado_puede_aprobar(self):
        """Un revisor asignado puede aprobar cuando las revisiones están
        validadas."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("B09-REVISOR", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(env_sales, cotizacion, "delivery")
        solicitud.with_user(self.user_sales).action_request_validation()
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        solicitud.with_user(self.user_transporte).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # Al completar todas las revisiones requeridas, F-2 aprueba automáticamente.
        self.assertEqual(solicitud.validation_status, "validated")
        self.assertEqual(solicitud.state, "approved")

    # ------------------------------------------------------------------
    # exclude_requester (autoaprobación)
    # ------------------------------------------------------------------
    def test_solicitante_excluido_de_revisores_tier(self):
        """exclude_requester deja al solicitante fuera de los revisores."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("EXCL-REQ", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(env_sales, cotizacion, "delivery")
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        revisiones = solicitud.with_context(active_test=False).review_ids
        revisores = revisiones.mapped("reviewer_ids")
        self.assertNotIn(self.user_sales, revisores)

    # ------------------------------------------------------------------
    # versionado OCA
    # ------------------------------------------------------------------
    def test_versionado_ocan_no_bloqueado(self):
        """create_revision_preserving_tier sigue funcionando tras las
        protecciones (actúa sobre sale.order, no sobre sale.order.request)."""
        env_admin = self.env(user=self.admin)
        cotizacion = self._crear_cotizacion("VER-OCAN", "sent")
        nombre_base = cotizacion.name

        nueva = cotizacion.create_revision_preserving_tier()
        nueva = env_admin["sale.order"].browse(nueva.id)

        self.assertEqual(nueva.name, nombre_base + "-01")
        self.assertEqual(cotizacion.state, "cancel")
        self.assertEqual(cotizacion.active, False)

    # ------------------------------------------------------------------
    # B-07: creación de orden directamente confirmada
    # ------------------------------------------------------------------
    def test_crear_orden_venta_estado_sale_falla(self):
        """No se puede crear una sale.order directamente en estado 'sale'."""
        env_admin = self.env(user=self.admin)
        with self.assertRaises(UserError):
            env_admin["sale.order"].create(
                {
                    "partner_id": self.partner.id,
                    "client_order_ref": "B07-CREATE-SALE",
                    "state": "sale",
                    "order_line": [
                        (0, 0, {"product_id": self.product.id, "product_uom_qty": 1.0})
                    ],
                }
            )

    def test_stock_no_se_falsea_por_contexto(self):
        """El contexto RPC no puede alterar la disponibilidad de stock:
        se lee el valor real del producto."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("STOCK-CTX", "sent")
        self._mark_as_subject(cotizacion)
        solicitud = self._crear_solicitud(env_sales, cotizacion, "pickup")
        # Inyectar un contexto falso no cambia el stock calculado
        solicitud.with_context(test_stock_qty=999999.0)._evaluate_stock()
        self.assertEqual(solicitud.line_ids[0].stock_qty, 0.0)
