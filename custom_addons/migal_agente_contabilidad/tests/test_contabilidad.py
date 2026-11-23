"""Pruebas del agente contabilidad (registro, herramientas, permisos, chat y eventos)."""
from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install", "migal_agente", "migal_agente_contabilidad")
class TestAgenteContabilidad(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("migal_agente.llm_enabled", "False")
        cls.hoy = fields.Date.context_today(cls.env.user)
        cls.ven = new_test_user(cls.env, login="ven_contabilidad", groups="sales_team.group_sale_salesman")
        cls.fco = new_test_user(cls.env, login="fco_contabilidad", groups="account.group_account_invoice")
        cls.ger = new_test_user(cls.env, login="ger_contabilidad",
                                groups="sales_team.group_sale_manager,account.group_account_manager")
        cls.sin_rol = new_test_user(cls.env, login="base_contabilidad", groups="base.group_user")

    def agente(self, user):
        return self.env["migal.agente"].with_user(user)

    def test_registrado(self):
        self.assertIn("contabilidad", self.env["migal.agente"]._agentes())

    def test_permiso_por_rol(self):
        res = self.agente(self.sin_rol).ejecutar_herramienta("pendientes_cierre", {})
        self.assertEqual(res["estado"], "sin_permiso", "Un usuario sin el rol no puede usar la herramienta")

    def test_chat_reconoce_frase(self):
        html, log = self.agente(self.fco).procesar_mensaje("pendientes de cierre", canal="prueba")
        self.assertIn("pendientes_cierre", log.tools_invoked)
        self.assertEqual(log.agente, "contabilidad")

    def test_pendientes_cierre_usa_consultas_reales(self):
        res = self.agente(self.fco).ejecutar_herramienta("pendientes_cierre", {})
        self.assertTrue(res["ok"])
        self.assertIn("igv_ventas", res["datos"])
        self.assertNotIn("Simulado", str(res["datos"]["tabla"]), "Cobranzas y pagos están instalados: respuesta real")
