# -*- coding: utf-8 -*-
{
    'name': 'Kit de contabilidad',
    'version': '19.0.1.0.0',
    'summary': 'Herramientas y reportes contables adicionales',
    'description': """
Kit de contabilidad
===================
Conjunto de extensiones contables para la gestión de activos y depreciaciones,
seguimiento de clientes, pagos masivos, facturación y pagos recurrentes,
conciliación e importación de extractos bancarios, límites de crédito,
revalorizaciones y reportes financieros.

Declara una dependencia obligatoria de Gestión de presupuestos para que
ambos addons se instalen conjuntamente.

No incluye ni depende de funcionalidades de soporte de Cybrosys.
""",
    'category': 'Accounting/Accounting',
    'license': 'LGPL-3',
    'depends': [
        'base_account_budget',
        'account',
        'account_check_printing',
        'analytic',
        'mail',
        'sale',
        'product',
        'web',
    ],
    'data': [
        # Seguridad
        'security/security.xml',
        'security/ir.model.access.csv',

        # Datos
        'data/account_pdc_data.xml',
        'data/account_financial_report_data.xml',
        'data/cash_flow_data.xml',
        'data/followup_levels.xml',
        'data/account_bulk_payment_data.xml',
        'data/multiple_invoice_data.xml',
        'data/account_recurring_invoice_data.xml',
        'data/account_asset_cron.xml',
        'data/recurring_entry_cron.xml',
        'data/followup_cron.xml',
        'data/bank_auto_reconcile_cron.xml',
        'data/mail_template_followup.xml',

        # Vistas de asistentes (acciones referenciadas por vistas)
        'wizard/asset_modify_views.xml',

        # Vistas
        'views/account_configuration.xml',
        'views/account_group.xml',
        'views/account_journal_views.xml',
        'views/account_move_views.xml',
        'views/account_move_line_views.xml',
        'views/account_payment_view.xml',
        'views/account_bank_statement_views.xml',
        'views/account_bank_statement_line_views.xml',
        'views/account_asset_category_views.xml',
        'views/account_asset_asset_views.xml',
        'views/account_followup.xml',
        'views/followup_line_views.xml',
        'views/followup_report.xml',
        'views/account_bulk_payment_views.xml',
        'views/multiple_invoice_layout_view.xml',
        'views/multiple_invoice_form.xml',
        'views/account_recurring_invoice_views.xml',
        'views/account_recurring_payments_view.xml',
        'views/credit_limit_view.xml',
        'views/product_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/reports_config_view.xml',
        'views/accounting_menu.xml',

        # Reportes
        'report/account_asset_report_views.xml',
        'report/res_partner_reports.xml',
        'report/res_partner_templates.xml',
        'report/report.xml',
        'report/report_financial_template.xml',
        'report/general_ledger_report_template.xml',
        'report/report_partner_ledger_template.xml',
        'report/report_aged_partner_template.xml',
        'report/report_journal_audit_template.xml',
        'report/report_tax_template.xml',
        'report/report_trial_balance_template.xml',
        'report/cash_flow_report_template.xml',
        'report/account_bank_book_template.xml',
        'report/account_cash_book_template.xml',
        'report/account_day_book_template.xml',
        'report/bulk_payment_report_templates.xml',
        'report/followup_report_templates.xml',
        'report/multiple_invoice_layouts.xml',
        'report/multiple_invoice_report_template.xml',

        # Vistas de asistentes
        'wizard/financial_report_views.xml',
        'wizard/account_report_general_ledger_views.xml',
        'wizard/account_report_partner_ledger_views.xml',
        'wizard/account_aged_trial_balance_views.xml',
        'wizard/account_print_journal_views.xml',
        'wizard/kit_account_tax_report_views.xml',
        'wizard/account_balance_report_views.xml',
        'wizard/account_bank_book_report_views.xml',
        'wizard/account_cash_book_report_views.xml',
        'wizard/account_day_book_report_views.xml',
        'wizard/cash_flow_report_views.xml',
        'wizard/asset_depreciation_confirmation_views.xml',
        'wizard/asset_disposal_views.xml',
        'wizard/asset_revaluation_views.xml',
        'wizard/import_bank_statement_views.xml',
        'wizard/account_lock_date_views.xml',
        'wizard/account_fx_revaluation_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'base_accounting_kit/static/src/scss/style.scss',
            'base_accounting_kit/static/src/scss/bank_rec_widget.css',
            'base_accounting_kit/static/src/js/action_manager.js',
            'base_accounting_kit/static/src/js/KanbanController.js',
            'base_accounting_kit/static/src/js/ListController.js',
            'base_accounting_kit/static/src/js/bank_reconcile_form_lines_widget.js',
            'base_accounting_kit/static/src/js/bank_reconcile_form_list_widget.js',
            'base_accounting_kit/static/src/xml/bank_reconcile_widget.xml',
            'base_accounting_kit/static/src/xml/bank_rec_widget.xml',
        ],
    },
    'external_dependencies': {
        'python': [
            'xlsxwriter',
            'openpyxl',
            'ofxparse',
            'qifparse',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
