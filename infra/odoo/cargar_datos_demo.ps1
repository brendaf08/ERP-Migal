# Carga los datos de demostracion opcionales [SIM] sobre la base restaurada (se puede repetir):
#  - Ventas + Punto de Venta para el estado de cuenta (cliente "PRUEBA - Inversiones del Norte")
#  - Stock, reposiciones y la cotizacion "[SIM-COB] Obra Pinedo" para la cobertura preliminar
# Uso:  .\cargar_datos_demo.ps1
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
foreach ($nombre in @('datos_demo_estado_cuenta', 'datos_demo_cobertura')) {
    Write-Host "== $nombre"
    docker compose cp "..\..\herramientas\$nombre.py" "odoo:/tmp/$nombre.py" 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Error "No se pudo copiar $nombre.py (esta levantado el contenedor odoo?)."; exit 1 }
    docker compose exec -T odoo sh -c "odoo shell -d ferre_inversiones_migal --no-http --log-level=error < /tmp/$nombre.py"
    if ($LASTEXITCODE -ne 0) { Write-Error "Fallo $nombre.py"; exit 1 }
}
Write-Host 'Datos de demostracion listos.'
