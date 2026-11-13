# Cambia la clave de un usuario de Odoo en el contenedor (se pide sin mostrarla).
# Uso:  .\cambiar_clave.ps1                                  (administrador@migal.test)
#       .\cambiar_clave.ps1 vendedor.pruebas@example.invalid
param([string]$Usuario = 'administrador@migal.test')
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
$segura = Read-Host "Nueva clave para $Usuario" -AsSecureString
$clave = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura))
if (-not $clave) { Write-Error 'La clave no puede estar vacia.'; exit 1 }
$script = @'
import os
u = env["res.users"].search([("login", "=", os.environ["MIGAL_USUARIO"])])
assert u, "No existe el usuario %s" % os.environ["MIGAL_USUARIO"]
u.password = os.environ["MIGAL_CLAVE"]
env.cr.commit()
print("Clave actualizada para", u.login)
'@
$tmp = Join-Path $env:TEMP 'migal_clave.py'
[IO.File]::WriteAllText($tmp, $script, (New-Object Text.UTF8Encoding($false)))
docker compose cp $tmp odoo:/tmp/migal_clave.py 2>$null
if ($LASTEXITCODE -ne 0) { Remove-Item $tmp; Write-Error 'No se pudo copiar el script (esta levantado el contenedor odoo?).'; exit 1 }
Remove-Item $tmp
docker compose exec -T -e "MIGAL_USUARIO=$Usuario" -e "MIGAL_CLAVE=$clave" odoo sh -c "odoo shell -d ferre_inversiones_migal --no-http --log-level=warn < /tmp/migal_clave.py"
$resultado = $LASTEXITCODE
docker compose exec -T -u root odoo rm -f /tmp/migal_clave.py
if ($resultado -ne 0) { Write-Error 'No se pudo cambiar la clave.'; exit 1 }
