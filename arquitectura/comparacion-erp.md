# Comparación de sistemas ERP

Este documento compara las capacidades, limitaciones, costos y condiciones de implementación de los ERP evaluados para **Ferre & Inversiones MIGAL**, proporcionando evidencia para la decisión arquitectónica de selección de plataforma.

## 1. Bases de evaluación

### 1.1. Alternativas consideradas

| Alternativa | Producto evaluado | Modelo |
|---|---|---|
| **StarSoft** | ERP PYMES y Gold Edition | Software comercial peruano. |
| **Odoo** | Odoo Community | Plataforma modular de código abierto. |
| **Microsoft Dynamics 365** | Business Central Essentials | ERP comercial por suscripción. |

La comparación se realiza entre productos y ediciones específicos. No se considera incluida una funcionalidad que dependa de otro producto, una extensión comercial o una contratación adicional.

### 1.2. Necesidades de MIGAL

MIGAL cuenta con una tienda, dos almacenes, dos propietarios, dos trabajadores y un catálogo superior a mil productos.

Sus necesidades principales comprenden:

- **CRM y ventas:** gestionar clientes, consultas, oportunidades, cotizaciones, ventas de mostrador y pedidos.
- **Inventario:** controlar existencias, ubicaciones y movimientos de productos.
- **Compras:** gestionar proveedores, abastecimiento y recepción de materiales.
- **Finanzas:** registrar facturas, cobranzas, pagos, obligaciones y resultados económicos.
- **Cumplimiento peruano:** atender los requerimientos tributarios aplicables.
- **Continuidad:** disponer de un sistema sostenible más allá del proyecto académico.

La evaluación considera tanto las funcionalidades como los recursos necesarios para implementarlas y mantenerlas.

### 1.3. Criterios

| Criterio | Prioridad | Aspectos evaluados |
|---|---|---|
| Cobertura funcional | Crítica | Procesos comerciales, operativos y financieros. |
| Integración | Crítica | Continuidad de información entre módulos. |
| Adecuación peruana | Crítica | Facturación, contabilidad y requisitos SUNAT. |
| Costo total | Crítica | Licencias, implementación, infraestructura y mantenimiento. |
| Ventas minoristas | Alta | POS, caja, medios de pago y ventas rápidas. |
| Inventario | Alta | Múltiples ubicaciones, reservas, transferencias y valorización. |
| Extensibilidad | Alta | Configuración, integraciones y desarrollos adicionales. |
| Soporte y mantenimiento | Alta | Asistencia, actualizaciones y continuidad técnica. |
| Usabilidad | Alta | Facilidad de adopción por propietarios y trabajadores. |
| Escalabilidad | Media | Incorporación futura de usuarios, procesos y funcionalidades. |

La comparación es cualitativa: no se asignan puntuaciones numéricas sin pruebas equivalentes y datos económicos completos.

## 2. Análisis de alternativas

### 2.1. StarSoft

StarSoft es una empresa peruana que comercializa soluciones ERP orientadas al mercado nacional. Se consideran sus ediciones **PYMES** y **Gold Edition**.

#### Capacidades disponibles

| Componente | Funcionalidades documentadas |
|---|---|
| **Ventas** | Cotizaciones, pedidos, boletas, facturas, notas de crédito, tickets, caja y puntos de venta. |
| **Inventarios** | Múltiples almacenes, inventarios físicos, Kardex, valorización, códigos de barras y productos equivalentes. |
| **Compras** | Requisiciones, solicitudes de cotización, órdenes y seguimiento a proveedores. |
| **Contabilidad** | Asientos, libros contables, estados financieros y registros asociados a obligaciones peruanas. |
| **Facturación electrónica** | FACTRON para emisión de documentos electrónicos. |
| **Cobranzas** | Estados de cuenta, límites de crédito, morosidad y documentos pendientes. |
| **Administración** | Caja, bancos, cuentas por pagar e informes gerenciales. |

Su principal característica es la orientación a operaciones empresariales y tributarias peruanas.

#### Diferencias entre PYMES y Gold Edition

StarSoft anuncia los mismos trece módulos principales para ambas ediciones, pero su matriz comercial identifica diferencias en herramientas complementarias.

