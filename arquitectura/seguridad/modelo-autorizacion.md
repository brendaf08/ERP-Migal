# Modelo de autorización y control de acceso

Este documento define los roles funcionales y administrativos propuestos para el sistema de información de **Ferre & Inversiones MIGAL**, sus responsabilidades, permisos generales y restricciones de acceso. Su finalidad es establecer quién puede realizar, consultar y autorizar las operaciones del sistema, de acuerdo con las necesidades del negocio y los principios de seguridad y segregación de funciones.

El modelo contempla las aplicaciones de **CRM, Contactos, Ventas, Punto de Venta, Inventario, Compras y Facturación** de Odoo 18 Community.&#x20;

Constituye la base funcional para la configuración de usuarios y grupos de acceso, así como para la elaboración de la matriz detallada de permisos.

---

## 1. Criterios del modelo de autorización

La asignación de permisos se fundamenta en los siguientes criterios:

- **Acceso por responsabilidades:** cada rol dispone de los permisos necesarios para desempeñar sus funciones.
- **Mínimo privilegio:** los usuarios no deben acceder a funciones o información ajenas a sus responsabilidades.
- **Segregación de funciones:** las operaciones sensibles deben contar con mecanismos de autorización y revisión.
- **Asignación flexible:** un usuario puede asumir más de un rol cuando sus responsabilidades lo justifiquen.
- **Trazabilidad:** las operaciones relevantes deben permitir identificar al usuario responsable y, cuando corresponda, al autorizador.

Los roles representan conjuntos de responsabilidades y permisos previstos para el sistema, y no necesariamente cargos o personas diferentes dentro de la organización.

## 2. Catálogo de roles

Se proponen seis roles para la administración y operación del sistema MIGAL.

| Código  | Rol                                | Responsabilidad principal                                                                          |
| ------- | ---------------------------------- | -------------------------------------------------------------------------------------------------- |
| **GER** | Gerencia                           | Supervisar las operaciones y autorizar decisiones comerciales, financieras y operativas sensibles. |
| **VEN** | Atención y Ventas                  | Gestionar clientes, oportunidades comerciales, cotizaciones y ventas.                              |
| **ALM** | Almacén y Despacho                 | Controlar existencias, recepciones, movimientos de inventario y entregas.                          |
| **CMP** | Compras y Abastecimiento           | Gestionar proveedores, solicitudes de presupuesto y preparación de órdenes de compra.              |
| **FCO** | Facturación, Contabilidad y Cobros | Gestionar facturación, pagos, cuentas pendientes, registros contables y seguimiento financiero.    |
| **SIS** | Administración del Sistema         | Administrar usuarios, grupos, permisos y configuraciones técnicas.                                 |

### Responsabilidades y límites por rol

**GER — Gerencia**

Supervisa las operaciones del negocio y autoriza negociaciones de precios y descuentos, modificaciones sensibles de precios, órdenes de compra, condiciones de crédito, ajustes extraordinarios de inventario y anulaciones restringidas.

En el ámbito financiero, supervisa los resultados, revisa las operaciones relevantes y autoriza los ajustes o decisiones sensibles que correspondan.

**Ambos propietarios pueden autorizar compras mediante GER**, aunque uno de ellos no tenga asignado CMP. GER no otorga por sí solo privilegios de administración técnica.

**VEN — Atención y Ventas**

Gestiona contactos comerciales, oportunidades, cotizaciones, pedidos y ventas ordinarias. Consulta precios y disponibilidad de productos y prepara cotizaciones con las condiciones vigentes.

Cuando un cliente solicita negociar precios o descuentos, deriva la decisión a Gerencia. Puede realizar cobros ordinarios de mostrador mediante Punto de Venta, conforme a los permisos de caja habilitados.

**ALM — Almacén y Despacho**

Gestiona recepciones, transferencias, preparación de pedidos, despachos y conteos físicos.

Las entradas y movimientos ordinarios no requieren autorización individual de Gerencia; los ajustes extraordinarios de existencias sí requieren su aprobación.

**CMP — Compras y Abastecimiento**

Gestiona información de proveedores, solicitudes de presupuesto, comparación de ofertas y preparación de órdenes de compra.

**Preparar y gestionar una compra (CMP) es distinto de autorizar su confirmación (GER)**. La confirmación que compromete a MIGAL con el proveedor está reservada a los propietarios mediante GER.

