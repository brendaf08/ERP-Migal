# INT-XX: [Nombre de la integración]

- **Fecha:** AAAA-MM-DD
- **Estado:** Propuesto
- **Responsable(s):** [Nombre(s)]
- **Decisiones relacionadas:** [ADR-XXX]
- **Versión de arquitectura:** [VER-XX]

> Esta plantilla establece la estructura de los documentos de integración. Cada integración se documenta en un archivo propio, denominado `INT-XX-nombre-descriptivo.md`, ubicado en `arquitectura/integraciones/`.
>
> Eliminar este bloque y las instrucciones entre corchetes al completar el documento. Cuando un apartado no corresponda, indicar "No aplica".

## 1. Propósito y alcance

[Describir la necesidad de negocio que origina la integración y su relación con Ferre & Inversiones MIGAL.]

[Precisar el alcance: qué intercambio, transición o dependencia comprende la integración y qué queda expresamente fuera de ella.]

## 2. Sistemas, aplicaciones y fronteras

[Identificar los sistemas o aplicaciones que participan y la frontera que los separa. Indicar si la integración es interna a la plataforma, manual o automática.]

| Participante | Tipo | Responsabilidad en la integración |
|---|---|---|
| [Aplicación o sistema] | [Aplicación de Odoo / Sistema externo / Canal externo] | [Función que cumple] |

| Frontera | Origen | Destino | Tipo de integración | Descripción |
|---|---|---|---|---|
| F-XX | [Participante origen] | [Participante destino] | [Interna / Manual / Automática] | [Qué cruza la frontera] |

Asignar a cada frontera un identificador `F-XX` que no esté en uso. Los identificadores `INT`, `EV` y `F` se registran de manera correlativa en los documentos de integración.

## 3. Eventos

[Enumerar los eventos que activan o forman parte de la integración, en el orden en que ocurren.]

| ID | Evento | Origen | Destino | Disparador | Precondiciones | Resultado |
|---|---|---|---|---|---|---|
| EV-XX | [Nombre del evento] | [Participante] | [Participante] | [Acción o condición que lo produce] | [Condiciones previas] | [Efecto sobre el proceso] |

Los eventos describen hechos de negocio. No presuponen un mecanismo técnico determinado.

## 4. Información intercambiada

[Identificar los datos que cruzan la frontera, su procedencia y su carácter obligatorio.]

| Dato | Origen | Destino | Obligatorio | Observaciones |
|---|---|---|---|---|
| [Dato o conjunto de datos] | [Participante] | [Participante] | [Sí / No / Condicionado] | [Referencia al diccionario de datos, formato o restricciones] |

Remitir al diccionario de datos para las definiciones. No duplicar definiciones en este documento.

## 5. Flujo y estados

[Describir la secuencia de la integración desde su inicio hasta su cierre, incluyendo los resultados alternativos.]

1. [Paso 1].
2. [Paso 2].
3. [Paso 3].

Cuando la integración maneje un objeto con ciclo de vida, definir sus estados y transiciones.

| Estado | Descripción | Transiciones posibles |
|---|---|---|
| [Estado] | [Significado] | [Estado siguiente y condición] |

## 6. Reglas, controles y excepciones

[Enumerar las condiciones que debe cumplir la integración, referenciando los identificadores del catálogo de reglas. No redefinir reglas ya documentadas.]

| Referencia | Condición o control | Aplicación en la integración |
|---|---|---|
| [RN / CT / EXC] | [Resumen] | [Dónde y cómo se verifica] |

### Excepciones

[Describir las situaciones que alteran el flujo normal y el tratamiento previsto para cada una.]

## 7. Responsabilidades y autorizaciones

[Indicar quién prepara, ejecuta, autoriza y verifica cada evento, conforme al modelo de autorización.]

| Evento | Prepara | Ejecuta | Autoriza | Verifica |
|---|---|---|---|---|
| EV-XX | [Rol] | [Rol] | [Rol] | [Rol] |

[Señalar los conflictos de segregación de funciones cuando una misma persona acumule varias responsabilidades y los controles compensatorios.]

## 8. Trazabilidad y auditoría

[Precisar qué registro deja cada evento, quién lo genera y cómo se relacionan los documentos involucrados.]

- **Registro de eventos:** [Usuario, fecha y resultado de cada evento].
- **Relación entre documentos:** [Cadena de referencias entre los registros de origen y de destino].
- **Referencia:** [Plan de trazabilidad y auditoría].

## 9. Implementación en Odoo

[Describir las aplicaciones, módulos y configuraciones con que se prevé implementar la integración. Distinguir lo propuesto de lo comprobado.]

| Elemento | Módulo o mecanismo | Clasificación |
|---|---|---|
| [Elemento funcional] | [Módulo técnico, configuración o desarrollo] | [Propuesto / Comprobado / Por validar] |

[Indicar los controles que no puedan aplicarse mediante la configuración estándar y requieran procedimientos o desarrollos adicionales.]

## 10. Validación, riesgos y pendientes

[Indicar las comprobaciones necesarias para confirmar el funcionamiento de la integración.]

- [Validación 1].
- [Validación 2].

**Riesgos relacionados:** [RSK-XXX].

**Pendientes:** [PEN-XXX] y demás asuntos abiertos, con su criterio de cierre.

[Distinguir, cuando corresponda, los hechos verificados, las interpretaciones, los supuestos y los pendientes. No presentar como implementado lo que únicamente se encuentra diseñado.]
