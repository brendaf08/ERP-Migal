# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install', 'p1_security')
class TestP1SecurityAgente(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_param('migal_agente.llm_enabled', False)
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente P1', 'phone': '+51987654321'})
        cls.order = cls.env['sale.order'].create({'partner_id': cls.partner.id})
        cls.order2 = cls.env['sale.order'].create({'partner_id': cls.partner.id})
        cls.user_sales = new_test_user(
            cls.env, login='p1_sales', groups='sales_team.group_sale_salesman')
        cls.user_basic = new_test_user(
            cls.env, login='p1_basic', groups='base.group_user')
        cls.order.user_id = cls.user_sales

    def test_registrar_rejects_non_allowed_model(self):
        agente = self.env['migal.agente'].with_user(self.user_sales)
        ok, info = agente._puede_escalar_a('res.users', self.user_sales.id)
        self.assertFalse(ok)
        self.assertEqual(info, 'modelo no permitido')

    def test_registrar_rejects_nonexistent_record(self):
        agente = self.env['migal.agente'].with_user(self.user_sales)
        ok, info = agente._puede_escalar_a('sale.order', 999999999)
        self.assertFalse(ok)
        self.assertEqual(info, 'registro inexistente')

    def test_registrar_rejects_user_without_access(self):
        # usuario básico sin acceso a sale.order
        agente = self.env['migal.agente'].with_user(self.user_basic)
        ok, info = agente._puede_escalar_a('sale.order', self.order.id)
        self.assertFalse(ok)

    def test_registrar_allows_authorized_sale_order(self):
        agente = self.env['migal.agente'].with_user(self.user_sales)
        ok, record = agente._puede_escalar_a('sale.order', self.order.id)
        self.assertTrue(ok)
        self.assertEqual(record.id, self.order.id)

    def test_whatsapp_wizard_rejects_envio_from_other_order(self):
        envio = self.env['migal.agente.whatsapp.envio'].create({
            'order_id': self.order2.id,
            'cotizacion': self.order2.name,
            'partner_id': self.partner.id,
            'telefono': '+51987654321',
            'mensaje': 'hola',
        })
        wiz = self.env['migal.agente.whatsapp.wizard'].create({
            'order_id': self.order.id,
            'habilitado': True,
            'telefono': '+51987654321',
            'mensaje': 'editado',
        })
        # simular resultado de herramienta con envio de otra cotización
        from unittest.mock import patch
        agente = self.env['migal.agente']
        fake_res = {'ok': True, 'datos': {'envio_id': envio.id}, 'reglas': [], 'mensaje': 'ok'}
        with patch.object(type(agente), 'ejecutar_herramienta', return_value=fake_res):
            with patch.object(type(agente), '_registrar', return_value=self.env['migal.agente.log']):
                with self.assertRaises(UserError):
                    wiz.action_registrar_envio()

    def test_whatsapp_widget_rejects_envio_from_other_order(self):
        envio = self.env['migal.agente.whatsapp.envio'].create({
            'order_id': self.order2.id,
            'cotizacion': self.order2.name,
            'partner_id': self.partner.id,
            'telefono': '+51987654321',
            'mensaje': 'original',
        })
        agente = self.env['migal.agente']
        fake_res = {'ok': True, 'datos': {'envio_id': envio.id}, 'reglas': [], 'mensaje': 'ok'}
        from unittest.mock import patch
        with patch.object(type(agente), 'ejecutar_herramienta', return_value=fake_res):
            with patch.object(type(agente), '_registrar', return_value=self.env['migal.agente.log']):
                res = agente._widget_registrar_envio(self.order, {'mensaje': 'editado'})
        envio.invalidate_recordset()
        self.assertEqual(envio.mensaje, 'original')