**FCO — Facturación, Contabilidad y Cobros**

Gestiona el registro y seguimiento de documentos de facturación, pagos, saldos, cuentas por cobrar y cuentas por pagar.

Incluye responsabilidades de consulta y gestión ordinaria de registros contables, conciliación de operaciones y preparación de información contable y financiera.

No autoriza nuevas condiciones crediticias, anulaciones sensibles ni ajustes extraordinarios cuya aprobación corresponda a Gerencia.

Se diferencia de VEN porque abarca el control administrativo y contable de las operaciones, no solamente el cobro ordinario en Punto de Venta.

La distribución de operaciones entre Odoo y KeyFacil permanece por definir.

**SIS — Administración del Sistema**

Administra usuarios, grupos, permisos, componentes y parámetros técnicos de Odoo.

Sus privilegios no constituyen autorización comercial o financiera. El responsable inicial de este rol es **Brenda Mirano**.

## 3. Permisos generales por aplicación o área funcional

La siguiente matriz representa el alcance funcional previsto. No acredita permisos ya configurados ni probados en Odoo.

| Aplicación / Área funcional                                | GER                                          | VEN                          | ALM                   | CMP                          | FCO                                                          | SIS        |
| ---------------------------------------------------------- | -------------------------------------------- | ---------------------------- | --------------------- | ---------------------------- | ------------------------------------------------------------ | ---------- |
| CRM                                                        | Supervisar                                   | Gestionar                    | —                     | —                            | —                                                            | Configurar |
| Contactos                                                  | Supervisar                                   | Gestionar clientes           | Consultar             | Gestionar proveedores        | Consultar                                                    | Configurar |
| Ventas                                                     | Supervisar y autorizar                       | Gestionar                    | Consultar pedidos     | Consultar demanda            | Consultar                                                    | Configurar |
| Punto de Venta                                             | Supervisar                                   | Operar                       | —                     | —                            | Revisar caja                                                 | Configurar |
| Inventario                                                 | Supervisar y autorizar                       | Consultar                    | Operar                | Consultar                    | Consultar                                                    | Configurar |
| Compras                                                    | Supervisar y autorizar                       | —                            | Consultar recepciones | Gestionar                    | Consultar                                                    | Configurar |
| Facturación (incluye funciones de Contabilidad y Finanzas) | Supervisar y autorizar operaciones sensibles | Consultar estados necesarios | —                     | Consultar estados necesarios | Gestionar operaciones contables y de facturación autorizadas | Configurar |

**Interpretación:**

- **Gestionar / Operar:** ejecutar las actividades ordinarias autorizadas para el rol.
- **Consultar:** visualizar la información necesaria para su función.
- **Supervisar:** revisar operaciones, estados e información de control.
- **Autorizar:** aprobar operaciones expresamente restringidas.
- **Configurar:** administrar parámetros técnicos y mecanismos de acceso.
- **—:** sin acceso funcional previsto de manera predeterminada.

Las responsabilidades de Contabilidad y Finanzas forman parte del alcance funcional de Facturación. Esto no implica que todas sus funciones estén disponibles para todos los usuarios ni que se otorguen automáticamente permisos contables amplios.

## 4. Autorizaciones y restricciones

| Operación                                                    | Responsable operativo                             | Autorización                                                  |
| ------------------------------------------------------------ | ------------------------------------------------- | ------------------------------------------------------------- |
| Negociación de descuentos o precios especiales               | VEN prepara la cotización y deriva la negociación | GER negocia y autoriza                                        |
| Modificación de precios maestros                             | VEN puede solicitar el cambio                     | GER autoriza la modificación                                  |
| Confirmación de órdenes de compra                            | CMP prepara la orden                              | GER confirma; ambos propietarios conservan esta facultad      |
| Ajustes extraordinarios de inventario                        | ALM identifica o reporta la diferencia            | GER autoriza                                                  |
| Otorgamiento o modificación de créditos                      | VEN o FCO comunica la solicitud                   | GER decide y autoriza                                         |
| Registro ordinario de facturas, cobros y pagos               | FCO ejecuta las operaciones de su competencia     | Sin aprobación individual de GER, salvo excepciones definidas |
| Consulta y revisión de registros contables                   | FCO realiza las actividades autorizadas           | GER supervisa                                                 |
| Conciliación ordinaria de operaciones                        | FCO ejecuta según los permisos establecidos       | GER supervisa y revisa excepciones                            |
| Anulación o ajuste extraordinario de operaciones financieras | FCO prepara o solicita la operación               | GER autoriza                                                  |
| Revisión de resultados financieros                           | FCO prepara la información                        | GER supervisa y evalúa                                        |
| Modificación de usuarios y permisos                          | SIS ejecuta                                       | GER autoriza la solicitud                                     |

