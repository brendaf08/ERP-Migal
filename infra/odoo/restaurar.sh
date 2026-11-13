#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
for file in .env restore/ferre_migal_docker.dump restore/filestore_ferre_inversiones_migal.zip; do
  test -f "$file" || { echo "Falta $file" >&2; exit 1; }
done
docker compose up -d --wait --wait-timeout 120 db
exists=$(docker compose exec -T db psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='ferre_inversiones_migal'")
if [[ "$exists" == "1" ]]; then
  echo 'La base ya existe. No se sobrescribe; use docker compose up -d odoo.' >&2
  exit 1
fi
docker compose run --rm --no-deps --user root --entrypoint python3 odoo /opt/migal/filestore.py
docker compose exec -T db createdb -U odoo -T template0 -E UTF8 ferre_inversiones_migal
docker compose exec -T db pg_restore -U odoo --exit-on-error --single-transaction --no-owner --role=odoo -d ferre_inversiones_migal /restore/ferre_migal_docker.dump
docker compose up -d odoo
echo 'Abra http://localhost:8069 (el arranque puede tardar; revise docker compose logs odoo)'
