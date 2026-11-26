# -*- coding: utf-8 -*-
import base64
import logging
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'p2_r05')
class TestMigalOcrR05(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.doc = cls.env['migal.ocr.documento'].create({
            'name': 'DOC R05',
            'company_id': cls.company.id,
        })
        # PNG pequeño válido
        cls.png_b64 = base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'0' * 32).decode()

    def _set_ocr(self, enabled=False, ack=False, key='k', modelos='gemini-3.5-flash-lite'):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('migal_ocr.llm_enabled', 'True' if enabled else 'False')
        icp.set_param('migal_ocr.llm_data_ack', 'True' if ack else 'False')
        icp.set_param('migal_ocr.llm_api_key', key or '')
        icp.set_param('migal_ocr.gemini_modelos', modelos or '')

    def test_ocr_disabled_blocks_external_call(self):
        self._set_ocr(enabled=False, ack=True, key='k')
        doc = self.doc.copy({'archivo': self.png_b64, 'archivo_nombre': 'x.png'})
        with patch('odoo.addons.migal_ocr.lib.lectura.leer_con_gemini') as mocked:
            with self.assertRaises(UserError):
                doc.action_leer()
            mocked.assert_not_called()

    def test_ocr_enabled_with_valid_config_allows(self):
        self._set_ocr(enabled=True, ack=True, key='k')
        doc = self.doc.copy({'archivo': self.png_b64, 'archivo_nombre': 'x.png'})
        with patch('odoo.addons.migal_ocr.lib.lectura.leer_con_gemini', return_value=('gemini-3.5-flash-lite', [('cemento', 1.0)])):
            doc.action_leer()
        self.assertEqual(doc.estado, 'leido')

    def test_ocr_missing_ack_blocks(self):
        self._set_ocr(enabled=True, ack=False, key='k')
        doc = self.doc.copy({'archivo': self.png_b64, 'archivo_nombre': 'x.png'})
        with patch('odoo.addons.migal_ocr.lib.lectura.leer_con_gemini') as mocked:
            with self.assertRaises(UserError):
                doc.action_leer()
            mocked.assert_not_called()

    def test_ocr_missing_key_blocks(self):
        self._set_ocr(enabled=True, ack=True, key='')
        self.env['ir.config_parameter'].sudo().set_param('migal_agente.llm_api_key', '')
        doc = self.doc.copy({'archivo': self.png_b64, 'archivo_nombre': 'x.png'})
        with patch('odoo.addons.migal_ocr.lib.lectura.leer_con_gemini') as mocked:
            with self.assertRaises(UserError):
                doc.action_leer()
            mocked.assert_not_called()

    def test_ocr_invalid_model_blocks(self):
        self._set_ocr(enabled=True, ack=True, key='k', modelos='claude-3')
        doc = self.doc.copy({'archivo': self.png_b64, 'archivo_nombre': 'x.png'})
        with patch('odoo.addons.migal_ocr.lib.lectura.leer_con_gemini') as mocked:
            with self.assertRaises(UserError):
                doc.action_leer()
            mocked.assert_not_called()

    def test_ocr_text_still_works_without_ai(self):
        self._set_ocr(enabled=False, ack=False, key='')
        doc = self.doc.copy({'texto_lista': '1 cemento\n2 fierro'})
        doc.action_leer()
        self.assertEqual(doc.estado, 'leido')
        self.assertTrue(doc.linea_ids)

    def test_agent_disabled_ocr_enabled_independent(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('migal_agente.llm_enabled', 'False')
        self._set_ocr(enabled=True, ack=True, key='k')
        doc = self.doc.copy({'archivo': self.png_b64, 'archivo_nombre': 'x.png'})
        with patch('odoo.addons.migal_ocr.lib.lectura.leer_con_gemini', return_value=('gemini-3.5-flash-lite', [('cemento', 1.0)])):
            doc.action_leer()
        self.assertEqual(doc.estado, 'leido')


    # ------------------------------------------------------------------
    # Verificación del consentimiento OCR explícito e independiente
    # ------------------------------------------------------------------
    def test_hook_upgrade_without_ocr_params_initializes_disabled_no_consent(self):
        """Upgrade sin params OCR: inicializa deshabilitado y sin consentimiento, sin copiar agente."""
        icp = self.env['ir.config_parameter'].sudo()
        # Simular instalación existente con agente configurado
        icp.set_param('migal_agente.llm_proveedor', 'gemini')
        icp.set_param('migal_agente.llm_enabled', 'True')
        icp.set_param('migal_agente.llm_data_ack', 'True')
        icp.set_param('migal_agente.llm_api_key', 'AGENT-SECRET-KEY')
        # Eliminar params OCR para simular upgrade
        icp.search([('key', 'in', ['migal_ocr.llm_enabled', 'migal_ocr.llm_data_ack',
                                   'migal_ocr.llm_api_key', 'migal_ocr.gemini_modelos'])]).unlink()

        from odoo.addons.migal_ocr.hooks import post_init_hook
        with self.assertLogs('odoo.addons.migal_ocr.hooks', level='INFO') as cm:
            post_init_hook(self.env)

        self.assertEqual(icp.get_param('migal_ocr.llm_enabled'), 'False')
        self.assertEqual(icp.get_param('migal_ocr.llm_data_ack'), 'False')
        # No debe copiar consentimiento ni activar por configuración del agente
        self.assertNotEqual(icp.get_param('migal_ocr.llm_data_ack'), 'True')
        # No debe copiar clave del agente
        self.assertFalse(icp.get_param('migal_ocr.llm_api_key'))
        # Clave del agente intacta
        self.assertEqual(icp.get_param('migal_agente.llm_api_key'), 'AGENT-SECRET-KEY')
        # Log no debe exponer claves
        joined = '\n'.join(cm.output)
        self.assertNotIn('AGENT-SECRET-KEY', joined)

    def test_hook_upgrade_with_existing_ocr_params_preserved(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('migal_ocr.llm_enabled', 'True')
        icp.set_param('migal_ocr.llm_data_ack', 'True')
        icp.set_param('migal_ocr.llm_api_key', 'OCR-KEY')
        icp.set_param('migal_ocr.gemini_modelos', 'gemini-custom')

        from odoo.addons.migal_ocr.hooks import post_init_hook
        post_init_hook(self.env)

        self.assertEqual(icp.get_param('migal_ocr.llm_enabled'), 'True')
        self.assertEqual(icp.get_param('migal_ocr.llm_data_ack'), 'True')
        self.assertEqual(icp.get_param('migal_ocr.llm_api_key'), 'OCR-KEY')
        self.assertEqual(icp.get_param('migal_ocr.gemini_modelos'), 'gemini-custom')

    def test_hook_new_install_defaults_disabled(self):
        icp = self.env['ir.config_parameter'].sudo()
        # Limpiar todo lo relacionado
        icp.search([('key', 'in', [
            'migal_ocr.llm_enabled', 'migal_ocr.llm_data_ack', 'migal_ocr.llm_api_key', 'migal_ocr.gemini_modelos',
            'migal_agente.llm_proveedor', 'migal_agente.llm_enabled', 'migal_agente.llm_data_ack', 'migal_agente.llm_api_key',
        ])]).unlink()
        from odoo.addons.migal_ocr.hooks import post_init_hook
        post_init_hook(self.env)
        self.assertEqual(icp.get_param('migal_ocr.llm_enabled'), 'False')
        self.assertEqual(icp.get_param('migal_ocr.llm_data_ack'), 'False')

    def test_agent_consent_but_ocr_no_consent_blocks(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('migal_agente.llm_enabled', 'True')
        icp.set_param('migal_agente.llm_data_ack', 'True')
        icp.set_param('migal_agente.llm_api_key', 'AGENT-KEY')
        icp.set_param('migal_agente.llm_proveedor', 'gemini')
        self._set_ocr(enabled=True, ack=False, key='AGENT-KEY')
        doc = self.doc.copy({'archivo': self.png_b64, 'archivo_nombre': 'x.png'})
        with patch('odoo.addons.migal_ocr.lib.lectura.leer_con_gemini') as mocked:
            with self.assertRaises(UserError) as cm:
                doc.action_leer()
            mocked.assert_not_called()
        self.assertNotIn('AGENT-KEY', str(cm.exception))

    def test_shared_agent_key_without_ocr_consent_no_external_call(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('migal_agente.llm_proveedor', 'gemini')
        icp.set_param('migal_agente.llm_api_key', 'SHARED-SECRET')
        # OCR sin clave propia, sin consentimiento, pero habilitado
        self._set_ocr(enabled=True, ack=False, key='')
        doc = self.doc.copy({'archivo': self.png_b64, 'archivo_nombre': 'x.png'})
        with patch('odoo.addons.migal_ocr.lib.lectura.leer_con_gemini') as mocked:
            with self.assertRaises(UserError) as cm:
                doc.action_leer()
            mocked.assert_not_called()
        self.assertNotIn('SHARED-SECRET', str(cm.exception))

    def test_ocr_error_messages_do_not_expose_key(self):
        secret = 'SUPER-SECRET-OCR-KEY'
        self._set_ocr(enabled=True, ack=False, key=secret)
        doc = self.doc.copy({'archivo': self.png_b64, 'archivo_nombre': 'x.png'})
        with patch('odoo.addons.migal_ocr.models.documento._logger.warning') as warn:
            with self.assertRaises(UserError) as err:
                doc.action_leer()
        self.assertNotIn(secret, str(err.exception))
        for call in warn.call_args_list:
            self.assertNotIn(secret, ' '.join(str(a) for a in call.args))
