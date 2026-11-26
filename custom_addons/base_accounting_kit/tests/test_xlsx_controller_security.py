# -*- coding: utf-8 -*-
import json

from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.base_accounting_kit.controllers.statement_report import (
    ALLOWED_XLSX_REPORT_MODELS,
    XLSXReportController,
)


@tagged('post_install', '-at_install', 'p0_xlsx')
class TestXlsxControllerValidation(TransactionCase):
    """Validaciones del controlador /xlsx_report sin tocar BD original."""

    def test_allowlist_contains_12_legitimate_models(self):
        expected = {
            "account.aged.trial.balance",
            "account.balance.report",
            "account.bank.book.report",
            "account.cash.book.report",
            "account.day.book.report",
            "account.print.journal",
            "account.report.general.ledger",
            "account.report.partner.ledger",
            "cash.flow.report",
            "financial.report",
            "kit.account.tax.report",
            "res.partner",
        }
        self.assertEqual(set(ALLOWED_XLSX_REPORT_MODELS), expected)

    def test_validate_report_name_rejects_invalid(self):
        invalid = ['', '   ', None, 123, 'a' * 121, 'bad/name', 'bad\\name',
                   'bad\nname', 'bad\rname', 'bad\x00name', '../bad']
        for value in invalid:
            with self.assertRaises(Exception):
                XLSXReportController._validate_report_name(value)

    def test_validate_report_name_accepts_normal(self):
        self.assertEqual(
            XLSXReportController._validate_report_name('  Cash Book  '),
            'Cash Book')

    def test_parse_options_rejects_invalid(self):
        invalid = [None, 123, '{"a":1', '[]', '"texto"', '1']
        for value in invalid:
            with self.assertRaises(Exception):
                XLSXReportController._parse_options(value)

    def test_parse_options_rejects_oversized(self):
        big = json.dumps({"data": "x" * (2 * 1024 * 1024 + 10)})
        with self.assertRaises(Exception):
            XLSXReportController._parse_options(big)

    def test_parse_options_accepts_dict(self):
        data = XLSXReportController._parse_options('{"ok": true}')
        self.assertEqual(data, {"ok": True})


