# -*- coding: utf-8 -*-
{
    'name': 'Gestión de presupuestos',
    'version': '19.0.1.0.0',
    'summary': 'Gestión de presupuestos analíticos y posiciones presupuestarias',
    'description': """
Gestión de presupuestos
=======================
Permite definir presupuestos, posiciones presupuestarias y líneas de presupuesto
vinculadas a cuentas contables y cuentas analíticas, y comparar importes
previstos frente a importes prácticos y teóricos.
""",
    'category': 'Accounting/Accounting',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'analytic',
        'mail',
    ],
    'data': [
        'security/account_budget_security.xml',
        'security/ir.model.access.csv',
        'views/account_budget_views.xml',
        'views/account_analytic_account_views.xml',
    ],
    'post_init_hook': 'enable_analytic_accounting',
    'installable': True,
    'application': False,
    'auto_install': False,
}
