# INT-02: Contratos entre agentes MIGAL

Este documento define cómo se relacionan el orquestador y los agentes especialistas de ERP-MIGAL: qué consultas puede hacer cada agente a otro, qué eventos emite y escucha, y los controles que aplica el orquestador. La fuente técnica es `custom_addons/migal_agente/agent/catalogo.py` (versión 1); este documento la explica y debe actualizarse junto con ella.

- **Tipo:** Interacción entre aplicaciones (módulos Odoo)
- **Estado:** En validación
- **Responsable:** Luis Núñez (orquestador); cada responsable de agente valida los contratos que ofrece

## 1. Alcance y participantes

| Componente o actor | Responsabilidad en la interacción |
|---|---|
| Orquestador (`migal_agente`, Luis Núñez) | Descubre agentes, aplica roles y vetos, media consultas y eventos, registra la bitácora y simula consultas pendientes. |
| Ventas (`migal_agente_ventas`, Brenda Mirano) | Implementa sus herramientas y las consultas que ofrece; emite sus eventos. |
| Marketing (`migal_agente_marketing`, Brenda Mirano) | Implementa sus herramientas y las consultas que ofrece; emite sus eventos. |
| Cadena de suministro (`migal_agente_suministro`, Alejandro Flores) | Implementa sus herramientas y las consultas que ofrece; emite sus eventos. |
| Cuentas por cobrar (`migal_agente_cobranzas`, Gabriel Martínez) | Implementa sus herramientas y las consultas que ofrece; emite sus eventos. |
| Cuentas por pagar (`migal_agente_pagos`, Diego Pinedo) | Implementa sus herramientas y las consultas que ofrece; emite sus eventos. |
| Contabilidad (`migal_agente_contabilidad`, César Joaquín) | Implementa sus herramientas y las consultas que ofrece; emite sus eventos. |

**Incluye:** consultas síncronas entre agentes, eventos de negocio entre agentes y herramientas expuestas al chat, al asistente y al modelo de IA.

**No incluye:** integraciones externas (KeyFacil, bancos, WhatsApp Business API) ni la relación CRM-ERP, documentada en [INT-01](INT-01-CRM-ERP.md).

## 2. Información compartida: consultas

| Consulta | Ofrece | Consumen | Entrada | Salida (claves de `datos`) | Restricción |
|---|---|---|---|---|---|
| `evaluar_cobertura_preliminar` | suministro | ventas | `cotizacion`: Referencia de la cotización, p. ej. S00573; `fecha_requerida`: AAAA-MM-DD (opcional) | `cotizacion`, `fecha_atencion`, `lineas` | - |
| `consultar_recepcion` | suministro | pagos | `orden_compra`: Referencia de la orden de compra, p. ej. P00020 | `orden_compra`, `estado_recepcion`, `tabla`, `productos` | - |
| `consultar_baja_rotacion` | suministro | marketing | `dias`: Ventana de análisis en días (opcional, 90 por defecto) | `dias`, `productos` | - |
| `consultar_situacion_credito` | cobranzas | ventas, marketing | `cliente`: Nombre, RUC/DNI o referencia del cliente | `cliente`, `deuda_total`, `deuda_vencida`, `dias_max_vencido`, `limite_credito`, `excede_limite`, `excluir` | marketing solo recibe cliente, excluir |
| `consultar_cotizaciones_perdidas` | ventas | marketing | `dias`: Ventana de análisis en días (opcional, 90 por defecto) | `dias`, `perdidas` | - |
| `resumen_cartera` | cobranzas | contabilidad | Ninguna | `por_cobrar`, `vencido`, `tramos` | - |
| `resumen_obligaciones` | pagos | contabilidad | Ninguna | `por_pagar`, `vencido`, `proximos_7_dias` | - |

Toda respuesta tiene la forma común `{ok, estado, titulo, mensaje, datos, avisos, reglas, controles, escalar_a}`. Si responde el simulador, se agrega `simulado: true` y un aviso.

Ejemplo de salida simulada (`consultar_situacion_credito`):

```json
{
  "ok": true,
  "estado": "ok",
  "titulo": "Situación de crédito (simulada)",
  "mensaje": "Sin deuda vencida.",
  "datos": {
    "cliente": "[PRUEBA] Cliente",
    "deuda_total": 0.0,
    "deuda_vencida": 0.0,
    "dias_max_vencido": 0,
    "limite_credito": 0.0,
    "excede_limite": false,
    "excluir": false
  }
}
```

### Eventos

| Evento | Nombre | Emite | Escuchan | Datos |
|---|---|---|---|---|
| EV-018 | Orden de venta confirmada | ventas | suministro, cobranzas | `orden`, `cliente`, `monto`, `lineas` |
| EV-027 | Recepción validada | suministro | ventas, pagos | `recepcion`, `orden_compra`, `proveedor`, `lineas` |
| EV-038 | Comprobante de venta emitido | cobranzas | contabilidad | `factura`, `cliente`, `monto`, `vencimiento` |
| EV-040 | Comprobante de compra recibido | pagos | contabilidad | `factura`, `proveedor`, `monto`, `orden_compra` |
| EV-043 | Pago aplicado a deuda | cobranzas | contabilidad | `pago`, `cliente`, `monto` |
| EV-055 | Pago a proveedor aplicado a obligación | pagos | contabilidad | `pago`, `proveedor`, `monto` |
| EV-057 | Campaña comercial aprobada | marketing | ventas | `campana`, `productos`, `vigencia` |
| EV-058 | Inconsistencia contable detectada | contabilidad | cobranzas, pagos | `tipo`, `documento`, `detalle` |

