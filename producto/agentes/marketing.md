# Agente de marketing

- **Responsable:** Brenda Mirano · **Revisa el PR:** Alejandro · **Aprobación final:** Luis
- **Módulo:** `custom_addons/migal_agente_marketing` · **Modelo:** `migal.agente.marketing` · **Rama:** `feat/agente-marketing`
- **Roles que atiende:** GER (Gerencia), VEN (Ventas)
- **Herramienta de código sugerida:** Codex
- **Estado:** TO-BE en construcción. Lo marcado «ya funciona» está implementado y probado en la base.

Lee primero [AGENTS.md](../../AGENTS.md) y la [guía del equipo](README.md). Los contratos completos están en [INT-02](../../arquitectura/integraciones/INT-02-contratos-agentes.md).

## 1. Ya funciona (punto de partida)

| Herramienta | Qué hace | Roles |
|---|---|---|
| `clientes_inactivos` | Clientes sin compras en N días con bandera de exclusión por morosidad (consulta a cobranzas). | GER, VEN |
| `productos_para_promocion` | Productos de baja rotación (consulta a suministro; hoy simulada). | GER, VEN |

## 2. Por construir (en este orden)

1. Segmentar clientes por monto, frecuencia y última compra (RFM simple) con `sale.order` confirmadas.
2. Analizar oportunidades por fuente (`utm.source`) y motivos de pérdida (consume `consultar_cotizaciones_perdidas`).
3. Redactar borrador de campaña (texto y lista) y dejarlo PARA APROBACIÓN de GER. Nunca enviar (RN-022).
4. Emitir EV-057 solo cuando GER apruebe la campaña.

Solo lectura, borradores o propuestas. El agente **no** confirma, aprueba, paga, descuenta ni envía en masa (ver [seguridad de agentes](../../arquitectura/seguridad/seguridad-agentes.md)).

## 3. Contratos con otros agentes

| Tipo | Contrato | Con | Estado |
|---|---|---|---|
| Consume (consulta) | `consultar_baja_rotacion` | suministro | Llamar con `self._consultar(...)` |
| Consume (consulta) | `consultar_situacion_credito` | cobranzas | Solo recibe: cliente, excluir |
| Consume (consulta) | `consultar_cotizaciones_perdidas` | ventas | Llamar con `self._consultar(...)` |
| Emite (evento) | `EV-057` Campaña comercial aprobada | ventas | Por implementar |

## 4. Datos de prueba

Los mismos clientes y oportunidades «[PRUEBA]» de ventas, con fuentes UTM y motivos de pérdida. Se cargan con `infra/odoo/cargar_datos_demo.ps1` (script `herramientas/datos_prueba_agentes.py`). Todo lo que crees para probar lleva el prefijo «[PRUEBA]».

## 5. Frases de prueba en el chat

- «clientes inactivos»
- «¿qué productos promocionar?»

## 6. Terminado significa

- Cada herramienta nueva declarada en `_herramientas()` con descripción, `input_schema` cerrado, roles y reglas RN.
- Pruebas en `tests/test_marketing.py` que pasan: herramienta, permiso por rol y frase de chat.
- Las consultas que ofreces devuelven las mismas claves que `ejemplo_salida` del catálogo.
- Toda la batería pasa (`-u migal_agente_marketing --test-tags /migal_agente,/migal_agente_marketing`).
- PR a `main` con las cuatro secciones de CONTRIBUTING, revisado por Alejandro y aprobado por Luis.
