# ERP-MIGAL · PC3 — Colaboración GitHub, auditoría Odoo y Docker

**Se aplica a:** fases 0–2 del [Plan Maestro](01-plan-maestro-pc3.md), verificaciones de la fase 4 y mejoras posteriores a PC3. Aquí se conservan los **prompts A y D**; los **B, C y E** están en [03 — Agente comercial](03-agente-comercial-pc3.md).
**Autoridad documental:** `brendaf08/ERP-Migal` (rama `main`) y su `CONTRIBUTING.md`. **No crear repositorio alternativo.**

## 1. Principio de organización

El **repositorio GitHub** es fuente de código, procesos y documentación. Una **carpeta padre local** permite a Codex/Cursor inspeccionar el agente y las personalizaciones de Odoo, pero **no es un segundo repositorio**. Una **base Odoo** es estado operacional independiente: Git no sincroniza sus registros ni restaura permisos por sí solo.

### Estructura acordable en `ERP-Migal`

```text
ERP-Migal/
├── README.md                         # existente
├── CONTRIBUTING.md                   # existente
├── arquitectura/                     # existente, conservar
├── procesos/                         # existente, ampliar con A1–4
├── datos/                            # existente, preservar
├── pruebas/                          # existente, no sobrescribir CP antiguos
├── fuentes/                          # existente, preservar
├── producto/
│   ├── pc3/                          # estos cuatro documentos de coordinación
│   └── agente-comercial/             # código y docs reales del agente
├── infra/odoo/                       # compose/config/guía del entorno
└── custom_addons/                    # solo addons verificados y aprobados
```

### Workspace de desarrollo local

```text
MIGAL-WORKSPACE/                    # carpeta de trabajo, no repositorio
├── ERP-Migal/                      # clon del repositorio oficial
├── odoo-original-referencia/       # lectura/auditoría; no publicar
└── backups-locales/               # privado; no publicar
```

No dar al asistente de programación acceso a contraseñas, backups empresariales, `.env` reales ni bases de datos que no necesite. Tener ambas carpetas visibles **no prueba** qué módulos/campos están instalados: eso requiere consultar la instancia autorizada.


### Prompt D — Diagnóstico de contexto desde la carpeta padre

**Cuándo:** después de crear el workspace y preferiblemente después de la auditoría inicial.


> Este prompt mantiene la idea de **contexto unificado** de tu archivo original, corrigiendo la afirmación de que abrir dos carpetas prueba automáticamente los campos configurados de Odoo.

```text
Actúa como Arquitecto de Software Empresarial (Odoo 19 Community + Python 3.12 + agente LLM).

He abierto el workspace local MIGAL-WORKSPACE, con:
- ERP-Migal/: clon del repositorio oficial brendaf08/ERP-Migal, que incluye documentación y, cuando estén aprobados, custom_addons/ y producto/agente-comercial/.
- odoo-original-referencia/: código oficial para consulta/auditoría de la versión realmente utilizada.

ANTES DE EDITAR:
1. Lee README.md, CONTRIBUTING.md, arquitectura/modulos-y-dependencias.md, procesos/catalogo-reglas.md, arquitectura/seguridad/modelo-autorizacion.md y producto/pc3/01-plan-maestro-pc3.md.
2. Identifica en qué carpeta y rama estamos y verifica git status.
3. Resume los módulos y campos que se observan en código; separa claramente lo verificado en instancia Odoo de lo inferido de los addons.
4. Compara las necesidades del agente con los modelos existentes y localiza discrepancias o decisiones funcionales pendientes.
5. Presenta un plan de archivos afectados, riesgos y pruebas antes de implementar.

RESTRICCIONES:
- No cambiar directamente main ni crear commits automáticos.
- No mover addons, editar core Odoo, borrar respaldos o acceder a secretos.
- No asumir integración real con WhatsApp, KeyFacil, módulo de Flota ni LLM externo.
- No agregar permisos de escritura al agente.

SALIDA: diagnóstico de contexto + brechas concretas + propuesta de siguiente paso verificable.
```

