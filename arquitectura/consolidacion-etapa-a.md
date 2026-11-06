# Consolidación selectiva — Etapa A

## Procedencia

Esta rama local consolida contenido por archivo desde las siguientes fuentes:

| Fuente | Autor de la rama/PR | SHA fijado |
|---|---|---|
| PR #3, `docs/actualizacion-arquitectura` | `dieg0-29` | `9be31b86beb6f77926e1205643f0c50c8b2e8ef2` |
| PR #4, `docs/actualizacion-arquitectura-y-procesos` | `brendaf08` | `fa25da0ea1536cfdbf05a3b787646bf2f4e72caf` |
| Base, `main` | `brendaf08` | `d0dd4da4fcd9f188e1442135e0ebf97196d2d7ef` |

La rama conserva contenido seleccionado y referencia su procedencia; no incorpora los commits originales de PR #3/#4 como historia Git.

## Política de conservación

Los 54 placeholders `B-` originales de `main` se conservan sin cambios. Se excluyen de PR #3 las eliminaciones de:

- `arquitectura/B-riesgos-y-controles.md`
- `arquitectura/integraciones/B-INT-01-CRM-ERP.md`
- `arquitectura/integraciones/B-plantilla-integracion.md`
- `arquitectura/versiones/B-README.md`
- `arquitectura/versiones/B-VER-01-erp.md`
- `arquitectura/versiones/B-VER-02-crm.md`
- `arquitectura/versiones/B-VER-03-crm-erp.md`
- `arquitectura/vistas/B-consolidado-diagramas.md`

Se excluyen de PR #4 los renombres cuyo origen son placeholders:

- `arquitectura/B-comparacion-erp.md` → `arquitectura/integraciones/B-INT-02-interacciones-internas-odoo.md`
- `arquitectura/B-riesgos-y-controles.md` → `arquitectura/integraciones/B-INT-03-odoo-keyfacil.md`
- `arquitectura/integraciones/B-plantilla-integracion.md` → `arquitectura/integraciones/B-INT-04-whatsapp-odoo.md`

Los tres destinos anteriores se excluyen igualmente. Estas exclusiones obedecen a la instrucción de preservar los placeholders durante Etapa A; su contenido y migración pertenecen a Etapa B.

## Decisiones históricas y conflictos de identificadores

- Se conservan los cuerpos originales de ADR-001, ADR-003 y ADR-004. Las notas posteriores se separan y enlazan sin sustituir su decisión.
- ADR-005 documenta el cambio de versión. El documento de adopción de CRM procedente de PR #4 pasa a ADR-006; su estado «Aceptado» procede de la fuente y su renumeración no implica nueva aprobación.
- PEN-011 y PEN-012 mantienen su significado original. Los asuntos CRM–ERP y complementos OCA de PR #4 pasan a PEN-016 y PEN-017, respectivamente; PEN-013 a PEN-015 se conservan como nuevos asuntos.
- Los 26 riesgos de PR #4 mantienen sus códigos. El riesgo de propagación del `.iuml`, identificado como RSK-009 en PR #3, se registra como RSK-027; RSK-009 de PR #4 sigue siendo ampliación no controlada del alcance.
- El catálogo de eventos de PR #4 se conserva sin cambios. INT-01 conserva sus eventos originales y documenta candidatos y equivalencias pendientes; EV-04 continúa sin equivalente exacto declarado.
- La plantilla concisa de PR #4 es la base. Se recuperan de PR #3 controles para fronteras, eventos, estados, responsables y trazabilidad.

Las modificaciones extensas de alcance y de formato de PEN-001…015 propuestas por PR #4 no sustituyen el registro histórico de `main`. Se incorporan únicamente los asuntos nuevos compatibles y con identificadores libres.

## Contenido de PR #4 no aplicado como reemplazo

- **ADR-001:** no se importa la reescritura de contexto, criterios, comparación dentro del ADR ni justificación. La comparación más extensa se conserva en `arquitectura/comparacion-erp.md`; ADR-001 mantiene su decisión original y añade solo una referencia complementaria.
- **ADR-003:** no se sustituye la opción D por la opción B ni se reemplazan alternativas, responsable o justificación original. La información posterior de versión 19, estado reportado de los módulos OCA, pendientes de validación y KeyFacil se conserva en una nota adicional atribuida a PR #4.
- **ADR-004:** se excluye la eliminación del ADR histórico de fronteras CRM–ERP. El nuevo ADR de adopción CRM se conserva como ADR-006, con el estado aceptado heredado y la nota de que renumerar no es una nueva aprobación.
- **Registro de pendientes:** no se importa la nueva tabla reestructurada ni los reemplazos de PEN-011/012. Se agregan PEN-013…017 en el formato histórico; PEN-016/017 reciben los dos asuntos renumerados y se conserva la metadata de responsables registrada en la fuente.
- **Alcance:** se incorpora el documento revisado de PR #4; la decisión sobre plataforma/versión se mantiene en ADRs y la inclusión de funciones no se presenta como implementación.
- **Placeholders:** se excluyen todas las bajas, movimientos y altas de `B-` enumeradas arriba, aunque aparezcan en ambos PR.

La conservación se verifica mediante comparaciones contra los blobs de `main` y de los PR fijados en la sección de procedencia.
