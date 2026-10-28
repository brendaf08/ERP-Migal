# Análisis de roles funcionales y responsabilidades

Este documento analiza la distribución de responsabilidades entre los roles funcionales propuestos para **Ferre & Inversiones MIGAL**, considerando los procesos comerciales, de abastecimiento, inventario, despacho, facturación, contabilidad y cobranzas.

Su objetivo es identificar quién prepara, autoriza, ejecuta y verifica las operaciones, evitando concentrar decisiones sensibles en usuarios que no cuentan con la responsabilidad correspondiente.

El análisis constituye una propuesta funcional para la implementación de **Odoo 18 Community**. No implica que los permisos hayan sido configurados ni que todas las restricciones propuestas puedan aplicarse directamente sin ajustes adicionales.

## 1. Roles funcionales considerados

Se mantienen seis roles funcionales y administrativos, que representan responsabilidades y no necesariamente puestos de trabajo independientes.

| Código  | Rol                                   | Responsabilidad principal                                                                                   |
| ------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **GER** | Gerencia                              | Supervisión y autorización de decisiones comerciales, operativas y financieras sensibles.                   |
| **VEN** | Atención y Ventas                     | Gestión de clientes, oportunidades comerciales, cotizaciones, pedidos y ventas.                             |
| **ALM** | Almacén y Despacho                    | Gestión de existencias, recepciones, transferencias, preparación y despacho de pedidos.                     |
| **CMP** | Compras y Abastecimiento              | Gestión de proveedores, solicitudes de presupuesto y preparación de compras.                                |
| **FCO** | Facturación, contabilidad y cobranzas | Gestión de documentos de facturación, pagos, saldos, cuentas pendientes y operaciones contables ordinarias. |
| **SIS** | Administración del Sistema            | Administración técnica de Odoo, usuarios, grupos de acceso y configuraciones.                               |

## 2. Criterio de distribución de responsabilidades

Para analizar las actividades se utilizan los siguientes códigos:

| Código | Significado               | Descripción                                                                                |
| ------ | ------------------------- | ------------------------------------------------------------------------------------------ |
| **P**  | Preparar                  | Elaborar o registrar la información necesaria antes de ejecutar o autorizar una operación. |
| **A**  | Autorizar                 | Aprobar una decisión u operación que requiere facultades específicas.                      |
| **E**  | Ejecutar                  | Realizar la operación correspondiente dentro del proceso.                                  |
| **V**  | Verificar                 | Revisar la operación, sus resultados o el cumplimiento de las condiciones establecidas.    |
| **—**  | Sin intervención asignada | El rol no tiene una responsabilidad funcional prevista para esa actividad.                 |

Un mismo rol puede asumir más de una responsabilidad, de acuerdo con las características de MIGAL. La distribución propuesta deberá contrastarse con las posibilidades reales de control de acceso de Odoo.

## 3. Análisis de responsabilidades comerciales

| Actividad                                       | GER | VEN | ALM | CMP | FCO | SIS |
| ----------------------------------------------- | --- | --- | --- | --- | --- | --- |
| Gestión de clientes y contactos comerciales     | V   | P/E | —   | —   | —   | —   |
| Gestión de oportunidades comerciales            | V   | P/E | —   | —   | —   | —   |
| Elaboración de cotizaciones                     | V   | P/E | —   | —   | —   | —   |
| Negociación de precios o descuentos especiales  | A   | P/E | —   | —   | —   | —   |
| Confirmación de pedidos ordinarios              | V   | E   | —   | —   | —   | —   |
| Consulta de disponibilidad de productos         | V   | E   | E   | E   | —   | —   |
| Registro de ventas ordinarias en Punto de Venta | V   | E   | —   | —   | V   | —   |
| Solicitud de crédito para un cliente            | A   | P   | —   | —   | P/V | —   |
| Modificación de condiciones crediticias         | A   | P   | —   | —   | P/V | —   |

### Consideraciones comerciales

- VEN gestiona las actividades comerciales ordinarias, utilizando precios y condiciones autorizadas.
- GER conserva las decisiones relacionadas con negociaciones especiales, descuentos y modificaciones sensibles de precios.
- No se establece un porcentaje máximo de descuento autónomo para VEN, debido a que todavía no existe una política formal validada.
- Las condiciones de crédito se autorizan mediante GER.
- Los registros del proceso comercial deben permitir identificar la operación y, cuando corresponda, al usuario que realizó la autorización.

## 4. Análisis de responsabilidades de compras, inventario y despacho

| Actividad                                              | GER | VEN | ALM | CMP | FCO | SIS |
| ------------------------------------------------------ | --- | --- | --- | --- | --- | --- |
| Registro y mantenimiento de información de proveedores | V   | —   | —   | P/E | —   | —   |
| Preparación de solicitudes de presupuesto              | V   | —   | —   | P/E | —   | —   |
| Comparación de ofertas de proveedores                  | V   | —   | —   | P/E | —   | —   |
| Preparación de órdenes de compra                       | V   | —   | —   | P   | —   | —   |
| Autorización y confirmación de compras                 | A/E | —   | —   | P   | —   | —   |
| Recepción de productos                                 | V   | —   | E   | V   | —   | —   |
| Transferencias internas ordinarias                     | V   | —   | E   | —   | —   | —   |
| Conteos físicos de inventario                          | V   | —   | P/E | —   | —   | —   |
| Ajustes extraordinarios de existencias                 | A   | —   | P/E | —   | —   | —   |
| Preparación de pedidos para despacho                   | V   | P   | E   | —   | —   | —   |
| Seguimiento de entregas                                | V   | P/V | E   | —   | —   | —   |

### Consideraciones operativas

