# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Pruebas de seguridad operativa y grupos/ACL — Fase B2 — sale_order_request.

Verifican los permisos de los grupos  (62/63/64) con usuarios sintéticos:

- Vendedor de solicitudes de orden de venta (grupo 62): puede leer/escribir/crear solicitudes de su compañía
- Abastecimiento (grupo 63): puede leer/escribir solicitudes de su compañía
- Transporte (grupo 64): puede leer/escribir solicitudes de su compañía
- Usuario sin grupo : solo lectura (base.group_user)
- Aislamiento multiempresa: un usuario no puede acceder a solicitudes de otra compañía
- Protección de operaciones sensibles: no se pueden eludir las validaciones de negocio

Usan usuarios sintéticos creados en la prueba (no usuarios reales de ).
"""

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestB2GruposACLUsuarios(TransactionCase):
    """Seguridad operativa: grupos, ACL y usuarios de Solicitud de orden de venta."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.admin = cls.env["res.users"].browse(2)
        cls.partner = cls.env["res.partner"].search(
            [("customer_rank", ">", 0)], limit=1
        )
        if not cls.partner:
            cls.partner = cls.env["res.partner"].create(
                {"name": "Cliente Test B2", "customer_rank": 1}
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

        cls.product = cls.env["product.product"].create({
            "name": "Producto B2",
            "type": "consu",
            "sale_ok": True,
        })

        # Crear almacenes para compañías 2 y 3 si no existen
        Warehouse = cls.env["stock.warehouse"]
        for comp in [cls.company_2, cls.company_3]:
            existing = Warehouse.search([("company_id", "=", comp.id)], limit=1)
            if not existing:
                Warehouse.create({
                    "name": "Almacén %s" % comp.name,
                    "code": "WH%s" % comp.id,
                    "company_id": comp.id,
                })

        # Usuarios de prueba sintéticos - COMPAÑÍA 1
        cls.user_sales_c1 = cls._crear_usuario(
            "user_b2_sales_c1", [cls.company_1.id],
            ["base.group_user", "sales_team.group_sale_salesman",
             "sale_order_request.group_sale_order_request_salesperson"]
        )
        cls.user_abast_c1 = cls._crear_usuario(
            "user_b2_abast_c1", [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_supply"]
        )
        cls.user_trans_c1 = cls._crear_usuario(
            "user_b2_trans_c1", [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_transport"]
        )
        cls.user_plain_c1 = cls._crear_usuario(
            "user_b2_plain_c1", [cls.company_1.id], ["base.group_user"]
        )

        # Usuarios de prueba sintéticos - COMPAÑÍA 2
        cls.user_sales_c2 = cls._crear_usuario(
            "user_b2_sales_c2", [cls.company_2.id],
            ["base.group_user", "sales_team.group_sale_salesman",
             "sale_order_request.group_sale_order_request_salesperson"]
        )
        cls.user_abast_c2 = cls._crear_usuario(
            "user_b2_abast_c2", [cls.company_2.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_supply"]
        )

        # Usuarios de prueba sintéticos - COMPAÑÍA 3
        cls.user_sales_c3 = cls._crear_usuario(
            "user_b2_sales_c3", [cls.company_3.id],
            ["base.group_user", "sales_team.group_sale_salesman",
             "sale_order_request.group_sale_order_request_salesperson"]
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
            "sale_request_applicable": sale_request_applicable,
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

    # ------------------------------------------------------------------
    # B2 - Permisos efectivos de cada grupo (misma compañía)
    # ------------------------------------------------------------------
    def test_vendedor_c1_puede_crear_leer_editar_solicitud_propia(self):
        """Vendedor de c1 puede crear, leer y editar su propia solicitud."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B2-VENTA-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        # Puede leer
        leida = env_sales["sale.order.request"].browse(solicitud.id)
        self.assertEqual(leida.id, solicitud.id)
        # Puede escribir (cambiar delivery_mode en borrador)
        leida.write({"delivery_mode": "delivery"})
        self.assertEqual(leida.delivery_mode, "delivery")

    def test_abast_c1_puede_leer_escribir_solicitud_su_compania(self):
        """Abastecimiento de c1 puede leer y escribir solicitudes de su compañía."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B2-ABAST-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        # Abastecimiento puede leer y operar en su compañía
        leida = env_abast["sale.order.request"].browse(solicitud.id)
        self.assertEqual(leida.id, solicitud.id)
        solicitud.with_user(self.user_abast_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_abast["sale.order.request"].browse(solicitud.id)
        # F-2: al completar la revisión requerida, la solicitud queda aprobada.
        self.assertEqual(solicitud.state, "approved")

    def test_trans_c1_puede_leer_escribir_solicitud_su_compania(self):
        """Transporte de c1 puede leer y escribir solicitudes de su compañía."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        env_trans = self.env(user=self.user_trans_c1)
        cotizacion = self._crear_cotizacion(
            "B2-TRANS-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "delivery", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        # Transporte puede leer
        leida = env_trans["sale.order.request"].browse(solicitud.id)
        self.assertEqual(leida.id, solicitud.id)
        # Para delivery, ambos revisores (abastecimiento y transporte) deben validar
        solicitud.with_user(self.user_abast_c1).validate_tier()
        solicitud.with_user(self.user_trans_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = env_trans["sale.order.request"].browse(solicitud.id)
        # F-2: al completar todas las revisiones requeridas, queda aprobada.
        self.assertEqual(solicitud.state, "approved")

    # ------------------------------------------------------------------
    # B2 - Usuario sin grupo : solo lectura
    # ------------------------------------------------------------------
    def test_usuario_sin_grupo_solicitud_solo_lectura(self):
        """Usuario sin grupo  solo puede leer solicitudes de su compañía."""
        env_plain = self.env(user=self.user_plain_c1)
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "B2-PLAIN-C1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        # Puede leer (base.group_user tiene read)
        leida = env_plain["sale.order.request"].browse(solicitud.id)
        self.assertEqual(leida.id, solicitud.id)
        # No puede escribir (no tiene grupo  / sin permiso de escritura ACL).
        # Escritura no-op con valor actual: evita guardia de negocio de solicitante
        # (write 339-340) y permite que BaseModel.write aplique check_access('write').
        with self.assertRaises(AccessError):
            env_plain["sale.order.request"].browse(solicitud.id).write(
                {"delivery_mode": solicitud.delivery_mode}
            )

    # ------------------------------------------------------------------
    # B2 - Aislamiento multiempresa
    # ------------------------------------------------------------------
    def test_vendedor_c1_no_puede_acceder_solicitud_c2(self):
        """Vendedor de c1 no puede leer/modificar solicitud de c2."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "B2-ISO-C2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )
        # No puede leer
        rec = env_sales_c1["sale.order.request"].browse(solicitud_c2.id)
        with self.assertRaises(AccessError):
            _ = rec.name
        # No puede escribir
        with self.assertRaises(AccessError):
            env_sales_c1["sale.order.request"].browse(solicitud_c2.id).write(
                {"delivery_mode": "delivery"}
            )

    def test_abast_c1_no_puede_aprobar_solicitud_c2(self):
        """Abastecimiento de c1 no puede aprobar solicitud de c2."""
        env_abast_c1 = self.env(user=self.user_abast_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "B2-ABAST-C2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )
        solicitud_c2.with_user(self.user_sales_c2).action_request_validation()
        # No puede aprobar
        with self.assertRaises(AccessError):
            env_abast_c1["sale.order.request"].browse(solicitud_c2.id).action_approve()

    # ------------------------------------------------------------------
    # B2 - Líneas de solicitud: aislamiento por compañía
    # ------------------------------------------------------------------
    def test_lineas_solicitud_aisladas_por_compania(self):
        """Usuario de c1 no puede leer líneas de solicitud de c2."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "B2-LINEAS-C2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )
        linea_id = solicitud_c2.line_ids[0].id
        rec = env_sales_c1["sale.order.request.line"].browse(linea_id)
        with self.assertRaises(AccessError):
            _ = rec.request_id

    # ------------------------------------------------------------------
    # B2 - Confirmación comercial sin autorización cruzada
    # ------------------------------------------------------------------
    def test_vendedor_c1_no_puede_confirmar_cotizacion_c2(self):
        """Vendedor de c1 no puede confirmar cotización de c2."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "B2-CONF-C2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )
        solicitud_c2.with_user(self.user_sales_c2).action_request_validation()
        solicitud_c2.with_user(self.user_abast_c2).validate_tier()
        self.env.invalidate_all()
        solicitud_c2 = env_sales_c2["sale.order.request"].browse(solicitud_c2.id)
        # Pickup + stock insuficiente (qty 5.0): F-2 aprueba al completar Abastecimiento.
        self.assertEqual(solicitud_c2.state, "approved")
        # Vendedor de c1 no puede confirmar cotización de c2
        with self.assertRaises(AccessError):
            env_sales_c1["sale.order"].browse(cotizacion_c2.id).action_confirm()

    # ------------------------------------------------------------------
    # B2 - Operaciones legítimas en compañía autorizada
    # ------------------------------------------------------------------
    def test_flujo_completo_compania_1(self):
        """Flujo completo legítimo en compañía 1."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abast_c1)
        cotizacion = self._crear_cotizacion(
            "B2-FLUJO-C1", self.company_1, self.user_sales_c1
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
        self.assertEqual(solicitud.state, "approved")

    def test_flujo_completo_compania_2(self):
        """Flujo completo legítimo en compañía 2."""
        env_sales = self.env(user=self.user_sales_c2)
        env_abast = self.env(user=self.user_abast_c2)
        cotizacion = self._crear_cotizacion(
            "B2-FLUJO-C2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion, self.user_sales_c2)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c2).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
        solicitud.with_user(self.user_abast_c2).validate_tier()
        self.env.invalidate_all()
        solicitud = env_abast["sale.order.request"].browse(solicitud.id)
        self.assertEqual(solicitud.state, "approved")

    def test_flujo_completo_compania_3(self):
        """Flujo completo legítimo en compañía 3 (solo vendedor)."""
        env_sales = self.env(user=self.user_sales_c3)
        cotizacion = self._crear_cotizacion(
            "B2-FLUJO-C3", self.company_3, self.user_sales_c3
        )
        self._mark_as_subject(cotizacion, self.user_sales_c3)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c3).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")
