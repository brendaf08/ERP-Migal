# Odoo 19 local para ERP-MIGAL

El entorno usa Odoo 19 Community y PostgreSQL 16. Las imágenes están fijadas a las revisiones del entorno local de referencia y el Dockerfile añade las dependencias de los addons. El proyecto `erp-migal-odoo` usa el puerto local 8070 y crea sus propios volúmenes para PostgreSQL y el filestore de Odoo.

## Arranque

1. Desde la raíz del repositorio, entra en `infra/odoo`. Copia `.env.example` como `.env` y `odoo.conf.example` como `odoo.conf`. En macOS/Linux puedes usar estos comandos. En PowerShell, usa `Copy-Item` en lugar de `cp`.

   ```sh
   cd infra/odoo
   cp .env.example .env
   cp odoo.conf.example odoo.conf
   ```

2. Abre `.env` y asigna una contraseña local a `ODOO_DB_PASSWORD`. En `odoo.conf`, reemplaza el valor de `admin_passwd` por una contraseña maestra local distinta. Conserva estos dos archivos fuera de Git.
3. Valida la configuración y levanta el entorno desde la misma carpeta.

   ```sh
   docker compose config --quiet
   docker compose up -d --build
   docker compose ps
   ```

4. Entra en <http://localhost:8070/web/database/manager>. Crea una base de prueba nueva o restaura el ZIP compartido por privado con el equipo. Al restaurar una copia para pruebas, usa un nombre nuevo y marca **Esta base de datos es una copia** y **Neutralizar**. Comprueba que se pueda abrir un adjunto incluido en el ZIP.

## Módulos y permisos

En una base nueva, activa el modo desarrollador y abre **Aplicaciones → Actualizar lista de aplicaciones**. Quita el filtro **Aplicaciones** y activa `sale_order_request`, `partner_relation_multi` y `base_accounting_kit`. Odoo instalará sus dependencias y quedarán los nueve módulos de [custom_addons](../../custom_addons/readme.md).

Para verificar el flujo de ventas, añade el grupo **Vendedor de solicitudes de orden de venta** a un usuario de prueba con permisos de Ventas. Guarda una cotización en borrador y comprueba que aparezcan **Marcar como cotización aplicable** y, tras pulsarlo, **Crear solicitud de orden de venta**. Usa usuarios distintos para las aprobaciones de abastecimiento y transporte. La referencia de asignación es el [modelo de autorización](../../arquitectura/seguridad/modelo-autorizacion.md).

## Persistencia y respaldo

`odoo-db-data` guarda PostgreSQL y `odoo-web-data` conserva los adjuntos. Usa el gestor de bases para crear un respaldo **ZIP** con **Include filestore**. Compártelo por un medio privado autorizado. El comando `docker compose down -v` elimina los volúmenes de este proyecto.

El [agente comercial](../../producto/pc3/03-agente-comercial-pc3.md) tiene su propio entregable y entorno de ejecución.
