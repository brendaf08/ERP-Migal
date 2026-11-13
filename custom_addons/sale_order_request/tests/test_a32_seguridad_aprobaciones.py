# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Pruebas de seguridad de aprobaciones — Fase A3.2 — sale_order_request.

Verifican las protecciones server-side sobre las aprobaciones Tier:

- Manipulación directa de tier.review.status / done_by no puede falsificar
  una aprobación (detectada en action_approve() vía _check_review_integrity()).
- Solo revisores asignados pueden aprobar/rechazar sus respectivas revisiones.
- No se puede aprobar una revisión asignada a otro grupo o responsable.
- No se puede aprobar una solicitud sin pertenecer al circuito de autorización.
- No se pueden usar llamadas directas para eludir los permisos.
- Las aprobaciones de Abastecimiento y Transporte son independientes y paralelas.
- Las transiciones de estado están protegidas (sin saltos, sin aprobaciones
  duplicadas, sin aprobar después de rechazo/cancelación).
- Una solicitud rechazada, cancelada o invalida no habilita confirmación.
- El flujo legítimo con ambas aprobaciones y con una sola aprobación funciona.

Nota de entorno: esta compilación de Odoo 19 Community tiene free_qty=0.0
para todos los productos, por lo que toda solicitud con qty >= 1.0 tiene
stock insuficiente y requiere aprobaciones según la matriz . Los flujos
legítimos se validan hasta approved (la aceptación final se bloquea por
stock insuficiente B-08, lo cual es el comportamiento esperado).