| Capacidad | PYMES | Gold Edition |
|---|---|---|
| Módulos empresariales principales | Disponibles | Disponibles |
| Portal web transaccional para contadores | No incluido | Incluido |
| Portal web de almacenes | No incluido | Incluido |
| Portal web de aprobaciones de compras | No incluido | Incluido |
| Portal B2B para clientes y proveedores | No incluido | Incluido |
| Portal de pedidos y ventas móviles | No incluido | Incluido |
| Herramientas OLAP y paneles web adicionales | Limitadas | Disponibles según componente |
| Comercio electrónico dentro de la oferta comparada | No incluido | Incluido |

Estas diferencias no permiten concluir que PYMES carezca de inventarios, compras o ventas. Significan que determinadas **interfaces y servicios complementarios** son propios de Gold Edition.

#### Limitaciones y aspectos no comprobados

| Aspecto | Hallazgo | Implicancia |
|---|---|---|
| **CRM** | No se confirmó un módulo específico de leads, oportunidades y embudo comercial equivalente al flujo considerado para MIGAL. | Requiere demostración funcional; no se afirma que sea imposible implementarlo. |
| **Licenciamiento** | La información pública no permite determinar el precio final de la configuración requerida. | Es necesario cotizar usuarios, módulos, instalación y servicios. |
| **Código fuente** | No se identificó disponibilidad de código abierto comparable a Community. | Las modificaciones pueden depender de herramientas y condiciones del proveedor. |
| **APIs** | Gold Edition publica una API REST para operaciones contables con JSON o XML, que exige licencia activa. | No debe suponerse que existe una API equivalente para todos los módulos. |
| **Soporte** | Se anuncian soporte y actualizaciones, sujetos a las condiciones comerciales efectivamente contratadas. | Deben verificarse alcance, tiempos de atención y costos de renovación. |
| **Despliegue** | Las modalidades y requisitos dependen de la solución contratada. | Requiere confirmar infraestructura y responsabilidades de administración. |

#### Ventajas

- Orientación directa al mercado peruano.
- Cobertura relevante de contabilidad, facturación electrónica e inventarios.
- Funcionalidades para ventas, créditos, cobranzas y caja.
- Servicios de asistencia y capacitación comercializados por el proveedor.
- Menor necesidad potencial de desarrollar componentes tributarios desde cero.

#### Desventajas y riesgos

- Dependencia comercial y técnica del proveedor.
- Costos de implementación y mantenimiento no cuantificados.
- Diferencias funcionales entre ediciones que deben revisarse antes de contratar.
- Menor autonomía para realizar adaptaciones directamente sobre el producto.
- Cobertura del CRM requerido todavía no demostrada.

**Hallazgo:** StarSoft dispone de una oferta funcionalmente relevante para MIGAL, especialmente en contabilidad peruana y ventas minoristas. Su conveniencia completa depende de conocer el costo contractual y comprobar los procesos comerciales requeridos.

### 2.2. Odoo Community

Odoo Community es una plataforma ERP gratuita y de código abierto. Su arquitectura permite integrar diversas aplicaciones empresariales y ampliarlas mediante módulos compatibles.

#### Capacidades disponibles

| Componente | Funcionalidades documentadas |
|---|---|
| **CRM** | Leads, oportunidades, actividades y seguimiento comercial. |
| **Contactos** | Registro compartido de personas, empresas y relaciones comerciales. |
| **Ventas** | Cotizaciones, pedidos, productos, tarifas y condiciones comerciales. |
| **Punto de Venta** | Ventas de mostrador, sesiones, caja y medios de pago. |
| **Inventario** | Almacenes, ubicaciones, existencias, transferencias y movimientos. |
| **Compras** | Proveedores, solicitudes de cotización, órdenes y recepciones. |
| **Facturación** | Facturas de clientes, facturas de proveedores, pagos y registros contables asociados. |
| **Extensibilidad** | Módulos comunitarios, desarrollos propios y mecanismos de integración. |

La plataforma facilita compartir información entre aplicaciones sin utilizar necesariamente sistemas independientes.

#### Funcionalidades limitadas o no incluidas

