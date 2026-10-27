
# Guía de contribución — Ferre & Inversiones MIGAL

Este documento establece las convenciones de colaboración y mantenimiento del repositorio.

Su finalidad es garantizar que los cambios sean **identificables, revisables y trazables**, manteniendo la coherencia documental sin introducir procedimientos innecesarios.

## 1. Flujo de colaboración

No realizar modificaciones directamente sobre `main`.

El flujo establecido es:

1. Actualizar la rama local `main`.
2. Crear una rama para un objetivo específico.
3. Realizar los cambios y commits correspondientes.
4. Abrir un Pull Request hacia `main`.
5. Revisar y validar las modificaciones.
6. Fusionar el PR y eliminar la rama de trabajo.

Cada rama debe representar **un objetivo principal**. No combinar modificaciones funcionales sin relación.

Los cambios relevantes requieren al menos una revisión de otro integrante antes de fusionarse.

La creación de un Pull Request no constituye, por sí misma, la aprobación del cambio.

## 2. Nomenclatura de ramas, commits y Pull Requests

### Ramas

Formato:

`tipo/descripcion-corta`

| Tipo | Uso |
|---|---|
| `docs/` | Documentación, procesos y modelos. |
| `feat/` | Nuevas funcionalidades implementadas. |
| `fix/` | Corrección de errores. |
| `refactor/` | Reorganización sin cambiar el comportamiento funcional. |
| `test/` | Casos y automatización de pruebas. |
| `data/` | Datos y catálogos. |
| `chore/` | Mantenimiento y configuración. |

Ejemplos:

- `docs/actualizar-flujo-o2c`
- `refactor/reorganizar-estructura-repositorio`
- `data/actualizar-catalogo-productos`
- `test/validar-pedido-condicionado`

Los nombres deben utilizar minúsculas, sin tildes ni espacios, con palabras separadas mediante guiones. Deben describir el trabajo realizado, no identificar a su autor.

### Commits

Formato:

`tipo(alcance): descripcion`

Ejemplos:

- `docs(o2c): actualizar validacion de pedidos`
- `refactor(repo): reorganizar estructura documental`
- `docs(crm): alinear decisiones comerciales`
- `test(o2c): agregar caso de pedido condicionado`

Cada commit debe representar una unidad lógica de cambio y puede comprender varios archivos relacionados.

Evitar mensajes genéricos como `avance`, `cambios` o `final`.

### Pull Requests

El título del PR debe seguir la misma nomenclatura de commits.

Su descripción contendrá cuatro apartados:

**Objetivo**
- Qué se modifica y por qué.

**Cambios realizados**
- Documentos, modelos o decisiones afectados.

**Validación y evidencia**
- Qué se comprobó y qué evidencia respalda el cambio.

**Impactos y pendientes**
- Consecuencias sobre otros artefactos, limitaciones y tareas pendientes.

Cuando un apartado no corresponda, indicar "No aplica". No declarar pruebas o validaciones que no se hayan realizado.

La plantilla se mantendrá en `.github/pull_request_template.md`, para que GitHub la cargue automáticamente al abrir un PR, una vez incorporada a la rama predeterminada.

La carpeta `.github/` se reserva para la configuración técnica de GitHub y no constituye una carpeta documental adicional del proyecto.

### Política de integración

- **Squash and Merge:** opción preferente para cambios compuestos por varios commits relacionados. El commit final debe utilizar el título del PR y respetar Conventional Commits.
- **Rebase and Merge:** permitido cuando los commits tienen valor independiente y todos respetan la nomenclatura.
- No utilizar mensajes genéricos en los commits integrados a `main`.

## 3. Organización del repositorio y diagramas

La documentación del proyecto se organiza en seis carpetas principales:

- `arquitectura/`
- `procesos/`
- `datos/`
- `producto/`
- `pruebas/`
- `fuentes/`

No añadir otras carpetas documentales de primer nivel sin una decisión expresa y justificada del equipo.

Se exceptúa `.github/`, destinada exclusivamente a la configuración de la plataforma.

### Profundidad de carpetas

Como regla general, se permiten **máximo tres niveles de carpetas desde la raíz hasta el archivo**.

Ejemplo:

`arquitectura/vistas/fuentes/c4-contexto.puml`

Las carpetas de diagramas `fuentes/` y `render/` podrán superar este límite cuando sea necesario conservar una organización comprensible de los archivos editables y generados.

Evitar subcarpetas que contengan un único archivo cuando este pueda identificarse directamente mediante su nombre.

### Nomenclatura de archivos

Utilizar nombres descriptivos, sin espacios ni tildes, con palabras separadas mediante guiones.

**Regla general:** nombres en minúsculas.

**Excepción:** los prefijos oficiales de identificación de artefactos, como `ADR`, `INT`, `CP` y `VER`, mantienen sus mayúsculas. El resto del nombre utiliza minúsculas.

Ejemplos:

- `ADR-001-seleccion-erp.md`
- `CP-01-caso-normal.md`
- `VER-01-erp-base.md`

Los nombres históricos consolidados, como `INT-01-CRM-ERP.md`, se conservarán hasta que una migración aprobada actualice tanto el archivo como todas sus referencias.

Esta excepción histórica no establece una convención para documentos nuevos.

### Diagramas

Los diagramas deben conservar el archivo editable y su representación exportada en directorios separados:

- `.../fuentes/`: archivos editables de los diagramas.
- `.../render/`: imágenes o representaciones generadas.

Ejemplo:

- `arquitectura/vistas/fuentes/c4-contexto.puml`
- `arquitectura/vistas/render/c4-contexto.png`

Los archivos relacionados deben mantener nombres equivalentes. Cuando se modifique una fuente, se debe actualizar su render correspondiente.

