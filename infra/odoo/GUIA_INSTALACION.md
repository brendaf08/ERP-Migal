# Guía maestra de instalación — Odoo 19 MIGAL + Agente MIGAL (Docker)

De una PC vacía a tener **Odoo 19 Community con los módulos de MIGAL, el Agente MIGAL y todos los datos de prueba**, en unos 20 minutos.

> Validada el 13/11/2026 en Windows 11 + Docker Desktop 29 con el respaldo `ferre_inversiones_migal_revision_2026-11-13_18-40-18.zip`: restauración sin errores (100 módulos, 487 archivos adjuntos, 4 usuarios), inicio de sesión correcto, agente operativo, PDF con estilos, QR público por túnel (contenedor `publicador`) y **29/29 pruebas automáticas aprobadas**.
>
> Revalidada el 23/11/2026 con el mismo respaldo y la rama `feat/agente-cotizaciones-versiones`: restauración desde cero con `restaurar.ps1` (incluye `actualizar.ps1`), `migal_reportes` y `migal_ocr` instalados, fierro corrugado y logotipo aplicados, sin aviso de base neutralizada y **235/235 pruebas automáticas aprobadas** (`migal_agente`, `migal_ocr`, `migal_reportes`, `sale_order_request` y revisiones OCA).
>
> Revalidada el 23/11/2026 en `main` con la base multiagente (PR #24): restauración desde cero, los seis módulos de agente instalados por `actualizar.ps1`, datos «[PRUEBA]» cargados y **353/353 pruebas automáticas aprobadas** (agentes, núcleo, OCR, reportes, solicitudes, revisiones y validación por niveles).

---

## 0. Qué vas a tener al final

| Componente | Detalle |
|---|---|
| Odoo 19 Community | Imagen oficial de Docker, con PostgreSQL 16 |
| Módulos | `sale_order_request` (solicitudes de orden de venta), aprobaciones y revisiones OCA, contabilidad (`base_accounting_kit`), `partner_relation_multi` |
| Agente MIGAL | Avatar flotante, chat (entiende errores de escritura, plurales y «cotización de Luis»), WhatsApp, QR, cobertura preliminar con diagnóstico en PDF y estado de cuenta |
| Cotizaciones por versiones | La versión anterior de una cotización sigue disponible hasta que vence; el agente pregunta qué cotización y qué versión cuando hay varias |
| Agentes por área | Orquestador y seis agentes (`migal_agente_ventas`, `_marketing`, `_suministro`, `_cobranzas`, `_pagos`, `_contabilidad`). Guía del equipo: `producto/agentes/README.md` |
| Escanear lista (`migal_ocr`) | Foto, PDF o texto de la lista del cliente → cada producto del catálogo con su % de coincidencia → se agrega a la cotización |
| Reportes MIGAL | PDF A4 y ticket 58 mm con vista previa antes de imprimir, logotipo MIGAL |
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
git config --global core.longpaths true
git clone https://github.com/brendaf08/ERP-Migal.git
cd ERP-Migal
cd infra\odoo
```

> Trabaja sobre `main` (la rama que queda al clonar). `core.longpaths` evita errores de rutas largas en Windows. Si vas a construir un agente, después de instalar crea tu rama `feat/agente-<area>` desde `main` (ver `producto/agentes/README.md`).

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

El script restaura la base y los adjuntos, deja listas las direcciones para que los PDF salgan con estilos y, al final,
ejecuta `actualizar.ps1`: instala los seis agentes, `migal_reportes` y `migal_ocr`, actualiza los demás módulos de `custom_addons`, crea
los productos de fierro corrugado que piden las notas de venta reales y aplica el logotipo MIGAL. Tarda unos minutos
más. **No sobrescribe nada**: si la base ya existe, se detiene.

### ¿Ya tenías Odoo instalado con una versión anterior?

No hace falta restaurar de nuevo. Descarga los cambios y actualiza los módulos sobre tu base:

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\actualizar.ps1
```

Conserva tus datos y claves. Recarga el navegador con **Ctrl+F5** al terminar.

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
- [ ] En el chat del agente: «cotización de Luis» → lista de cotizaciones abiertas → responder «1».
- [ ] **Disponibilidad** → **Ver diagnóstico de disponibilidad** → se abre el PDF; debajo, el mensaje por producto para el cliente.
- [ ] Una cotización → **Imprimir** → vista previa con selector **A4 / Ticket 58 mm**.
- [ ] Una cotización sin productos → avatar → **Escanear lista del cliente** → pegar `10 bls cemento sol` → **Leer lista** → **Agregar a la cotización**.

## 8. Datos de prueba para la demo y los agentes

El respaldo ya trae los datos del equipo. Para los casos de la demostración y los datos «[PRUEBA]» que usan los agentes (compras, facturas de proveedor, cartera y CRM), ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\cargar_datos_demo.ps1
```

Este comando agrega:
- **Estado de cuenta:** el cliente «PRUEBA - Inversiones del Norte» con facturas, nota de crédito, pagos, un abono sin aplicar y una venta «a cuenta» en el **Punto de Venta** (crea la caja «Caja MIGAL [SIM]»).
- **Cobertura:** stock, reposiciones previstas y la cotización «[SIM-COB] Obra Pinedo», con todos los casos (stock, reposición, regla habitual y faltante).

Se puede ejecutar varias veces: no duplica nada.

### 8.1 Inteligencia artificial con Google Gemini

El chat del agente y la lectura de fotos en **Escanear lista** usan Gemini. Sin clave, todo lo demás funciona: el chat
usa su intérprete propio y en Escanear lista se puede pegar la lista como texto.

1. Crea una clave en Google AI Studio (proyecto con facturación habilitada).
2. Odoo → **Ajustes** → **Agente MIGAL** → bloque **Inteligencia artificial**.
3. Proveedor **Google Gemini**, pega la **Clave de API**, marca **Autorizo enviar datos al proveedor de IA** y,
   si quieres respuestas redactadas por IA en el chat, **Usar IA en el chat**. Guarda.

La clave queda en la base de datos de tu PC, nunca en el repositorio. Si un modelo de Gemini está saturado o sin cuota,
el sistema pasa al siguiente automáticamente.

### 8.2 Escanear la lista de productos de un cliente

1. Abre una cotización (guárdala si es nueva) y pulsa **Escanear lista**, o usa el avatar del agente.
2. Sube la foto o el PDF de la lista: se lee al instante. También puedes pegar el texto y pulsar **Leer lista**.
3. Cada línea muestra el producto propuesto, el **% de coincidencia** (verde, amarillo o rojo) y otras sugerencias del
   mismo tipo. Cambia lo que haga falta y pulsa **Agregar a la cotización**: los productos repetidos se suman.

La IA solo transcribe; el producto lo propone el emparejador (normalizador ferretero + similitud difusa) y lo confirma la
persona. Los términos ferreteros propios («huincha», «terokal»…) se editan en **Ventas › Configuración › Términos
ferreteros**. Las fotos de notas de venta reales para la demo se comparten por el canal privado del equipo: contienen
datos de clientes y **no se suben a GitHub**.

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
| Actualizar el código del equipo | `git pull` → `powershell -ExecutionPolicy Bypass -File .\actualizar.ps1` |
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