- [ ] Codex identificó carpetas y rama sin modificar ni publicar secretos.
- [ ] Diferenció campos vistos en código de campos verificados en Odoo.

## 2. Fase de auditoría de personalizaciones (solo lectura inicialmente)

**Entrada:** código recibido del compañero + origen/versión exacta de Odoo.

- [ ] Recibir copia íntegra, con explicación de su procedencia y modificaciones conocidas.
- [ ] Identificar rama, etiqueta o SHA del núcleo original; no asumir que `19.0` remoto actual coincide con la base usada.
- [ ] Inventariar `__manifest__.py`, dependencias, Python, XML, CSV de seguridad y datos.
- [ ] Distinguir addons **propios**, de **terceros**, **nativos** y archivos temporales.
- [ ] Comparar contra la **misma revisión** del núcleo, excluyendo `.git`, filestore, dependencias y binarios generados.
- [ ] Inspeccionar cambios de `odoo/addons` y marcarlos como **riesgo de intrusión**, no moverlos automáticamente.
- [ ] Identificar cambios en `res.partner`, `product.product`, `sale.order`, inventario, flota, precios y permisos.
- [ ] Documentar riesgo, recomendación, fuente, archivos concretos y aprobación necesaria.
- [ ] Guardar `REPORTE_AUDITORIA_MIGAL.md` con hallazgos verificados y pendientes.
- [ ] **Solo tras revisión:** extraer módulos a `custom_addons/` y probarlos sin borrar originales.

**Puerta de salida:** hay una tabla de diferencias + dependencias; la extracción no ha destruido fuentes ni confundido versiones.


### Prompt A — Auditoría de solo lectura

**Cuándo:** una vez recibido el código del compañero y antes de extraer addons.


> **Conservado del plan corregido anterior:** auditoría primero, sin modificaciones destructivas. Sustituye la orden original de mover archivos y borrar temporales por una evaluación de solo lectura.

```text
Actúa como Ingeniero DevOps y Auditor de Odoo 19 Community.

Estoy trabajando con el código de una instancia Odoo configurada para Ferre & Inversiones MIGAL.

Necesito una auditoría estrictamente de SOLO LECTURA.

1. Identifica versión, rama, commit y estructura del código disponible.
2. Determina qué módulos son nativos, de terceros o personalizaciones propias.
3. Compara las modificaciones con el código oficial de la misma versión y revisión, cuando esté disponible.
4. Identifica archivos modificados en el núcleo, modelos extendidos, campos personalizados, manifiestos, dependencias, controles de seguridad y vistas.
5. Clasifica los riesgos de compatibilidad con Odoo 19.
6. Propón qué componentes podrían incorporarse a `custom_addons/`.
7. Genera `REPORTE_AUDITORIA_MIGAL.md`, distinguiendo hallazgos comprobados y aspectos pendientes.

RESTRICCIONES:
- No mover ni eliminar archivos.
- No modificar el código fuente.
- No instalar dependencias ni ejecutar migraciones.
- No modificar bases de datos.
- No crear commits o Pull Requests.
- No asumir que una diferencia corresponde a una personalización sin verificarla.

Antes de proponer cambios, presenta el inventario y las recomendaciones.
```

- [ ] `REPORTE_AUDITORIA_MIGAL.md` distingue hallazgos de supuestos y fue revisado.
- [ ] No se movió/eliminó código durante la auditoría.

## 3. Docker reproducible: plantilla de referencia

**Ruta propuesta:** `infra/odoo/compose.yaml` (desde esa ubicación, `../../custom_addons` apunta a la raíz del repositorio). Este Compose es una plantilla que el equipo **debe comprobar** contra su instalación real; no obliga a reinstalar si ya existe entorno estable.

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Configurar en entorno local}
    volumes:
      - db-data:/var/lib/postgresql/data

  web:
    image: odoo:19.0
    depends_on:
      - db
    ports:
      - "127.0.0.1:8069:8069"
    environment:
      HOST: db
      USER: odoo
      PASSWORD: ${POSTGRES_PASSWORD:?Configurar en entorno local}
    volumes:
      - odoo-data:/var/lib/odoo
      - ../../custom_addons:/mnt/extra-addons