**Distinción obligatoria:**

- `/fuentes/`, ubicado en la raíz, contiene bibliografía, licencias, atribuciones y declaraciones de uso de IA.
- Las subcarpetas locales `.../fuentes/` contienen los archivos editables de diagramas del área correspondiente.

Aunque comparten nombre, cumplen funciones diferentes.

### Cambios estructurales

Las reorganizaciones importantes deben realizarse en una rama independiente, sin mezclarlas con modificaciones funcionales no relacionadas.

Antes del merge, se debe:

1. Verificar que los archivos estén preservados o consolidados justificadamente.
2. Actualizar enlaces relativos y referencias internas.
3. Comprobar la correspondencia entre fuentes y renders.
4. Identificar archivos duplicados, rutas antiguas o referencias incorrectas.
5. Revisar el impacto sobre la documentación relacionada.

## 4. Calidad documental y revisión

Los documentos deben mantener un propósito definido, utilizar información verificable y conservar coherencia con los demás artefactos.

Cuando corresponda, distinguir entre:

| Clasificación | Significado |
|---|---|
| Evidencia o hecho verificado | Información sustentada por una fuente o comprobación. |
| Interpretación | Conclusión razonada del equipo. |
| Supuesto | Condición adoptada sin confirmación suficiente. |
| Pendiente | Información o validación todavía necesaria. |
| TO-BE | Funcionamiento propuesto, no necesariamente implementado. |

No presentar como implementadas funcionalidades que únicamente están diseñadas.

Cada tema debe contar con un documento responsable que actúe como referencia principal, evitando duplicar definiciones en distintos archivos.

Antes de aprobar un PR, revisar según corresponda:

- coherencia con el alcance vigente;
- consistencia entre artefactos relacionados;
- integridad de enlaces, rutas y diagramas;
- correspondencia de reglas, eventos e identificadores;
- respaldo de las afirmaciones y decisiones;
- ausencia de información sensible;
- límites y pendientes correctamente declarados.

Si una modificación afecta otros documentos, estos deben actualizarse en el mismo cambio o registrarse explícitamente como pendientes.

## 5. Datos, privacidad y uso de IA

No incorporar al repositorio:

- contraseñas, tokens, claves o credenciales;
- datos personales sensibles;
- información privada de clientes o proveedores sin autorización;
- conversaciones confidenciales;
- información comercial no autorizada.

Los datos utilizados para pruebas deben ser sintéticos, anonimizados o contar con autorización expresa.

Se debe mantener `.gitignore` para excluir archivos temporales, configuraciones locales y posibles secretos.

Antes de realizar commits, es obligatorio revisar los archivos preparados para confirmar que no contienen información sensible. Se recomienda utilizar herramientas de detección como `git-secrets` o `detect-secrets`, cuando estén disponibles.

`.gitignore` no sustituye la revisión ni elimina secretos previamente incorporados al historial.

Las fuentes externas deben poder identificarse y contrastarse.

El uso de herramientas de IA debe declararse conforme a [fuentes/uso-ia.md](fuentes/uso-ia.md), indicando su propósito y las limitaciones correspondientes.

La revisión y aprobación del contenido generado con apoyo de IA son responsabilidad del equipo.

## 6. Identificadores y trazabilidad

Cada identificador debe conservar su significado y contar con un documento responsable.

Antes de crear un código nuevo, verificar que no esté asignado y que corresponda al catálogo adecuado.

| Prefijo | Significado | Documento responsable |
|---|---|---|
| `RN`, `CT`, `EXC` | Reglas, controles y excepciones | `procesos/catalogo-reglas.md` |
| `INT`, `EV`, `F` | Integraciones, eventos y fronteras | `arquitectura/integraciones/INT-01-CRM-ERP.md` |
| `ADR` | Decisiones arquitectónicas | `arquitectura/decisiones/` |
| `VER` | Versiones de arquitectura | `arquitectura/versiones/` |
| `RSK` | Riesgos | `arquitectura/riesgos-y-controles.md` |
| `R`, `SOD` | Responsabilidades y segregación de funciones | `arquitectura/seguridad/modelo-autorizacion.md` |
| `DQ` | Calidad de datos | `datos/reglas-calidad.md` |
| `TR` | Trazabilidad y auditoría | `datos/trazabilidad/plan-trazabilidad-auditoria.md` |
| `CP` | Casos de prueba | `pruebas/` |
| `O2C-K`, `P2P-K` | Indicadores de procesos | `procesos/o2c/indicadores.md` y `procesos/p2p/indicadores.md` |

Los demás identificadores existentes deben conservarse en sus documentos especializados.

No reutilizar códigos retirados para representar conceptos diferentes.

Cuando se modifique, retire o renombre un identificador, se deben actualizar las referencias correspondientes y preservar su trazabilidad.

## 7. Changelog y cierre del Pull Request

Actualizar `CHANGELOG.md` cuando se produzcan modificaciones relevantes en:

- estructura del repositorio;
- alcance y arquitectura;
- reglas, controles o procesos;
- datos, producto o pruebas;
- decisiones o evidencias importantes.

No registrar cada commit ni correcciones menores de redacción o formato.

Una modificación lógica debe resumirse en una sola entrada, aunque comprenda varios commits.

Antes de fusionar un PR, comprobar que:

1. El objetivo del cambio esté cumplido.
2. La revisión se haya realizado y sus observaciones estén atendidas.
3. Los enlaces, rutas e identificadores sean consistentes.
4. Las evidencias, limitaciones y pendientes estén identificados.
5. No existan archivos accidentales o información sensible.
6. Se haya actualizado el CHANGELOG, cuando corresponda.

Una vez integrado el PR, eliminar la rama de trabajo.