### Condiciones de aplicación

- **Descuentos:** el personal de ventas utiliza los precios establecidos; cualquier negociación especial con el cliente se deriva al propietario. No se establece un porcentaje autónomo de descuento para VEN.
- **Compras:** CMP prepara y gestiona las órdenes; GER las autoriza y confirma. **El dueño mantiene la facultad de autorización mediante GER, aunque no tenga CMP.**
- **Créditos:** únicamente Gerencia decide sobre su otorgamiento y modificación.
- **Inventario:** ALM realiza las recepciones y movimientos ordinarios; los ajustes extraordinarios requieren autorización de Gerencia.
- **Facturación y cobros:** FCO realiza las operaciones administrativas y contables ordinarias que correspondan a sus responsabilidades.
- **Contabilidad y Finanzas:** FCO gestiona y consulta la información contable autorizada; GER supervisa y conserva las decisiones financieras sensibles.
- **Reportes financieros:** el acceso debe limitarse según las responsabilidades del rol y validarse cuando las funcionalidades correspondientes estén disponibles.

Las operaciones ordinarias no deben depender de aprobaciones innecesarias. Los procedimientos específicos se documentarán en los procesos correspondientes; su aplicación técnica deberá comprobarse en Odoo.

## 5. Asignación y combinación de roles

Los roles se asignan a usuarios individuales según sus responsabilidades. Una persona puede tener varios roles cuando sus actividades lo justifiquen.

| Usuario       | Roles asignados             | Alcance / aclaración                                                           |
| ------------- | --------------------------- | ------------------------------------------------------------------------------ |
| Dueña         | **GER, VEN, ALM, CMP, FCO** | Gestiona y autoriza compras; tiene acceso funcional amplio, sin SIS.           |
| Dueño         | **GER, VEN, ALM, FCO**      | No gestiona Compras mediante CMP, **pero sí puede autorizarlas mediante GER**. |
| Trabajador 1  | **VEN, ALM**                | Atención comercial, ventas y operaciones de almacén.                           |
| Trabajador 2  | **ALM**                     | Inventario y despacho.                                                         |
| Brenda Mirano | **SIS**                     | Responsable inicial de la administración técnica del sistema.                  |

Esta asignación es una definición funcional inicial y no implica que los usuarios o grupos ya estén configurados.

La combinación de roles no debe servir para eludir controles de autorización; cuando no sea viable separar funciones, se deberán definir medidas de revisión y trazabilidad.

## 6. Implementación y validación

El modelo deberá contrastarse con los grupos de seguridad y mecanismos de control de acceso disponibles en Odoo 18 Community.

La acumulación de grupos puede ampliar los permisos de un usuario, y ciertas restricciones ,incluida la separación entre gestión y aprobación de compras, podrían requerir configuración o personalización adicional.

En el ámbito de Facturación, Contabilidad y Finanzas, deberá comprobarse particularmente:

- Que FCO pueda realizar las operaciones ordinarias previstas sin recibir permisos administrativos innecesarios.
- Que GER pueda supervisar la información financiera y autorizar operaciones sensibles.
- Que SIS pueda administrar técnicamente el sistema sin disponer de autorización funcional para las decisiones financieras.
- Que las operaciones contables sensibles estén sujetas a los controles establecidos.
- Que los reportes financieros sean accesibles únicamente a los usuarios autorizados.
- Que los permisos se verifiquen con usuarios representativos, no solamente con un administrador de pruebas.

Los permisos específicos por aplicación, operación y tipo de acceso se detallarán en [matriz-permisos.xlsx](matriz-permisos.xlsx).

Las cuestiones abiertas y las pruebas por realizar se seguirán en el [registro de pendientes](../../producto/registro-pendientes.md), incluida la definición del intercambio de información entre Odoo y KeyFacil.

Las decisiones documentadas aquí deberán actualizarse si cambian las responsabilidades del negocio o si las pruebas técnicas obligan a revisar el modelo.