Los códigos son los del [catálogo de eventos](../../procesos/catalogo-eventos.md). EV-057 y EV-058 se incorporan con esta integración.

### Herramientas del núcleo con dueño

| Herramienta | Agente dueño |
|---|---|
| `preparar_whatsapp_cotizacion` | ventas |
| `registrar_envio_whatsapp` | ventas |
| `generar_qr_cotizacion` | ventas |
| `buscar_cotizaciones` | ventas |
| `consultar_cotizacion` | ventas |
| `generar_estado_cuenta` | cobranzas |
| `compartir_estado_cuenta` | cobranzas |

## 3. Secuencia de interacción

| Paso | Condición o disparador | Acción o intercambio | Resultado esperado |
|---|---|---|---|
| 1 | Un agente necesita un dato de otro | Llama `self._consultar(contrato, args)` | El orquestador verifica que el contrato exista y que el agente sea consumidor |
| 2 | El dueño implementa la consulta | El orquestador la ejecuta con el usuario actual (roles y validación de entrada) | Respuesta real, filtrada por `campos_por_consumidor` |
| 3 | El dueño aún no la implementa o no está instalado | El orquestador devuelve `ejemplo_salida` | Respuesta marcada `simulado: true` |
| 4 | Ocurre un hecho de negocio (p. ej. se valida una recepción) | El dueño llama `self._emitir(evento, datos)` desde su módulo | Cada oyente recibe una copia de los datos dentro de un punto de guardado |
| 5 | Siempre | El orquestador registra la consulta o el evento | Fila en `migal.agente.log` con canal `consulta` o `evento` y el agente |

**Mecanismo de ejecución:** llamadas en el mismo proceso de Odoo (modelos abstractos y ORM), en la transacción del usuario. Sin colas ni servicios externos.

## 4. Reglas y excepciones

| Situación | Regla o control | Tratamiento de excepción |
|---|---|---|
| Consulta fuera del catálogo o de un agente no autorizado | El orquestador la rechaza | Respuesta `estado: contrato`, registrada en bitácora |
| Usuario sin el rol de la herramienta consultada | Control de roles del orquestador | Respuesta `estado: sin_permiso` |
| Agente que emite un evento ajeno | Solo emite el dueño | El evento se descarta y se registra una advertencia |
| Un oyente falla | Punto de guardado por oyente | Se revierte solo ese oyente; la operación del usuario continúa |
| Cambio de un contrato | Agregar campos opcionales es libre; cambiar o quitar requiere acuerdo del consumidor | Se sube `VERSION` del catálogo y se actualiza este documento |

Los roles y vetos se aplican según el [modelo de autorización](../seguridad/modelo-autorizacion.md) y la [seguridad de agentes](../seguridad/seguridad-agentes.md).

## 5. Validación y evidencias

| Escenario de prueba | Resultado esperado | Evidencia | Resultado |
|---|---|---|---|
| Catálogo coherente con los agentes instalados | Consumidores, emisores y oyentes existen | `test_contratos.test_catalogo_consistente` | Validado 2026-11-23 |
| Consulta no acordada | Rechazada con `estado: contrato` | `test_contratos.test_consulta_no_acordada` | Validado 2026-11-23 |
| Consulta pendiente de implementar | Respuesta simulada | `test_ventas.test_simulador_para_consulta_pendiente` | Validado 2026-11-23 |
| Mínimo privilegio | Marketing solo recibe `cliente` y `excluir` | `test_marketing.test_marketing_solo_recibe_bandera_de_credito` | Validado 2026-11-23 |
| Evento real | Confirmar una venta entrega EV-018 a suministro y cobranzas | `test_ventas.test_confirmar_venta_emite_ev018` | Validado 2026-11-23 |
| Oyente que falla | La operación continúa | `test_contratos.test_oyente_que_falla_no_rompe` | Validado 2026-11-23 |
| Flujos completos con agentes terminados | Sin respuestas simuladas | Pruebas integradas del 30/11 | Pendiente |

**Resultado general:** Validación parcial (mecanismo validado; contratos pendientes de implementar por sus dueños).

## 6. Referencias y asuntos abiertos

**Documentos relacionados:**

- [ADR-007 Arquitectura multiagente](../decisiones/ADR-007-arquitectura-multiagente.md)
- [Guía del equipo y fichas de agentes](../../producto/agentes/README.md)
- [Catálogo de eventos](../../procesos/catalogo-eventos.md) y [catálogo de reglas](../../procesos/catalogo-reglas.md)
- [Modelo de autorización](../seguridad/modelo-autorizacion.md)

**Asuntos abiertos:** contratos versión 1 por cerrar en la reunión del 25/11; implementación de `consultar_baja_rotacion` y `consultar_cotizaciones_perdidas`; emisión de EV-057 y EV-058.
