# Agente de cuentas por cobrar

- **Responsable:** Gabriel Martínez · **Revisa el PR:** Diego · **Aprobación final:** Luis
- **Módulo:** `custom_addons/migal_agente_cobranzas` · **Modelo:** `migal.agente.cobranzas` · **Rama:** `feat/agente-cobranzas`
- **Roles que atiende:** FCO (Facturación, contabilidad y cobros), GER (Gerencia)
- **Herramienta de código sugerida:** Google AI Pro (Gemini CLI / Jules)
- **Estado:** TO-BE en construcción. Lo marcado «ya funciona» está implementado y probado en la base.

Lee primero [AGENTS.md](../../AGENTS.md) y la [guía del equipo](README.md). Los contratos completos están en [INT-02](../../arquitectura/integraciones/INT-02-contratos-agentes.md).

## 1. Ya funciona (punto de partida)

| Herramienta | Qué hace | Roles |
|---|---|---|
| `consultar_situacion_credito` | Deuda total y vencida frente al límite de crédito (la consumen ventas y marketing). | VEN, FCO, GER |
| `resumen_cartera` | Por cobrar y vencido por tramos (la consume contabilidad). | FCO, GER |
| (núcleo) estado de cuenta y compartirlo | Ya existían; pertenecen a cobranzas y siguen en `migal_agente`. | FCO, GER |

## 2. Por construir (en este orden)

1. Lista priorizada de cobranza del día (monto × días vencidos).
2. Borrador de recordatorio de pago por cliente (WhatsApp con revisión humana; nunca envío masivo).
3. Escuchar EV-018: alertar si la venta supera el límite de crédito (RN-004).
4. Escuchar EV-058: registrar la observación contable.

Solo lectura, borradores o propuestas. El agente **no** confirma, aprueba, paga, descuenta ni envía en masa (ver [seguridad de agentes](../../arquitectura/seguridad/seguridad-agentes.md)).

## 3. Contratos con otros agentes

| Tipo | Contrato | Con | Estado |
|---|---|---|---|
| Ofrece (consulta) | `consultar_situacion_credito` | ventas, marketing | Implementada |
| Ofrece (consulta) | `resumen_cartera` | contabilidad | Implementada |
| Emite (evento) | `EV-038` Comprobante de venta emitido | contabilidad | Se emite |
| Emite (evento) | `EV-043` Pago aplicado a deuda | contabilidad | Se emite |
| Escucha (evento) | `EV-018` Orden de venta confirmada | ventas | Método creado, lógica por hacer |
| Escucha (evento) | `EV-058` Inconsistencia contable detectada | contabilidad | Método creado, lógica por hacer |

## 4. Datos de prueba

5 clientes «[PRUEBA]» con facturas en todos los tramos de antigüedad (por vencer, 0-30, 31-60, 61-90, +90). Se cargan con `infra/odoo/cargar_datos_demo.ps1` (script `herramientas/datos_prueba_agentes.py`). Todo lo que crees para probar lleva el prefijo «[PRUEBA]».

## 5. Frases de prueba en el chat

- «cartera»
- «situación de crédito de [PRUEBA] Constructora»

## 6. Terminado significa

- Cada herramienta nueva declarada en `_herramientas()` con descripción, `input_schema` cerrado, roles y reglas RN.
- Pruebas en `tests/test_cobranzas.py` que pasan: herramienta, permiso por rol y frase de chat.
- Las consultas que ofreces devuelven las mismas claves que `ejemplo_salida` del catálogo.
- Toda la batería pasa (`-u migal_agente_cobranzas --test-tags /migal_agente,/migal_agente_cobranzas`).
- PR a `main` con las cuatro secciones de CONTRIBUTING, revisado por Diego y aprobado por Luis.
