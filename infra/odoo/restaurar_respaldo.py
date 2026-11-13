"""Restaura un respaldo de Odoo (.zip del gestor de bases: dump.sql + filestore/ + manifest.json).

Se ejecuta dentro del contenedor de Odoo (usuario root) desde restaurar.ps1 / restaurar.sh:
- Acepta ZIP con o sin carpeta superior y con basura de macOS (__MACOSX, .DS_Store).
- Exige un respaldo de Odoo 19 y no sobrescribe una base o un filestore existentes.
- Limpia las líneas que agrega pg_dump 18 (\\restrict, \\unrestrict, SET transaction_timeout) para
  poder cargar el SQL en PostgreSQL 16, y omite cambios de propietario.
- Restaura en una sola transacción: si algo falla, la base queda vacía y se informa el error.
- Deja la dirección de la web y de los reportes en http://127.0.0.1:8069 (PDF con estilos).
"""
import glob
import io
import json
import os
import pwd
import re
import subprocess
import sys
import zipfile
from pathlib import Path

DB = "ferre_inversiones_migal"
DESTINO = Path("/var/lib/odoo/filestore") / DB
OMITIR = re.compile(r"^(\\restrict |\\unrestrict |SET transaction_timeout|ALTER .+ OWNER TO .+;$)")


def fallar(msg):
    sys.exit("ERROR: %s" % msg)


def entorno():
    env = os.environ.copy()
    env.update(PGHOST="db", PGUSER="odoo", PGPASSWORD=os.environ.get("DB_PASSWORD", ""))
    if not env["PGPASSWORD"]:
        fallar("Falta DB_PASSWORD en .env")
    return env


def psql(sql, db="postgres"):
    r = subprocess.run(["psql", "-tA", "-v", "ON_ERROR_STOP=1", "-d", db, "-c", sql],
                       env=entorno(), capture_output=True, text=True)
    if r.returncode:
        fallar(r.stderr.strip())
    return r.stdout.strip()


def buscar_respaldo():
    encontrados = []
    for ruta in sorted(glob.glob("/restore/*.zip")):
        with zipfile.ZipFile(ruta) as z:
            for nombre in z.namelist():
                if nombre.endswith("manifest.json") and "__MACOSX" not in nombre:
                    encontrados.append((ruta, nombre[: -len("manifest.json")]))
                    break
    if not encontrados:
        fallar("No hay en restore/ un respaldo de Odoo (.zip con manifest.json, dump.sql y filestore/).")
    if len(encontrados) > 1:
        fallar("Hay más de un respaldo en restore/: deje solo uno.")
    return encontrados[0]


def main():
    ruta, prefijo = buscar_respaldo()
    z = zipfile.ZipFile(ruta)
    manifest = json.loads(z.read(prefijo + "manifest.json"))
    if manifest.get("major_version") != "19.0":
        fallar("El respaldo es de Odoo %s; se requiere 19.0." % manifest.get("major_version"))
    if prefijo + "dump.sql" not in z.namelist():
        fallar("El ZIP no contiene dump.sql.")
    print("Respaldo: %s (base de origen %s, %s módulos)" % (
        os.path.basename(ruta), manifest.get("db_name"), len(manifest.get("modules", {}))))

    if psql("SELECT 1 FROM pg_database WHERE datname = '%s'" % DB) == "1":
        fallar("La base %s ya existe. No se sobrescribe." % DB)
    if DESTINO.exists() and any(DESTINO.iterdir()):
        fallar("El filestore ya contiene datos. No se sobrescribe.")

    print("1/3 Restaurando la base de datos (puede tardar unos minutos)...")
    psql("CREATE DATABASE %s ENCODING 'UTF8' TEMPLATE template0" % DB)
    proceso = subprocess.Popen(["psql", "-q", "-v", "ON_ERROR_STOP=1", "--single-transaction", "-d", DB],
                               stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, env=entorno(),
                               text=True, encoding="utf-8")
    with z.open(prefijo + "dump.sql") as crudo:
        for linea in io.TextIOWrapper(crudo, encoding="utf-8", newline=""):
            if not OMITIR.match(linea):
                proceso.stdin.write(linea)
    proceso.stdin.close()
    if proceso.wait():
        fallar("psql no pudo restaurar el SQL (ver mensaje anterior). La base quedó vacía.")

    print("2/3 Restaurando el filestore (adjuntos e imágenes)...")
    DESTINO.mkdir(parents=True, exist_ok=True)
    base_fs = prefijo + "filestore/"
    archivos = 0
    for item in z.infolist():
        if not item.filename.startswith(base_fs) or item.is_dir() or "__MACOSX" in item.filename:
            continue
        relativo = item.filename[len(base_fs):]
        destino = (DESTINO / relativo).resolve()
        if not destino.is_relative_to(DESTINO.resolve()):
            fallar("Ruta no permitida dentro del ZIP: %s" % item.filename)
        destino.parent.mkdir(parents=True, exist_ok=True)
        with z.open(item) as origen, open(destino, "wb") as salida:
            salida.write(origen.read())
        archivos += 1
    usuario = pwd.getpwnam("odoo")
    for p in [DESTINO.parent, DESTINO, *DESTINO.rglob("*")]:
        os.chown(p, usuario.pw_uid, usuario.pw_gid)

    print("3/3 Ajustando direcciones para Docker...")
    for clave, valor in (("web.base.url", "http://127.0.0.1:8069"), ("report.url", "http://127.0.0.1:8069"),
                         ("web.base.url.freeze", "True")):
        psql("INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date) "
             "VALUES ('%s', '%s', 1, 1, now(), now()) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
             % (clave, valor), DB)
    psql("DELETE FROM ir_config_parameter WHERE key IN ('migal_agente.url_publica', 'migal_agente.llm_api_key')", DB)

    usuarios = psql("SELECT login FROM res_users WHERE active AND NOT share ORDER BY id", DB).splitlines()
    print("Listo: %s archivos de filestore. Usuarios internos: %s" % (archivos, ", ".join(usuarios)))


if __name__ == "__main__":
    main()
