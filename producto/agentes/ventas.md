# Agente de ventas

- **Responsable:** Brenda Mirano · **Revisa el PR:** Alejandro · **Aprobación final:** Luis
- **Módulo:** `custom_addons/migal_agente_ventas` · **Modelo:** `migal.agente.ventas` · **Rama:** `feat/agente-ventas`
- **Roles que atiende:** VEN (Ventas), GER (Gerencia)
- **Herramienta de código sugerida:** Codex
- **Estado:** TO-BE en construcción. Lo marcado «ya funciona» está implementado y probado en la base.

Lee primero [AGENTS.md](../../AGENTS.md) y la [guía del equipo](README.md). Los contratos completos están en [INT-02](../../arquitectura/integraciones/INT-02-contratos-agentes.md).

## 1. Ya funciona (punto de partida)

| Herramienta | Qué hace | Roles |
|---|---|---|
| `cotizaciones_por_vencer` | Cotizaciones abiertas que vencen en los próximos días. | VEN, GER |
| (núcleo) buscar/consultar cotización, WhatsApp, QR | Ya existían; pertenecen a ventas y siguen en `migal_agente`. | VEN, GER |

## 2. Por construir (en este orden)

1. `consultar_cotizaciones_perdidas` (la consume marketing; hoy responde el simulador). Fuente: `sale.order` canceladas/vencidas y `crm.lead` perdidas con `lost_reason_id`.
2. Seguimiento de oportunidades CRM sin próxima actividad (RN-001).
3. Al confirmar venta (EV-018 ya se emite): resumen para el vendedor con cobertura (`_consultar('evaluar_cobertura_preliminar', ...)`) y crédito (`_consultar('consultar_situacion_credito', ...)`).
4. Escuchar EV-027: avisar qué cotizaciones abiertas esperaban los productos recibidos.
5. Escuchar EV-057: mostrar la promoción vigente a los vendedores.

Solo lectura, borradores o propuestas. El agente **no** confirma, aprueba, paga, descuenta ni envía en masa (ver [seguridad de agentes](../../arquitectura/seguridad/seguridad-agentes.md)).

## 3. Contratos con otros agentes

| Tipo | Contrato | Con | Estado |
|---|---|---|---|
| Ofrece (consulta) | `consultar_cotizaciones_perdidas` | marketing | Por implementar (hoy: simulador) |
| Consume (consulta) | `evaluar_cobertura_preliminar` | suministro | Llamar con `self._consultar(...)` |
| Consume (consulta) | `consultar_situacion_credito` | cobranzas | Llamar con `self._consultar(...)` |
| Emite (evento) | `EV-018` Orden de venta confirmada | suministro, cobranzas | Se emite |
| Escucha (evento) | `EV-027` Recepción validada | suministro | Método creado, lógica por hacer |
| Escucha (evento) | `EV-057` Campaña comercial aprobada | marketing | Método creado, lógica por hacer |

## 4. Datos de prueba

12 oportunidades y 3 leads «[PRUEBA]» con etiquetas, fuentes y motivos de pérdida; 5 clientes segmentados con 8 ventas facturadas. Se cargan con `infra/odoo/cargar_datos_demo.ps1` (script `herramientas/datos_prueba_agentes.py`). Todo lo que crees para probar lleva el prefijo «[PRUEBA]».

## 5. Frases de prueba en el chat

- «cotizaciones por vencer»
- «¿qué cotizaciones vencen pronto?»

## 6. Terminado significa

- Cada herramienta nueva declarada en `_herramientas()` con descripción, `input_schema` cerrado, roles y reglas RN.
- Pruebas en `tests/test_ventas.py` que pasan: herramienta, permiso por rol y frase de chat.
- Las consultas que ofreces devuelven las mismas claves que `ejemplo_salida` del catálogo.
- Toda la batería pasa (`-u migal_agente_ventas --test-tags /migal_agente,/migal_agente_ventas`).
- PR a `main` con las cuatro secciones de CONTRIBUTING, revisado por Alejandro y aprobado por Luis.
