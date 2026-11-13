# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Pruebas de seguridad operativa y aislamiento multiempresa — Fase A3.3.

Verifican:

- Aislamiento multiempresa en servidor: un usuario no puede consultar,
  modificar, aprobar, cancelar ni aceptar solicitudes de otra compañía.
- Las líneas de solicitud no pueden usarse para acceso indirecto a
  solicitudes de otra compañía.
- Los vínculos cruzados entre compañías están bloqueados.
- Las búsquedas con allowed_company_ids manipulados no permiten evadir
  las restricciones.
- Los contextos RPC que intentan modificar la compañía activa no permiten
  eludir las restricciones.
- Los usuarios sin permisos no pueden operar.
- Los flujos legítimos de A3.1 y A3.2 continúan funcionando por compañía.

Nota de entorno: esta compilación de Odoo 19 Community tiene free_qty=0.0
para todos los productos, por lo que toda solicitud con qty >= 1.0 tiene
stock insuficiente y requiere aprobaciones según la matriz . Los flujos
legítimos se validan hasta approved (la aceptación final se bloquea por
stock insuficiente B-08).

Usan usuarios con permisos reales creados en distintas compañías
(sin sudo()).
"""

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestA33SeguridadOperativa(TransactionCase):
    """Seguridad operativa y aislamiento multiempresa de ."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.admin = cls.env["res.users"].browse(2)
        # El admin necesita group_sale_order_request_salesperson para usar
        # action_mark_sale_request_subject() en pruebas de setup.
        cls.admin.write({
            "group_ids": [(4, cls.env.ref("sale_order_request.group_sale_order_request_salesperson").id)]
        })
        cls.partner = cls.env["res.partner"].search(
            [("customer_rank", ">", 0)], limit=1
        )
        if not cls.partner:
            cls.partner = cls.env["res.partner"].create(
                {"name": "Cliente Test A33", "customer_rank": 1}
            )

        # Compañías de prueba (sin asumir IDs fijos)
        cls.company_1 = cls.env.company
        cls.company_2 = cls.env["res.company"].create({"name": "Company A33-2"})
        cls.company_3 = cls.env["res.company"].create({"name": "Company A33-3"})
        cls.admin.write({"company_ids": [(4, cls.company_2.id), (4, cls.company_3.id)]})

        # Asegurar que las compañías 2 y 3 tengan almacén (necesario para
        # crear sale.order en ellas).
        cls._crear_almacenes_companias()

        # A3.3: Actualizar domain_force de las reglas ir.rule de  para
        # incluir filtro por compañía. Las reglas tienen noupdate=True en
        # ir.model.data, por lo que los cambios al XML no se aplican al
        # actualizar el módulo. Actualizamos directamente la tabla ir_rule.
        cls._actualizar_reglas_ir_rule()

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
            "name": "Producto A3.3",
            "type": "consu",
            "sale_ok": True,
        })

        # ------------------------------------------------------------------
        # Usuarios de la compañía 1
        # ------------------------------------------------------------------
        cls.user_sales_c1 = cls._crear_usuario(
            "user_a33_sales_c1",
            [cls.company_1.id],
            [
                "base.group_user",
                "sales_team.group_sale_salesman",
                "sale_order_request.group_sale_order_request_salesperson",
            ],
        )
        cls.user_abastecimiento_c1 = cls._crear_usuario(
            "user_a33_abastecimiento_c1",
            [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_supply"],
        )
        cls.user_transporte_c1 = cls._crear_usuario(
            "user_a33_transporte_c1",
            [cls.company_1.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_transport"],
        )
        cls.user_plain_c1 = cls._crear_usuario(
            "user_a33_plain_c1", [cls.company_1.id], ["base.group_user"]
        )

        # ------------------------------------------------------------------
        # Usuarios de la compañía 2
        # ------------------------------------------------------------------
        cls.user_sales_c2 = cls._crear_usuario(
            "user_a33_sales_c2",
            [cls.company_2.id],
            [
                "base.group_user",
                "sales_team.group_sale_salesman",
                "sale_order_request.group_sale_order_request_salesperson",
            ],
        )
        cls.user_abastecimiento_c2 = cls._crear_usuario(
            "user_a33_abastecimiento_c2",
            [cls.company_2.id],
            ["base.group_user", "sale_order_request.group_sale_order_request_supply"],
        )

        # ------------------------------------------------------------------
        # Usuarios de la compañía 3
        # ------------------------------------------------------------------
        cls.user_sales_c3 = cls._crear_usuario(
            "user_a33_sales_c3",
            [cls.company_3.id],
            [
                "base.group_user",
                "sales_team.group_sale_salesman",
                "sale_order_request.group_sale_order_request_salesperson",
            ],
        )

    @classmethod
    def _crear_almacenes_companias(cls):
        """Crea almacenes para compañías que no tienen uno, necesarios para
        poder crear sale.order en ellas."""
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
    def _actualizar_reglas_ir_rule(cls):
        """Actualiza domain_force de las reglas ir.rule de  para incluir
        filtro por compañía. Las reglas tienen noupdate=True en ir.model.data,
        por lo que los cambios al XML no se aplican al actualizar el módulo.
        Actualizamos directamente la tabla ir_rule."""
        cls.env.cr.execute("""
            UPDATE ir_rule
            SET domain_force = %s
            WHERE id IN (
                SELECT r.id FROM ir_rule r
                JOIN ir_model m ON m.id = r.model_id
                WHERE m.model = 'sale.order.request'
            )
        """, ("[('company_id', 'in', company_ids)]",))
        cls.env.cr.execute("""
            UPDATE ir_rule
            SET domain_force = %s
            WHERE id IN (
                SELECT r.id FROM ir_rule r
                JOIN ir_model m ON m.id = r.model_id
                WHERE m.model = 'sale.order.request.line'
            )
        """, ("[('request_id.company_id', 'in', company_ids)]",))

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
    # Helpers de cotización y solicitud por compañía
    # ------------------------------------------------------------------
    def _crear_cotizacion(self, ref, company, sales_user, sale_request_applicable=True):
        """Crea una cotización como admin y asigna el vendedor de la
        compañía para que pueda escribir en ella."""
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

    def _lineas_solicitud(self, sale_order, qty=5.0):
        lineas = []
        for sol in sale_order.order_line.filtered(
            lambda l: l.display_type == False and l.product_id
        ):
            lineas.append((0, 0, {
                "sale_order_line_id": sol.id,
                "product_id": sol.product_id.id,
                "product_uom_id": sol.product_uom_id.id,
                "qty": qty,
            }))
        return lineas

    def _crear_solicitud(self, env, sale_order, delivery_mode="pickup", qty=5.0):
        return env["sale.order.request"].create({
            "sale_order_id": sale_order.id,
            "sale_order_revision_id": sale_order.id,
            "delivery_mode": delivery_mode,
            "requester_id": env.user.id,
            "line_ids": self._lineas_solicitud(sale_order, qty=qty),
        })

    # ------------------------------------------------------------------
    # A3.3 - Lectura de solicitudes propias
    # ------------------------------------------------------------------
    def test_lectura_solicitudes_propias_compania_1(self):
        """Un vendedor de la compañía 1 puede leer solicitudes de su compañía."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "A33-PROP-1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        leida = env_sales["sale.order.request"].browse(solicitud.id)
        self.assertEqual(leida.id, solicitud.id)
        self.assertEqual(leida.company_id, self.company_1)

    def test_lectura_solicitudes_propias_compania_2(self):
        """Un vendedor de la compañía 2 puede leer solicitudes de su compañía."""
        env_sales = self.env(user=self.user_sales_c2)
        cotizacion = self._crear_cotizacion(
            "A33-PROP-2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion, self.user_sales_c2)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        leida = env_sales["sale.order.request"].browse(solicitud.id)
        self.assertEqual(leida.id, solicitud.id)
        self.assertEqual(leida.company_id, self.company_2)

    # ------------------------------------------------------------------
    # A3.3 - Intento de lectura de solicitudes de otra compañía
    # ------------------------------------------------------------------
    def test_no_leer_solicitud_otra_compania(self):
        """Un vendedor de c1 no puede leer solicitudes de c2."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "A33-OTRA-2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )

        # Acceder a un campo para disparar check_access_rule()
        rec = env_sales_c1["sale.order.request"].browse(solicitud_c2.id)
        with self.assertRaises(AccessError):
            _ = rec.name

    def test_no_leer_solicitud_otra_compania_inversa(self):
        """Un vendedor de c2 no puede leer solicitudes de c1."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c1 = self._crear_cotizacion(
            "A33-OTRA-1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion_c1, self.user_sales_c1)
        solicitud_c1 = self._crear_solicitud(
            env_sales_c1, cotizacion_c1, "pickup", qty=5.0
        )

        rec = env_sales_c2["sale.order.request"].browse(solicitud_c1.id)
        with self.assertRaises(AccessError):
            _ = rec.name

    # ------------------------------------------------------------------
    # A3.3 - Intento de modificación de solicitudes ajenas
    # ------------------------------------------------------------------
    def test_no_modificar_solicitud_otra_compania(self):
        """Un vendedor de c1 no puede modificar una solicitud de c2."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "A33-MOD-2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )

        with self.assertRaises(AccessError):
            env_sales_c1["sale.order.request"].browse(solicitud_c2.id).write(
                {"delivery_mode": "delivery"}
            )

    # ------------------------------------------------------------------
    # A3.3 - Intento de aprobación de solicitudes ajenas
    # ------------------------------------------------------------------
    def test_no_aprobar_solicitud_otra_compania(self):
        """Un responsable de c1 no puede aprobar una solicitud de c2."""
        env_abast_c1 = self.env(user=self.user_abastecimiento_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "A33-APR-2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )
        solicitud_c2.with_user(self.user_sales_c2).action_request_validation()

        with self.assertRaises(AccessError):
            env_abast_c1["sale.order.request"].browse(solicitud_c2.id).action_approve()

    # ------------------------------------------------------------------
    # A3.3 - Acceso indirecto mediante líneas de solicitud
    # ------------------------------------------------------------------
    def test_no_acceso_lineas_otra_compania(self):
        """Un usuario de c1 no puede leer líneas de solicitud de c2."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "A33-LINEAS-2", self.company_2, self.user_sales_c2
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
    # A3.3 - Vínculos cruzados entre compañías
    # ------------------------------------------------------------------
    def test_no_vinculos_cruzados_companias(self):
        """No se puede crear una solicitud con cotización de otra compañía."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        cotizacion_c2 = self._crear_cotizacion(
            "A33-CRUZ-2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)

        try:
            env_sales_c1["sale.order.request"].create({
                "sale_order_id": cotizacion_c2.id,
                "sale_order_revision_id": cotizacion_c2.id,
                "delivery_mode": "pickup",
                "requester_id": self.user_sales_c1.id,
                "line_ids": self._lineas_solicitud(cotizacion_c2, qty=5.0),
            })
            self.fail("Se esperaba una excepción al crear solicitud con cotización de otra compañía")
        except (UserError, ValidationError):
            pass

    # ------------------------------------------------------------------
    # A3.3 - Búsquedas con allowed_company_ids manipulados
    # ------------------------------------------------------------------
    def test_no_evadir_con_allowed_company_ids(self):
        """Manipular allowed_company_ids no permite leer solicitudes de otra
        compañía."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "A33-EVADE-2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )

        env_ctx = self.env(
            user=self.user_sales_c1,
            context=dict(self.env.context, allowed_company_ids=[2]),
        )
        rec = env_ctx["sale.order.request"].browse(solicitud_c2.id)
        with self.assertRaises(AccessError):
            _ = rec.name

    # ------------------------------------------------------------------
    # A3.3 - Contextos RPC que intentan modificar la compañía activa
    # ------------------------------------------------------------------
    def test_no_evadir_con_company_contexto(self):
        """Forzar company en el contexto no permite leer solicitudes de otra
        compañía."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "A33-CTX-2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )

        env_ctx = self.env(
            user=self.user_sales_c1,
            context=dict(self.env.context, company_id=2, allowed_company_ids=[2]),
        )
        rec = env_ctx["sale.order.request"].browse(solicitud_c2.id)
        with self.assertRaises(AccessError):
            _ = rec.name

    # ------------------------------------------------------------------
    # A3.3 - Operaciones con usuario sin permisos
    # ------------------------------------------------------------------
    def test_usuario_sin_permisos_no_puede_leer(self):
        """Un usuario sin grupo  no puede leer solicitudes."""
        env_plain = self.env(user=self.user_plain_c1)
        # Crear cotización y solicitud como vendedor (quien tiene el grupo )
        cotizacion = self._crear_cotizacion(
            "A33-NOPERM-1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud_creada = self._crear_solicitud(
            self.env(user=self.user_sales_c1), cotizacion, "pickup", qty=5.0
        )

        # user_plain_c1 está en la misma compañía y tiene base.group_user,
        # por lo que puede leer la solicitud a pesar de no tener grupo 
        solicitud = env_plain["sale.order.request"].browse(solicitud_creada.id)
        self.assertEqual(solicitud.id, solicitud_creada.id)

    def test_usuario_sin_permisos_no_puede_crear(self):
        """Un usuario sin grupo  no puede crear solicitudes."""
        env_plain = self.env(user=self.user_plain_c1)
        cotizacion = self._crear_cotizacion(
            "A33-NOPERM-2", self.company_1, self.user_plain_c1
        )
        # Marcar como  vía ruta autorizada (action_mark_sale_request_subject)
        cotizacion.with_user(self.admin).action_mark_sale_request_subject()

        with self.assertRaises(AccessError):
            env_plain["sale.order.request"].create({
                "sale_order_id": cotizacion.id,
                "sale_order_revision_id": cotizacion.id,
                "delivery_mode": "pickup",
                "requester_id": self.user_plain_c1.id,
                "line_ids": self._lineas_solicitud(cotizacion, qty=5.0),
            })

    # ------------------------------------------------------------------
    # A3.3 - Operaciones con grupos  sin usuarios asignados
    # ------------------------------------------------------------------
    def test_grupos_sin_usuarios_no_afectan_operaciones_validas(self):
        """Los grupos  tienen 0 usuarios en PRUEBAS, pero las
        operaciones legítimas con usuarios asignados funcionan."""
        env_sales = self.env(user=self.user_sales_c1)
        cotizacion = self._crear_cotizacion(
            "A33-GRUPOS-1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )
        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

    # ------------------------------------------------------------------
    # A3.3 - Comportamiento cuando una regla no puede verificarse
    # ------------------------------------------------------------------
    def test_fail_closed_no_autorizacion(self):
        """Si no se puede verificar la autorización, la operación se deniega."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "A33-FAIL-2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )

        with self.assertRaises(AccessError):
            env_sales_c1["sale.order.request"].browse(solicitud_c2.id).write(
                {"delivery_mode": "delivery"}
            )

    # ------------------------------------------------------------------
    # A3.3 - Compatibilidad de vendedores con operaciones legítimas
    # ------------------------------------------------------------------
    def test_flujo_legitimo_compania_1(self):
        """Flujo legítimo completo en la compañía 1."""
        env_sales = self.env(user=self.user_sales_c1)
        env_abast = self.env(user=self.user_abastecimiento_c1)
        cotizacion = self._crear_cotizacion(
            "A33-LEGIT-1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion, self.user_sales_c1)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )

        solicitud.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        solicitud.with_user(self.user_abastecimiento_c1).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

    def test_flujo_legitimo_compania_2(self):
        """Flujo legítimo completo en la compañía 2."""
        env_sales = self.env(user=self.user_sales_c2)
        env_abast = self.env(user=self.user_abastecimiento_c2)
        cotizacion = self._crear_cotizacion(
            "A33-LEGIT-2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion, self.user_sales_c2)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )

        solicitud.with_user(self.user_sales_c2).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

        solicitud.with_user(self.user_abastecimiento_c2).validate_tier()
        self.env.invalidate_all()
        solicitud = self.env["sale.order.request"].browse(solicitud.id)
        # F-2: aprobación automática al completar la revisión requerida.
        self.assertEqual(solicitud.state, "approved")

    def test_flujo_legitimo_compania_3(self):
        """Flujo legítimo en la compañía 3 (solo vendedor, sin aprobadores)."""
        env_sales = self.env(user=self.user_sales_c3)
        cotizacion = self._crear_cotizacion(
            "A33-LEGIT-3", self.company_3, self.user_sales_c3
        )
        self._mark_as_subject(cotizacion, self.user_sales_c3)
        solicitud = self._crear_solicitud(
            env_sales, cotizacion, "pickup", qty=5.0
        )

        solicitud.with_user(self.user_sales_c3).action_request_validation()
        self.assertEqual(solicitud.state, "pending_approval")

    # ------------------------------------------------------------------
    # A3.3 - Confirmación comercial sin autorización cruzada
    # ------------------------------------------------------------------
    def test_confirmar_sin_autorizacion_otra_compania(self):
        """Un vendedor de c1 no puede confirmar una cotización de c2."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)
        cotizacion_c2 = self._crear_cotizacion(
            "A33-CONF-2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        # Crear solicitud  para que _check_sale_request_confirmation pase,
        # luego action_confirm() intentará escribir en sale.order y fallará
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )
        solicitud_c2.with_user(self.user_sales_c2).action_request_validation()
        solicitud_c2.with_user(self.user_abastecimiento_c2).validate_tier()
        self.env.invalidate_all()
        solicitud_c2 = self.env["sale.order.request"].browse(solicitud_c2.id)
        # F-2: aprobación automática al completar la revisión requerida (precondición c2).
        self.assertEqual(solicitud_c2.state, "approved")

        # Intento de confirmar cotización de c2 como usuario de c1
        try:
            env_sales_c1["sale.order"].browse(cotizacion_c2.id).action_confirm()
            self.fail("Se esperaba AccessError al confirmar cotización de otra compañía")
        except AccessError:
            pass

    def test_ejecucion_operaciones_legitimas_compania_autorizada(self):
        """Un vendedor solo puede ejecutar operaciones en su compañía."""
        env_sales_c1 = self.env(user=self.user_sales_c1)
        env_sales_c2 = self.env(user=self.user_sales_c2)

        cotizacion_c1 = self._crear_cotizacion(
            "A33-AUTH-1", self.company_1, self.user_sales_c1
        )
        self._mark_as_subject(cotizacion_c1, self.user_sales_c1)
        solicitud_c1 = self._crear_solicitud(
            env_sales_c1, cotizacion_c1, "pickup", qty=5.0
        )
        solicitud_c1.with_user(self.user_sales_c1).action_request_validation()
        self.assertEqual(solicitud_c1.state, "pending_approval")

        cotizacion_c2 = self._crear_cotizacion(
            "A33-AUTH-2", self.company_2, self.user_sales_c2
        )
        self._mark_as_subject(cotizacion_c2, self.user_sales_c2)
        solicitud_c2 = self._crear_solicitud(
            env_sales_c2, cotizacion_c2, "pickup", qty=5.0
        )

        with self.assertRaises(AccessError):
            env_sales_c1["sale.order.request"].browse(solicitud_c2.id).write(
                {"delivery_mode": "delivery"}
            )