| Aspecto | Situación en Community | Implicancia |
|---|---|---|
| **Contabilidad integral** | No incluye toda la funcionalidad avanzada de Contabilidad de Enterprise. | Requiere evaluar complementos y comprobar la cobertura real. |
| **Reportes financieros** | Los informes estándar avanzados pueden estar limitados frente a Enterprise. | Pueden utilizarse módulos comunitarios adicionales. |
| **Odoo Studio** | Funcionalidad propia de Enterprise. | Las personalizaciones deben realizarse con herramientas alternativas o desarrollo. |
| **Soporte funcional del fabricante** | No incluido gratuitamente. | Requiere soporte comunitario, equipo propio o contratación externa. |
| **Alojamiento administrado** | No incluido por utilizar Community. | MIGAL o su proveedor debe administrar la infraestructura. |
| **Migraciones entre versiones** | No se incluye un servicio automático de migración de Community. | Se necesita un procedimiento técnico y pruebas. |
| **Facturación electrónica peruana** | La documentación general contempla localizaciones peruanas, pero la cobertura íntegra en Community no está demostrada. | Deben verificarse módulos, licencias, servicios y requisitos específicos. |

La edición Community no debe confundirse con una edición de prueba de Enterprise. Son productos con diferencias funcionales y de servicios.

#### Complementos financieros

Existen módulos de la **Odoo Community Association (OCA)** que permiten ampliar los reportes financieros.

Para Odoo 19 están publicados:

- `account_financial_report`: conjunto de informes financieros.
- `mis_builder`: construcción de reportes e indicadores personalizados.
- `mis_builder_budget`: funciones adicionales relacionadas con presupuestos.

Estos componentes no forman parte necesariamente de la instalación estándar.

Su disponibilidad pública tampoco garantiza que estén configurados, probados o que cubran todas las necesidades contables de MIGAL. Deben revisarse sus dependencias y licencias.

#### Localización peruana

La documentación general de Odoo contempla módulos para el contexto peruano, entre ellos:

- `l10n_pe`: configuración contable peruana.
- `l10n_pe_edi`: facturación electrónica.
- `l10n_pe_reports`: reportes tributarios.
- `l10n_pe_edi_stock`: guías de remisión electrónicas.
- `l10n_pe_pos`: funcionalidades peruanas relacionadas con POS.

Sin embargo, **la existencia de un módulo en la documentación general no confirma su disponibilidad y funcionamiento en Community**. Algunos componentes dependen de funcionalidades, servicios o condiciones específicas de la edición.

Por tanto, no debe afirmarse que la instalación Community cubre íntegramente SUNAT sin pruebas adicionales.

#### Restricciones operativas relevantes

**Punto de Venta sin conexión**

Odoo documenta operaciones de POS durante interrupciones temporales de Internet. No obstante, existen restricciones:

- Las operaciones que requieren el servidor pueden no estar disponibles.
- La generación de facturas puede quedar pendiente hasta recuperar conectividad.
- Las órdenes sin sincronizar dependen temporalmente de los datos almacenados en el navegador.
- Cerrar o recargar el navegador antes de sincronizar puede comprometer la información pendiente.

La disponibilidad del modo sin conexión no equivale a continuidad completa de todas las aplicaciones del ERP.

**Mantenimiento y actualizaciones**

Una instalación propia debe recibir actualizaciones de seguridad y correcciones, además de contar con respaldos.

También se deben distinguir:

- **Actualización de mantenimiento:** aplicar correcciones dentro de la misma versión principal.
- **Migración:** adaptar la base de datos y los componentes para utilizar una versión principal posterior.

Ambas operaciones pueden requerir intervención técnica.

#### Ventajas

- Ausencia de licencias recurrentes de Community.
- Aplicaciones empresariales integradas.
- Acceso al código fuente y documentación técnica pública.
- Amplias posibilidades de extensión.
- Implementación gradual.
- Menor dependencia de un único proveedor para desarrollar funcionalidades.

#### Desventajas y riesgos

- Responsabilidad directa sobre infraestructura y mantenimiento.
- Dependencia de conocimientos técnicos para administración y personalización.
- Limitaciones frente a Enterprise en determinadas funcionalidades.
- Compatibilidad y mantenimiento de módulos de terceros.
- Incertidumbre sobre la cobertura tributaria peruana completa.
- Posibilidad de que el costo de personalizaciones reduzca la ventaja inicial de licenciamiento.

**Hallazgo:** Odoo Community ofrece una plataforma integrada y flexible, pero su viabilidad empresarial depende de resolver las necesidades contables y tributarias y asegurar mantenimiento técnico continuo.

### 2.3. Microsoft Dynamics 365 Business Central

Business Central es un ERP comercial de Microsoft orientado a la gestión financiera, comercial y operativa.