volumes:
  db-data:
  odoo-data:
```

**Advertencias:** gestionar contraseña maestra de Odoo por configuración segura; verificar que `custom_addons/` exista; comprobar versión de imagen y entorno PostgreSQL; no exponer el puerto públicamente; una instalación con addons incompatibles puede fallar aunque `compose config` sea válido.

### `.env.example` de infraestructura

```dotenv
POSTGRES_PASSWORD=CAMBIAR_SOLO_EN_COPIA_LOCAL
```

La plantilla no debe usarse como credencial efectiva. Crear `.env` local con una contraseña fuerte y mantenerlo fuera del repositorio.

### Arranque de validación en PowerShell

```powershell
# Solo si el árbol Git está limpio y no se pisa una instalación existente
git status
git switch main
git pull --ff-only
git switch -c chore/pc3-entorno-reproducible

# Después de crear infra/odoo/.env local (fuera de Git)
docker compose --env-file infra/odoo/.env -f infra/odoo/compose.yaml config
docker compose --env-file infra/odoo/.env -f infra/odoo/compose.yaml up -d
docker compose --env-file infra/odoo/.env -f infra/odoo/compose.yaml ps
```

> `config` prueba estructura y variables, **no** confirma que Odoo funcione ni que los addons sean compatibles. Registrar `docker compose logs`, estado de base y acceso de usuario de prueba cuando se valide.

### Checklist de reproducibilidad del entorno

- [ ] Contenedores/volúmenes y accesos locales verificados sin tocar una instalación ajena.
- [ ] Módulos, campos, permisos y datos de prueba comprobados **en instancia**, no solo en manifiestos.
- [ ] `.env`, backups y filestore excluidos de Git.
- [ ] Otro integrante pudo levantar/consultar el entorno siguiendo instrucciones.

## 4. Datos: base inicial, fixtures y backups

| Artefacto | Dónde va | Recomendación |
|---|---|---|
| Código y configuración no secreta | GitHub | Revisar mediante PR |
| CSV/JSON con datos `[SIM]` | GitHub | Versionar para reproducibilidad |
| Backup completo base + filestore | Medio privado autorizado | Solo si es necesario; controlar acceso y retención |
| Credenciales/API keys | Variables locales o gestor autorizado | Nunca en Git, ZIP o video |
| Logs de ejecución con datos sensibles | Almacenamiento restringido | Anonimizar antes de compartir |

- [ ] Se decidió si los tests usarán dataset mock o base de prueba restaurada.
- [ ] No se compartieron datos personales reales sin autorización.
- [ ] Se identificó qué backup corresponde a qué versión/addons.
- [ ] Se documentaron pasos de restore en entorno **de prueba**, sin sobrescribir una DB valiosa.
- [ ] No se confundió «copia de DB» con «sincronización bidireccional».

## 5. `.gitignore`: ampliar sin sobrescribir

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/

# Secretos locales
.env
.env.*
!**/.env.example

# DB y copias privadas
backups-locales/
data_dir/
*.sql
*.dump

# Registros operativos
**/output/
audit_log.jsonl
escalations.jsonl

# Núcleo temporal descargado
odoo-original-referencia/
odoo_base_temp/
```

No ignorar `*.zip` indiscriminadamente: el ZIP es entregable oficial de PC3. Preservar las reglas existentes de `.gitignore` y revisar antes de aplicar.

## 6. GitHub y PR conforme a CONTRIBUTING

**Propuestas de ramas** (crear según trabajo real):

- `docs/pc3-coordinacion` — estos Markdown y vínculos de referencia.
- `feat/pc3-agente-comercial` — código del agente.
- `test/pc3-agente` — pruebas y fixtures.
- `chore/pc3-entorno-reproducible` — Docker/configuración no secreta.
- `docs/pc3-informe-presentacion` — enlaces y documentación final.