@tagged('post_install', '-at_install', 'p0_xlsx')
class TestXlsxControllerHttp(HttpCase):
    """Pruebas HTTP/CSRF del endpoint /xlsx_report."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'name': 'P0 XLSX User',
            'login': 'p0_xlsx_user',
            'password': 'p0_xlsx_user',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def _csrf_token(self):
        resp = self.url_open('/web/login')
        text = resp.text or ''
        marker = 'csrf_token: "'
        idx = text.find(marker)
        if idx == -1:
            marker = 'name="csrf_token" value="'
            idx = text.find(marker)
            if idx == -1:
                return None
            start = idx + len(marker)
            end = text.find('"', start)
            return text[start:end]
        start = idx + len(marker)
        end = text.find('"', start)
        return text[start:end]

    def _post(self, data, csrf=True, authenticated=True, allow_redirects=True):
        payload = dict(data)
        if authenticated:
            self.authenticate('p0_xlsx_user', 'p0_xlsx_user')
        else:
            try:
                self.logout()
            except Exception:
                pass
            self.opener.cookies.clear()
        if csrf:
            token = self._csrf_token()
            if token:
                payload['csrf_token'] = token
        return self.url_open('/xlsx_report', data=payload, allow_redirects=allow_redirects)

    def _assert_rejected(self, resp, statuses=(400, 403)):
        self.assertIn(resp.status_code, statuses)
        body = resp.text or ''
        self.assertNotIn('Traceback', body)
        self.assertNotIn('/home/', body)
        self.assertNotIn('SELECT ', body)

    @mute_logger('odoo.addons.base_accounting_kit.controllers.statement_report')
    def test_rejects_non_allowlisted_model(self):
        resp = self._post({
            'model': 'res.users',
            'options': '{}',
            'output_format': 'xlsx',
            'report_name': 'Bad',
        })
        self._assert_rejected(resp, statuses=(403,))

    @mute_logger('odoo.addons.base_accounting_kit.controllers.statement_report')
    def test_rejects_authenticated_user_without_read_permission(self):
        # p0_xlsx_user tiene base.group_user pero no grupos contables; los
        # asistentes contables requieren account.group_account_user.
        resp = self._post({
            'model': 'account.report.general.ledger',
            'options': '{}',
            'output_format': 'xlsx',
            'report_name': 'General Ledger',
        })
        self._assert_rejected(resp, statuses=(403,))
        body = resp.text or ''
        self.assertNotIn('Traceback', body)

    @mute_logger('odoo.addons.base_accounting_kit.controllers.statement_report')
    def test_rejects_empty_model(self):
        resp = self._post({
            'model': '',
            'options': '{}',
            'output_format': 'xlsx',
            'report_name': 'Bad',
        })
        self._assert_rejected(resp, statuses=(400, 403))

    @mute_logger('odoo.addons.base_accounting_kit.controllers.statement_report')
    def test_rejects_bad_output_format(self):
        resp = self._post({
            'model': 'res.partner',
            'options': '{}',
            'output_format': 'pdf',
            'report_name': 'Bad',
        })
        self._assert_rejected(resp, statuses=(400,))

    @mute_logger('odoo.addons.base_accounting_kit.controllers.statement_report')
    def test_rejects_invalid_json_options(self):
        resp = self._post({
            'model': 'res.partner',
            'options': '{bad',
            'output_format': 'xlsx',
            'report_name': 'Bad',
        })
        self._assert_rejected(resp, statuses=(400,))

    @mute_logger('odoo.addons.base_accounting_kit.controllers.statement_report')
    def test_rejects_non_object_options(self):
        resp = self._post({
            'model': 'res.partner',
            'options': '[]',
            'output_format': 'xlsx',
            'report_name': 'Bad',
        })
        self._assert_rejected(resp, statuses=(400,))

    @mute_logger('odoo.addons.base_accounting_kit.controllers.statement_report')
    def test_rejects_oversized_options(self):
        big = json.dumps({"x": "a" * (2 * 1024 * 1024 + 100)})
        resp = self._post({
            'model': 'res.partner',
            'options': big,
            'output_format': 'xlsx',
            'report_name': 'Bad',
        })
        self._assert_rejected(resp, statuses=(400,))

    @mute_logger('odoo.addons.base_accounting_kit.controllers.statement_report')
    def test_rejects_bad_report_name(self):
        for name in ['', 'a' * 121, '../x', 'a/b', 'a\\b']:
            resp = self._post({
                'model': 'res.partner',
                'options': '{}',
                'output_format': 'xlsx',
                'report_name': name,
            })
            self._assert_rejected(resp, statuses=(400,))

    def test_rejects_unauthenticated(self):
        resp = self._post({
            'model': 'res.partner',
            'options': '{}',
            'output_format': 'xlsx',
            'report_name': 'Bad',
        }, authenticated=False, allow_redirects=False)
        self.assertIn(resp.status_code, (303, 302, 401, 403))

    @mute_logger('odoo.addons.base_accounting_kit.controllers.statement_report')
    def test_rejects_without_csrf(self):
        resp = self._post({
            'model': 'res.partner',
            'options': '{}',
            'output_format': 'xlsx',
            'report_name': 'Bad',
        }, csrf=False)
        self.assertIn(resp.status_code, (400, 403, 303))

    def test_allows_authorized_allowlisted_model(self):
        data = {
            'customer': 'Test', 'street': '', 'street2': '', 'city': '',
            'state': '', 'zip': '',
            'my_data': [{
                'invoice_date': '2020-01-01',
                'name': 'INV/001',
                'invoice_date_due': '2020-01-31',
                'sub_total': 100.0,
                'amount_due': 100.0,
                'balance': 100.0,
            }],
            'total': 100.0,
            'balance': 100.0,
            'currency': '$',
        }
        resp = self._post({
            'model': 'res.partner',
            'options': json.dumps(data),
            'output_format': 'xlsx',
            'report_name': 'Partner Statement',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('application/vnd.ms-excel', resp.headers.get('Content-Type', ''))
        disposition = resp.headers.get('Content-Disposition', '')
        self.assertTrue(
            'Partner' in disposition or 'Partner%20Statement' in disposition,
            disposition)

    def test_customer_statement_action_accepted_by_endpoint(self):
        """Estado de cuenta cliente: acción legítima y endpoint acepta petición."""
        partner = self.env['res.partner'].create({'name': 'Cliente P0 XLSX'})
        product = self.env['product.product'].create({
            'name': 'Producto P0', 'type': 'service', 'list_price': 100.0,
        })
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': '2020-02-01',
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })
        move.action_post()
        action = partner.action_print_xlsx()
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(action['data']['model'], 'res.partner')
        self.assertEqual(action['data']['output_format'], 'xlsx')

        resp = self._post({
            'model': action['data']['model'],
            'options': action['data']['options'],
            'output_format': action['data']['output_format'],
            'report_name': action['data']['report_name'],
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('application/vnd.ms-excel', resp.headers.get('Content-Type', ''))
        self.assertTrue(resp.content.startswith(b'PK'))
