# Odoo 19 local para ERP-MIGAL

El entorno usa Odoo 19 Community y PostgreSQL 16. Las imágenes están fijadas a las revisiones del entorno local de referencia y el Dockerfile incorpora los nueve addons de MIGAL y sus dependencias Python. La imagen local se etiqueta como `erp-migal-odoo:19.0-20261112`. El proyecto `erp-migal-odoo` usa el puerto local 8070 y crea sus propios volúmenes para PostgreSQL y el filestore de Odoo.

## Arranque

En Windows, inicia **Docker Desktop con WSL 2 y contenedores Linux**. Las imágenes fijadas de Odoo y PostgreSQL incluyen variantes `linux/amd64` y `linux/arm64`. Docker selecciona la que corresponde al equipo. La configuración base se probó en macOS con Apple Silicon. La restauración del respaldo de MIGAL y la comprobación funcional de esta revisión quedan pendientes. [Instalación de Docker Desktop en Windows](https://docs.docker.com/desktop/setup/install/windows-install/)

1. Desde la raíz del repositorio, prepara los archivos locales con el bloque de tu sistema.

   **Windows (PowerShell)**

   ```powershell
   Set-Location .\infra\odoo
   Copy-Item .env.example .env
   Copy-Item odoo.conf.example odoo.conf
   ```

   **macOS y Linux**

   ```sh
   cd infra/odoo
   cp .env.example .env
   cp odoo.conf.example odoo.conf
   ```

2. Abre `.env` y asigna una contraseña local a `ODOO_DB_PASSWORD`. En `odoo.conf`, reemplaza el valor de `admin_passwd` por una contraseña maestra local distinta. Si reutilizas un `odoo.conf` de la versión anterior, cambia `addons_path` a `/opt/migal/addons`. Conserva los dos archivos fuera de Git.
3. Valida la configuración y levanta el entorno desde la misma carpeta. Los comandos de Docker son los mismos en PowerShell, macOS y Linux.

   ```sh
   docker compose config --quiet
   docker compose up -d --build
   docker compose ps
   ```

4. Abre el [gestor de bases de datos](http://localhost:8070/web/database/manager). Si cambiaste `ODOO_HTTP_PORT`, usa el puerto configurado en `.env`.

## Restaurar los datos de MIGAL

La imagen trae el código de los módulos. El respaldo privado aporta el catálogo, los usuarios, los permisos, los documentos y los adjuntos de la base de origen. Restaura una base con un nombre nuevo para conservar las que ya existen.

- **ZIP exportado por Odoo con filestore.** Usa **Restaurar base de datos** en el gestor de Odoo. Marca **Esta base de datos es una copia** y **Neutralizar** si es una base para pruebas. Los módulos instalados en el respaldo se cargan desde la imagen. Si eliges crear una base vacía, instala `sale_order_request`, `partner_relation_multi` y `base_accounting_kit` desde **Aplicaciones** para incorporar los nueve addons mediante sus dependencias.
- **Paquete entregado por el equipo el 12 de noviembre.** Es un ZIP que contiene un respaldo `.backup` de PostgreSQL 16 y una carpeta de filestore con rutas de Windows. Para usarlo en Docker, hay que restaurar el `.backup` con `pg_restore` en el servicio `db` y colocar los adjuntos en `/var/lib/odoo/filestore/<nombre_de_la_base>`, con acceso para el usuario `odoo` del contenedor. La alternativa más sencilla para distribuirlo es exportar desde la instancia de origen un ZIP de Odoo con **Include filestore**.

`odoo-db-data` guarda PostgreSQL y `odoo-web-data` conserva los adjuntos. Comparte los respaldos por un medio privado. El comando `docker compose down -v` elimina los volúmenes de este proyecto.

## Usar una imagen ya compilada

En un equipo con Docker, la imagen se puede entregar como un archivo generado con `docker save` y cargar con `docker load`. La imagen debe coincidir con la plataforma del equipo. Después de cargar la imagen con su etiqueta original, prepara `.env` y `odoo.conf` y arranca con `docker compose up -d --no-build`.

Para distribuir la misma etiqueta a equipos Intel/AMD y Apple Silicon, podemos publicar una imagen con variantes `linux/amd64` y `linux/arm64` en Docker Hub o GitHub Container Registry. Una vez publicada y con acceso al registro, el equipo configura `ODOO_IMAGE` en `.env` con la etiqueta completa, ejecuta `docker compose pull` y arranca con `docker compose up -d --no-build`. El respaldo se entrega por separado.

El [agente comercial](../../producto/pc3/03-agente-comercial-pc3.md) tiene su propio entregable y entorno de ejecución.
