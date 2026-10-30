# ADR-004: Adoptar Odoo CRM como solución de gestión comercial

- **Fecha:** 2026-10-28
- **Estado:** Aceptado
- **Responsable de la decisión:** Equipo ERP-MIGAL

## 1. Contexto y problema

MIGAL recibe consultas de clientes y maestros de obra mediante atención presencial, llamadas y WhatsApp. La información comercial se gestiona principalmente mediante comunicaciones y registros manuales, lo que dificulta centralizar las necesidades, cotizaciones y seguimientos.

La selección previa de Odoo como plataforma ERP no determina automáticamente qué solución CRM debe utilizarse. Es necesario evaluar si conviene aprovechar el CRM incluido en Odoo o utilizar una plataforma externa.

La solución elegida debe atender el seguimiento comercial sin introducir costos, duplicidades o dependencias innecesarias para una empresa pequeña.

## 2. Criterios de decisión

| Criterio | Consideración |
|---|---|
| **Cobertura comercial** | Registrar clientes potenciales, oportunidades, actividades y seguimiento de cotizaciones. |
| **Integración con ERP** | Compartir contactos y relacionar oportunidades con cotizaciones y pedidos. |
| **Costo total** | Considerar licencias, implementación, integraciones y mantenimiento. |
| **Simplicidad operativa** | Evitar que los trabajadores deban gestionar información duplicada en varios sistemas. |
| **Extensibilidad** | Permitir adaptar las funcionalidades a nuevas necesidades. |
| **Sostenibilidad** | Reducir dependencias técnicas y comerciales difíciles de mantener. |

## 3. Alternativas evaluadas

| Alternativa | Ventajas | Limitaciones |
|---|---|---|
| **A. CRM nativo de Odoo** | Comparte plataforma y contactos con Ventas; permite relacionar oportunidades y cotizaciones; evita incorporar otro CRM. | Su funcionalidad estándar puede requerir configuración o ampliaciones ante necesidades comerciales más especializadas. |
| **B. CRM externo integrado con Odoo** | Permite utilizar soluciones especializadas como HubSpot o Zoho CRM, con capacidades comerciales adicionales según producto y plan. | Requiere definir sincronización, tratamiento de errores, responsabilidades sobre los datos y costos de integración. |
| **C. CRM externo independiente** | Permite operar una herramienta comercial sin modificar inicialmente el ERP. | Obliga a transferir información manualmente, con mayor riesgo de duplicidades e inconsistencias. |

Las alternativas externas se consideran opciones arquitectónicas; no se dispone de una evaluación comercial completa de licencias y planes específicos de esos proveedores.

## 4. Decisión y justificación

Se decide adoptar la **alternativa A: utilizar Odoo CRM como solución de gestión comercial de MIGAL**, dentro de la misma instancia de Odoo Community seleccionada para el ERP.

La decisión se fundamenta en cuatro aspectos:

**1. Cobertura suficiente para las necesidades iniciales.** Odoo CRM dispone de herramientas para registrar leads, gestionar oportunidades, organizar actividades y dar seguimiento al proceso comercial. Las necesidades específicas de MIGAL deberán comprobarse mediante pruebas.

**2. Continuidad con las operaciones de ventas.** Las oportunidades pueden vincularse con las cotizaciones gestionadas en Ventas, utilizando contactos de la misma plataforma. Esto evita establecer un mecanismo de sincronización entre dos CRM o bases independientes.

**3. Menor complejidad de implementación y mantenimiento.** Un CRM externo introduciría decisiones adicionales sobre licenciamiento, integraciones, duplicidad de datos y recuperación ante fallas. Para el alcance actual, esa complejidad no se encuentra justificada.

**4. Extensibilidad.** Odoo permite incorporar configuraciones y módulos adicionales si surgen nuevas necesidades, aunque cada ampliación deberá evaluarse por compatibilidad y mantenimiento.

La elección no implica que Odoo CRM sea superior a todas las herramientas especializadas. Si MIGAL requiere posteriormente funcionalidades que el CRM seleccionado no pueda satisfacer de manera razonable, podrá reconsiderarse una alternativa externa.

### Implicación arquitectónica

CRM y ERP operarán como capacidades funcionales de **una misma instancia de Odoo**, no como dos plataformas conectadas mediante una API externa.

La coordinación entre gestión comercial y ejecución operativa se documentará en [INT-01: CRM–ERP](../integraciones/INT-01-CRM-ERP.md). Este contrato establecerá qué validaciones deben cumplirse antes de confirmar un pedido.

La aceptación comercial de una cotización no deberá interpretarse por sí sola como aprobación operativa del pedido. La aplicación efectiva de esta restricción deberá verificarse en Odoo.

## 5. Consecuencias

### Positivas

- Uso de una plataforma común para CRM y operaciones ERP.
- Menor necesidad de duplicar información de clientes y cotizaciones.
- Reducción de integraciones externas y costos potenciales asociados.
- Continuidad entre seguimiento comercial y ventas.
- Posibilidad de extender el CRM progresivamente.

### Limitaciones y riesgos

- Algunas necesidades específicas podrían requerir configuración o desarrollo.
- La ausencia de integración automática con WhatsApp exige procedimientos de registro manual.
- Compartir una plataforma no garantiza por sí solo la calidad de los datos ni el cumplimiento de autorizaciones.
- La aplicación de controles comerciales puede requerir procedimientos operativos o restricciones adicionales.
- La dependencia de una sola plataforma implica asegurar disponibilidad, respaldos y mantenimiento.

## 6. Validación

La decisión se considera aceptada arquitectónicamente, pero deben comprobarse en la instalación de Odoo 19 Community:

- Registro y seguimiento de leads y oportunidades.
- Reutilización de contactos existentes sin duplicar clientes.
- Vinculación entre oportunidades y cotizaciones.
- Disponibilidad de la información comercial requerida por MIGAL.
- Permisos de usuarios comerciales y aprobación de excepciones.
- Aplicación de las validaciones operativas previas a confirmar pedidos.

Estas pruebas no se consideran realizadas por el hecho de documentar la decisión.

**Referencias:**

- [Documentación oficial de Odoo CRM 19](https://www.odoo.com/documentation/19.0/es/applications/sales/crm.html).
- [Documentación de cotizaciones de Odoo 19](https://www.odoo.com/documentation/19.0/applications/sales/sales/sales_quotations/create_quotations.html).
- [INT-01: CRM–ERP](../integraciones/INT-01-CRM-ERP.md).
- [ADR-001: Selección de ERP](ADR-001-seleccion-erp.md).