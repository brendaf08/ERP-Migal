"""Pruebas del agente cuentas por pagar (registro, herramientas, permisos, chat y eventos)."""
from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install", "migal_agente", "migal_agente_pagos")
class TestAgentePagos(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("migal_agente.llm_enabled", "False")
        cls.hoy = fields.Date.context_today(cls.env.user)
        cls.ven = new_test_user(cls.env, login="ven_pagos", groups="sales_team.group_sale_salesman")
        cls.fco = new_test_user(cls.env, login="fco_pagos", groups="account.group_account_invoice")
        cls.ger = new_test_user(cls.env, login="ger_pagos",
                                groups="sales_team.group_sale_manager,account.group_account_manager")
        cls.sin_rol = new_test_user(cls.env, login="base_pagos", groups="base.group_user")

    def agente(self, user):
        return self.env["migal.agente"].with_user(user)

    def test_registrado(self):
        self.assertIn("pagos", self.env["migal.agente"]._agentes())

    def test_permiso_por_rol(self):
        res = self.agente(self.sin_rol).ejecutar_herramienta("facturas_por_vencer", {})
        self.assertEqual(res["estado"], "sin_permiso", "Un usuario sin el rol no puede usar la herramienta")

    def test_chat_reconoce_frase(self):
        html, log = self.agente(self.fco).procesar_mensaje("facturas por vencer", canal="prueba")
        self.assertIn("facturas_por_vencer", log.tools_invoked)
        self.assertEqual(log.agente, "pagos")

    def test_facturas_por_vencer(self):
        proveedor = self.env["res.partner"].create({"name": "Proveedor prueba pagos"})
        producto = self.env["product.product"].create({"name": "Producto prueba pagos"})
        factura = self.env["account.move"].create({
            "move_type": "in_invoice", "partner_id": proveedor.id, "invoice_date": self.hoy - timedelta(days=40),
            "invoice_date_due": self.hoy - timedelta(days=10), "ref": "PRUEBA-PAGOS-1",
            "invoice_line_ids": [Command.create({"product_id": producto.id, "price_unit": 50, "tax_ids": []})]})
        if "l10n_latam_document_number" in factura._fields and factura.l10n_latam_use_documents:
            factura.l10n_latam_document_number = "F001-99990001"
        factura.action_post()
        res = self.agente(self.fco).ejecutar_herramienta("facturas_por_vencer", {"dias": 7, "proveedor": "prueba pagos"})
        self.assertIn(factura.name, res["datos"]["vencidas"])
        res = self.agente(self.fco).ejecutar_herramienta("resumen_obligaciones", {})
        self.assertGreaterEqual(res["datos"]["vencido"], 50)
