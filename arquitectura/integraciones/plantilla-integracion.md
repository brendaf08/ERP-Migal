# INT-XX: [Nombre de la integración o interacción]

Este documento define cómo se relacionan [componentes o sistemas] en ERP-MIGAL, especificando el intercambio de información, las responsabilidades y los controles necesarios para su funcionamiento.

- **Tipo:** Transición funcional interna | Interacción entre aplicaciones | Interoperabilidad externa
- **Estado:** Propuesto | En validación | Validado
- **Responsable:** [Responsable de la definición y validación]

## 1. Alcance y participantes

Indicar qué relación se documenta, qué componentes intervienen y qué aspectos quedan fuera de ella.

| Componente o actor | Responsabilidad en la interacción |
|---|---|
| [Componente A] | [Responsabilidad específica] |
| [Componente B] | [Responsabilidad específica] |

**Incluye:** [Operaciones o intercambios cubiertos].

**No incluye:** [Operaciones o integraciones excluidas].

## 2. Información compartida

Identificar los datos que intervienen en la relación, su origen, destino y responsable de mantenerlos consistentes.

| Información | Origen | Destino o consumidor | Fuente autorizada | Mecanismo |
|---|---|---|---|---|
| [Dato o documento] | [Componente] | [Componente] | [Responsable del dato] | [Compartido / Interno / Manual / Automático] |

**Criterio:** la información no debe duplicarse innecesariamente. Cuando dos sistemas mantengan registros relacionados, se deberá definir cuál es la fuente autorizada y cómo se identifican las operaciones correspondientes.

## 3. Secuencia de interacción

Describir únicamente los pasos necesarios para comprender el intercambio o la transición entre componentes, sin reproducir el proceso empresarial completo.

| Paso | Condición o disparador | Acción o intercambio | Resultado esperado |
|---|---|---|---|
| 1 | [Condición inicial] | [Acción] | [Resultado] |
| 2 | [Condición siguiente] | [Acción] | [Resultado] |
| 3 | [Condición final] | [Acción] | [Resultado] |

**Mecanismo de ejecución:** [Explicar si la interacción utiliza funcionalidades internas de Odoo, registros compartidos, un procedimiento manual o una conexión técnica].

No se debe asumir la existencia de automatizaciones, interfaces o bloqueos técnicos sin haberlos verificado.

## 4. Reglas y excepciones

Documentar las condiciones necesarias para mantener la integridad y consistencia de la información entre los componentes.

| Situación | Regla o control | Tratamiento de excepción |
|---|---|---|
| [Situación habitual] | [Validación requerida] | [Acción ante incumplimiento] |
| [Información inconsistente] | [Control de consistencia] | [Corrección o revisión] |
| [Operación no completada] | [Condición de seguimiento] | [Recuperación o regularización] |

Las autorizaciones y políticas operativas se referencian desde sus documentos correspondientes, sin reproducir sus definiciones completas.

## 5. Validación y evidencias

Indicar cómo se comprobará que la relación funciona conforme a lo documentado.

| Escenario de prueba | Resultado esperado | Evidencia | Resultado |
|---|---|---|---|
| [Interacción normal] | [Comportamiento esperado] | [Registro o prueba] | Pendiente |
| [Excepción relevante] | [Comportamiento esperado] | [Registro o prueba] | Pendiente |
| [Consistencia de datos] | [Comportamiento esperado] | [Registro o prueba] | Pendiente |

**Resultado general:** [No validado / Validación parcial / Validado].

La definición documental no implica que el comportamiento esté configurado o probado en Odoo.

## 6. Referencias y asuntos abiertos

**Documentos relacionados:**

- [ADR correspondiente](../decisiones/)
- [Procesos relacionados](../../procesos/)
- [Modelo de autorización](../seguridad/modelo-autorizacion.md)
- [Registro de riesgos](../riesgos-y-controles.md)

**Asuntos abiertos:** registrar únicamente las cuestiones que afectan directamente a esta interacción y enlazar sus identificadores en el [registro de pendientes](../../producto/registro-pendientes.md).

No duplicar en este archivo las decisiones arquitectónicas, los flujos empresariales completos ni el seguimiento general de riesgos y pendientes.