Usan usuarios con permisos reales (sin sudo()).
"""

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestA32SeguridadAprobaciones(TransactionCase):
    """Seguridad de aprobaciones Tier en Solicitud de orden de venta."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.admin = cls.env["res.users"].browse(2)
        cls.admin.write({
            "group_ids": [(4, cls.env.ref(
                "sale_order_request.group_sale_order_request_salesperson").id)]
        })
        cls.partner = cls.env["res.partner"].search(
            [("customer_rank", ">", 0)], limit=1
        )
        if not cls.partner:
            cls.partner = cls.env["res.partner"].create(
                {"name": "Cliente Test A32", "customer_rank": 1}
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

        # Usuarios de prueba con permisos reales
        cls.user_sales = cls._crear_usuario(
            "user_a32_sales",
            [
                "base.group_user",
                "sales_team.group_sale_salesman",
                "sale_order_request.group_sale_order_request_salesperson",
            ],
        )
        cls.user_abastecimiento = cls._crear_usuario(
            "user_a32_abastecimiento",
            ["base.group_user", "sale_order_request.group_sale_order_request_supply"],
        )
        cls.user_transporte = cls._crear_usuario(
            "user_a32_transporte",
            ["base.group_user", "sale_order_request.group_sale_order_request_transport"],
        )
        cls.user_plain = cls._crear_usuario(
            "user_a32_plain", ["base.group_user"]
        )

        # Producto consumible: free_qty = 0.0 en esta compilación.
        cls.product = cls.env["product.product"].create({
            "name": "Producto A3.2",
            "type": "consu",
            "sale_ok": True,
        })

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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _crear_cotizacion(self, ref, sale_request_applicable=True):
        env = self.env(user=self.admin)
        order = env["sale.order"].create({
            "partner_id": self.partner.id,
            "client_order_ref": ref,
            "order_line": [
                (0, 0, {
                    "product_id": self.product.id,
                    "product_uom_qty": 5.0,
                })
            ],
        })
        if sale_request_applicable:
            # Marcar como  vía ruta autorizada (action_mark_sale_request_subject).
            # Se ejecuta como admin para tener acceso de escritura; el método
            # verifica internamente group_sale_order_request_salesperson.
            order.with_user(self.admin).action_mark_sale_request_subject()
        order.with_user(env.user).write({"state": "sent"})
        order.write({"user_id": self.user_sales.id})
        return order

    def _mark_as_subject(self, cotizacion):
        cotizacion.with_user(self.user_sales).action_mark_sale_request_subject()
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

    def _snap_reviews(self, request):
        return [
            {
                "id": r.id,
                "definition_id": r.definition_id.id,
                "status": r.status,
                "done_by": r.done_by.id if r.done_by else None,
                "reviewed_date": r.reviewed_date,
            }
            for r in request.with_context(active_test=False).review_ids.sorted("id")
        ]

    def _obtener_def_abastecimiento(self):
        return self.env.ref("sale_order_request.tier_def_sale_order_request_supply")

    def _obtener_def_transporte(self):
        return self.env.ref("sale_order_request.tier_def_sale_order_request_transport")

    # ------------------------------------------------------------------
    # A3.2 - 1.1: Protección de tier.review (manipulación directa)
    # ------------------------------------------------------------------
    def test_manipulacion_directa_tier_review_detectada(self):
        """Escribir directamente tier.review.status se detecta en
        action_approve() vía _check_review_integrity()."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-MANIP-1", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Intentar escribir directamente en tier.review (el ACL de OCA puede
        # permitirlo para base.group_user, pero action_approve() debe
        # rechazar la falsificación).
        revisiones = solicitud.with_context(active_test=False).review_ids
        def_transporte = self._obtener_def_transporte()
        review_t = revisiones.filtered(
            lambda r: r.definition_id.id == def_transporte.id
        )

        try:
            review_t.with_user(self.user_sales).write({
                "status": "approved",
                "done_by": self.user_sales.id,
                "reviewed_date": fields.Datetime.now(),
            })
            escritura_directa_posible = True
        except (UserError, AccessError):
            escritura_directa_posible = False

        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)

        # action_approve() debe rechazar si la revisión fue falsificada
        # (user_sales no es reviewer de Transporte)
        if escritura_directa_posible:
            with self.assertRaises(UserError):
                solicitud.with_user(self.user_transporte).action_approve()

    def test_falsificacion_done_by_detectada(self):
        """Establecer done_by=otro_usuario en tier.review se detecta."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-FAKE-DONEBY", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()

        revisiones = solicitud.with_context(active_test=False).review_ids
        def_transporte = self._obtener_def_transporte()
        review_t = revisiones.filtered(
            lambda r: r.definition_id.id == def_transporte.id
        )

        # Falsificar done_by como abastecimiento (no reviewer de Transporte)
        try:
            review_t.with_user(self.user_sales).write({
                "status": "approved",
                "done_by": self.user_abastecimiento.id,
                "reviewed_date": fields.Datetime.now(),
            })
        except (UserError, AccessError):
            pass

        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)

        # action_approve() debe rechazar la falsificación
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_transporte).action_approve()

    # ------------------------------------------------------------------
    # A3.2 - 1.2: Permisos de aprobación
    # ------------------------------------------------------------------
    def test_usuario_no_asignado_no_puede_validar_revision_tier(self):
        """Un usuario no asignado como revisor no puede validar una revisión Tier.

        Verifica que validate_tier(), invocado por un usuario sin asignación de
        revisor, no completa ninguna revisión ni altera la solicitud. La
        posibilidad de validar se conserva para el revisor asignado.
        """
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-NO-AUTORIZADO", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
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

        # user_sales no es reviewer de Abastecimiento ni de Transporte:
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

        # El revisor asignado (Abastecimiento) conserva la posibilidad de validar su revisión.
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        review_abast = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_abastecimiento.id
        )
        review_trans = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_transporte.id
        )
        self.assertEqual(review_abast.status, "approved")
        self.assertEqual(review_abast.done_by, self.user_abastecimiento)
        self.assertTrue(review_abast.reviewed_date)
        self.assertEqual(review_trans.status, "pending")
        self.assertFalse(review_trans.done_by)
        self.assertFalse(review_trans.reviewed_date)
        self.assertEqual(solicitud.state, "pending_approval")

    def test_aprobacion_revision_de_otro_responsable_falla(self):
        """Un revisor de Transporte no puede aprobar sin validar su revisión."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-CRUZ", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        # Solo Abastecimiento valida; Transporte no valida aún
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)

        # Transporte intenta aprobar sin haber validado su propia revisión
        # (validation_status no es 'validado' porque falta Transporte)
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_transporte).action_approve()

    def test_aprobacion_duplicada_bloqueada(self):
        """Una vez aprobada, no se puede aprobar nuevamente."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-DUP-APR", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        # pickup + stock insuficiente → requiere Abastecimiento
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: al completar la revisión requerida, la solicitud queda aprobada.
        self.assertEqual(solicitud.state, "approved")
        approval_date = solicitud.approval_date
        reviews_before = solicitud.review_ids.read(
            ["status", "done_by", "reviewed_date"]
        )
        messages_before = len(solicitud.message_ids)

        # Intentar aprobar nuevamente (segunda aprobación rechazada, sin efectos)
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales).action_approve()

        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "approved")
        self.assertEqual(solicitud.approval_date, approval_date)
        self.assertEqual(
            solicitud.review_ids.read(["status", "done_by", "reviewed_date"]),
            reviews_before,
        )
        self.assertEqual(len(solicitud.message_ids), messages_before)

    def test_aprobacion_despues_de_rechazo_bloqueada(self):
        """Una solicitud rechazada no puede aprobarse."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-RECH-BLOQ", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)

        # Rechazar
        solicitud.with_user(self.user_abastecimiento).action_reject()
        self.assertEqual(solicitud.state, "rejected")

        # Intentar aprobar después de rechazar
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_transporte).action_approve()

    def test_aprobacion_despues_de_cancelacion_bloqueada(self):
        """Una solicitud cancelada no puede aprobarse."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-CANC-BLOQ", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # Cancelar
        solicitud.with_user(self.user_sales).action_cancel()
        self.assertEqual(solicitud.state, "cancel")

        # Intentar aprobar después de cancelar
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales).action_approve()

    # ------------------------------------------------------------------
    # A3.2 - 1.3: Invalidación de aprobaciones ante cambios de condiciones
    # ------------------------------------------------------------------
    def test_modificacion_lineas_despues_aprobar_bloqueada(self):
        """No se pueden modificar líneas después de aprobar."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-MOD-LINEAS", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        linea = solicitud.line_ids[0]
        with self.assertRaises(UserError):
            solicitud.write(
                {"line_ids": [(1, linea.id, {"qty": 10.0})]}
            )

    def test_cambio_recojo_a_despacho_despues_aprobar_bloqueado(self):
        """No se puede cambiar de recojo a despacho después de aprobar."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-CAMBIO-MODO", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # Intentar cambiar a despacho después de aprobar
        with self.assertRaises(UserError):
            solicitud.write({"delivery_mode": "delivery"})

    def test_cambio_despacho_a_recojo_despues_aprobar_bloqueado(self):
        """No se puede cambiar de despacho a recojo después de aprobar."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-CAMBIO-MODO2", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        # delivery + stock insuficiente → requiere Abastecimiento + Transporte
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        solicitud.with_user(self.user_transporte).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar todas las revisiones requeridas.
        self.assertEqual(solicitud.state, "approved")

        # Intentar cambiar a recojo después de aprobar
        with self.assertRaises(UserError):
            solicitud.write({"delivery_mode": "pickup"})

    def test_solicitud_rechazada_no_habilita_confirmacion(self):
        """Una solicitud rechazada no permite confirmar la cotización."""
        env_sales = self.env(user=self.user_sales)
        env_admin = self.env(user=self.admin)
        cotizacion = self._crear_cotizacion("A32-RECH-NO-CONFIRMA", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        solicitud.with_user(self.user_abastecimiento).action_reject()

        # Intentar confirmar la cotización directamente
        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales).action_confirm()
        self.assertNotEqual(cotizacion.state, "sale")

    def test_solicitud_cancelada_no_habilita_confirmacion(self):
        """Una solicitud cancelada no permite confirmar la cotización."""
        env_sales = self.env(user=self.user_sales)
        env_admin = self.env(user=self.admin)
        cotizacion = self._crear_cotizacion("A32-CANC-NO-CONFIRMA", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")
        solicitud.with_user(self.user_sales).action_cancel()

        # Intentar confirmar la cotización directamente
        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales).action_confirm()
        self.assertNotEqual(cotizacion.state, "sale")

    # ------------------------------------------------------------------
    # A3.2 - 1.4: Transiciones de estado protegidas
    # ------------------------------------------------------------------
    def test_salto_estado_por_write_bloqueado(self):
        """No se puede saltar estado mediante write() directo."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-SALTO-WRITE", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Intentar escribir directamente de pending_approval a confirmed
        with self.assertRaises(UserError):
            solicitud.with_user(self.user_sales).write(
                {"state": "confirmed"}
            )
        self.assertEqual(solicitud.state, "pending_approval")

    def test_salto_estado_por_rpc_con_contexto_bloqueado(self):
        """Inyectar contexto no autoriza saltos de estado."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-SALTO-RPC", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        with self.assertRaises(UserError):
            solicitud.with_context(sale_order_request_allow_state_write=True).with_user(
                self.user_sales
            ).write({"state": "approved"})
        self.assertEqual(solicitud.state, "pending_approval")

    def test_confirmar_con_solicitud_pendiente_bloqueada(self):
        """No se puede confirmar cotización con solicitud pendiente."""
        env_sales = self.env(user=self.user_sales)
        env_admin = self.env(user=self.admin)
        cotizacion = self._crear_cotizacion("A32-CONF-PEND", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        with self.assertRaises(UserError):
            cotizacion.with_user(self.user_sales).action_confirm()
        self.assertNotEqual(cotizacion.state, "sale")

    # ------------------------------------------------------------------
    # Flujos legítimos (hasta approved; accepted bloqueado por stock B-08)
    # ------------------------------------------------------------------
    def test_flujo_legítimo_una_aprobacion(self):
        """Flujo válido: pickup + stock insuficiente → solo Abastecimiento
        → aprobación → estado approved."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-FLUJO-1", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )

        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Solo se requiere Abastecimiento (pickup + stock insuficiente)
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.validation_status, "validated")
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

        # La aceptación final se permite con aprobaciones completas pese a stock insuficiente
        solicitud.with_user(self.user_sales).action_accept()
        self.assertEqual(solicitud.state, "confirmed")
        self.assertEqual(self.env["sale.order"].browse(cotizacion.id).state, "sale")

    def test_flujo_legítimo_ambas_aprobaciones(self):
        """Flujo válido: despacho + stock insuficiente → Abastecimiento +
        Transporte → aprobación → estado approved."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-FLUJO-2", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )

        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
        self.assertEqual(len(solicitud.review_ids), 2)

        # Abastecimiento y Transporte validan en paralelo
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        solicitud.with_user(self.user_transporte).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.validation_status, "validated")
        # F-2: aprobación automática al completar todas las revisiones requeridas.
        self.assertEqual(solicitud.state, "approved")

        # La aceptación final se permite con aprobaciones completas pese a stock insuficiente
        solicitud.with_user(self.user_sales).action_accept()
        self.assertEqual(solicitud.state, "confirmed")
        self.assertEqual(self.env["sale.order"].browse(cotizacion.id).state, "sale")

    def test_aprobaciones_independientes_y_paralelas(self):
        """Abastecimiento y Transporte pueden validar en cualquier orden."""
        env_sales = self.env(user=self.user_sales)
        cotizacion = self._crear_cotizacion("A32-PARALELAS", "sent")
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        # Transporte valida primero
        solicitud.with_user(self.user_transporte).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        def_transporte = self._obtener_def_transporte()
        review_t = solicitud.review_ids.filtered(
            lambda r: r.definition_id.id == def_transporte.id
        )
        self.assertEqual(review_t.status, "approved")

        # Luego Abastecimiento valida
        solicitud.with_user(self.user_abastecimiento).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.validation_status, "validated")
