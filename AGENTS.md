# AGENTS.md — instrucciones para asistentes de código

Este archivo lo leen directamente Codex, OpenCode, Cursor y Jules. `CLAUDE.md` (Claude Code) y `GEMINI.md` (Gemini CLI) lo importan con `@AGENTS.md`, y `.github/copilot-instructions.md` (GitHub Copilot) resume sus reglas y remite aquí. Si eres una persona del equipo, empieza por la [guía del equipo](producto/agentes/README.md).

## Proyecto

ERP de Ferre & Inversiones MIGAL sobre **Odoo 19 Community** en Docker. Los módulos propios están en `custom_addons/`. El sistema multiagente tiene un orquestador (`migal_agente`) y seis agentes especialistas, cada uno en su propio módulo:

| Código | Módulo | Responsable |
|---|---|---|
| ventas | `migal_agente_ventas` | Brenda |
| marketing | `migal_agente_marketing` | Brenda |
| suministro | `migal_agente_suministro` | Alejandro |
| cobranzas | `migal_agente_cobranzas` | Gabriel |
| pagos | `migal_agente_pagos` | Diego |
| contabilidad | `migal_agente_contabilidad` | César |

Arquitectura: [ADR-007](arquitectura/decisiones/ADR-007-arquitectura-multiagente.md). Contratos entre agentes: [INT-02](arquitectura/integraciones/INT-02-contratos-agentes.md) y `custom_addons/migal_agente/agent/catalogo.py`. Seguridad: [seguridad de agentes](arquitectura/seguridad/seguridad-agentes.md).

## Reglas obligatorias

1. **Trabaja solo en el módulo de tu agente** (`custom_addons/migal_agente_<codigo>/`). No edites `migal_agente` (núcleo), el catálogo ni el módulo de otro integrante. Si necesitas un cambio ahí, descríbelo en el PR y lo hace Luis.
2. **Una consulta a otro agente siempre pasa por `self._consultar("<contrato>", args)`.** Nunca importes ni llames directamente el modelo de otro agente. Si el contrato no existe en el catálogo, no lo inventes: pídelo.
3. **Un evento solo lo emite su dueño** con `self._emitir("EV-xxx", datos)`. Escuchar es declarar `_eventos_escuchados()` y el método.
4. **Los agentes no ejecutan decisiones de negocio:** no confirman órdenes, no aprueban compras, no registran ni ejecutan pagos, no otorgan crédito ni descuentos, no ajustan inventario, no envían mensajes masivos. Leen, calculan, proponen y preparan borradores.
5. **Nunca subas secretos ni datos reales:** nada de `.env`, claves de API (Gemini va en Ajustes de Odoo), respaldos `.zip`, filestore ni fotos de notas reales. Los datos de prueba llevan el prefijo «[PRUEBA]».
6. **No cambies la firma de un contrato** (nombre, entradas obligatorias, claves de salida). Agregar un campo opcional sí se puede.
7. **No toques** `infra/`, `.github/`, otros módulos de `custom_addons/` ni la documentación general salvo la ficha de tu agente.

## Cómo se escribe un agente

```python
class AgentePagos(models.AbstractModel):
    _name = "migal.agente.pagos"
    _inherit = "migal.agente.especialista"
    _agente_codigo = "pagos"
    _agente_nombre = "Cuentas por pagar"

    def _herramientas(self):            # contratos de herramientas: el orquestador las registra solo
        return {"facturas_por_vencer": {
            "description": "...", "input_schema": {"type": "object", "properties": {...},
                                                   "required": [], "additionalProperties": False},
            "roles": ["FCO", "GER"], "escritura": "Ninguna (solo bitácora).", "reglas": ["RN-014"],
            "metodo": "facturas_por_vencer"}}

    def _eventos_escuchados(self):      # {"EV-027": "_al_validarse_recepcion"}
    def _reconocer(self, texto):        # frase normalizada (minúsculas, sin tildes) -> (herramienta, args) o None
    def _acciones_widget(self, record): # botones del asistente flotante para un registro
    def _argumentos_widget(self, accion, record, params):

    def facturas_por_vencer(self, dias=7, proveedor=None):
        ...
        return self._resultado(True, "ok", "Título", "Mensaje corto.", reglas=["RN-014"], avisos=[...],
                               datos={"...": ..., "tabla": {"columnas": [...], "filas": [[...]]}})
```

- Toda herramienta devuelve `self._resultado(ok, estado, titulo, mensaje, ...)`. `datos["tabla"]` se dibuja como tabla en el chat.
- `estado` habitual: `ok`, `alerta`, `error`, `ambiguo` (con `datos["candidatos_ids"]`), `sin_permiso` (lo pone el orquestador).
- Roles válidos: `VEN`, `ALM`, `CMP`, `FCO`, `GER`, `SIS`.
- Nombres: herramientas y métodos en español con `snake_case`; código de evento `EV-xxx`; reglas `RN-xxx`.
- Usa el ORM con el usuario actual (sin `sudo()`), para que Odoo aplique sus permisos.
- Fechas con `self._hoy()`; montos con dos decimales.

## Pruebas

Cada herramienta nueva necesita pruebas en `custom_addons/migal_agente_<codigo>/tests/` (herramienta, permiso por rol y frase de chat). Corre las de tu módulo y las del núcleo:

```bash
cd infra/odoo
docker compose run --rm --no-deps odoo odoo -d ferre_inversiones_migal -u migal_agente_<codigo> \
  --test-enable --test-tags /migal_agente,/migal_agente_<codigo> --stop-after-init --http-port=8070
```

En Git Bash de Windows antepón `MSYS_NO_PATHCONV=1` para que `/migal_agente` no se convierta en una ruta. Las pruebas no deben llamar a Gemini: desactiva `migal_agente.llm_enabled` en `setUpClass`.

## Commits y PR

- Rama `feat/agente-<codigo>` creada desde `main`.
- Commits `tipo(agente-<codigo>): descripcion` (Conventional Commits, en español, sin tildes en el tipo).
- PR a `main` con las secciones Objetivo, Cambios realizados, Validación y evidencia, Impactos y pendientes. No declares pruebas que no corriste.