Cada PR debe describir **Objetivo / Cambios realizados / Validación y evidencia / Impactos y pendientes** y ser revisado por otra persona. Un PR sin revisión no implica aprobación.

### Publicar los cuatro Markdown de coordinación — PowerShell (paso inmediato)

**Alcance:** esta operación solamente agrega `producto/pc3/01` a `04` en una rama documental. No publica código del agente, configuración de Odoo ni secretos. Los comandos se ejecutarán **en el equipo local de Luis**, cuando tenga los archivos disponibles; este documento no acredita que ya se hayan ejecutado.

**1. Comprobar identidad de Git** (el correo debe corresponder a la cuenta GitHub `LuisRodrigo2024`):

```powershell
git config --global user.name
git config --global user.email
```

Si la identidad que realmente se usará para el commit no es correcta, definirla con el **correo verificado** en GitHub, preferentemente solo en este repositorio para no afectar otros proyectos. Estos comandos sin `--global` deben ejecutarse **dentro de la carpeta del repositorio** (después del paso 2); fuera de ella Git responde «not in a git directory»:

```powershell
git config user.name "Luis Rodrigo Núñez Príncipe"
git config user.email "CORREO_VERIFICADO_EN_GITHUB"
git config --show-origin --get user.email
```

No incluir el correo personal real en un archivo versionado; el valor anterior es únicamente un marcador.

**2. Acceder a un clon existente o clonar el repositorio:**

```powershell
# Solo si aún no existe un clon:
New-Item -ItemType Directory -Force "C:\MIGAL-WORKSPACE"
Set-Location "C:\MIGAL-WORKSPACE"
git clone https://github.com/brendaf08/ERP-Migal.git
Set-Location .\ERP-Migal

# Para un clon ya existente, simplemente entrar a su carpeta.
git status
```

Si hay modificaciones locales, **detenerse y resolverlas** antes de cambiar de rama. No asumir que un estado distinto de limpio es seguro.

```powershell
git switch main
git pull --ff-only
git switch -c docs/pc3-coordinacion
```

Si la rama ya existe, comprobar su estado y cambiar a ella; no intentar recrearla ni borrar trabajo anterior.

**3. Copiar solamente los cuatro Markdown actualizados** (adaptar la ruta local de origen):

Los archivos de origen pueden tener otros nombres; se copian renombrándolos para que coincidan con los enlaces internos:

```powershell
$src = "C:\Users\TU_USUARIO\Downloads"
New-Item -ItemType Directory -Force producto\pc3
Copy-Item "$src\PC3_01_Plan_Maestro.md"        producto\pc3\01-plan-maestro-pc3.md
Copy-Item "$src\PC3_02_Distribucion_Equipo.md" producto\pc3\02-distribucion-equipo-pc3.md
Copy-Item "$src\PC3_03_Agente_Comercial.md"    producto\pc3\03-agente-comercial-pc3.md
Copy-Item "$src\PC3_04_Odoo_GitHub.md"         producto\pc3\04-colaboracion-odoo-github-pc3.md
Get-ChildItem producto\pc3
```

Deben aparecer `01-plan-maestro-pc3.md`, `02-distribucion-equipo-pc3.md`, `03-agente-comercial-pc3.md` y `04-colaboracion-odoo-github-pc3.md`, sin versiones antiguas adicionales.

**4. Comprobar los archivos de destino citados en los enlaces**, desde la raíz de `ERP-Migal`:

```powershell
"README.md","CONTRIBUTING.md","arquitectura/contexto-empresa.md","fuentes/fuentes-negocio.md",
"procesos/p2p/flujo.md","procesos/o2c/flujo.md","procesos/inventario/flujo.md",
"procesos/catalogo-reglas.md","arquitectura/seguridad/modelo-autorizacion.md",
"arquitectura/integraciones/INT-01-CRM-ERP.md","arquitectura/modulos-y-dependencias.md",
"producto/registro-pendientes.md" | ForEach-Object { "{0}  {1}" -f (Test-Path $_), $_ }
```