La evaluación considera principalmente **Business Central Essentials**, diferenciándolo de Business Central Premium y de otras aplicaciones de Dynamics 365.

#### Capacidades disponibles

| Componente | Funcionalidades documentadas |
|---|---|
| **Finanzas** | Contabilidad, cuentas por cobrar y pagar, registros financieros y conciliación. |
| **Ventas** | Clientes, cotizaciones, pedidos y facturación. |
| **Relaciones comerciales** | Contactos, interacciones, oportunidades y ciclos de venta. |
| **Inventario** | Productos, atributos, existencias, reservas y trazabilidad. |
| **Almacenes** | Ubicaciones, transferencias y operaciones de almacén. |
| **Compras** | Proveedores, órdenes de compra y obligaciones. |
| **Integración** | APIs, extensiones y servicios del ecosistema Microsoft. |
| **Administración** | Actualizaciones y servicios de infraestructura en la modalidad Online. |

Business Central incluye funciones de gestión de oportunidades, aunque las capacidades especializadas de **Dynamics 365 Sales** pertenecen a otro producto.

#### Funcionalidades limitadas o adicionales

| Aspecto | Situación en Essentials | Implicancia |
|---|---|---|
| **POS minorista** | No se identificó una aplicación POS minorista equivalente a Odoo POS dentro de la funcionalidad estándar evaluada. | Requiere evaluar extensiones comerciales. |
| **Localización peruana** | Perú figura como mercado localizado mediante partners. | Debe identificarse la extensión tributaria apropiada y su costo. |
| **CRM especializado** | Incluye contactos y oportunidades, pero no toda la funcionalidad de Dynamics 365 Sales. | Algunas necesidades comerciales avanzadas pueden requerir otra licencia. |
| **Fabricación y gestión avanzada de servicios** | Funcionalidades adicionales de Premium. | No forman parte del alcance estándar de Essentials. |
| **Personalización** | Mediante extensiones y herramientas especializadas. | Puede requerirse personal con conocimientos de AL y Business Central. |
| **Licenciamiento** | Suscripción comercial. | Genera costos recurrentes por usuarios y servicios. |

#### Modelo económico

Los precios públicos de referencia de Microsoft son:

| Licencia | Precio de referencia |
|---|---|
| Business Central Essentials | US$ 80 por usuario al mes |
| Business Central Premium | US$ 110 por usuario al mes |
| Business Central Team Members | US$ 8 por usuario al mes |

Los precios se presentan con facturación anual y antes de impuestos. Team Members tiene permisos limitados y no sustituye automáticamente a un usuario Essentials.

El costo final de MIGAL dependería de los usuarios que requieran acceso, las licencias apropiadas, la localización peruana, el POS y los servicios de implementación.

#### Dependencias técnicas y comerciales

**Punto de Venta**

Existen soluciones de terceros orientadas a integrar operaciones minoristas con Business Central, como productos de LS Retail.

Sin embargo, estas soluciones implican revisar su licenciamiento, compatibilidad, mantenimiento y cobertura funcional.

**Localización peruana**

Microsoft identifica a Perú como un mercado atendido mediante partners. Esto permite utilizar soluciones locales, pero no significa que la suscripción estándar incluya automáticamente todas las funcionalidades de SUNAT.

**Mantenimiento**

Business Central Online permite delegar parte de la administración de infraestructura y actualizaciones a Microsoft.

Esto reduce ciertas responsabilidades técnicas, pero no elimina la necesidad de gestionar usuarios, datos, extensiones, configuraciones y procedimientos internos.

#### Ventajas

- Cobertura financiera y administrativa amplia.
- Gestión comercial e inventario integrados.
- Infraestructura administrada en modalidad Online.
- Ecosistema empresarial consolidado.
- Documentación y servicios especializados.
- Posibilidad de extender funcionalidades mediante aplicaciones compatibles.

#### Desventajas y riesgos

- Licenciamiento recurrente.
- Dependencia de partners para localización peruana y determinados servicios.
- Posible necesidad de una solución POS adicional.
- Costos de implementación y extensión no incluidos en el precio base.
- Mayor dependencia comercial de Microsoft y su ecosistema.
- Necesidad de revisar la compatibilidad de extensiones durante actualizaciones.

**Hallazgo:** Business Central presenta una cobertura empresarial sólida, pero la venta minorista, la localización peruana y las licencias introducen dependencias adicionales relevantes para una empresa pequeña.

