"""Pruebas del agente marketing (registro, herramientas, permisos, chat y eventos)."""
from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install", "migal_agente", "migal_agente_marketing")
class TestAgenteMarketing(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("migal_agente.llm_enabled", "False")
        cls.hoy = fields.Date.context_today(cls.env.user)
        cls.ven = new_test_user(cls.env, login="ven_marketing", groups="sales_team.group_sale_salesman")
        cls.fco = new_test_user(cls.env, login="fco_marketing", groups="account.group_account_invoice")
        cls.ger = new_test_user(cls.env, login="ger_marketing",
                                groups="sales_team.group_sale_manager,account.group_account_manager")
        cls.sin_rol = new_test_user(cls.env, login="base_marketing", groups="base.group_user")

    def agente(self, user):
        return self.env["migal.agente"].with_user(user)

    def test_registrado(self):
        self.assertIn("marketing", self.env["migal.agente"]._agentes())

    def test_permiso_por_rol(self):
        res = self.agente(self.sin_rol).ejecutar_herramienta("clientes_inactivos", {})
        self.assertEqual(res["estado"], "sin_permiso", "Un usuario sin el rol no puede usar la herramienta")

    def test_chat_reconoce_frase(self):
        html, log = self.agente(self.ger).procesar_mensaje("clientes inactivos", canal="prueba")
        self.assertIn("clientes_inactivos", log.tools_invoked)
        self.assertEqual(log.agente, "marketing")

    def test_productos_para_promocion_usa_simulador(self):
        res = self.agente(self.ger).ejecutar_herramienta("productos_para_promocion", {"dias": 90})
        self.assertTrue(res.get("simulado"), "Hasta que suministro implemente consultar_baja_rotacion")

    def test_marketing_solo_recibe_bandera_de_credito(self):
        cliente = self.env["res.partner"].create({"name": "Cliente prueba marketing"})
        res = self.env["migal.agente"].with_user(self.ger).consultar(
            "marketing", "consultar_situacion_credito", {"cliente": cliente.name})
        self.assertEqual(set(res["datos"]), {"cliente", "excluir"}, "Mínimo privilegio: sin montos de deuda")

    def test_clientes_inactivos(self):
        res = self.agente(self.ger).ejecutar_herramienta("clientes_inactivos", {"dias": 60})
        self.assertTrue(res["ok"])
