# ADR-007: Arquitectura multiagente con orquestador, registro y contratos

- **Fecha:** 2026-11-23
- **Estado:** Propuesto
- **Responsable(s):** Luis Núñez

## 1. Contexto y problema

El Agente MIGAL ([A9](../../producto/agente-comercial/agente.md)) nació como un único módulo con herramientas comerciales y de estado de cuenta. El equipo construirá seis agentes de área (ventas, marketing, cadena de suministro, cuentas por cobrar, cuentas por pagar y contabilidad), cada uno a cargo de una persona distinta y con asistentes de código distintos, en un plazo de una semana.

Se necesita una estructura que permita trabajar en paralelo sin conflictos de código, con las mismas convenciones de seguridad y nomenclatura, y que deje a los agentes comunicarse sin depender de que los demás estén terminados.

## 2. Criterios de decisión

- **Trabajo en paralelo:** cada integrante debe poder avanzar y probar sin esperar a los demás.
- **Seguridad:** el control de roles y los vetos deben aplicarse igual a todos los agentes y no depender de cada implementación.
- **Trazabilidad:** toda consulta, evento y herramienta debe quedar en la bitácora con el agente que la originó.
- **Simplicidad:** sin servicios adicionales fuera de Odoo ni infraestructura nueva.
- **Integración final:** conectar los agentes reales no debe exigir reescribir código.

## 3. Alternativas evaluadas

| Alternativa | Descripción | Ventajas | Limitaciones |
|---|---|---|---|
| **A. Un solo módulo compartido** | Todos agregan herramientas a `migal_agente`. | Sin diseño nuevo. | Conflictos de fusión constantes; sin dueños claros; un error rompe a todos. |
| **B. Servicios externos por agente** | Cada agente como API separada (por ejemplo, un servidor Python con un marco de agentes). | Independencia total. | Infraestructura, autenticación y permisos duplicados fuera de Odoo; fuera de alcance para una semana. |
| **C. Módulos Odoo por agente con orquestador** | Un módulo por agente que hereda una clase base; el orquestador los descubre, aplica permisos y media las consultas y eventos según un catálogo de contratos. | Paralelo, permisos únicos, bitácora común, sin infraestructura nueva. | Requiere disciplina con los contratos y un dueño del núcleo. |

## 4. Decisión y justificación

Se decide **la alternativa C**:

- Cada agente es un módulo `migal_agente_<codigo>` con un modelo abstracto `migal.agente.<codigo>` que hereda `migal.agente.especialista` y declara sus herramientas, eventos escuchados, frases de chat y botones del asistente.
- El orquestador (`migal_agente`) descubre los agentes instalados en el registro de Odoo, valida entradas, aplica roles y vetos, registra la bitácora y solo ofrece al modelo de IA las herramientas del rol del usuario.
- La comunicación entre agentes usa dos mecanismos, definidos en `agent/catalogo.py` y en [INT-02](../integraciones/INT-02-contratos-agentes.md):
  - **consultas** síncronas (`consultar`), permitidas solo a los consumidores declarados y con filtro de campos por consumidor;
  - **eventos** (`emitir`) con los códigos del [catálogo de eventos](../../procesos/catalogo-eventos.md); solo el dueño emite y cada oyente corre aislado.
- Mientras el agente dueño no implemente una consulta, el orquestador devuelve la salida de ejemplo del contrato marcada como simulada.
- La cobertura preliminar pasa del núcleo al agente de cadena de suministro.

## 5. Consecuencias

### Positivas

- Seis personas trabajan en módulos separados sin conflictos.
- Seguridad y bitácora uniformes, porque el orquestador las aplica a todos.
- Integración progresiva: al instalar o completar un agente, las consultas simuladas pasan a ser reales sin cambiar a los consumidores.

### Limitaciones y riesgos

- El catálogo es un punto central: sus cambios requieren acuerdo y una persona responsable.
- Las consultas son síncronas y comparten la transacción del usuario; una consulta lenta se nota en la respuesta.
- Las herramientas comerciales y de estado de cuenta anteriores siguen físicamente en el núcleo (con dueño asignado) hasta trasladarlas.

## 6. Validación

- Pruebas automáticas del orquestador (`migal_agente/tests/test_contratos.py`): consistencia del catálogo, nombres únicos, consultas no acordadas, simulador con mínimo privilegio, emisión solo por el dueño, oyente que falla sin romper y filtrado por rol de lo que ve la IA.
- Pruebas de cada agente: registro, herramienta, permiso por rol, frase de chat y evento emitido.
- Comprobado el 2026-11-23 en la base de demostración. La validación con los agentes completos queda pendiente para el 30/11.