**Compras.** CMP prepara y gestiona las operaciones de abastecimiento. La autorización corresponde a GER. Ambos propietarios conservan la facultad de aprobar compras, aunque solamente la dueña tenga asignado CMP.

**Inventario.** ALM ejecuta recepciones, transferencias, conteos y actividades ordinarias de almacén. Los ajustes extraordinarios requieren autorización de GER.

**Despacho y logística.** Se mantiene pendiente precisar la distribución de responsabilidades relacionadas con programación del transporte, entrega, conformidad de recepción y guías de remisión. No se asignan estas actividades de manera definitiva sin validación.

## 5. Análisis de responsabilidades de facturación, contabilidad y cobranzas

Las siguientes responsabilidades forman parte del área funcional de **Facturación, Contabilidad y Cobros (FCO)**.

| Actividad                                                   | GER | VEN | ALM | CMP | FCO | SIS |
| ----------------------------------------------------------- | --- | --- | --- | --- | --- | --- |
| Preparación de información para facturación                 | V   | P   | —   | —   | E   | —   |
| Registro y seguimiento de facturas de clientes              | V   | —   | —   | —   | P/E | —   |
| Registro y seguimiento de facturas de proveedores           | V   | —   | —   | P   | P/E | —   |
| Registro y seguimiento de cobros                            | V   | E\* | —   | —   | P/E | —   |
| Registro y seguimiento de pagos a proveedores               | V   | —   | —   | —   | P/E | —   |
| Seguimiento de cuentas por cobrar                           | V   | —   | —   | —   | E   | —   |
| Seguimiento de cuentas por pagar                            | V   | —   | —   | —   | E   | —   |
| Consulta y revisión de registros contables                  | V   | —   | —   | —   | E   | —   |
| Conciliación de movimientos y pagos                         | V   | —   | —   | —   | P/E | —   |
| Preparación de reportes contables y financieros             | V   | —   | —   | —   | P/E | —   |
| Análisis de resultados financieros                          | V   | —   | —   | —   | P   | —   |
| Autorización de anulaciones y ajustes financieros sensibles | A   | —   | —   | —   | P   | —   |

\*VEN puede ejecutar cobros ordinarios de mostrador mediante Punto de Venta, conforme a los permisos de caja que se definan.

### Consideraciones contables y financieras

- FCO gestiona las operaciones ordinarias de facturación, cobros, pagos y seguimiento de saldos.
- FCO contempla la consulta de registros contables y la preparación de información financiera necesaria para el funcionamiento del negocio.
- GER supervisa las operaciones financieras y conserva la autorización de decisiones sensibles.
- La generación de reportes financieros y los permisos asociados deben validarse en la solución definitiva.
- Las funciones de registro, conciliación, reversión y ajuste pueden requerir diferentes niveles de acceso. La matriz de permisos deberá especificarlos.
- La aprobación de operaciones sensibles no debe confundirse con la simple posibilidad técnica de ejecutarlas en Odoo.

## 6. Administración técnica del sistema

SIS se encarga de las actividades técnicas necesarias para mantener y configurar Odoo.

| Actividad                                              | GER | SIS |
| ------------------------------------------------------ | --- | --- |
| Solicitar y autorizar altas o modificaciones de acceso | A   | E   |
| Crear y administrar usuarios                           | V   | E   |
| Configurar grupos y permisos                           | A   | E   |
| Configurar componentes y parámetros técnicos           | V   | E   |
| Aplicar mantenimiento técnico                          | V   | E   |
| Revisar incidencias técnicas y necesidades de acceso   | V   | P/E |

Las facultades técnicas de SIS no representan autorización para modificar precios, conceder créditos, aprobar compras o ejecutar decisiones financieras en nombre de GER.

## 7. Asignación de roles a personas

Se mantiene la distribución funcional definida para MIGAL.

| Persona           | Roles asignados         | Observaciones                                                                   |
| ----------------- | ----------------------- | ------------------------------------------------------------------------------- |
| **Dueña**         | GER, VEN, ALM, CMP, FCO | Gestiona compras y conserva facultades de gerencia y administración financiera. |
| **Dueño**         | GER, VEN, ALM, FCO      | Puede autorizar compras mediante GER, aunque no tenga CMP.                      |
| **Trabajador 1**  | VEN, ALM                | Participa en atención comercial y operaciones de almacén.                       |
| **Trabajador 2**  | ALM                     | Participa en operaciones de almacén y despacho.                                 |
| **Brenda Mirano** | SIS                     | Responsable inicial de la administración técnica del sistema.                   |

Una persona puede desempeñar varios roles, pero esta acumulación debe evaluarse al configurar los permisos para evitar accesos no deseados.

## 8. Restricciones y validaciones pendientes

La distribución anterior representa el diseño funcional previsto. Para su aplicación se requiere:

- Verificar los grupos de acceso disponibles en Odoo 18 Community.
- Validar los permisos efectivos de GER, VEN, ALM, CMP, FCO y SIS.
- Comprobar qué operaciones financieras puede realizar FCO sin facultades de administración técnica.
- Verificar las autorizaciones de compras, descuentos, créditos, anulaciones y ajustes extraordinarios.
- Comprobar el acceso a reportes contables y financieros según las responsabilidades asignadas.
- Definir controles cuando un propietario acumule funciones de preparación, ejecución y autorización.
- Precisar las responsabilidades logísticas y de emisión de guías de remisión.

La matriz detallada de permisos y los casos de prueba deberán utilizarse para demostrar qué restricciones pueden aplicarse mediante configuración y cuáles necesitan mecanismos adicionales.

Este análisis debe mantenerse alineado con el modelo de autorización, sin sustituir la matriz técnica de permisos ni asumir que las funcionalidades propuestas ya están implementadas.
