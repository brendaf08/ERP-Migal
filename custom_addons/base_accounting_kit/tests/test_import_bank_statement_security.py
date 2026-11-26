# -*- coding: utf-8 -*-
import base64

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install', 'p1_security')
class TestImportBankStatementSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company_2 = cls.env['res.company'].create({'name': 'Empresa P1'})
        cls.journal = cls.env['account.journal'].create({
            'name': 'Banco P1',
            'type': 'bank',
            'code': 'BP1',
            'company_id': cls.company.id,
        })
        cls.journal_c2 = cls.env['account.journal'].create({
            'name': 'Banco C2',
            'type': 'bank',
            'code': 'BC2',
            'company_id': cls.company_2.id,
        })
        cls.user_no_acc = new_test_user(
            cls.env, login='p1_no_acc', groups='base.group_user')
        cls.user_acc = new_test_user(
            cls.env, login='p1_acc', groups='account.group_account_basic')
        cls.csv = base64.b64encode(
            b"date,name,amount\n2024-01-01,Test,100.0\n"
        ).decode()

    def _wizard(self, user, journal):
        return self.env['import.bank.statement'].with_user(user).create({
            'attachment': self.csv,
            'file_name': 'test.csv',
            'journal_id': journal.id,
        })

    def test_user_without_accounting_group_denied(self):
        with self.assertRaises(AccessError):
            self._wizard(self.user_no_acc, self.journal)

    def test_accounting_user_can_import(self):
        wiz = self._wizard(self.user_acc, self.journal)
        action = wiz.action_statement_import()
        self.assertEqual(action.get('res_model'), 'account.bank.statement')

    def test_journal_other_company_denied(self):
        wiz = self._wizard(self.user_acc, self.journal_c2)
        with self.assertRaises(AccessError):
            wiz.action_statement_import()

    def test_invalid_journal_type_denied(self):
        sale_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'), ('company_id', '=', self.company.id)
        ], limit=1)
        if not sale_journal:
            sale_journal = self.env['account.journal'].create({
                'name': 'Venta P1', 'type': 'sale', 'code': 'SVP1',
                'company_id': self.company.id,
            })
        wiz = self._wizard(self.user_acc, sale_journal)
        with self.assertRaises(ValidationError):
            wiz.action_statement_import()