## 3. Matriz comparativa de capacidades

### 3.1. Cobertura funcional

La clasificación utilizada es:

- **Incluido:** funcionalidad documentada dentro de la alternativa evaluada.
- **Parcial:** capacidad disponible, pero con limitaciones respecto al requerimiento.
- **Adicional:** requiere un componente, servicio o licencia independiente.
- **Por verificar:** no existe evidencia suficiente para confirmar el alcance.

| Necesidad de MIGAL | StarSoft | Odoo Community | Business Central Essentials |
|---|---|---|---|
| Contactos y clientes | Incluido | Incluido | Incluido |
| Leads y oportunidades | Por verificar | Incluido | Incluido |
| Cotizaciones y pedidos | Incluido | Incluido | Incluido |
| Ventas de mostrador y POS | Incluido | Incluido | Adicional |
| Gestión de caja | Incluido | Incluido | Incluido; integración POS por verificar |
| Inventario multialmacén | Incluido | Incluido | Incluido |
| Transferencias internas | Incluido | Incluido | Incluido |
| Conteos y ajustes | Incluido | Incluido | Incluido |
| Compras y proveedores | Incluido | Incluido | Incluido |
| Cuentas por cobrar | Incluido | Parcial según controles requeridos | Incluido |
| Cuentas por pagar | Incluido | Parcial según controles requeridos | Incluido |
| Contabilidad integral | Incluido | Parcial | Incluido |
| Informes financieros avanzados | Incluido | Adicional | Incluido |
| Facturación electrónica peruana | FACTRON; contratación por verificar | Por verificar | Adicional |
| Guías de remisión electrónicas | Alcance por verificar | Por verificar | Por verificar |
| Código fuente abierto | No confirmado | Incluido | No incluido |
| Extensiones y desarrollos | Según herramientas y servicios del proveedor | Incluido | Incluido mediante extensiones |
| Soporte funcional personalizado | Según contratación | No incluido gratuitamente | Según suscripción y servicios |
| Alojamiento administrado incluido | Según contrato | No incluido | Incluido en Online |

**Importante:** «Incluido» representa una capacidad documentada, no una prueba funcional ejecutada en MIGAL.

### 3.2. Diferencias técnicas y operativas

| Criterio | StarSoft | Odoo Community | Business Central |
|---|---|---|---|
| Modelo tecnológico | Software comercial del proveedor | Código abierto y arquitectura modular | Plataforma comercial y extensible |
| Independencia del fabricante | Limitada por condiciones comerciales | Mayor autonomía sobre código y despliegue | Limitada por licenciamiento y servicios |
| Integración de aplicaciones | Módulos integrados de la suite | Modelos y aplicaciones compartidas | Procesos integrados y APIs |
| Integraciones externas | Interfaces documentadas de alcance específico | APIs y desarrollos propios | APIs y extensiones |
| Responsabilidad técnica | Según proveedor y contrato | MIGAL o proveedor contratado | Microsoft y partners según servicio |
| Actualizaciones | Según producto y contrato | Administración propia o contratada | Administradas en Online, con seguimiento de extensiones |
| Documentación pública | Funcional y comercial; detalles técnicos adicionales por solicitar | Amplia documentación oficial y código público | Amplia documentación oficial |
| Adaptación a requerimientos propios | Servicios y herramientas del proveedor | Configuración, módulos y desarrollo | Configuración y extensiones especializadas |

## 4. Evaluación económica y de riesgos

### 4.1. Costo total de propiedad

El costo de un ERP comprende más que su licencia.

| Componente | StarSoft | Odoo Community | Business Central |
|---|---|---|---|
| Licencia de software | Comercial; cotización requerida | Sin licencia recurrente de Community | Suscripción comercial |
| Instalación | Según proveedor y modalidad | Equipo propio o servicio contratado | Partner o equipo especializado |
| Infraestructura | Según contrato | MIGAL o proveedor de alojamiento | Incluida en modalidad Online |
| Migración de datos | Servicio o trabajo adicional | Trabajo técnico propio o contratado | Servicio o trabajo de implementación |
| Personalización | Según contrato | Desarrollo propio o de terceros | Extensiones y servicios especializados |
| Capacitación | Según contratación | Equipo interno o servicio externo | Partner o recursos especializados |
| Soporte | Según contrato | Comunitario o contratado | Según servicios y condiciones |
| Actualizaciones futuras | Según contrato | Gestión técnica propia o contratada | Plataforma Online administrada; extensiones bajo seguimiento |