Si aparece `False`, investigar y corregir la ruta en el Markdown antes del commit. Revisar también los enlaces entre `01`–`04`.

**5. Preparar y revisar el commit:**

```powershell
git add producto/pc3/
git status
git diff --cached --name-only
git diff --cached --check
```

Los únicos archivos preparados deben ser los cuatro `.md`. **No ignorar automáticamente las advertencias de `--check`**: revisar y resolver espacios finales antes del commit, conservando saltos de párrafo válidos en Markdown.

```powershell
git commit -m "docs(pc3): incorporar plan maestro y distribucion del equipo"
git push -u origin docs/pc3-coordinacion
```

Si se obtiene `403` o `Permission denied`, pedir a Brenda que habilite acceso de colaboración o preparar un fork. No modificar permisos ni remotos a ciegas.

**6. Abrir Pull Request:** base `main`, rama `docs/pc3-coordinacion`. Utilizar esta descripción **solo después de comprobar las afirmaciones de validación**:

```markdown
## Objetivo
Incorporar los documentos de coordinación de la PC3 para que el equipo tenga una referencia común de fases, responsables, agente comercial y colaboración en GitHub/Odoo.

## Cambios realizados
- `producto/pc3/01-plan-maestro-pc3.md`: fases, camino crítico y entregables oficiales.
- `producto/pc3/02-distribucion-equipo-pc3.md`: actividades A1–A11 (sin cambios) y propuesta de DEC-01 a DEC-05.
- `producto/pc3/03-agente-comercial-pc3.md`: especificación, pruebas CP3-AI-01/02/03 y demo.
- `producto/pc3/04-colaboracion-odoo-github-pc3.md`: auditoría Odoo, entorno y flujo de PR.

## Validación y evidencia
- Enlaces relativos comprobados contra `main`.
- Solo se agregan archivos en `producto/pc3/`; no se modifica contenido existente.

## Impactos y pendientes
- DEC-01 a DEC-05 están marcados como **propuestos**; se actualizarán cuando el equipo confirme.
- No incluye código, configuración de Odoo ni datos.
```

Solicitar revisión a Brenda o Gabriel. **No fusionar el PR sin revisión**.

- [ ] Identidad y correo Git verificados sin compartir credenciales.
- [ ] Rama `docs/pc3-coordinacion` creada desde `main` actualizado y limpio.
- [ ] Solo cuatro archivos en `producto/pc3/`, con enlaces y `git diff --cached --check` revisados.
- [ ] Push efectuado, PR abierto, revisor solicitado; el PR sigue sin fusionar hasta recibir revisión.

### Checklist por PR

- [ ] Rama con objetivo específico y cambios acotados; no modificar `main` directamente.
- [ ] Sin secretos, respaldos ni addons/core no autorizados.
- [ ] Formato, enlaces, fuentes y pruebas comprobados o limitación documentada.
- [ ] PR con **Objetivo / Cambios / Validación y evidencia / Impactos y pendientes**, revisado por otro integrante.

## 7. Tareas posteriores a PC3 (P2, no bloquear entrega)

- [ ] Evaluar API JSON-2 en reemplazo de XML-RPC tras revisar compatibilidad y modalidad de despliegue.
- [ ] Evaluar addon nativo `migal_ai_assistant` y uso de ORM interno solo mediante nueva decisión de arquitectura.
- [ ] Automatizar instalación de fixtures y validaciones de permisos.
- [ ] Incorporar control de versiones de esquema de datos, CI y pruebas de regresión.
- [ ] Definir estrategia de backups y de actualizaciones de Odoo a largo plazo.

**Cierre de esta fase para PC3:** código y documentación conservados, entorno entendible, acceso seguro, pruebas en modo declarado; no exige desplegar producción ni migrar el agente a addon.
