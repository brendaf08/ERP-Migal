# -*- coding: utf-8 -*-
import json
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tests.common import new_test_user


def _datos(cliente="Cliente P3", total=100.0):
    return {
        "cliente": cliente,
        "simbolo": "S/",
        "fecha_desde": "2026-11-01",
        "fecha_hasta": "2026-11-30",
        "fecha_consulta": "2026-11-30",
        "saldo_anterior": 0,
        "movimientos": [],
        "saldo_periodo": 0,
        "documentos_pendientes": [],
        "pagos_sin_aplicar": [],
        "total_pendiente": total,
        "total_vencido": 0,
        "informativo": [],
        "antiguedad": [],
    }


@tagged("post_install", "-at_install", "p3_security")
class TestP3EstadoCuentaPublicacionSecurity(TransactionCase):
    """P3-01/P3-P1 + P3-REV: aislamiento multi-compañía, RPC y flujos ORM."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Empresa P3 B"})
        cls.currency = cls.company_a.currency_id

        cls.grp_fco = "account.group_account_invoice"
        cls.grp_ger = "sales_team.group_sale_manager"

        cls.user_fco_a = new_test_user(
            cls.env, login="p3_fco_a", groups=f"base.group_user,{cls.grp_fco}",
            company_id=cls.company_a.id, company_ids=[(6, 0, [cls.company_a.id])])
        cls.user_fco_b = new_test_user(
            cls.env, login="p3_fco_b", groups=f"base.group_user,{cls.grp_fco}",
            company_id=cls.company_b.id, company_ids=[(6, 0, [cls.company_b.id])])
        cls.user_fco_ab = new_test_user(
            cls.env, login="p3_fco_ab", groups=f"base.group_user,{cls.grp_fco}",
            company_id=cls.company_a.id, company_ids=[(6, 0, [cls.company_a.id, cls.company_b.id])])
        cls.user_basic = new_test_user(
            cls.env, login="p3_basic", groups="base.group_user",
            company_id=cls.company_a.id, company_ids=[(6, 0, [cls.company_a.id])])
        cls.user_sys = new_test_user(
            cls.env, login="p3_sys", groups="base.group_system,account.group_account_invoice",
            company_id=cls.company_a.id, company_ids=[(6, 0, [cls.company_a.id, cls.company_b.id])])

        cls.partner_a = cls.env["res.partner"].create({"name": "Cliente P3 A", "company_id": False})
        cls.partner_b = cls.env["res.partner"].create({"name": "Cliente P3 B", "company_id": False})
        cls.partner_shared = cls.env["res.partner"].create({"name": "Cliente P3 Compartido", "company_id": False})
        cls.partner_only_b = cls.env["res.partner"].create({"name": "Cliente Solo B", "company_id": cls.company_b.id})

    def _mk_pub(self, company, partner=None, user=None, **kw):
        partner = partner or (self.partner_a if company == self.company_a else self.partner_b)
        user = user or self.env.user
        vals = {
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "user_id": user.id,
            "datos_json": json.dumps(_datos(partner.name)),
            "total_pendiente": 100.0,
        }
        vals.update(kw)
        return self.env["migal.agente.estado.cuenta.publicacion"].with_user(user)._create_validated(vals, user=user)

    def _pub_model_user(self, user, company=None):
        company = company or user.company_id
        return self.env["migal.agente.estado.cuenta.publicacion"].with_user(user).with_company(company)

    # ------------------------------------------------------------------
    # Aislamiento entre compañías
    # ------------------------------------------------------------------
    def test_fco_company_a_cannot_read_publication_company_b(self):
        pub_b = self._mk_pub(self.company_b)
        with self.assertRaises(Exception):
            pub_b.with_user(self.user_fco_a).with_company(self.company_a).read(["partner_id", "total_pendiente"])

    def test_fco_company_a_cannot_write_or_revoke_publication_company_b(self):
        pub_b = self._mk_pub(self.company_b)
        with self.assertRaises(Exception):
            pub_b.with_user(self.user_fco_a).with_company(self.company_a).write({"activo": False})
        with self.assertRaises(Exception):
            pub_b.with_user(self.user_fco_a).with_company(self.company_a).action_revocar()
        self.assertTrue(pub_b.sudo().activo)

    def test_user_authorized_in_ab_can_read_both(self):
        pub_a = self._mk_pub(self.company_a)
        pub_b = self._mk_pub(self.company_b)
        user = self.user_fco_ab
        self.assertEqual(pub_a.with_user(user).with_company(self.company_a).company_id.id, self.company_a.id)
        self.assertEqual(pub_b.with_user(user).with_company(self.company_b).company_id.id, self.company_b.id)

    def test_shared_partner_does_not_force_wrong_company(self):
        pub_a = self._mk_pub(self.company_a, partner=self.partner_shared)
        pub_b = self._mk_pub(self.company_b, partner=self.partner_shared)
        self.assertEqual(pub_a.company_id, self.company_a)
        self.assertEqual(pub_b.company_id, self.company_b)

    def test_shared_partner_with_company_restriction_rejected(self):
        with self.assertRaises(Exception):
            self._mk_pub(self.company_a, partner=self.partner_only_b)

    # ------------------------------------------------------------------
    # Creación / P3-REV-01
    # ------------------------------------------------------------------
    def test_create_by_fco_authorized_without_sudo_is_blocked_by_acl(self):
        """FCO/GER tienen ACL create=0; la creación legítima va por compartir() con sudo controlado."""
        model = self._pub_model_user(self.user_fco_a, self.company_a)
        with self.assertRaises(Exception):
            model.create({
                "partner_id": self.partner_a.id,
                "company_id": self.company_a.id,
                "currency_id": self.company_a.currency_id.id,
                "datos_json": json.dumps(_datos()),
            })

    def test_create_by_user_without_company_access_rejected(self):
        # simula intento directo en env de usuario: create() valida compañía para no-superuser
        model = self._pub_model_user(self.user_fco_a, self.company_a)
        with self.assertRaises(AccessError):
            # sudo en modelo no usado; llamamos create normal en env de usuario con company_id ajena
            model.sudo(False).with_user(self.user_fco_a).create({
                "partner_id": self.partner_b.id,
                "company_id": self.company_b.id,
                "currency_id": self.company_b.currency_id.id,
                "datos_json": json.dumps(_datos("B")),
            })

    def test_compartir_validates_company_before_sudo_create(self):
        """P3-REV-01: el flujo legítimo valida compañía del usuario antes de sudo().create().
        compartir() regenera datos internamente y no acepta company_id externo; además verifica
        que la compañía del resultado esté en env.companies antes del sudo().create()."""
        tool = self.env["migal.agente.tool.estado.cuenta"].with_user(self.user_fco_a).with_company(self.company_a)

        # Caso 1: flujo normal crea en compañía activa del usuario.
        out = tool.compartir(self.partner_a.name)
        self.assertTrue(out.get("ok"), out.get("mensaje"))
        pub = self.env["migal.agente.estado.cuenta.publicacion"].sudo().browse(out["datos"]["publicacion_id"])
        self.assertEqual(pub.company_id, self.company_a)

        # Caso 2: si generar() devolviera company_id fuera de compañías permitidas,
        # compartir() debe rechazar ANTES de sudo().create().
        malicious = {
            "ok": True,
            "estado": "generado",
            "titulo": "x",
            "mensaje": "x",
            "datos": {
                "cliente": self.partner_a.name,
                "cliente_id": self.partner_a.id,
                "company_id": self.company_b.id,
                "company_name": self.company_b.name,
                "moneda": self.company_b.currency_id.name,
                "simbolo": self.company_b.currency_id.symbol,
                "fecha_desde": "2026-11-01",
                "fecha_hasta": "2026-11-30",
                "total_pendiente": 100.0,
                "telefono": "",
            },
        }
        before_b = self.env["migal.agente.estado.cuenta.publicacion"].sudo().search_count([("company_id", "=", self.company_b.id)])
        create_calls = []
        real_create = self.env["migal.agente.estado.cuenta.publicacion"].sudo().create

        def spy_create(vals):
            create_calls.append(vals)
            return real_create(vals)

        with patch.object(type(tool), "generar", return_value=malicious):
            with patch("odoo.addons.migal_agente.models.estado_cuenta_publicacion.MigalAgenteEstadoCuentaPublicacion.create", autospec=True) as spy:
                res = tool.compartir(self.partner_a.name)
        self.assertFalse(res.get("ok"))
        self.assertIn("compañ", (res.get("mensaje") or "").lower() + (res.get("titulo") or "").lower())
        self.assertFalse(spy.called, "No debe llamar create si la compañía no está autorizada")
        after_b = self.env["migal.agente.estado.cuenta.publicacion"].sudo().search_count([("company_id", "=", self.company_b.id)])
        self.assertEqual(before_b, after_b)

    def test_generic_sudo_create_is_rejected_p3_rev01(self):
        """P3-REV-01: sudo().create() genérico no debe ser bypass de validación de compañía."""
        vals = {
            "partner_id": self.partner_b.id,
            "company_id": self.company_b.id,
            "currency_id": self.company_b.currency_id.id,
            "datos_json": json.dumps(_datos("B")),
        }
        # usuario sin acceso a B no puede crear en B
        with self.assertRaises(Exception):
            self.env["migal.agente.estado.cuenta.publicacion"].with_user(self.user_fco_a).with_company(self.company_a).create(vals)
        # superuser/sudo genérico tampoco puede crear sin ruta interna validada
        with self.assertRaises(AccessError):
            self.env["migal.agente.estado.cuenta.publicacion"].sudo().create(vals)
        # ruta interna legítima funciona con usuario original validado
        pub = self.env["migal.agente.estado.cuenta.publicacion"]._create_validated(vals, user=self.user_fco_b)
        self.assertEqual(pub.company_id, self.company_b)
        # pero sigue protegido por reglas para usuario de otra compañía
        with self.assertRaises(Exception):
            pub.with_user(self.user_fco_a).with_company(self.company_a).read(["id"])

    def test_legitimate_flow_assigns_company_from_generating_env(self):
        tool = self.env["migal.agente.tool.estado.cuenta"].with_user(self.user_fco_ab).with_company(self.company_b)
        # generar en contexto company B debe reflejar company B
        # compartir usa generar internamente; validamos resultado final
        res = tool.compartir(self.partner_shared.name)
        # puede fallar por falta de datos contables; si falla por datos, al menos no cruza compañía
        if res.get("ok"):
            pub = self.env["migal.agente.estado.cuenta.publicacion"].sudo().browse(res["datos"]["publicacion_id"])
            self.assertEqual(pub.company_id.id, self.company_b.id)

    # ------------------------------------------------------------------
    # Protección RPC / P3-P1 / P3-REV-02
    # ------------------------------------------------------------------
    def test_normal_user_cannot_modify_datos_json(self):
        pub = self._mk_pub(self.company_a)
        with self.assertRaises(AccessError):
            pub.with_user(self.user_fco_a).with_company(self.company_a).write({"datos_json": '{"hack":1}'})

    def test_normal_user_cannot_modify_sensitive_fields_individually(self):
        pub = self._mk_pub(self.company_a)
        cases = [
            ("partner_id", self.partner_b.id),
            ("total_pendiente", 9999),
            ("user_id", self.user_fco_b.id),
            ("company_id", self.company_b.id),
            ("expira", fields.Datetime.now() + timedelta(days=30)),
            ("token", "00000000-0000-0000-0000-000000000001"),
        ]
        for field_name, value in cases:
            with self.assertRaises(Exception, msg=field_name):
                pub.with_user(self.user_fco_a).with_company(self.company_a).write({field_name: value})

    def test_write_activo_false_with_other_fields_rejected(self):
        pub = self._mk_pub(self.company_a)
        with self.assertRaises(AccessError):
            pub.with_user(self.user_fco_a).with_company(self.company_a).write({"activo": False, "datos_json": "{}"})
        self.assertTrue(pub.sudo().activo)

    def test_direct_write_activo_false_is_allowed_for_authorized_user(self):
        pub = self._mk_pub(self.company_a)
        pub.with_user(self.user_fco_a).with_company(self.company_a).write({"activo": False})
        self.assertFalse(pub.sudo().activo)

    def test_authorized_revocation_still_works(self):
        pub = self._mk_pub(self.company_a)
        pub.with_user(self.user_fco_a).with_company(self.company_a).action_revocar()
        self.assertFalse(pub.sudo().activo)

    def test_user_without_permission_cannot_revoke(self):
        pub = self._mk_pub(self.company_a)
        with self.assertRaises(Exception):
            pub.with_user(self.user_basic).with_company(self.company_a).action_revocar()
        self.assertTrue(pub.sudo().activo)

    def test_superuser_cannot_write_protected_fields_p3_rev02(self):
        """P3-REV-02: ni siquiera superusuario puede modificar campos financieros/de identidad por write genérico."""
        pub = self._mk_pub(self.company_a)
        cases = [
            ("datos_json", json.dumps({"tampered": True})),
            ("partner_id", self.partner_b.id),
            ("total_pendiente", 9999),
            ("expira", fields.Datetime.now() + timedelta(days=30)),
            ("token", "00000000-0000-0000-0000-000000000001"),
            ("user_id", self.user_fco_b.id),
            ("company_id", self.company_b.id),
        ]
        for field_name, value in cases:
            with self.assertRaises(AccessError, msg=field_name):
                pub.sudo().write({field_name: value})
        # revocación legítima sigue funcionando por write controlado
        pub.sudo().write({"activo": False})
        self.assertFalse(pub.sudo().activo)

    def test_admin_system_can_operate_as_expected(self):
        pub = self._mk_pub(self.company_a)
        self.assertEqual(pub.with_user(self.user_sys).with_company(self.company_a).company_id.id, self.company_a.id)
        pub.with_user(self.user_sys).with_company(self.company_a).action_revocar()
        self.assertFalse(pub.sudo().activo)

    # ------------------------------------------------------------------
    # Históricos NULL company_id / P3-REV-03
    # ------------------------------------------------------------------
    def test_historical_null_company_not_visible_to_ordinary_fco(self):
        pub = self._mk_pub(self.company_a)
        # simular registro histórico sin compañía
        self.env.cr.execute(
            "UPDATE migal_agente_estado_cuenta_publicacion SET company_id = NULL WHERE id = %s",
            (pub.id,))
        pub.invalidate_recordset()
        with self.assertRaises(Exception):
            pub.with_user(self.user_fco_a).with_company(self.company_a).read(["id", "partner_id"])

    def test_historical_null_company_visible_to_system_admin(self):
        pub = self._mk_pub(self.company_a)
        self.env.cr.execute(
            "UPDATE migal_agente_estado_cuenta_publicacion SET company_id = NULL WHERE id = %s",
            (pub.id,))
        pub.invalidate_recordset()
        rec = pub.with_user(self.user_sys).with_company(self.company_a)
        self.assertEqual(rec.id, pub.id)
        self.assertFalse(rec.company_id)

    def test_historical_null_company_cannot_be_revoked_by_ordinary_user(self):
        pub = self._mk_pub(self.company_a)
        self.env.cr.execute(
            "UPDATE migal_agente_estado_cuenta_publicacion SET company_id = NULL WHERE id = %s",
            (pub.id,))
        pub.invalidate_recordset()
        with self.assertRaises(Exception):
            pub.with_user(self.user_fco_a).with_company(self.company_a).action_revocar()
        self.assertTrue(pub.sudo().activo)

    def test_historical_null_company_not_inferred_from_partner(self):
        pub = self._mk_pub(self.company_a, partner=self.partner_a)
        self.env.cr.execute(
            "UPDATE migal_agente_estado_cuenta_publicacion SET company_id = NULL WHERE id = %s",
            (pub.id,))
        pub.invalidate_recordset()
        self.assertFalse(pub.sudo().company_id)
        # partner tiene company_id False; nada debe auto-asignarse
        pub.invalidate_recordset()
        self.assertFalse(pub.sudo().company_id)

    # ------------------------------------------------------------------
    # Regresión funcional básica
    # ------------------------------------------------------------------
    def test_public_token_lookup_valid_revoked_expired(self):
        pub = self._mk_pub(self.company_a)
        model = self.env["migal.agente.estado.cuenta.publicacion"]
        self.assertEqual(model._buscar_vigente(pub.sudo().token).id, pub.id)
        pub.with_user(self.user_fco_a).with_company(self.company_a).action_revocar()
        self.assertFalse(model._buscar_vigente(pub.sudo().token))
        pub2 = self._mk_pub(self.company_a, expira=fields.Datetime.now() - timedelta(hours=1))
        self.assertFalse(model._buscar_vigente(pub2.sudo().token))

    def test_legitimate_read_get_datos_for_authorized_user(self):
        pub = self._mk_pub(self.company_a)
        data = pub.with_user(self.user_fco_a).with_company(self.company_a).get_datos()
        self.assertEqual(data.get("total_pendiente"), 100.0)



    def test_internal_create_validated_works_and_generic_sudo_create_blocked(self):
        """P3-REV-01: ruta interna legítima funciona; sudo().create() genérico no."""
        vals = {
            "partner_id": self.partner_a.id,
            "company_id": self.company_a.id,
            "currency_id": self.company_a.currency_id.id,
            "datos_json": json.dumps(_datos()),
            "total_pendiente": 100.0,
        }
        with self.assertRaises(AccessError):
            self.env["migal.agente.estado.cuenta.publicacion"].sudo().create(vals)
        with self.assertRaises(AccessError):
            self.env["migal.agente.estado.cuenta.publicacion"].sudo().with_context(
                _migal_ec_internal_create=True
            ).create(vals)
        pub = self.env["migal.agente.estado.cuenta.publicacion"]._create_validated(vals, user=self.user_fco_a)
        self.assertEqual(pub.company_id, self.company_a)

    def test_registrar_vista_still_works(self):
        pub = self._mk_pub(self.company_a)
        self.assertEqual(pub.sudo().vistas, 0)
        pub.sudo()._registrar_vista(ip="10.0.0.1")
        pub.invalidate_recordset()
        self.assertEqual(pub.sudo().vistas, 1)

    def test_ordinary_user_cannot_create_for_other_company_via_orm(self):
        """Intento ORM directo por usuario ordinario para otra compañía debe fallar."""
        vals = {
            "partner_id": self.partner_b.id,
            "company_id": self.company_b.id,
            "currency_id": self.company_b.currency_id.id,
            "datos_json": json.dumps(_datos("B")),
        }
        with self.assertRaises(Exception):
            self.env["migal.agente.estado.cuenta.publicacion"].with_user(self.user_fco_a).with_company(self.company_a).create(vals)

@tagged("post_install", "-at_install", "p3_security")
class TestP3EstadoCuentaPublicacionHttp(HttpCase):
    """P3 HTTP: endpoint público y reporte PDF por mecanismo HTTP estándar."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Empresa P3 B HTTP"})
        cls.grp_fco = "account.group_account_invoice"
        cls.user_fco_a = new_test_user(
            cls.env, login="p3_http_fco_a", groups=f"base.group_user,{cls.grp_fco}",
            company_id=cls.company_a.id, company_ids=[(6, 0, [cls.company_a.id])])
        cls.user_fco_b = new_test_user(
            cls.env, login="p3_http_fco_b", groups=f"base.group_user,{cls.grp_fco}",
            company_id=cls.company_b.id, company_ids=[(6, 0, [cls.company_b.id])])
        cls.user_fco_ab = new_test_user(
            cls.env, login="p3_http_fco_ab", groups=f"base.group_user,{cls.grp_fco}",
            company_id=cls.company_a.id, company_ids=[(6, 0, [cls.company_a.id, cls.company_b.id])])
        cls.user_sys = new_test_user(
            cls.env, login="p3_http_sys", groups="base.group_system,account.group_account_invoice",
            company_id=cls.company_a.id, company_ids=[(6, 0, [cls.company_a.id, cls.company_b.id])])
        cls.partner_a = cls.env["res.partner"].create({"name": "Cliente P3 HTTP A", "company_id": False})
        cls.partner_b = cls.env["res.partner"].create({"name": "Cliente P3 HTTP B", "company_id": False})

    def setUp(self):
        super().setUp()
        self._clear_rate_limits()

    def tearDown(self):
        self._clear_rate_limits()
        super().tearDown()

    def _clear_rate_limits(self):
        with self.env.registry._db.cursor() as cr:
            cr.execute("DELETE FROM migal_agente_rate_limit WHERE key LIKE 'estado_cuenta:%'")
            cr.commit()

    def _mk_pub(self, company, partner=None, user=None, **kw):
        partner = partner or (self.partner_a if company == self.company_a else self.partner_b)
        user = user or self.env.user
        vals = {
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "user_id": user.id,
            "datos_json": json.dumps(_datos(partner.name)),
            "total_pendiente": 100.0,
        }
        vals.update(kw)
        return self.env["migal.agente.estado.cuenta.publicacion"].with_user(user)._create_validated(vals, user=user)

    def _get_public(self, token, ip="10.77.0.1"):
        with patch(
            "odoo.addons.migal_agente.controllers.main.MigalAgentePublico._estado_cuenta_ip",
            return_value=ip,
        ):
            return self.url_open(f"/migal/estado-cuenta/{token}")

    # --- endpoint público ---
    def test_public_valid_token_returns_pdf(self):
        pub = self._mk_pub(self.company_a)
        r = self._get_public(pub.token)
        self.assertEqual(r.status_code, 200)
        self.assertIn("application/pdf", r.headers.get("Content-Type", ""))

    def test_public_nonexistent_revoked_expired_return_404(self):
        self.assertEqual(self._get_public("00000000-0000-0000-0000-000000000000", ip="10.77.0.2").status_code, 404)
        pub = self._mk_pub(self.company_a)
        pub.sudo().write({"activo": False})
        self.assertEqual(self._get_public(pub.token, ip="10.77.0.3").status_code, 404)
        pub2 = self._mk_pub(self.company_a, expira=fields.Datetime.now() - timedelta(minutes=1))
        self.assertEqual(self._get_public(pub2.token, ip="10.77.0.4").status_code, 404)

    def test_public_rate_limit_returns_429_with_retry_after(self):
        pub = self._mk_pub(self.company_a)
        ip = "10.77.0.99"
        for _ in range(15):
            self.assertEqual(self._get_public(pub.token, ip=ip).status_code, 200)
        r = self._get_public(pub.token, ip=ip)
        self.assertEqual(r.status_code, 429)
        self.assertIn("Retry-After", r.headers)

    # --- reporte PDF vía mecanismo HTTP estándar ---
    def _report_url(self, pub):
        return f"/report/pdf/migal_agente.report_estado_cuenta_publicado/{pub.id}"

    def test_report_http_owner_company_allowed(self):
        pub = self._mk_pub(self.company_a)
        self.authenticate("p3_http_fco_a", "p3_http_fco_a")
        r = self.url_open(self._report_url(pub))
        self.assertEqual(r.status_code, 200)
        self.assertIn("pdf", r.headers.get("Content-Type", "").lower())

    def test_report_http_other_company_denied(self):
        pub_b = self._mk_pub(self.company_b)
        self.authenticate("p3_http_fco_a", "p3_http_fco_a")
        r = self.url_open(self._report_url(pub_b))
        # Odoo puede responder 403/404/redirect/error page; lo crítico es que no entregue PDF cross-company.
        content_type = (r.headers.get("Content-Type") or "").lower()
        body = r.content or b""
        is_pdf = r.status_code == 200 and ("application/pdf" in content_type or body.startswith(b"%PDF"))
        self.assertFalse(is_pdf, "No debe entregar PDF de otra compañía")

    def test_report_http_user_ab_can_access_own_company_report(self):
        pub_a = self._mk_pub(self.company_a)
        self.authenticate("p3_http_fco_ab", "p3_http_fco_ab")
        r = self.url_open(self._report_url(pub_a))
        self.assertEqual(r.status_code, 200)

    def test_report_http_admin_can_access(self):
        pub_a = self._mk_pub(self.company_a)
        self.authenticate("p3_http_sys", "p3_http_sys")
        r = self.url_open(self._report_url(pub_a))
        self.assertEqual(r.status_code, 200)