La información disponible no permite construir una comparación exacta del costo total a tres o cinco años.

Por ello, **no debe confundirse la ausencia de licencias recurrentes de Odoo Community con ausencia de costos operativos**.

### 4.2. Riesgos comparados

| Riesgo | Alternativas expuestas | Consecuencia potencial |
|---|---|---|
| Licencias recurrentes elevadas para el tamaño de la empresa | Business Central; StarSoft según cotización | Mayor gasto fijo. |
| Dependencia de proveedor | StarSoft y Business Central | Menor autonomía ante cambios o nuevos requerimientos. |
| Dependencia de conocimientos técnicos propios | Odoo Community | Dificultad de mantenimiento sin personal capacitado. |
| Complementos incompatibles tras actualizaciones | Odoo y Business Central | Retrabajos o interrupciones funcionales. |
| Cobertura contable insuficiente en edición base | Odoo Community | Necesidad de módulos adicionales o procesos complementarios. |
| POS no integrado de forma estándar | Business Central | Costos y mantenimiento de una extensión. |
| Cobertura tributaria pendiente de validación | Odoo Community y Business Central | Necesidad de soluciones adicionales o coexistencia con sistemas externos. |
| Costos contractuales no cuantificados | StarSoft | Dificultad para comparar la inversión real. |
| Baja adopción por los trabajadores | Todas | Uso parcial del ERP y permanencia de registros paralelos. |
| Pérdida de datos o interrupción del servicio | Todas | Afectación de ventas, almacén y administración. |

### 4.3. Sostenibilidad posterior al proyecto académico

| Alternativa | Principal condición de continuidad |
|---|---|
| **StarSoft** | Mantener condiciones de licenciamiento, soporte y servicios del proveedor. |
| **Odoo Community** | Disponer de administración técnica, respaldos, actualizaciones y mantenimiento de complementos. |
| **Business Central** | Mantener suscripciones, gestionar extensiones y contar con soporte de los servicios contratados. |

Ninguna alternativa garantiza continuidad únicamente por disponer de funcionalidades suficientes. También se necesita capacidad operativa, responsables definidos y recursos de mantenimiento.

## 5. Síntesis comparativa

La investigación identifica diferencias relevantes entre las alternativas:

| Dimensión | Hallazgo |
|---|---|
| **Adecuación tributaria peruana** | StarSoft destaca por sus soluciones contables y de facturación electrónica orientadas al mercado nacional. |
| **Flexibilidad tecnológica** | Odoo Community proporciona código abierto y mayor libertad para desarrollar y modificar componentes. |
| **Gestión financiera integrada** | StarSoft y Business Central ofrecen capacidades contables amplias dentro de sus productos comerciales. |
| **Ventas minoristas** | StarSoft y Odoo documentan funcionalidades de punto de venta; Business Central requiere evaluar soluciones adicionales. |
| **Costos de licenciamiento** | Odoo Community no tiene licencias recurrentes; Business Central utiliza suscripciones; StarSoft requiere cotización. |
| **Mantenimiento administrado** | Business Central Online ofrece administración de infraestructura y actualizaciones; StarSoft dispone de servicios contractuales; Odoo Community requiere gestión técnica propia o contratada. |
| **Dependencia del proveedor** | StarSoft y Business Central presentan mayor dependencia comercial; Odoo reduce esta dependencia, pero aumenta las responsabilidades técnicas. |
| **Información aún insuficiente** | Faltan costos totales comparables, pruebas funcionales equivalentes y validaciones tributarias específicas. |

Cada plataforma presenta ventajas acompañadas de compromisos:

- **StarSoft:** fortalece la adecuación administrativa y tributaria peruana, con dependencia de las condiciones comerciales del proveedor.
- **Odoo Community:** ofrece flexibilidad, integración y autonomía tecnológica, a cambio de mayores responsabilidades de mantenimiento y posibles complementos.
- **Business Central:** proporciona gestión empresarial y servicios administrados, con costos recurrentes y posibles dependencias de extensiones o partners.

La comparación no establece una superioridad universal ni sustituye la decisión arquitectónica. La selección de plataforma y sus fundamentos se registran en el [ADR-001](decisiones/ADR-001-seleccion-erp.md).

