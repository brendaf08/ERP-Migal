#!/usr/bin/env bash
# Aplica a una base ya restaurada los modulos de la version actual del repositorio
# (instala los agentes, migal_reportes y migal_ocr si faltan y actualiza los demas modulos de custom_addons).
set -euo pipefail
cd -- "$(dirname -- "$0")"
test -f .env || { echo "Falta .env (copie .env.example a .env y defina las claves)." >&2; exit 1; }
modulos=base_account_budget,base_accounting_kit,base_revision,base_tier_validation,migal_agente,migal_agente_ventas,migal_agente_marketing,migal_agente_suministro,migal_agente_cobranzas,migal_agente_pagos,migal_agente_contabilidad,migal_reportes,migal_ocr,partner_relation_multi,sale_order_request,sale_order_revision,sale_revision_tier_compat,sale_tier_validation
docker compose build odoo
docker compose up -d --wait --wait-timeout 120 db
docker compose stop odoo
echo 'Actualizando modulos (1-3 minutos)...'
docker compose run --rm --no-deps odoo odoo -d ferre_inversiones_migal -i migal_agente_ventas,migal_agente_marketing,migal_agente_suministro,migal_agente_cobranzas,migal_agente_pagos,migal_agente_contabilidad,migal_reportes,migal_ocr -u "$modulos" --stop-after-init --http-port=8070
docker compose exec -T db psql -U odoo -d ferre_inversiones_migal -c "DELETE FROM ir_config_parameter WHERE key = 'database.is_neutralized'; UPDATE ir_ui_view SET active = false WHERE key = 'web.neutralize_banner';"
docker compose up -d odoo
puerto=$(grep -E '^ODOO_PORT=' .env | cut -d= -f2 || true)
echo "Listo. Abra http://localhost:${puerto:-8069} (Ctrl+F5 si ya estaba abierto)"
