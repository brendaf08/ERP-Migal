# Agente de cuentas por pagar

- **Responsable:** Diego Pinedo · **Revisa el PR:** Gabriel · **Aprobación final:** Luis
- **Módulo:** `custom_addons/migal_agente_pagos` · **Modelo:** `migal.agente.pagos` · **Rama:** `feat/agente-pagos`
- **Roles que atiende:** FCO (Facturación, contabilidad y cobros), GER (Gerencia)
- **Herramienta de código sugerida:** Claude Code
- **Estado:** TO-BE en construcción. Lo marcado «ya funciona» está implementado y probado en la base.

Lee primero [AGENTS.md](../../AGENTS.md) y la [guía del equipo](README.md). Los contratos completos están en [INT-02](../../arquitectura/integraciones/INT-02-contratos-agentes.md).

## 1. Ya funciona (punto de partida)

| Herramienta | Qué hace | Roles |
|---|---|---|
| `facturas_por_vencer` | Facturas de proveedor sin pagar que vencen pronto o ya vencieron. | FCO, GER |
| `resumen_obligaciones` | Por pagar, vencido y próximos 7 días (la consume contabilidad). | FCO, GER |

## 2. Por construir (en este orden)

1. Cruce de tres vías: orden de compra, recepción (`_consultar('consultar_recepcion', ...)`) y factura; marcar diferencias de cantidad y precio (RN-013, CT-007).
2. Leer la factura del proveedor con OCR reutilizando `migal_ocr` (Gemini) y proponer el borrador.
3. Programa de pagos sugerido por vencimiento; el pago lo ejecuta FCO (RN-014).
4. Escuchar EV-027: preparar el cruce cuando llegue la factura.
5. Escuchar EV-058: registrar la observación contable.

Solo lectura, borradores o propuestas. El agente **no** confirma, aprueba, paga, descuenta ni envía en masa (ver [seguridad de agentes](../../arquitectura/seguridad/seguridad-agentes.md)).

## 3. Contratos con otros agentes

| Tipo | Contrato | Con | Estado |
|---|---|---|---|
| Ofrece (consulta) | `resumen_obligaciones` | contabilidad | Implementada |
| Consume (consulta) | `consultar_recepcion` | suministro | Llamar con `self._consultar(...)` |
| Emite (evento) | `EV-040` Comprobante de compra recibido | contabilidad | Se emite |
| Emite (evento) | `EV-055` Pago a proveedor aplicado a obligación | contabilidad | Se emite |
| Escucha (evento) | `EV-027` Recepción validada | suministro | Método creado, lógica por hacer |
| Escucha (evento) | `EV-058` Inconsistencia contable detectada | contabilidad | Método creado, lógica por hacer |

## 4. Datos de prueba

5 facturas de proveedor «[PRUEBA]» con plazo de 30 días (vencida, por vencer, parcial, pagada) y las órdenes de compra relacionadas. Se cargan con `infra/odoo/cargar_datos_demo.ps1` (script `herramientas/datos_prueba_agentes.py`). Todo lo que crees para probar lleva el prefijo «[PRUEBA]».

## 5. Frases de prueba en el chat

- «facturas por vencer»
- «¿qué debemos a proveedores?»

## 6. Terminado significa

- Cada herramienta nueva declarada en `_herramientas()` con descripción, `input_schema` cerrado, roles y reglas RN.
- Pruebas en `tests/test_pagos.py` que pasan: herramienta, permiso por rol y frase de chat.
- Las consultas que ofreces devuelven las mismas claves que `ejemplo_salida` del catálogo.
- Toda la batería pasa (`-u migal_agente_pagos --test-tags /migal_agente,/migal_agente_pagos`).
- PR a `main` con las cuatro secciones de CONTRIBUTING, revisado por Gabriel y aprobado por Luis.
