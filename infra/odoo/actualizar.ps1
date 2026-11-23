# Aplica a una base ya restaurada los modulos de la version actual del repositorio
# (instala migal_reportes y migal_ocr si faltan y actualiza los demas modulos de custom_addons).
# Uso: powershell -ExecutionPolicy Bypass -File .\actualizar.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Invoke-Compose {
    & docker compose @args
    if ($LASTEXITCODE -ne 0) { throw "docker compose fallo ($LASTEXITCODE). Se detuvo la actualizacion." }
}
if (-not (Test-Path -LiteralPath '.env')) { throw 'Falta .env (copie .env.example a .env y defina las claves).' }
$modulos = 'base_account_budget,base_accounting_kit,base_revision,base_tier_validation,migal_agente,migal_reportes,migal_ocr,partner_relation_multi,sale_order_request,sale_order_revision,sale_revision_tier_compat,sale_tier_validation'
Invoke-Compose build odoo
Invoke-Compose up -d --wait --wait-timeout 120 db
Invoke-Compose stop odoo
Write-Host 'Actualizando modulos (1-3 minutos)...'
Invoke-Compose run --rm --no-deps odoo odoo -d ferre_inversiones_migal -i 'migal_reportes,migal_ocr' -u $modulos --stop-after-init --http-port=8070
# Sin la franja roja de «base neutralizada» (la neutralizacion sigue: no se envian correos).
Invoke-Compose exec -T db psql -U odoo -d ferre_inversiones_migal -c "DELETE FROM ir_config_parameter WHERE key = 'database.is_neutralized'; UPDATE ir_ui_view SET active = false WHERE key = 'web.neutralize_banner';"
Invoke-Compose up -d odoo
$puerto = '8069'
$linea = Get-Content .env | Where-Object { $_ -match '^ODOO_PORT=(\d+)' } | Select-Object -First 1
if ($linea) { $puerto = ($linea -split '=')[1].Trim() }
Write-Host "Listo. Abra http://localhost:$puerto (Ctrl+F5 si ya estaba abierto)"
