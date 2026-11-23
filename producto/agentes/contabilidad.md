# Agente de contabilidad

- **Responsable:** César Joaquín · **Revisa el PR:** Luis · **Aprobación final:** Luis
- **Módulo:** `custom_addons/migal_agente_contabilidad` · **Modelo:** `migal.agente.contabilidad` · **Rama:** `feat/agente-contabilidad`
- **Roles que atiende:** FCO (Facturación, contabilidad y cobros), GER (Gerencia)
- **Herramienta de código sugerida:** Gratuitas: Gemini CLI con cuenta personal, GitHub Copilot (Student Pack) u OpenCode
- **Estado:** TO-BE en construcción. Lo marcado «ya funciona» está implementado y probado en la base.

Lee primero [AGENTS.md](../../AGENTS.md) y la [guía del equipo](README.md). Los contratos completos están en [INT-02](../../arquitectura/integraciones/INT-02-contratos-agentes.md).

## 1. Ya funciona (punto de partida)

| Herramienta | Qué hace | Roles |
|---|---|---|
| `pendientes_cierre` | Revisión de cierre: borradores, pagos sin conciliar, facturas sin OC, IGV referencial y saldos (consulta a cobranzas y pagos). | FCO, GER |

## 2. Por construir (en este orden)

1. Conciliación bancaria asistida: pagos sin conciliar con su posible extracto.
2. Detectar inconsistencias (factura sin recepción, pago sin factura, montos que no cuadran) y emitir EV-058.
3. IGV del mes por tipo de comprobante (referencial; KeyFacil emite, RN-009).
4. Escuchar EV-038/040/043/055: acumular movimientos del mes.

Solo lectura, borradores o propuestas. El agente **no** confirma, aprueba, paga, descuenta ni envía en masa (ver [seguridad de agentes](../../arquitectura/seguridad/seguridad-agentes.md)).

## 3. Contratos con otros agentes

| Tipo | Contrato | Con | Estado |
|---|---|---|---|
| Consume (consulta) | `resumen_cartera` | cobranzas | Llamar con `self._consultar(...)` |
| Consume (consulta) | `resumen_obligaciones` | pagos | Llamar con `self._consultar(...)` |
| Emite (evento) | `EV-058` Inconsistencia contable detectada | cobranzas, pagos | Por implementar |
| Escucha (evento) | `EV-038` Comprobante de venta emitido | cobranzas | Método creado, lógica por hacer |
| Escucha (evento) | `EV-040` Comprobante de compra recibido | pagos | Método creado, lógica por hacer |
| Escucha (evento) | `EV-043` Pago aplicado a deuda | cobranzas | Método creado, lógica por hacer |
| Escucha (evento) | `EV-055` Pago a proveedor aplicado a obligación | pagos | Método creado, lógica por hacer |

## 4. Datos de prueba

Todas las facturas y pagos «[PRUEBA]» de clientes y proveedores; los saldos de cobranzas y pagos llegan por consulta. Se cargan con `infra/odoo/cargar_datos_demo.ps1` (script `herramientas/datos_prueba_agentes.py`). Todo lo que crees para probar lleva el prefijo «[PRUEBA]».

## 5. Frases de prueba en el chat

- «pendientes de cierre»
- «¿cómo va la contabilidad?»

## 6. Terminado significa

- Cada herramienta nueva declarada en `_herramientas()` con descripción, `input_schema` cerrado, roles y reglas RN.
- Pruebas en `tests/test_contabilidad.py` que pasan: herramienta, permiso por rol y frase de chat.
- Las consultas que ofreces devuelven las mismas claves que `ejemplo_salida` del catálogo.
- Toda la batería pasa (`-u migal_agente_contabilidad --test-tags /migal_agente,/migal_agente_contabilidad`).
- PR a `main` con las cuatro secciones de CONTRIBUTING, revisado por Luis y aprobado por Luis.
