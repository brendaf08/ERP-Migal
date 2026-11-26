# -*- coding: utf-8 -*-
import json
from datetime import timedelta
from unittest.mock import patch
import threading

from odoo import api, fields
from odoo.tests import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install", "p2_r04")
class TestEstadoCuentaPublicoR04(HttpCase):
    """Pruebas del límite de solicitudes y del comportamiento del endpoint público."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Cliente P2 R04"})
        cls.Pub = cls.env["migal.agente.estado.cuenta.publicacion"].sudo()
        cls.datos = {
            "cliente": cls.partner.name, "simbolo": "S/", "fecha_desde": "2026-11-01",
            "fecha_hasta": "2026-11-13", "fecha_consulta": "2026-11-13", "saldo_anterior": 0,
            "movimientos": [], "saldo_periodo": 0, "documentos_pendientes": [], "pagos_sin_aplicar": [],
            "total_pendiente": 0, "total_vencido": 0, "informativo": [], "antiguedad": [],
        }

    def setUp(self):
        super().setUp()
        self._clear_rate_limits()

    def tearDown(self):
        self._clear_rate_limits()
        super().tearDown()

    def _clear_rate_limits(self):
        with self.env.registry._db.cursor() as cr:
            cr.execute("DELETE FROM migal_agente_rate_limit")
            cr.commit()

    def _pub(self, **kw):
        vals = {"partner_id": self.partner.id, "datos_json": json.dumps(self.datos)}
        vals.update(kw)
        return self.Pub.create(vals)

    def _get(self, token, ip="10.10.10.1"):
        with patch(
            "odoo.addons.migal_agente.controllers.main.MigalAgentePublico._estado_cuenta_ip",
            return_value=ip,
        ):
            return self.url_open(f"/migal/estado-cuenta/{token}")

    def test_valid_token_returns_pdf(self):
        pub = self._pub()
        r = self._get(pub.token)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("Content-Type"), "application/pdf")
        self.assertIn("no-store", r.headers.get("Cache-Control", ""))
        self.assertIn("noindex", r.headers.get("X-Robots-Tag", ""))
        self.assertEqual(r.headers.get("Referrer-Policy"), "no-referrer")

    def test_expired_revoked_invalid_return_404(self):
        pub = self._pub(expira=fields.Datetime.now() - timedelta(minutes=1))
        self.assertEqual(self._get(pub.token, ip="10.0.0.2").status_code, 404)

        pub2 = self._pub(activo=False)
        self.assertEqual(self._get(pub2.token, ip="10.0.0.3").status_code, 404)

        self.assertEqual(self._get("00000000-0000-0000-0000-000000000000", ip="10.0.0.4").status_code, 404)
        self.assertEqual(self._get("not-a-uuid", ip="10.0.0.5").status_code, 404)

    def test_rate_limit_blocks_abuse_and_returns_429(self):
        pub = self._pub()
        ip = "10.20.30.40"
        # por debajo del límite
        for _ in range(15):
            r = self._get(pub.token, ip=ip)
            self.assertEqual(r.status_code, 200)
        # por encima del límite
        r = self._get(pub.token, ip=ip)
        self.assertEqual(r.status_code, 429)
        self.assertIn("Retry-After", r.headers)

    def test_invalid_tokens_cannot_evade_rate_limit(self):
        ip = "10.20.30.41"
        # 15 solicitudes inválidas bajo el límite
        for i in range(15):
            token = f"00000000-0000-0000-0000-{i:012d}"
            self.assertEqual(self._get(token, ip=ip).status_code, 404)
        # la siguiente debe ser bloqueada aunque el token sea inválido
        blocked = False
        for j in range(5):
            r = self._get(f"00000000-0000-0000-0000-{100+j:012d}", ip=ip)
            if r.status_code == 429:
                blocked = True
                break
        self.assertTrue(blocked, "Tokens inválidos no deben evadir el rate limit")

    def test_rate_limit_isolated_by_ip(self):
        pub = self._pub()
        ip_a = "10.20.30.50"
        ip_b = "10.20.30.51"
        for _ in range(15):
            self.assertEqual(self._get(pub.token, ip=ip_a).status_code, 200)
        self.assertEqual(self._get(pub.token, ip=ip_a).status_code, 429)
        # otro origen no debe ser bloqueado inmediatamente
        self.assertEqual(self._get(pub.token, ip=ip_b).status_code, 200)

    def test_vistas_deduplicated(self):
        pub = self._pub()
        ip = "10.20.30.60"
        self.assertEqual(self._get(pub.token, ip=ip).status_code, 200)
        pub.invalidate_recordset()
        self.assertEqual(pub.vistas, 1)
        # segunda vista inmediata no debe incrementar
        self.assertEqual(self._get(pub.token, ip=ip).status_code, 200)
        pub.invalidate_recordset()
        self.assertEqual(pub.vistas, 1)


    # ------------------------------------------------------------------
    # Pruebas adicionales del límite de solicitudes
    # ------------------------------------------------------------------
    def test_404_persists_counter_across_requests(self):
        self._clear_rate_limits()
        for _ in range(15):
            r = self.url_open('/migal/estado-cuenta/%s' % ('0' * 36))
            self.assertEqual(r.status_code, 404)
        r = self.url_open('/migal/estado-cuenta/%s' % ('0' * 36))
        self.assertEqual(r.status_code, 429)

    def test_429_persists_counter(self):
        self._clear_rate_limits()
        for _ in range(15):
            self.url_open('/migal/estado-cuenta/%s' % ('0' * 36))
        r1 = self.url_open('/migal/estado-cuenta/%s' % ('0' * 36))
        self.assertEqual(r1.status_code, 429)
        r2 = self.url_open('/migal/estado-cuenta/%s' % ('0' * 36))
        self.assertEqual(r2.status_code, 429)

    def test_spoofed_x_forwarded_for_does_not_change_bucket(self):
        """Sin proxy confiable, no se debe confiar en XFF para separar buckets."""
        self._clear_rate_limits()
        token = self._pub().token
        # Agotar límite desde "misma" conexión remota aunque cambie XFF
        for i in range(15):
            self.url_open('/migal/estado-cuenta/%s' % ('0' * 36),
                          headers={'X-Forwarded-For': '1.2.3.%s' % i})
        r = self.url_open('/migal/estado-cuenta/%s' % token,
                          headers={'X-Forwarded-For': '9.9.9.9'})
        # Si XFF fuera confiado, podría evadir; con remote_addr debe seguir limitado
        self.assertEqual(r.status_code, 429)

    def test_in_test_mode_detection_uses_real_cursor_path(self):
        """La detección robusta debe identificar modo test sin usar nombre frágil."""
        import odoo.modules.module
        self.assertTrue(bool(getattr(odoo.modules.module, "current_test", False)))
        # El contador debe persistir incluso tras 404 (rollback request) en HttpCase
        self._clear_rate_limits()
        self.url_open('/migal/estado-cuenta/%s' % ('0' * 36))
        with self.env.registry._db.cursor() as cr:
            cr.execute("SELECT COUNT(*) FROM migal_agente_rate_limit")
            count = cr.fetchone()[0]
        self.assertGreaterEqual(count, 1)



@tagged("post_install", "-at_install", "p2_r04")
class TestRateLimitConcurrencyP2R04(TransactionCase):
    """Concurrencia del rate limit fuera de HttpCase para evitar interferencia con servidor HTTP."""

    def setUp(self):
        super().setUp()
        self._cleanup()

    def tearDown(self):
        self._cleanup()
        super().tearDown()

    def _cleanup(self):
        with self.registry._db.cursor() as cr:
            cr.execute("DELETE FROM migal_agente_rate_limit WHERE key LIKE 'estado_cuenta:conc_p21_%'")
            cr.commit()

    def test_concurrent_hits_are_counted_atomically(self):
        """Prueba concurrente: el resultado final no debe perder incrementos."""
        key = "estado_cuenta:conc_p21_127.0.0.1"
        limit = 100
        window = 60
        hits = 10
        errors = []
        errors_lock = threading.Lock()

        def _hit():
            try:
                # Cursor real independiente (no TestCursor) para concurrencia real en DB.
                from odoo.orm.environments import Transaction
                with self.registry._db.cursor() as cr:
                    # Evitar Registry(cr.dbname) que toma el lock de Registry en hilos.
                    if cr.transaction is None:
                        cr.transaction = Transaction(self.registry)
                    env = api.Environment(cr, self.env.uid, {})
                    env["migal.agente.rate.limit"].check_and_hit(key, limit, window)
                    cr.commit()
            except Exception as e:
                with errors_lock:
                    errors.append(repr(e))

        threads = [threading.Thread(target=_hit, name=f"p21-r04-{i}") for i in range(hits)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        alive = [t.name for t in threads if t.is_alive()]
        self.assertFalse(alive, "Hilos vivos tras timeout: %s; errores=%s" % (alive, errors[:3]))
        self.assertFalse(errors, "Errores en concurrencia: %s" % errors[:3])
        with self.registry.cursor() as cr:
            cr.execute("SELECT count FROM migal_agente_rate_limit WHERE key=%s", (key,))
            row = cr.fetchone()
        self.assertTrue(row, "No se encontró contador para la clave concurrente")
        self.assertEqual(row[0], hits)
