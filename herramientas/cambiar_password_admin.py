"""Cambia la contraseña de un usuario de Odoo directamente en la base de datos.

Uso (desde C:\\Users\\luisn\\Downloads\\odoo19):
    python herramientas\\cambiar_password_admin.py
    python herramientas\\cambiar_password_admin.py --login otro@usuario --db otra_bd
    python herramientas\\cambiar_password_admin.py --check   (solo verifica, no cambia nada)

La contraseña se pide por teclado (no se muestra ni se guarda en ningún archivo).
"""
import argparse
import getpass
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'odoo'))

parser = argparse.ArgumentParser()
parser.add_argument('--login', default='administrador@migal.test')
parser.add_argument('--db', default='ferre_inversiones_migal')
parser.add_argument('--conf', default=os.path.join(BASE, 'odoo.conf'))
parser.add_argument('--check', action='store_true', help='solo verifica que el usuario exista')
args = parser.parse_args()

import odoo  # noqa: E402
from odoo.tools import config  # noqa: E402

config.parse_config(['-c', args.conf, '--log-level=warn'])

from odoo.api import Environment, SUPERUSER_ID  # noqa: E402
from odoo.orm.registry import Registry  # noqa: E402

registry = Registry(args.db)
with registry.cursor() as cr:
    env = Environment(cr, SUPERUSER_ID, {})
    user = env['res.users'].with_context(active_test=False).search([('login', '=', args.login)], limit=1)
    if not user:
        sys.exit(f'No existe el usuario "{args.login}" en la base "{args.db}".')
    print(f'Usuario encontrado: {user.name} ({user.login}) en la base {args.db}')
    if args.check:
        sys.exit(0)

    pw = getpass.getpass('Nueva contraseña (no se ve al escribir): ')
    pw2 = getpass.getpass('Repite la contraseña: ')
    if not pw:
        sys.exit('La contraseña no puede estar vacía. No se cambió nada.')
    if pw != pw2:
        sys.exit('Las contraseñas no coinciden. No se cambió nada.')

    user.write({'password': pw, 'active': True})
    cr.commit()
    print('Contraseña actualizada. Ya puedes iniciar sesión en http://127.0.0.1:8069')
