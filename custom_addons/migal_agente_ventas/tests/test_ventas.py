"""Pruebas del agente ventas (registro, herramientas, permisos, chat y eventos)."""
from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install", "migal_agente", "migal_agente_ventas")
class TestAgenteVentas(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("migal_agente.llm_enabled", "False")
        cls.hoy = fields.Date.context_today(cls.env.user)
        cls.ven = new_test_user(cls.env, login="ven_ventas", groups="sales_team.group_sale_salesman")
        cls.fco = new_test_user(cls.env, login="fco_ventas", groups="account.group_account_invoice")
        cls.ger = new_test_user(cls.env, login="ger_ventas",
                                groups="sales_team.group_sale_manager,account.group_account_manager")
        cls.sin_rol = new_test_user(cls.env, login="base_ventas", groups="base.group_user")

    def agente(self, user):
        return self.env["migal.agente"].with_user(user)

    def test_registrado(self):
        self.assertIn("ventas", self.env["migal.agente"]._agentes())

    def test_permiso_por_rol(self):
        res = self.agente(self.sin_rol).ejecutar_herramienta("cotizaciones_por_vencer", {})
        self.assertEqual(res["estado"], "sin_permiso", "Un usuario sin el rol no puede usar la herramienta")

    def test_chat_reconoce_frase(self):
        html, log = self.agente(self.ven).procesar_mensaje("cotizaciones por vencer", canal="prueba")
        self.assertIn("cotizaciones_por_vencer", log.tools_invoked)
        self.assertEqual(log.agente, "ventas")

    def test_cotizaciones_por_vencer(self):
        cliente = self.env["res.partner"].create({"name": "Cliente prueba ventas"})
        producto = self.env["product.product"].create({"name": "Producto prueba ventas", "list_price": 10})
        orden = self.env["sale.order"].create({"partner_id": cliente.id, "validity_date": self.hoy + timedelta(days=3),
                                               "user_id": self.ven.id,
                                               "order_line": [Command.create({"product_id": producto.id})]})
        res = self.agente(self.ven).ejecutar_herramienta("cotizaciones_por_vencer", {"dias": 7})
        self.assertIn(orden.name, res["datos"]["cotizaciones"])

    def test_confirmar_venta_emite_ev018(self):
        cliente = self.env["res.partner"].create({"name": "Cliente prueba EV-018"})
        producto = self.env["product.product"].create({"name": "Producto prueba EV-018", "list_price": 10})
        orden = self.env["sale.order"].create({"partner_id": cliente.id,
                                               "order_line": [Command.create({"product_id": producto.id})]})
        entregados = []
        original = type(self.env["migal.agente"]).emitir

        def espia(modelo, evento, datos, desde=None):
            resultado = original(modelo, evento, datos, desde=desde)
            entregados.append((evento, resultado))
            return resultado
        with patch.object(type(self.env["migal.agente"]), "emitir", espia):
            orden.action_confirm()
        evento, recibieron = entregados[-1]
        self.assertEqual(evento, "EV-018")
        self.assertTrue({"suministro", "cobranzas"} <= set(recibieron), recibieron)

    def test_simulador_para_consulta_pendiente(self):
        res = self.env["migal.agente"].consultar("marketing", "consultar_cotizaciones_perdidas", {"dias": 90})
        self.assertTrue(res.get("simulado"), "Mientras ventas no la implemente, responde el simulador")
