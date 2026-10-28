# Alcance del sistema de información

Este documento define el alcance del sistema de información propuesto para **Ferre & Inversiones MIGAL**, basado en **Odoo 18 Community**, estableciendo los sistemas, aplicaciones, procesos empresariales y límites considerados dentro del proyecto.

La solución busca integrar la gestión comercial, ventas, inventario, compras, facturación y finanzas, centralizando la información y mejorando la trazabilidad de las operaciones.

El alcance corresponde a la solución propuesta (TO-BE) y no implica que todas sus funcionalidades se encuentren implementadas.

## 1. Sistemas comprendidos

La solución utiliza **Odoo 18 Community** como plataforma principal, integrando las funciones de CRM y ERP dentro de un mismo entorno.

| Sistema o componente    | Alcance                                                                       |
| ----------------------- | ----------------------------------------------------------------------------- |
| **CRM de Odoo**         | Gestión de relaciones comerciales, clientes potenciales y oportunidades.      |
| **ERP de Odoo**         | Gestión de ventas, inventario, compras, facturación y finanzas.               |
| **KeyFacil**            | Sistema externo que se mantiene para la emisión de comprobantes electrónicos. |
| **WhatsApp y llamadas** | Canales externos de comunicación comercial.                                   |

## 2. Aplicaciones incluidas

El proyecto contempla las siguientes aplicaciones de Odoo 18 Community:

| Área      | Aplicación     | Funcionalidades principales                                                       |
| --------- | -------------- | --------------------------------------------------------------------------------- |
| CRM       | CRM            | Leads, oportunidades y seguimiento comercial.                                     |
| CRM / ERP | Contactos      | Clientes, proveedores y contactos comerciales.                                    |
| ERP       | Ventas         | Cotizaciones, pedidos y condiciones comerciales.                                  |
| ERP       | Punto de Venta | Ventas de mostrador y operaciones de caja.                                        |
| ERP       | Inventario     | Existencias, ubicaciones, movimientos y despachos.                                |
| ERP       | Compras        | Cotizaciones de proveedores, órdenes de compra y abastecimiento.                  |
| ERP       | Facturación    | Facturas, cobros, pagos, cuentas pendientes, contabilidad y reportes financieros. |

Se contempla la incorporación de los módulos técnicos y complementos necesarios para cubrir las funcionalidades definidas. Su identificación y dependencias se documentan en `modulos-y-dependencias.md`.

## 3. Procesos empresariales incluidos

El proyecto comprende dos macroprocesos principales:

| Macroproceso             | Alcance                                                                                                                                         |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Order to Cash (O2C)**  | Gestión del ciclo comercial, desde la captación del cliente hasta la atención del pedido, entrega, facturación y cobro.                         |
| **Procure to Pay (P2P)** | Gestión del abastecimiento, desde la identificación de la necesidad de compra hasta la recepción de productos, facturación y pago al proveedor. |

Adicionalmente, se considera **Gestión de Inventario como proceso de apoyo**, limitado a transferencias internas, conteos físicos, ajustes de existencias y control de pérdidas o productos dañados.

Los procedimientos, reglas de negocio, responsabilidades y flujos detallados se desarrollan en la documentación de procesos correspondiente.

## 4. Límites y exclusiones

### 4.1. Límites de integración

- **CRM y ERP:** forman parte de una misma plataforma Odoo, con una frontera funcional definida en su documentación específica.
- **KeyFacil:** permanece como sistema externo de emisión fiscal. Su integración automática con Odoo no forma parte del alcance inicial.
- **WhatsApp y llamadas:** se mantienen como canales externos; el registro de la información relevante en Odoo será manual.
- **Operaciones físicas:** la solución contempla el registro y seguimiento de las actividades de almacén y despacho, sin automatizar el transporte físico.

### 4.2. Funcionalidades excluidas

No se contempla inicialmente:

- Comercio electrónico (*e-commerce*).
- Automatización de campañas mediante aplicaciones especializadas de marketing.
- Integración automática con WhatsApp.
- Sustitución de KeyFacil como sistema de emisión fiscal.
- Sistemas de recursos humanos y planillas.
- Sistemas especializados de gestión de flotas, GPS u optimización de rutas.
- Desarrollo de funcionalidades adicionales que no correspondan a los requerimientos definidos para MIGAL.

Las exclusiones podrán revisarse si se presentan nuevos requerimientos y se aprueban los cambios correspondientes.
