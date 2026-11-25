# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'p2_r05')
class TestMigalAgenteR05(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_param('migal_agente.llm_enabled', False)

    def test_agent_rules_mode_works_without_llm(self):
        res = self.env['migal.agente'].procesar_mensaje("ayuda")
        # procesar_mensaje retorna (html, log)
        self.assertTrue(res)
        if isinstance(res, tuple):
            self.assertTrue(res[0])

    def test_agent_enabled_ocr_disabled_independent(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('migal_agente.llm_enabled', 'True')
        icp.set_param('migal_agente.llm_data_ack', 'True')
        icp.set_param('migal_agente.llm_api_key', 'k')
        icp.set_param('migal_agente.llm_proveedor', 'gemini')
        icp.set_param('migal_ocr.llm_enabled', 'False')
        # agente config should still be active for agent; OCR disabled independently
        cfg = self.env['migal.agente']._llm_config()
        self.assertTrue(cfg['activo'])
        self.assertFalse(self.env['ir.config_parameter'].sudo().get_param('migal_ocr.llm_enabled') in ('True', '1', True))
