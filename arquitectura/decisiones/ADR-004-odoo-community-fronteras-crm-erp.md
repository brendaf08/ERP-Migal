# ADR-004: Establecer fronteras funcionales entre CRM y ERP en Odoo

- **Fecha:** 2026-10-28
- **Estado:** Aceptado
- **Responsable de la decisión:** Equipo ERP-MIGAL

## 1. Contexto y problema

**Ferre & Inversiones MIGAL** necesita integrar la gestión de relaciones comerciales con la ejecución de sus operaciones empresariales, manteniendo la continuidad de la información desde la atención inicial del cliente hasta la venta y su correspondiente cobro.

La solución contempla actividades comerciales como el registro de leads, oportunidades y cotizaciones, así como operaciones empresariales relacionadas con pedidos, inventario, compras, entregas, facturación y finanzas.

Aunque estas actividades están relacionadas, presentan responsabilidades diferentes. El CRM administra las oportunidades y compromisos comerciales, mientras que el ERP debe verificar las condiciones operativas antes de confirmar y ejecutar un pedido.

Por ello, se requiere definir cómo se organizarán ambas áreas dentro de la arquitectura, evitando duplicidad de información, confirmaciones sin validación y una complejidad de integración innecesaria.

## 2. Criterios de decisión

- **Integración:** mantener la continuidad de la información entre las actividades comerciales y operativas.
- **Separación de responsabilidades:** distinguir la gestión comercial de la validación y ejecución empresarial.
- **Trazabilidad:** conservar la relación entre oportunidades, cotizaciones, solicitudes y pedidos.
- **Consistencia de datos:** evitar registros duplicados de clientes, productos y operaciones.
- **Control operativo:** verificar la viabilidad de los compromisos comerciales antes de confirmar pedidos.
- **Complejidad y costo:** priorizar una arquitectura sostenible para MIGAL, sin introducir integraciones técnicas innecesarias.

## 3. Alternativas evaluadas

| Alternativa | Descripción | Ventajas | Limitaciones |
|---|---|---|---|
| **A. CRM y ERP independientes** | Utilizar sistemas separados e intercambiar información mediante integraciones. | Independencia tecnológica y posibilidad de seleccionar soluciones especializadas. | Mayor complejidad de integración, sincronización y mantenimiento. |
| **B. Plataforma unificada sin fronteras funcionales** | Utilizar Odoo para todas las actividades sin establecer responsabilidades diferenciadas entre CRM y ERP. | Menor esfuerzo inicial de definición de procesos. | Riesgo de confundir la aceptación comercial con la confirmación operativa y dificultar los controles. |
| **C. Plataforma unificada con fronteras funcionales** | Utilizar CRM y ERP dentro de Odoo, estableciendo responsabilidades, condiciones de transición y mecanismos de trazabilidad. | Integración de información, separación de responsabilidades y menor dependencia de conectores externos. | Requiere definir y validar controles, estados y procedimientos de transición. |

## 4. Decisión y justificación

Se decide adoptar la **Opción C: utilizar CRM y ERP dentro de una misma plataforma Odoo, estableciendo fronteras funcionales claras entre ambas áreas**.

La decisión establece las siguientes responsabilidades:

- **CRM:** gestiona el proceso comercial, desde la captación del lead hasta la oportunidad, cotización y aceptación de las condiciones por parte del cliente.
- **ERP:** verifica la viabilidad operativa de las condiciones aceptadas y gestiona los pedidos confirmados, inventario, compras, entregas, facturación y finanzas.
- **Contactos:** mantiene la información compartida de clientes, proveedores y otras personas o empresas relacionadas con las operaciones.

La frontera funcional se establece mediante una **solicitud de pedido**, generada a partir de una cotización aceptada por el cliente.

Esta solicitud permite que el ERP evalúe las condiciones acordadas, incluyendo principalmente la disponibilidad de productos, las autorizaciones correspondientes y la viabilidad de atención.

- Si la solicitud es **aceptada**, se habilita la confirmación del pedido de venta y continúa su ejecución operativa.
- Si la solicitud es **condicionada o rechazada**, la gestión retorna al ámbito comercial para revisar o renegociar las condiciones necesarias.

De esta manera, **la aceptación de una cotización por el cliente no equivale automáticamente a la confirmación de un pedido de venta**.

La arquitectura seleccionada permite utilizar las aplicaciones de Odoo dentro de un mismo entorno, compartiendo información sin requerir una integración entre plataformas independientes.

Esta frontera representa una **separación de responsabilidades de negocio**, no necesariamente una separación técnica entre módulos ni la creación obligatoria de un nuevo objeto en Odoo. Su implementación concreta se definirá en la documentación de integración CRM–ERP.

## 5. Consecuencias

### Positivas

- Centralización de la información comercial y operativa en Odoo.
- Menor dependencia de integraciones entre sistemas independientes.
- Separación clara entre compromisos comerciales y confirmaciones operativas.
- Mayor trazabilidad entre oportunidades, cotizaciones y pedidos.
- Reducción de duplicidad de información mediante datos compartidos.
- Posibilidad de establecer controles antes de confirmar operaciones.

### Limitaciones y riesgos

- La plataforma unificada no garantiza por sí sola el cumplimiento de las fronteras funcionales.
- El mecanismo de solicitud, validación y respuesta puede requerir configuración, procedimientos o desarrollos adicionales.
- La disponibilidad registrada en inventario puede diferir de las existencias físicas.
- Las autorizaciones de precios, descuentos y condiciones excepcionales requieren controles definidos.
- El personal deberá respetar las responsabilidades y procedimientos establecidos.
- Una transición incorrectamente configurada podría permitir confirmar pedidos sin la validación operativa prevista.

## 6. Validación

La decisión establece una arquitectura funcional propuesta, cuyo comportamiento deberá comprobarse en la instancia de Odoo 18 Community.

Se requiere validar:

- La continuidad de información entre CRM, Contactos y Ventas.
- La relación entre la oportunidad comercial, la cotización aceptada y el pedido.
- El mecanismo mediante el cual se representa y procesa la solicitud de pedido.
- La verificación de disponibilidad, autorizaciones y condiciones operativas antes de confirmar el pedido.
- El tratamiento de solicitudes aceptadas, condicionadas y rechazadas.
- La trazabilidad de las decisiones y la participación de los responsables autorizados.

Estas validaciones permitirán determinar qué controles pueden implementarse mediante las funcionalidades existentes de Odoo y cuáles requieren configuración adicional o procedimientos específicos.

La decisión se considera **aceptada a nivel arquitectónico**, mientras que los mecanismos de transición y su implementación permanecen sujetos a validación técnica.