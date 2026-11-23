"""Pruebas del agente cuentas por cobrar (registro, herramientas, permisos, chat y eventos)."""
from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install", "migal_agente", "migal_agente_cobranzas")
class TestAgenteCobranzas(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("migal_agente.llm_enabled", "False")
        cls.hoy = fields.Date.context_today(cls.env.user)
        cls.ven = new_test_user(cls.env, login="ven_cobranzas", groups="sales_team.group_sale_salesman")
        cls.fco = new_test_user(cls.env, login="fco_cobranzas", groups="account.group_account_invoice")
        cls.ger = new_test_user(cls.env, login="ger_cobranzas",
                                groups="sales_team.group_sale_manager,account.group_account_manager")
        cls.sin_rol = new_test_user(cls.env, login="base_cobranzas", groups="base.group_user")

    def agente(self, user):
        return self.env["migal.agente"].with_user(user)

    def test_registrado(self):
        self.assertIn("cobranzas", self.env["migal.agente"]._agentes())

    def test_permiso_por_rol(self):
        res = self.agente(self.sin_rol).ejecutar_herramienta("resumen_cartera", {})
        self.assertEqual(res["estado"], "sin_permiso", "Un usuario sin el rol no puede usar la herramienta")

    def test_chat_reconoce_frase(self):
        html, log = self.agente(self.fco).procesar_mensaje("cartera", canal="prueba")
        self.assertIn("resumen_cartera", log.tools_invoked)
        self.assertEqual(log.agente, "cobranzas")

    def test_situacion_credito_y_cartera(self):
        cliente = self.env["res.partner"].create({"name": "Cliente prueba cobranzas", "credit_limit": 50})
        producto = self.env["product.product"].create({"name": "Producto prueba cobranzas", "list_price": 100})
        factura = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": cliente.id, "invoice_date": self.hoy - timedelta(days=60),
            "invoice_date_due": self.hoy - timedelta(days=45),
            "invoice_line_ids": [Command.create({"product_id": producto.id, "price_unit": 100, "tax_ids": []})]})
        factura.action_post()
        res = self.agente(self.fco).ejecutar_herramienta("consultar_situacion_credito", {"cliente": cliente.name})
        self.assertTrue(res["datos"]["excede_limite"])
        self.assertTrue(res["datos"]["excluir"])
        self.assertGreaterEqual(res["datos"]["dias_max_vencido"], 45)
        res = self.agente(self.fco).ejecutar_herramienta("resumen_cartera", {})
        self.assertGreater(res["datos"]["vencido"], 0)
        log = self.env["migal.agente.log"].sudo().search([("canal", "=", "evento"), ("input_prompt", "like", "EV-038")],
                                                          order="id desc", limit=1)
        self.assertTrue(log, "Contabilizar una factura de cliente emite EV-038")
