"""Restaura solo un filestore nuevo y rechaza rutas fuera del destino."""
import os
import pwd
import zipfile
from pathlib import Path

target = Path('/var/lib/odoo/filestore/ferre_inversiones_migal')
if target.exists() and any(target.iterdir()):
    raise SystemExit('El filestore ya contiene datos; no se sobrescribe.')
with zipfile.ZipFile('/restore/filestore_ferre_inversiones_migal.zip') as archive:
    for item in archive.infolist():
        path = (target / item.filename).resolve()
        if not path.is_relative_to(target.resolve()):
            raise SystemExit('Ruta no permitida dentro del ZIP')
    archive.extractall(target)
user = pwd.getpwnam('odoo')
for path in [target.parent, target, *target.rglob('*')]:
    os.chown(path, user.pw_uid, user.pw_gid)
