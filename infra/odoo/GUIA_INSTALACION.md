# Guía maestra de instalación — Odoo 19 MIGAL + Agente MIGAL (Docker)

De una PC vacía a tener **Odoo 19 Community con los módulos de MIGAL, el Agente MIGAL y todos los datos de prueba**, en unos 20 minutos.

> Validada el 13/11/2026 en Windows 11 + Docker Desktop 29 con el respaldo `ferre_inversiones_migal_revision_2026-11-13_18-40-18.zip`: restauración sin errores (100 módulos, 487 archivos adjuntos, 4 usuarios), inicio de sesión correcto, agente operativo, PDF con estilos, QR público por túnel (contenedor `publicador`) y **29/29 pruebas automáticas aprobadas**.

---

## 0. Qué vas a tener al final

| Componente | Detalle |
|---|---|
| Odoo 19 Community | Imagen oficial de Docker, con PostgreSQL 16 |
| Módulos | `sale_order_request` (solicitudes de orden de venta), aprobaciones y revisiones OCA, contabilidad (`base_accounting_kit`), `partner_relation_multi` |
| Agente MIGAL | Avatar flotante, chat, WhatsApp, QR, cobertura preliminar y estado de cuenta |
| Datos | Catálogo MIGAL, clientes, 54 ventas DEMO, facturas, pagos y solicitudes de prueba |
| Configuración | Empresa, métodos de pago, roles de usuario y reglas habituales de cobertura (todo viene en el respaldo) |

## 1. Requisitos (una sola vez)

1. **Windows 10/11** con al menos 8 GB de RAM y 5 GB libres.
2. **Docker Desktop**: descárgalo de <https://www.docker.com/products/docker-desktop/>, instálalo (con WSL 2), reinicia si te lo pide y **ábrelo**. Espera a que diga *Engine running*.
3. **Git**: <https://git-scm.com/download/win> (deja las opciones por defecto).
4. El **respaldo de la base**: `ferre_inversiones_migal_revision_….zip`. Pídelo al equipo por el canal privado (Drive o WhatsApp). **No lo subas a GitHub.**

Comprueba en **PowerShell**:

```powershell
docker --version
git --version
```

## 2. Descargar el proyecto

```powershell
cd $HOME\Documents
git clone https://github.com/brendaf08/ERP-Migal.git
cd ERP-Migal
git switch feature/pc3-agente-docker
cd infra\odoo
```

> Cuando la rama se fusione a `main`, el paso `git switch` ya no hará falta.

## 3. Colocar el respaldo

Copia el `.zip` del respaldo **tal cual, sin descomprimirlo**, dentro de la carpeta `infra\odoo\restore\`:

```text
ERP-Migal\infra\odoo\restore\ferre_inversiones_migal_revision_2026-11-13_18-40-18.zip
```

Deja **un solo respaldo** en esa carpeta.

## 4. Configurar las claves del entorno

```powershell
Copy-Item .env.example .env
notepad .env
```

Cambia los dos valores por claves propias (inventadas, solo para tu PC) y guarda:

```text
DB_PASSWORD=una-clave-para-la-base
ADMIN_PASSWD=una-clave-maestra
ODOO_PORT=8069
```

- `DB_PASSWORD`: clave interna de PostgreSQL. **Defínela antes del primer arranque y no la cambies después.**
- `ADMIN_PASSWD`: clave maestra de Odoo (gestión de bases). No es la clave de los usuarios.
- `ODOO_PORT`: si ya tienes otro Odoo en el 8069, pon por ejemplo `8079`.

## 5. Construir y restaurar (todo automático)

```powershell
docker compose build
powershell -ExecutionPolicy Bypass -File .\restaurar.ps1
```

Debes ver algo así:

```text
Respaldo: ferre_inversiones_migal_revision_….zip (… 100 módulos)
1/3 Restaurando la base de datos (puede tardar unos minutos)...
2/3 Restaurando el filestore (adjuntos e imágenes)...
3/3 Ajustando direcciones para Docker...
Listo: 487 archivos de filestore. Usuarios internos: administrador@migal.test, vendedor.pruebas@example.invalid, ...
Abra http://localhost:8069
```

El script restaura la base y los adjuntos, y deja listas las direcciones para que los PDF salgan con estilos. **No sobrescribe nada**: si la base ya existe, se detiene.

## 6. Entrar a Odoo

1. Espera 1 o 2 minutos y abre **<http://localhost:8069>** (o el puerto que pusiste).
2. Usuario: **`administrador@migal.test`**. La clave es la del respaldo (pídela al equipo) o pon una propia:

```powershell
powershell -ExecutionPolicy Bypass -File .\cambiar_clave.ps1
```

   Te pide la nueva clave sin mostrarla. Para otro usuario: `.\cambiar_clave.ps1 vendedor.pruebas@example.invalid`.

| Usuario | Rol |
|---|---|
| `administrador@migal.test` | Administrador (GER/FCO/SIS) |
| `vendedor.pruebas@example.invalid` | Vendedor (VEN) |
| `abastecimiento.pruebas@example.invalid` | Abastecimiento |
| `transporte.pruebas@example.invalid` | Transporte |

## 7. Verificar que todo funciona (5 minutos)

- [ ] En el menú principal aparece **Agente MIGAL**.
- [ ] Abajo a la derecha está el **avatar morado** del agente.
- [ ] **Ventas** → abre una cotización con productos → avatar → pestaña **Disponibilidad** → **Cobertura preliminar**.
- [ ] Pestaña **Enviar cotización** → **Cliente a distancia: WhatsApp** → se generan el mensaje y el PDF.
- [ ] **Contactos** → un cliente con facturas → avatar → **Estado de cuenta** → **Descargar PDF**. El PDF debe tener logo, colores y el recuadro de métodos de pago.

## 8. (Opcional) Datos extra para la demo

El respaldo ya trae los datos del equipo. Si además quieres los casos preparados para la demostración, ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\cargar_datos_demo.ps1
```

