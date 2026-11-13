# Odoo 19 Community · MIGAL

> **¿Primera vez?** Siga la [guía maestra de instalación](GUIA_INSTALACION.md): de cero a Odoo + módulos + Agente MIGAL + datos.

Incluye diez módulos propios/comunitarios y seis herramientas. El respaldo y filestore se comparten por un canal privado; no están en este repositorio. El núcleo se obtiene de la imagen oficial. No se modifica el código de los addons.

## Requisitos

Windows 11 con Docker Desktop iniciado (contenedores Linux, WSL2), Docker Compose v2 y Git. Linux: Docker Engine y Compose; macOS: Docker Desktop. Puerto 8069 libre. Para QR se requiere además Python en el host y cloudflared.

## Inicio en Windows (PowerShell)

```powershell
git clone https://github.com/brendaf08/ERP-Migal.git
cd ERP-Migal
git switch feature/pc3-agente-docker
cd infra/odoo
Copy-Item .env.example .env
notepad .env
# Cambie DB_PASSWORD y ADMIN_PASSWD por valores propios.
# Copie los DOS archivos del paquete privado a restore/.
docker compose build
.\restaurar.ps1
```

Si la política de PowerShell impide ejecutar el script, úselo solo para este proceso: `powershell -ExecutionPolicy Bypass -File .\restaurar.ps1`.
En Linux/macOS: `cp .env.example .env`, edite los valores, copie el paquete, ejecute `docker compose build` y `bash restaurar.sh`.
Abra http://localhost:8069. Inicie sesión con `administrador@migal.test` o `vendedor.pruebas@example.invalid` y la contraseña del LEEME.txt privado. ADMIN_PASSWD es la clave maestra de gestión de bases, no la contraseña del usuario.

Los scripts esperan el healthcheck de PostgreSQL, rechazan bases existentes, extraen el filestore con propietario odoo y restauran con `--no-owner --role=odoo`. Si fallan, se detienen y conservan el estado para diagnóstico; no eliminan volúmenes ni sobrescriben una instalación. Para reanudar una instalación restaurada: `docker compose up -d`. Para detenerla: `docker compose down` (conserva datos). No use `down -v` sobre datos que necesite conservar. Una restauración fallida puede dejar la base vacía y/o filestore: inspeccione los logs antes de eliminar manualmente esos datos de prueba.

## Configuración

El archivo versionado odoo.conf es una plantilla sin secretos. `iniciar.py` combina la plantilla con DB_PASSWORD y ADMIN_PASSWD en `/var/lib/odoo/runtime.conf`, con permisos 0600. ODOO_RC apunta a este archivo también al ejecutar comandos con `exec`. Nunca copie el odoo.conf local original. PostgreSQL no publica puertos y Odoo escucha en el host únicamente en 127.0.0.1:8069. Dentro del contenedor escucha normalmente en 8069.

El filestore se extrae en `/var/lib/odoo/filestore/ferre_inversiones_migal`. El ZIP contiene sus archivos directamente, sin una carpeta superior. No cambie DB_PASSWORD después de inicializar el volumen de PostgreSQL sin cambiar también la contraseña del rol en la base.

```powershell
docker compose exec odoo python3 -c "import odoo;print(list(odoo.__path__))"
docker compose logs --tail 100 odoo
```

La imagen añade qifparse 0.5. Anthropic es opcional y no se instala: la capa LLM está apagada en el paquete. La etiqueta odoo:19 recibe actualizaciones; el registro de validación indica el digest probado. Para una reproducción binaria exacta, use ese digest en FROM y registre también el digest de PostgreSQL.

## Verificación y pruebas

Compruebe el menú Agente MIGAL y el avatar flotante. En Ventas, abra S00586 → Disponibilidad → Cobertura preliminar. Desde el agente o el cliente de prueba genere el estado de cuenta y revise visualmente el PDF.

```powershell
docker compose exec odoo odoo -d ferre_inversiones_migal --test-tags migal_agente --stop-after-init --http-port=8070 '--db-filter=^ferre_inversiones_migal$'
```

En una base ya instalada, para asegurar que se seleccionan y ejecutan las pruebas del módulo añada `-u migal_agente` y desactive cron en ese proceso:

```powershell
docker compose exec odoo odoo -d ferre_inversiones_migal -u migal_agente --test-tags migal_agente --stop-after-init --http-port=8070 --max-cron-threads=0 '--db-filter=^ferre_inversiones_migal$'
```

La ejecución validada detiene el servidor para evitar conflictos de escritura de assets:

```powershell
docker compose stop odoo
docker compose run --rm --no-deps odoo odoo -d ferre_inversiones_migal -u migal_agente --test-tags migal_agente --stop-after-init --http-port=8070 --max-cron-threads=0 '--db-filter=^ferre_inversiones_migal$'
docker compose up -d odoo
```

Use exclusivamente la base de pruebas. Compruebe el resumen de tests, no solo el código de salida; un resumen de cero pruebas no valida las 29 esperadas.

## Publicador QR

Descargue cloudflared desde [Cloudflare](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) y colóquelo en `herramientas/cloudflared/cloudflared.exe` (ignorado por Git). Desde la raíz del repositorio:

```powershell
python herramientas/publicar_cotizaciones.py
```

Mantenga la consola abierta. El portero local 8090 publica solo las rutas de PDF autorizadas; la URL temporal deja de funcionar al cerrarlo. El navegador en el mismo PC consulta el portero local. No se configura un túnel al puerto 8069. Puede indicar otra ruta con `--cloudflared RUTA`.

Los scripts datos_demo_* y datos_pago_ficticios se ejecutan mediante el shell de Odoo, no con Python independiente. Ya están aplicados en el respaldo; no es necesario repetirlos. `cambiar_password_admin.py` conserva su implementación original para un entorno Python/Odoo local; no está adaptado al host sin el núcleo. En Docker cambie las contraseñas desde la interfaz de Odoo.

## Problemas frecuentes

- PDF sin estilos: `report.url=http://127.0.0.1:8069`, `web.base.url=http://127.0.0.1:8069`, `web.base.url.freeze=True`, en parámetros del sistema. La dirección del informe debe resolver dentro del contenedor.
- Puerto ocupado: detenga la instancia local de Odoo antes de iniciar Docker. No detenga PostgreSQL local: son instalaciones independientes.
- Motor Docker no disponible: abra Docker Desktop y espere a que el motor Linux esté listo (`docker info`).
- Falta un módulo: verifique el montaje custom_addons y reconstruya la imagen si cambió una dependencia Python.
- Error de autenticación PostgreSQL después de cambiar .env: el volumen conserva la clave inicial; editar .env no modifica el rol existente.

Consulte VALIDACION.md para resultados observados y límites de la entrega.
