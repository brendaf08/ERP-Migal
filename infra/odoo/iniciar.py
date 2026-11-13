"""Materializa secretos del entorno sin modificar el archivo montado."""
import configparser
import os
import sys
from pathlib import Path

config = configparser.ConfigParser(interpolation=None)
config.read('/etc/odoo/odoo.conf')
for name in ('DB_PASSWORD', 'ADMIN_PASSWD'):
    if not os.environ.get(name):
        raise SystemExit(f'Falta {name} en .env')
config['options']['db_password'] = os.environ['DB_PASSWORD']
config['options']['admin_passwd'] = os.environ['ADMIN_PASSWD']
path = Path('/var/lib/odoo/runtime.conf')
os.umask(0o077)
with path.open('w') as output:
    config.write(output)
os.chmod(path, 0o600)
os.environ['ODOO_RC'] = str(path)
os.execv('/entrypoint.sh', ['/entrypoint.sh', *sys.argv[1:]])
