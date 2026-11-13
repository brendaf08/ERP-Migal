# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Pruebas automatizadas para sale_revision_tier_compat.

Prueban:
- Conservacion del historial tier.review al crear revisiones.
- Independencia de aprobaciones entre revisiones sucesivas.
- Creacion de revisiones sucesivas sin eliminacion accidental.
- Proteccion de confirmacion sin aprobaciones requeridas.
- Alcance limitado del contexto preserve_tier_reviews_on_revision.
"""

from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestSaleRevisionTierCompat(TransactionCase):
    """Pruebas de compatibilidad entre OCA Revision y Tier Validation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.admin = cls.env.ref("base.user_admin", raise_if_not_found=False) or cls.env["res.users"].browse(2)
        if not cls.admin.exists():
            cls.admin = cls.env.user

        def _ensure_reviewer(xmlid, login, name):
            user = cls.env.ref(xmlid, raise_if_not_found=False)
            if user and user.exists():
                return user
            user = cls.env["res.users"].search([("login", "=", login)], limit=1)
            if user:
                return user
            vals = {
                "name": name,
                "login": login,
                "email": f"{login}@example.com",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
            if "autopost_bills" in cls.env["res.partner"]._fields:
                vals["autopost_bills"] = "ask"
            return cls.env["res.users"].create(vals)

        cls.aprobador_a = _ensure_reviewer(
            "base.user_demo", "compat_reviewer_a", "Compat Reviewer A"
        )
        cls.aprobador_b = _ensure_reviewer(
            "sale_revision_tier_compat.reviewer_b", "compat_reviewer_b", "Compat Reviewer B"
        )

        # Partner y producto existentes o creados para BD limpia
        cls.partner = cls.env["res.partner"].browse(9)
        if not cls.partner.exists():
            cls.partner = cls.env["res.partner"].search(
                [("customer_rank", ">", 0)], limit=1
            )
        if not cls.partner:
            cls.partner = cls.env["res.partner"].create(
                {"name": "Partner Test Compat", "customer_rank": 1}
            )
        cls.product = cls.env["product.product"].browse(64)
        if not cls.product.exists():
            cls.product = cls.env["product.product"].search(
                [("sale_ok", "=", True)], limit=1
            )
        if not cls.product:
            cls.product = cls.env["product.product"].create(
                {"name": "Product Test Compat", "sale_ok": True, "type": "consu"}
            )

        # Definiciones Tier de prueba para escenarios con client_order_ref TIER-TEST
        so_model = cls.env["ir.model"].search([("model", "=", "sale.order")], limit=1)
        if so_model:
            domain_tier = "[('client_order_ref', '=', 'TIER-TEST')]"
            # Alinear con supuestos del test (definicion 1 -> aprobador_a, 2 -> aprobador_b)
            def_by_id = {d.id: d for d in cls.env["tier.definition"].browse([1, 2]).exists()}
            for def_id, reviewer in ((1, cls.aprobador_a), (2, cls.aprobador_b)):
                d = def_by_id.get(def_id)
                if d and d.model_id == so_model:
                    d.write(
                        {
                            "review_type": "individual",
                            "reviewer_id": reviewer.id,
                            "definition_domain": domain_tier,
                            "active": True,
                        }
                    )
            defs = cls.env["tier.definition"].search(
                [("model_id", "=", so_model.id), ("definition_domain", "=", domain_tier), ("active", "=", True)]
            )
            existing_reviewers = defs.mapped("reviewer_id").ids
            for reviewer in (cls.aprobador_a, cls.aprobador_b):
                if reviewer.id in existing_reviewers:
                    continue
                cls.env["tier.definition"].create(
                    {
                        "name": f"Compat Tier {reviewer.login}",
                        "model_id": so_model.id,
                        "review_type": "individual",
                        "reviewer_id": reviewer.id,
                        "definition_domain": domain_tier,
                        "active": True,
                    }
                )

    def _crear_cotizacion(self, ref, estado="sent"):
        """Crea una cotizacion ficticia y opcionalmente la pasa a 'sent'."""
        order = (
            self.env["sale.order"]
            .with_user(self.admin)
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
            order.with_user(self.admin).write({"state": "sent"})
        return order

    def _snap_reviews(self, order):
        """Devuelve una copia de las revisiones Tier de una orden
        (incluyendo archivadas con active_test=False)."""
        return [
            {
                "id": r.id,
                "definition_id": r.definition_id.id,
                "status": r.status,
                "done_by": r.done_by.id if r.done_by else None,
                "done_by_login": r.done_by.login if r.done_by else None,
                "reviewed_date": str(r.reviewed_date)
                if r.reviewed_date
                else None,
                "comment": r.comment or "",
            }
            for r in order.with_context(active_test=False).review_ids.sorted("id")
        ]

    def _ids_reviews(self, rows):
        return [r["id"] for r in rows]

    def _aprobar_revisiones(self, order):
        """Solicita y aprueba todas las revisiones Tier de una orden."""
        order.with_user(self.admin).request_validation()
        order.with_user(self.aprobador_a).validate_tier()
        order.with_user(self.aprobador_b).validate_tier()
        return self._snap_reviews(order)

    # ------------------------------------------------------------------
    # Caso A: versionado sin aprobaciones previas
    # ------------------------------------------------------------------
    def test_caso_a_versionado_sin_aprobaciones(self):
        """Versionado de cotizacion sin historial Tier."""
        orden = self._crear_cotizacion("TEST-A-NO-TIER", "sent")
        nombre_base = orden.name

        nueva = orden.create_revision_preserving_tier()
        self.env.invalidate_all()
        nueva = self.env["sale.order"].browse(nueva.id)

        self.assertEqual(nueva.name, nombre_base + "-01")
        self.assertEqual(nueva.revision_number, 1)
        self.assertEqual(nueva.unrevisioned_name, nombre_base)
        self.assertEqual(nueva.state, "draft")
        self.assertEqual(nueva.active, True)
        self.assertEqual(orden.state, "cancel")
        self.assertEqual(orden.active, False)
        self.assertEqual(orden.current_revision_id, nueva)
        self.assertFalse(nueva.current_revision_id)
        self.assertEqual(self._snap_reviews(nueva), [])

    # ------------------------------------------------------------------
    # Caso B: versionado con dos aprobaciones completadas
    # ------------------------------------------------------------------
    def test_caso_b_versionado_con_aprobaciones_completadas(self):
        """Historial Tier conservado al crear revision de cotizacion aprobada."""
        orden = self._crear_cotizacion("TIER-TEST", "sent")
        orden.with_user(self.admin).request_validation()
        orden.with_user(self.aprobador_a).validate_tier()
        orden.with_user(self.aprobador_b).validate_tier()

        antes = self._snap_reviews(orden)
        ids_antes = self._ids_reviews(antes)
        self.assertEqual(len(antes), 2)
        self.assertTrue(all(r["status"] == "approved" for r in antes))

        nueva = orden.create_revision_preserving_tier()
        self.env.invalidate_all()
        orden = self.env["sale.order"].browse(orden.id)
        nueva = self.env["sale.order"].browse(nueva.id)

        # La orden anterior conserva su historial
        despues = self._snap_reviews(orden)
        ids_despues = self._ids_reviews(despues)
        self.assertEqual(ids_despues, ids_antes)
        self.assertTrue(all(r["status"] == "approved" for r in despues))
        self.assertEqual(
            {r["done_by"] for r in despues},
            {self.aprobador_a.id, self.aprobador_b.id},
        )
        self.assertTrue(all(r["reviewed_date"] for r in despues))

        # La orden anterior esta cancelada y archivada
        self.assertEqual(orden.state, "cancel")
        self.assertEqual(orden.active, False)

        # La nueva revision no hereda historial
        self.assertEqual(self._snap_reviews(nueva), [])

        # La nueva revision debe cumplir el dominio Tier para generar
        # sus propias aprobaciones: asignar client_order_ref y invalidar
        # el campo computed need_validation.
        nueva.with_user(self.admin).write({"client_order_ref": "TIER-TEST"})
        nueva.invalidate_recordset(["need_validation"])
        self.env.invalidate_all()
        nueva = self.env["sale.order"].browse(nueva.id)
        self.assertTrue(nueva.need_validation)

        # La nueva revision genera su propio ciclo de aprobacion
        nueva.with_user(self.admin).request_validation()
        self.env.invalidate_all()
        nueva = self.env["sale.order"].browse(nueva.id)
        nuevas_reviews = self._snap_reviews(nueva)
        self.assertEqual(len(nuevas_reviews), 2)
        self.assertFalse(set(self._ids_reviews(nuevas_reviews)) & set(ids_antes))

    # ------------------------------------------------------------------
    # Caso C: versionado con aprobaciones rechazadas
    # ------------------------------------------------------------------
    def test_caso_c_versionado_con_rechazo(self):
        """Historial de rechazo conservado al crear revision."""
        orden = self._crear_cotizacion("TIER-TEST", "sent")
        orden.with_user(self.admin).request_validation()

        # Rechazar una de las dos revisiones (aprobador A), usando el registro real del fixture
        review_a = orden.review_ids.filtered(
            lambda r: r.reviewer_id == self.aprobador_a
        )
        if not review_a:
            review_a = orden.review_ids.filtered(
                lambda r: self.aprobador_a in r.reviewer_ids
            )
        if not review_a:
            review_a = orden.review_ids.filtered(
                lambda r: r.definition_id.reviewer_id == self.aprobador_a
            )
        review_a = review_a[:1]
        review_a.write({"status": "rejected"})

        antes = self._snap_reviews(orden)
        ids_antes = self._ids_reviews(antes)
        self.assertEqual(len(antes), 2)
        rechazadas = [r for r in antes if r["status"] == "rejected"]
        self.assertEqual(len(rechazadas), 1)
        self.assertEqual(rechazadas[0]["done_by"], None)

        nueva = orden.create_revision_preserving_tier()
        self.env.invalidate_all()
        orden = self.env["sale.order"].browse(orden.id)

        despues = self._snap_reviews(orden)
        ids_despues = self._ids_reviews(despues)
        self.assertEqual(ids_despues, ids_antes)
        rechazadas_despues = [r for r in despues if r["status"] == "rejected"]
        self.assertEqual(len(rechazadas_despues), 1)

        # La nueva revision genera su propio ciclo
        nueva = self.env["sale.order"].browse(orden.current_revision_id.id)
        nueva.with_user(self.admin).write({"client_order_ref": "TIER-TEST"})
        nueva.invalidate_recordset(["need_validation"])
        self.env.invalidate_all()
        nueva = self.env["sale.order"].browse(nueva.id)
        nueva.with_user(self.admin).request_validation()
        self.env.invalidate_all()
        nueva = self.env["sale.order"].browse(nueva.id)
        nuevas_reviews = self._snap_reviews(nueva)
        self.assertEqual(len(nuevas_reviews), 2)
        self.assertTrue(all(r["status"] == "pending" for r in nuevas_reviews))

    # ------------------------------------------------------------------
    # Caso D: varias revisiones sucesivas
    # ------------------------------------------------------------------
    def test_caso_d_varias_revisiones_sucesivas(self):
        """Cadena de 4 revisiones de una misma familia con historial independiente."""
        orden = self._crear_cotizacion("TIER-TEST", "sent")
        nombre_base = orden.name

        revisiones = [orden]
        for i in range(1, 4):
            prev = revisiones[-1]
            # Aprobar la revision anterior antes de crear la siguiente
            prev.with_user(self.admin).write({"client_order_ref": "TIER-TEST"})
            prev.invalidate_recordset(["need_validation"])
            self.env.invalidate_all()
            prev = self.env["sale.order"].browse(prev.id)
            prev.with_user(self.admin).request_validation()
            prev.with_user(self.aprobador_a).validate_tier()
            prev.with_user(self.aprobador_b).validate_tier()

            nueva = prev.create_revision_preserving_tier()
            self.env.invalidate_all()
            nueva = self.env["sale.order"].browse(nueva.id)
            revisiones.append(nueva)

        # Verificar familia completa
        familia = (
            self.env["sale.order"]
            .with_context(active_test=False)
            .search([("unrevisioned_name", "=", nombre_base)])
        )
        self.assertEqual(len(familia), 4)

        # Verificar numeracion
        nombres_ordenados = sorted(familia.mapped("name"))
        self.assertEqual(
            nombres_ordenados,
            [nombre_base, nombre_base + "-01", nombre_base + "-02", nombre_base + "-03"],
        )

        # Solo la ultima esta vigente
        vigentes = self.env["sale.order"].search(
            [("unrevisioned_name", "=", nombre_base)]
        )
        self.assertEqual(len(vigentes), 1)
        self.assertEqual(vigentes, revisiones[-1])
        self.assertEqual(revisiones[-1].state, "draft")
        self.assertEqual(revisiones[-1].active, True)

        # Las anteriores estan canceladas y archivadas
        for r in revisiones[:-1]:
            self.assertEqual(r.state, "cancel")
            self.assertEqual(r.active, False)

        # Aprobar tambien la ultima revision (no se aprobo dentro del bucle)
        ultima = revisiones[-1]
        ultima.with_user(self.admin).write({"client_order_ref": "TIER-TEST"})
        ultima.invalidate_recordset(["need_validation"])
        self.env.invalidate_all()
        ultima = self.env["sale.order"].browse(ultima.id)
        ultima.with_user(self.admin).request_validation()
        ultima.with_user(self.aprobador_a).validate_tier()
        ultima.with_user(self.aprobador_b).validate_tier()

        # Cada revision tiene su propio historial (2 aprobaciones cada una)
        for i, r in enumerate(revisiones):
            self.env.invalidate_all()
            r = self.env["sale.order"].browse(r.id)
            reviews = self._snap_reviews(r)
            self.assertEqual(len(reviews), 2)
            self.assertTrue(all(r2["status"] == "approved" for r2 in reviews))

        # No hay registros eliminados o duplicados
        total_reviews = (
            self.env["tier.review"]
            .with_context(active_test=False)
            .search_count(
                [
                    ("model", "=", "sale.order"),
                    ("res_id", "in", familia.ids),
                ]
            )
        )
        self.assertEqual(total_reviews, 8)  # 4 revisiones x 2 aprobaciones

    # ------------------------------------------------------------------
    # Caso E: proteccion de confirmacion
    # ------------------------------------------------------------------
    def test_caso_e_proteccion_confirmacion(self):
        """Una cotizacion con aprobaciones pendientes no puede confirmarse."""
        orden = self._crear_cotizacion("TIER-TEST", "sent")
        orden.with_user(self.admin).request_validation()

        with self.assertRaises(ValidationError):
            orden.with_user(self.admin).action_confirm()

    # ------------------------------------------------------------------
    # Caso F: operaciones ajenas al versionado
    # ------------------------------------------------------------------
    def test_caso_f_operaciones_afora_versionado(self):
        """El contexto no afecta operaciones normales de Tier Validation."""
        # Cancelacion ordinaria (sin crear revision) elimina revisiones segun
        # el comportamiento estandar de Tier Validation
        orden = self._crear_cotizacion("TIER-TEST", "sent")
        orden.with_user(self.admin).request_validation()
        orden.with_user(self.aprobador_a).validate_tier()
        orden.with_user(self.aprobador_b).validate_tier()

        antes = self._snap_reviews(orden)
        self.assertEqual(len(antes), 2)

        orden.with_user(self.admin).action_cancel()
        self.env.invalidate_all()
        orden = self.env["sale.order"].browse(orden.id)
        despues = self._snap_reviews(orden)
        self.assertEqual(despues, [])

    # ------------------------------------------------------------------
    # Alcance del contexto
    # ------------------------------------------------------------------
    def test_contexto_alcance_limitado(self):
        """preserve_tier_reviews_on_revision solo afecta a create_revision,
        no a operaciones normales."""
        orden = self._crear_cotizacion("TIER-TEST", "sent")
        orden.with_user(self.admin).request_validation()
        orden.with_user(self.aprobador_a).validate_tier()
        orden.with_user(self.aprobador_b).validate_tier()

        antes = self._snap_reviews(orden)
        ids_antes = self._ids_reviews(antes)

        # Sin el contexto, una cancelacion ordinaria sigue eliminando revisiones
        orden.with_user(self.admin).action_cancel()
        self.env.invalidate_all()
        orden = self.env["sale.order"].browse(orden.id)
        despues = self._snap_reviews(orden)
        self.assertEqual(despues, [])
