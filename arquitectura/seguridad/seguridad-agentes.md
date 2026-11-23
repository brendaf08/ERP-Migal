# Seguridad de los agentes MIGAL

Controles que aplican a todos los agentes. Complementa el [modelo de autorización](modelo-autorizacion.md) sin repetirlo.

## 1. Principios

| Principio | Cómo se aplica |
|---|---|
| El agente asiste, la persona decide | Los agentes leen, calculan, proponen y preparan borradores. Confirmar, aprobar, pagar, otorgar crédito o descuentos, ajustar inventario y enviar en masa quedan en manos del rol responsable. |
| Mismos permisos que el usuario | Las herramientas usan el ORM con el usuario actual. El orquestador exige además el rol declarado en el contrato (`roles`). |
| Mínimo privilegio entre agentes | Cada consulta tiene consumidores declarados. `campos_por_consumidor` limita lo que recibe cada uno (por ejemplo, marketing solo sabe si un cliente debe excluirse, no cuánto debe). |
| La IA no amplía permisos | El modelo de IA solo recibe las herramientas del rol del usuario y toda llamada pasa por la misma validación y control de roles. |
| Todo queda registrado | Herramientas, consultas (`canal = consulta`) y eventos (`canal = evento`) se guardan en `migal.agente.log` con el agente que los originó. |

## 2. Vetos

El orquestador bloquea antes de ejecutar las solicitudes que intentan:

| Veto | Regla |
|---|---|
| Dar descuentos, cambiar precios u otorgar crédito | RN-004 |
| Confirmar o aprobar una venta, orden o solicitud | RN-006 |
| Emitir comprobantes (los emite KeyFacil) | RN-009 |
| Anular o cancelar ventas, órdenes o facturas | RN-010 |
| Confirmar o enviar una orden de compra | RN-012 |
| Registrar cobros o pagar a proveedores | RN-014 |
| Reservar o separar stock | RN-015 |
| Ajustar inventario | RN-017 |
| Enviar mensajes o campañas masivas | RN-022 |

Los patrones están en `migal_agente/agent/guardrails.py`. Un agente nuevo que necesite otro veto lo solicita al responsable del núcleo.

## 3. Roles por agente

| Agente | Roles que atiende |
|---|---|
| Ventas | VEN, GER |
| Marketing | GER, VEN (las campañas requieren aprobación de GER) |
| Cadena de suministro | CMP, ALM, GER, VEN (cobertura) |
| Cuentas por cobrar | FCO, GER; VEN consulta la situación de crédito |
| Cuentas por pagar | FCO, GER |
| Contabilidad | FCO, GER |

Los roles se resuelven con los grupos de Odoo definidos en `ROLE_GROUPS` (`migal_agente/agent/contracts.py`).

## 4. Secretos y datos

- Las claves de IA se guardan en **Ajustes → Agente MIGAL**, nunca en el código, en `.env` versionado ni en mensajes.
- No se suben al repositorio respaldos de base, el filestore, fotos de notas reales ni datos de clientes. Las evidencias usan datos «[PRUEBA]» o anonimizados.
- Las pruebas automáticas desactivan la IA y no llaman servicios externos.

## 5. Revisión de un PR de agente

- [ ] Solo cambia archivos de su módulo (y su ficha).
- [ ] Cada herramienta declara roles, reglas y `additionalProperties: False`.
- [ ] No hay `sudo()` salvo justificación escrita en el PR.
- [ ] No hay escrituras de negocio (confirmar, aprobar, pagar, publicar, enviar).
- [ ] Las consultas a otros agentes usan `_consultar`; los eventos, `_emitir`.
- [ ] Sin claves, datos reales ni archivos generados.
- [ ] Pruebas incluidas y en verde.