Este comando agrega:
- **Estado de cuenta:** el cliente «PRUEBA - Inversiones del Norte» con facturas, nota de crédito, pagos, un abono sin aplicar y una venta «a cuenta» en el **Punto de Venta** (crea la caja «Caja MIGAL [SIM]»).
- **Cobertura:** stock, reposiciones previstas y la cotización «[SIM-COB] Obra Pinedo», con todos los casos (stock, reposición, regla habitual y faltante).

Se puede ejecutar varias veces: no duplica nada.

## 9. (Opcional) QR que abra desde cualquier celular

No necesitas instalar nada más: el publicador corre en su propio contenedor (portero + túnel seguro de Cloudflare). Con Odoo encendido, en `infra\odoo`:

```powershell
docker compose --profile qr up -d --build publicador
docker compose logs publicador
```

Cuando el registro diga `Túnel activo: https://….trycloudflare.com`, los QR y enlaces que genere el agente ya abren desde cualquier red (datos móviles incluidos). El agente lo detecta solo; no hay que configurar nada en Odoo.

- Solo publica los PDF de cotizaciones y estados de cuenta con su token; el resto de Odoo no es accesible.
- Para despublicar: `docker compose stop publicador` (los QR emitidos dejan de abrir).
- La dirección cambia cada vez que lo enciendes: genera los QR después de encenderlo.

## 10. Uso diario

| Quiero… | Comando (en `ERP-Migal\infra\odoo`) |
|---|---|
| Encender Odoo | `docker compose up -d` |
| Encender / apagar el QR público | `docker compose --profile qr up -d publicador` / `docker compose stop publicador` |
| Apagarlo (conserva los datos) | `docker compose --profile qr down` |
| Ver si hay errores | `docker compose logs --tail 100 odoo` |
| Actualizar el código del equipo | `git pull` → `docker compose build` → `docker compose up -d` |
| Aplicar cambios de un módulo | `docker compose stop odoo` → `docker compose run --rm --no-deps odoo odoo -d ferre_inversiones_migal -u migal_agente --stop-after-init` → `docker compose up -d` |
| Correr las pruebas del agente | `docker compose stop odoo` → `docker compose run --rm --no-deps odoo odoo -d ferre_inversiones_migal -u migal_agente --test-tags migal_agente --stop-after-init --http-port=8070` → `docker compose up -d` |

Después de reiniciar la PC: abre Docker Desktop y ejecuta `docker compose up -d`.

## 11. Empezar de cero (borra todo)

> ⚠️ Elimina la base y los adjuntos de **tu** instalación Docker. Úsalo solo si quieres reinstalar.

```powershell
docker compose down -v
powershell -ExecutionPolicy Bypass -File .\restaurar.ps1
```

## 12. Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `failed to connect to the docker API` | Docker Desktop no está abierto. Ábrelo y espera *Engine running*. |
| `port is already allocated` | Otro programa usa el puerto. Cambia `ODOO_PORT` en `.env` (por ejemplo `8079`) y ejecuta `docker compose up -d`. |
| `La base ya existe. No se sobrescribe` | Ya está restaurada: usa `docker compose up -d`. Para reinstalar, ve al punto 11. |
| `No hay en restore/ un respaldo de Odoo` | El `.zip` no está en `infra\odoo\restore\` o está descomprimido. |
| `Hay más de un respaldo en restore/` | Deja un solo `.zip` en esa carpeta. |
| No puedo iniciar sesión | `.\cambiar_clave.ps1` para poner una clave nueva. |
| PDF sin colores ni logo | Ajustes → Técnico → Parámetros del sistema: `report.url` y `web.base.url` = `http://127.0.0.1:8069` y `web.base.url.freeze` = `True` (el restaurador ya lo hace). |
| El agente avisa «No hay publicación activa» | El publicador no está encendido o aún no abrió el túnel: `docker compose logs publicador` (punto 9). |
| El script `.ps1` no se ejecuta | Usa `powershell -ExecutionPolicy Bypass -File .\script.ps1`, como en esta guía. |
| Error de autenticación de PostgreSQL | Cambiaste `DB_PASSWORD` después del primer arranque. Vuelve a la clave original o reinstala (punto 11). |

## 13. Qué nunca se sube a GitHub

`.env`, respaldos (`.zip`, `.dump`, `.backup`), filestore, `odoo.conf` con claves reales, binarios de `cloudflared` y archivos de credenciales. El `.gitignore` del repositorio ya los excluye.

---

**Referencias:** `README.md` (detalle técnico del entorno), `VALIDACION.md` (resultados de la validación) y la documentación del agente en `custom_addons/migal_agente`.