## 6. Fuentes y limitaciones de la investigación

### 6.1. Fuentes principales

**Fecha de revisión:** 28 de octubre de 2026.

| Plataforma | Fuente | Información utilizada |
|---|---|---|
| StarSoft | [Catálogo de productos](https://www.starsoft.com.pe/productos.php) | Oferta empresarial y módulos disponibles. |
| StarSoft | [Gold Edition](https://www.starsoft.com.pe/prod_erp_gold_edition.html) | Funciones de inventarios, ventas, compras y finanzas. |
| StarSoft | [PYMES](https://www.starsoft.com.pe/producto-pymes.php) | Oferta de módulos de la edición PYMES. |
| StarSoft | [Comparación Gold y PYMES](https://www.starsoft.com.pe/cuadro_comparativo_gold_y_pymes.html) | Diferencias entre ediciones. |
| StarSoft | [API de integración](https://starsoftweb.com/apisintegracion/) | Integración contable y requisitos de licencia. |
| Odoo | [Comparación de ediciones](https://www.odoo.com/page/editions) | Community frente a Enterprise. |
| Odoo | [Contabilidad y Facturación](https://www.odoo.com/documentation/19.0/es_419/applications/finance/accounting.html) | Diferencias entre las aplicaciones financieras. |
| Odoo | [Localización de Perú](https://www.odoo.com/documentation/19.0/applications/finance/fiscal_localizations/peru.html) | Módulos fiscales y sus funciones. |
| Odoo | [POS sin conexión](https://www.odoo.com/documentation/19.0/applications/sales/point_of_sale/use.html) | Restricciones de operación sin Internet. |
| Odoo | [Actualizaciones de instalación propia](https://www.odoo.com/documentation/19.0/administration/on_premise/update.html) | Mantenimiento y correcciones. |
| OCA | [Financial Reporting 19.0](https://github.com/OCA/account-financial-reporting/blob/19.0/README.md) | Disponibilidad de módulos de reportes. |
| OCA | [MIS Builder 19.0](https://github.com/OCA/mis-builder/blob/19.0/README.md) | Herramientas de informes personalizados. |
| Microsoft | [Precios y planes](https://www.microsoft.com/en-us/dynamics-365/products/business-central) | Licenciamiento de Business Central. |
| Microsoft | [Guía de licenciamiento](https://www.microsoft.com/licensing/guidance/Dynamics-365-Business-Central) | Funcionalidades por edición. |
| Microsoft Learn | [Gestión de oportunidades](https://learn.microsoft.com/en-us/dynamics365/business-central/marketing-manage-sales-opportunities) | CRM y procesos comerciales. |
| Microsoft Learn | [Inventarios y transferencias](https://learn.microsoft.com/en-us/dynamics365/business-central/inventory-how-transfer-between-locations) | Movimientos entre almacenes. |
| Microsoft Learn | [Disponibilidad por país](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/compliance/apptest-countries-and-translations) | Localización de Perú mediante partners. |
| LS Retail | [Extensibilidad de LS Express](https://help.lsexpress.lsretail.com/Content/Extend-Verticalize.htm) | Dependencias de una solución POS adicional. |

### 6.2. Limitaciones de la evidencia

- La información publicada por fabricantes describe capacidades y servicios, pero no equivale a pruebas ejecutadas en MIGAL.
- No se realizaron pruebas piloto equivalentes con StarSoft y Business Central.
- No existen cotizaciones completas que permitan comparar costos totales de implementación y mantenimiento.
- Determinadas capacidades pueden variar según edición, contratación, versión y complementos instalados.
- La disponibilidad de localizaciones y módulos no garantiza su funcionamiento para los requerimientos específicos de MIGAL.

### 6.3. Información pendiente de obtener

| Alternativa | Evidencia pendiente |
|---|---|
| **StarSoft** | Cotización, demostración de CRM, alcance de APIs y condiciones de soporte. |
| **Odoo Community** | Pruebas de contabilidad, reportes financieros, localización peruana y continuidad técnica. |
| **Business Central** | Cotización con POS, localización peruana, licencias e implementación. |
| **Todas** | Demostración de los principales procesos de MIGAL y estimación comparable del costo total. |

Los hallazgos deberán actualizarse si se obtienen pruebas, cotizaciones o información técnica que modifique la comparación.