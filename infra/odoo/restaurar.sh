#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
test -f .env || { echo "Falta .env (copie .env.example a .env y defina las claves)." >&2; exit 1; }
docker compose up -d --wait --wait-timeout 120 db

if [[ -f restore/ferre_migal_docker.dump ]]; then
  # Modo paquete privado: ferre_migal_docker.dump + filestore_ferre_inversiones_migal.zip
  test -f restore/filestore_ferre_inversiones_migal.zip || { echo "Falta restore/filestore_ferre_inversiones_migal.zip" >&2; exit 1; }
  exists=$(docker compose exec -T db psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='ferre_inversiones_migal'")
  if [[ "$exists" == "1" ]]; then
    echo 'La base ya existe. No se sobrescribe; use docker compose up -d odoo.' >&2
    exit 1
  fi
  docker compose run --rm --no-deps --user root --entrypoint python3 odoo /opt/migal/filestore.py
  docker compose exec -T db createdb -U odoo -T template0 -E UTF8 ferre_inversiones_migal
  docker compose exec -T db pg_restore -U odoo --exit-on-error --single-transaction --no-owner --role=odoo -d ferre_inversiones_migal /restore/ferre_migal_docker.dump
else
  # Modo respaldo de Odoo: un .zip del gestor de bases (dump.sql + filestore/ + manifest.json)
  ls restore/*.zip >/dev/null 2>&1 || { echo "Coloque en restore/ el respaldo .zip de Odoo (o el paquete privado)." >&2; exit 1; }
  docker compose run --rm --no-deps --user root --entrypoint python3 odoo /opt/migal/restaurar_respaldo.py
fi
docker compose up -d odoo
puerto=$(grep -E '^ODOO_PORT=' .env | cut -d= -f2 || true)
echo "Abra http://localhost:${puerto:-8069} (el primer arranque tarda 1-2 minutos; revise docker compose logs odoo)"
