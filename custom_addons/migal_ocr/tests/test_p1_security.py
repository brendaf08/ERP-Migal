# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install', 'p1_security')
class TestMigalOcrSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company_2 = cls.env['res.company'].create({'name': 'Empresa OCR P1'})
        cls.user_c1 = new_test_user(
            cls.env, login='p1_ocr_c1', groups='sales_team.group_sale_salesman',
            company_id=cls.company.id, company_ids=[(6, 0, [cls.company.id])])
        cls.user_c2 = new_test_user(
            cls.env, login='p1_ocr_c2', groups='sales_team.group_sale_salesman',
            company_id=cls.company_2.id, company_ids=[(6, 0, [cls.company_2.id])])
        cls.doc = cls.env['migal.ocr.documento'].create({
            'name': 'DOC P1',
            'company_id': cls.company.id,
            'texto_lista': '10 cemento sol',
        })
        cls.line = cls.env['migal.ocr.linea'].create({
            'documento_id': cls.doc.id,
            'secuencia': 1,
            'texto_crudo': '10 cemento sol',
        })

    def test_authorized_user_same_company_can_read(self):
        doc = self.doc.with_user(self.user_c1)
        doc.check_access('read')
        self.assertEqual(doc.name, 'DOC P1')

    def test_user_other_company_cannot_read(self):
        with self.assertRaises(AccessError):
            self.doc.with_user(self.user_c2).check_access('read')

    def test_line_respects_document_access(self):
        self.line.with_user(self.user_c1).check_access('read')
        with self.assertRaises(AccessError):
            self.line.with_user(self.user_c2).check_access('read')

    def test_admin_can_access(self):
        self.doc.with_user(self.env.ref('base.user_admin')).check_access('read')
        self.line.with_user(self.env.ref('base.user_admin')).check_access('read')

    def test_text_processing_still_works(self):
        doc = self.env['migal.ocr.documento'].with_user(self.user_c1).create({
            'name': 'DOC TEXTO P1',
            'company_id': self.company.id,
            'texto_lista': '1 cemento\n2 fierro',
        })
        doc.action_leer()
        self.assertEqual(doc.estado, 'leido')
        self.assertTrue(doc.linea_ids)
