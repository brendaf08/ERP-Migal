# Agente de cadena de suministro

- **Responsable:** Alejandro Flores · **Revisa el PR:** Brenda · **Aprobación final:** Luis
- **Módulo:** `custom_addons/migal_agente_suministro` · **Modelo:** `migal.agente.suministro` · **Rama:** `feat/agente-suministro`
- **Roles que atiende:** CMP (Compras), ALM (Almacén), GER (Gerencia), VEN (Ventas)
- **Herramienta de código sugerida:** Google AI Pro (Gemini CLI / Jules)
- **Estado:** TO-BE en construcción. Lo marcado «ya funciona» está implementado y probado en la base.

Lee primero [AGENTS.md](../../AGENTS.md) y la [guía del equipo](README.md). Los contratos completos están en [INT-02](../../arquitectura/integraciones/INT-02-contratos-agentes.md).

## 1. Ya funciona (punto de partida)

| Herramienta | Qué hace | Roles |
|---|---|---|
| `evaluar_cobertura_preliminar` | Cobertura de una cotización con stock y reposiciones (trasladada del núcleo). | VEN, ALM, CMP, GER |
| `listar_compras_pendientes` | Órdenes de compra por aprobar, por recibir y atrasadas. | CMP, ALM, GER |
| `consultar_recepcion` | Pedido, recibido y pendiente de una orden de compra (la consume pagos). | CMP, ALM, FCO, GER |

## 2. Por construir (en este orden)

1. `consultar_baja_rotacion` (la consume marketing; hoy responde el simulador).
2. Sugerir reposición con las reglas de stock mínimo (`stock.warehouse.orderpoint`, disparador manual) (RN-011).
3. Preparar BORRADOR de orden de compra; confirmar es de GER (RN-012).
4. Comparar proveedores por precio y plazo (`product.supplierinfo`).
5. Despachos pendientes y entregas parciales (RN-018).
6. Escuchar EV-018: revisar si la venta deja productos bajo el mínimo.

Solo lectura, borradores o propuestas. El agente **no** confirma, aprueba, paga, descuenta ni envía en masa (ver [seguridad de agentes](../../arquitectura/seguridad/seguridad-agentes.md)).

## 3. Contratos con otros agentes

| Tipo | Contrato | Con | Estado |
|---|---|---|---|
| Ofrece (consulta) | `evaluar_cobertura_preliminar` | ventas | Implementada |
| Ofrece (consulta) | `consultar_recepcion` | pagos | Implementada |
| Ofrece (consulta) | `consultar_baja_rotacion` | marketing | Por implementar (hoy: simulador) |
| Emite (evento) | `EV-027` Recepción validada | ventas, pagos | Se emite |
| Escucha (evento) | `EV-018` Orden de venta confirmada | ventas | Método creado, lógica por hacer |

## 4. Datos de prueba

5 proveedores, 23 precios de proveedor, 8 reglas de stock mínimo y 9 órdenes de compra «[PRUEBA]» (borrador, enviada, confirmada, atrasada, recibida, parcial 80 %, precio +8 %, factura vencida, pagada). Se cargan con `infra/odoo/cargar_datos_demo.ps1` (script `herramientas/datos_prueba_agentes.py`). Todo lo que crees para probar lleva el prefijo «[PRUEBA]».

## 5. Frases de prueba en el chat

- «compras pendientes»
- «recepción de la P00020»

## 6. Terminado significa

- Cada herramienta nueva declarada en `_herramientas()` con descripción, `input_schema` cerrado, roles y reglas RN.
- Pruebas en `tests/test_suministro.py` que pasan: herramienta, permiso por rol y frase de chat.
- Las consultas que ofreces devuelven las mismas claves que `ejemplo_salida` del catálogo.
- Toda la batería pasa (`-u migal_agente_suministro --test-tags /migal_agente,/migal_agente_suministro`).
- PR a `main` con las cuatro secciones de CONTRIBUTING, revisado por Brenda y aprobado por Luis.
