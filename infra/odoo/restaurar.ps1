$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Invoke-Compose {
    & docker compose @args
    if ($LASTEXITCODE -ne 0) { throw "docker compose fallo ($LASTEXITCODE). Se detuvo la restauracion." }
}
if (-not (Test-Path -LiteralPath '.env')) { throw 'Falta .env (copie .env.example a .env y defina las claves).' }
Invoke-Compose up -d --wait --wait-timeout 120 db

if (Test-Path -LiteralPath 'restore/ferre_migal_docker.dump') {
    # Modo paquete privado: ferre_migal_docker.dump + filestore_ferre_inversiones_migal.zip
    if (-not (Test-Path -LiteralPath 'restore/filestore_ferre_inversiones_migal.zip')) { throw 'Falta restore/filestore_ferre_inversiones_migal.zip' }
    $exists = Invoke-Compose exec -T db psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='ferre_inversiones_migal'"
    if (($exists -join '').Trim() -eq '1') { throw 'La base ya existe. No se sobrescribe; use docker compose up -d odoo para reanudar.' }
    Invoke-Compose run --rm --no-deps --user root --entrypoint python3 odoo /opt/migal/filestore.py
    Invoke-Compose exec -T db createdb -U odoo -T template0 -E UTF8 ferre_inversiones_migal
    Invoke-Compose exec -T db pg_restore -U odoo --exit-on-error --single-transaction --no-owner --role=odoo -d ferre_inversiones_migal /restore/ferre_migal_docker.dump
} else {
    # Modo respaldo de Odoo: un .zip del gestor de bases (dump.sql + filestore/ + manifest.json)
    if (-not (Get-ChildItem -LiteralPath 'restore' -Filter '*.zip' -File)) { throw 'Coloque en restore/ el respaldo .zip de Odoo (o el paquete privado).' }
    Invoke-Compose run --rm --no-deps --user root --entrypoint python3 odoo /opt/migal/restaurar_respaldo.py
}
Invoke-Compose up -d odoo
$puerto = '8069'
$linea = Get-Content .env | Where-Object { $_ -match '^ODOO_PORT=(\d+)' } | Select-Object -First 1
if ($linea) { $puerto = ($linea -split '=')[1].Trim() }
Write-Host "Abra http://localhost:$puerto (el primer arranque tarda 1-2 minutos; revise docker compose logs odoo)"
