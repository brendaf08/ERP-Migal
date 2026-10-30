# Catálogo de eventos

Un **evento de negocio** es un acontecimiento relevante que ocurre en la empresa y que puede iniciar, modificar o finalizar un proceso, generar un compromiso o producir una decisión. En Ferre & Inversiones MIGAL, los eventos se identifican independientemente del sistema utilizado para gestionarlos, considerando tanto los hechos de su operación actual como los previstos en el proceso propuesto. Las actividades rutinarias, como consultar precios o verificar existencias, no constituyen eventos independientes por sí mismas.

## 1. Convenciones del catálogo

| Elemento              | Criterio                                                                                                             |
| --------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Identificador**     | Código único `EV-XXX`, asignado consecutivamente al incorporar un evento.                                            |
| **Organización**      | Los eventos se agrupan por ámbito empresarial, sin exigir continuidad numérica dentro de cada sección.               |
| **Actual (AS-IS)**    | Acontecimiento identificado en la operación actual de MIGAL, independientemente de cómo se registre.                 |
| **Propuesto (TO-BE)** | Acontecimiento que se propone incorporar o formalizar como parte del proceso rediseñado.                             |
| **Mixto**             | Acontecimiento que ya ocurre en MIGAL, pero cuyo tratamiento, registro o control se propone modificar.               |
| **Incorporaciones**   | Los nuevos eventos reciben el siguiente identificador global disponible y se ubican en la categoría correspondiente. |
| **Retiro**            | Un identificador retirado no se reutiliza; se conserva su equivalencia cuando corresponde.                           |

La situación de los eventos se basa en la información empresarial disponible y en las propuestas del proyecto. Su clasificación deberá ratificarse cuando se contraste con los responsables de MIGAL.

## 2. Registro de eventos

### 2.1. Gestión comercial y cotizaciones

| ID     | Evento                              | Descripción                                                                                                                        | Situación |
| ------ | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | --------- |
| EV-001 | Consulta comercial recibida         | Un cliente solicita información sobre productos, precios o condiciones de venta.                                                   | Actual    |
| EV-002 | Solicitud de cotización recibida    | El cliente solicita una propuesta para determinados productos y cantidades.                                                        | Actual    |
| EV-003 | Cotización elaborada                | La empresa establece una propuesta con productos, cantidades, precios y condiciones comerciales.                                   | Actual    |
| EV-004 | Cotización comunicada               | La propuesta es entregada o enviada al cliente para su evaluación.                                                                 | Actual    |
| EV-005 | Modificación de cotización acordada | Durante la negociación se acuerdan cambios en productos, cantidades, precios o condiciones de una propuesta previamente elaborada. | Mixto     |
| EV-006 | Cotización aceptada                 | El cliente manifiesta conformidad con una propuesta y sus condiciones.                                                             | Actual    |
| EV-007 | Cotización rechazada                | El cliente comunica que no acepta la propuesta presentada.                                                                         | Actual    |
| EV-008 | Cotización vencida                  | Finaliza el período de vigencia establecido para una propuesta sin que se haya acordado su continuidad o renovación.               | Propuesto |

### 2.2. Evaluación y autorización de pedidos de venta

| ID     | Evento                                 | Descripción                                                                                                                                                                | Situación |
| ------ | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| EV-009 | Solicitud de Orden de Venta presentada | Se solicita evaluar formalmente la viabilidad de atender una cotización aceptada por el cliente.                                                                           | Propuesto |
| EV-010 | Abastecimiento evaluado                | El responsable concluye la evaluación de disponibilidad y suministro de los productos, registrando un resultado favorable, condicionado o no viable, con su justificación. | Propuesto |
| EV-012 | Despacho evaluado                      | El responsable concluye la evaluación de transporte y entrega, registrando un resultado favorable, condicionado o no viable, con su justificación.                         | Propuesto |
| EV-014 | Solicitud de Orden de Venta resuelta   | Se emite la decisión interna de aprobar o rechazar la solicitud, considerando las evaluaciones y autorizaciones correspondientes.                                          | Propuesto |
| EV-016 | Condiciones del pedido renegociadas    | A partir de observaciones operativas, el cliente y la empresa acuerdan nuevas condiciones para intentar viabilizar la operación.                                           | Propuesto |

La **Solicitud de Orden de Venta** representa una solicitud interna de evaluación propuesta para MIGAL. No presupone la existencia de un documento tecnológico independiente.

Las evaluaciones de abastecimiento y despacho pueden producir diferentes resultados, pero cada una constituye un único tipo de evento.

### 2.3. Ventas y pedidos

| ID     | Evento                     | Descripción                                                                                           | Situación |
| ------ | -------------------------- | ----------------------------------------------------------------------------------------------------- | --------- |
| EV-017 | Venta inmediata concretada | Se realiza una venta de atención inmediata sin requerir necesariamente una cotización formal previa.  | Actual    |
| EV-018 | Orden de venta confirmada  | La empresa formaliza el compromiso de atender un pedido bajo las condiciones aceptadas y autorizadas. | Mixto     |
| EV-019 | Pedido modificado          | Se autorizan cambios relevantes en un pedido previamente confirmado.                                  | Mixto     |
| EV-020 | Pedido cancelado           | Se formaliza la cancelación de un pedido previamente confirmado.                                      | Mixto     |

### 2.4. Compras y abastecimiento

| ID     | Evento                                        | Descripción                                                                                                        | Situación |
| ------ | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | --------- |
| EV-021 | Necesidad de abastecimiento identificada      | Se determina que es necesario adquirir o reponer productos por una necesidad comercial, operativa o de inventario. | Actual    |
| EV-022 | Pedido a proveedor formalizado                | La empresa establece y comunica un compromiso de compra bajo cantidades, precios y condiciones determinadas.       | Actual    |
| EV-023 | Pedido confirmado por proveedor               | El proveedor confirma expresamente su aceptación de las condiciones de suministro solicitadas.                     | Mixto     |
| EV-024 | Incumplimiento de abastecimiento identificado | Se detecta que un suministro no cumplirá o no ha cumplido las condiciones acordadas.                               | Mixto     |
| EV-025 | Compra cancelada                              | Se formaliza la cancelación de una compra previamente comprometida.                                                | Mixto     |

### 2.5. Inventario y almacenes

| ID     | Evento                                | Descripción                                                                                                                               | Situación |
| ------ | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| EV-026 | Productos recibidos                   | La empresa recibe físicamente productos procedentes de una compra u otro origen identificado.                                             | Actual    |
| EV-027 | Recepción validada                    | Se comprueba la cantidad y condición de los productos recibidos, dejando constancia de su conformidad o de las diferencias identificadas. | Mixto     |
| EV-028 | Diferencia de inventario identificada | Se detecta una discrepancia entre las existencias registradas y las existencias físicas.                                                  | Mixto     |
| EV-029 | Ajuste de inventario autorizado       | El responsable correspondiente aprueba una corrección de las existencias registradas, sustentada en una causa identificada.               | Mixto     |
| EV-056 | Ajuste de inventario ejecutado        | Se realiza la corrección autorizada y se deja constancia de las cantidades modificadas y su justificación.                                | Propuesto |
| EV-030 | Traslado interno completado           | Se trasladan físicamente productos entre ubicaciones o almacenes de la empresa.                                                           | Actual    |
| EV-031 | Pérdida o deterioro identificado      | Se detectan productos perdidos, dañados o no aptos para su comercialización habitual.                                                     | Mixto     |

### 2.6. Transporte y entregas

| ID     | Evento                             | Descripción                                                                                                                 | Situación |
| ------ | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------- |
| EV-032 | Despacho programado                | Se establecen la fecha y las condiciones para entregar un pedido.                                                           | Mixto     |
| EV-033 | Pedido preparado                   | Los productos han sido reunidos y acondicionados para su entrega o despacho.                                                | Actual    |
| EV-054 | Guía de remisión emitida           | Se emite el documento que sustenta el traslado de productos cuando corresponde según la operación y la normativa aplicable. | Propuesto |
| EV-034 | Productos despachados              | La mercancía sale de las instalaciones o se entrega al transportista responsable de su traslado.                            | Actual    |
| EV-035 | Productos entregados               | El cliente o receptor autorizado recibe físicamente los productos.                                                          | Actual    |
| EV-036 | Incidencia de entrega identificada | Se detecta una entrega incompleta, incorrecta, dañada, retrasada o con otra diferencia respecto a lo acordado.              | Mixto     |
| EV-037 | Entrega pendiente regularizada     | Se resuelve una obligación de entrega que había quedado pendiente.                                                          | Mixto     |

La emisión de una guía de remisión es diferente de la emisión de un comprobante de venta. EV-054 aplica únicamente a las operaciones que requieran dicho documento; su inclusión no significa que todos los traslados deban generar una guía del mismo tipo.

### 2.7. Facturación

| ID     | Evento                          | Descripción                                                                                   | Situación |
| ------ | ------------------------------- | --------------------------------------------------------------------------------------------- | --------- |
| EV-038 | Comprobante de venta emitido    | Se emite el comprobante correspondiente a una operación comercial.                            | Mixto     |
| EV-039 | Comprobante corregido o anulado | Se formaliza la corrección o anulación de un comprobante mediante el procedimiento aplicable. | Mixto     |
| EV-040 | Comprobante de compra recibido  | La empresa recibe el documento que sustenta una adquisición realizada al proveedor.           | Actual    |

### 2.8. Pagos, créditos y cobranzas

| ID     | Evento                                 | Descripción                                                                                                                             | Situación |
| ------ | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| EV-041 | Venta a crédito autorizada             | Se concede al cliente la posibilidad de pagar una operación posteriormente, bajo condiciones determinadas.                              | Actual    |
| EV-042 | Pago de cliente recibido               | La empresa recibe un pago total o parcial por una operación o deuda.                                                                    | Actual    |
| EV-043 | Pago aplicado a deuda                  | Un pago recibido se asigna a una obligación concreta, actualizando el saldo pendiente.                                                  | Mixto     |
| EV-044 | Obligación de pago vencida             | Una deuda alcanza su fecha de vencimiento sin haberse saldado completamente.                                                            | Mixto     |
| EV-045 | Deuda de cliente saldada               | El saldo pendiente de una obligación del cliente queda completamente extinguido mediante los pagos o regularizaciones correspondientes. | Actual    |
| EV-046 | Pago a proveedor realizado             | La empresa efectúa un pago total o parcial correspondiente a una obligación con un proveedor.                                           | Actual    |
| EV-055 | Pago a proveedor aplicado a obligación | Un pago realizado se vincula con una obligación específica del proveedor, permitiendo determinar el saldo pendiente.                    | Mixto     |

EV-042 y EV-043 distinguen la recepción del dinero de su aplicación a una deuda. De manera equivalente, EV-046 y EV-055 distinguen el pago realizado al proveedor de su aplicación a una obligación determinada.

La comprobación o conciliación del pago se realizará conforme a los controles correspondientes. No se considera automáticamente que realizar un pago equivale a tenerlo aplicado y conciliado.

### 2.9. Posventa e incidencias

| ID     | Evento                        | Descripción                                                                         | Situación |
| ------ | ----------------------------- | ----------------------------------------------------------------------------------- | --------- |
| EV-047 | Reclamo recibido              | Un cliente comunica una disconformidad relacionada con una operación comercial.     | Actual    |
| EV-048 | Devolución autorizada         | La empresa acepta la devolución de productos bajo determinadas condiciones.         | Mixto     |
| EV-049 | Productos devueltos recibidos | La empresa recibe físicamente los productos que el cliente devuelve.                | Mixto     |
| EV-050 | Reclamo resuelto              | Se formaliza una solución para atender la disconformidad comunicada por el cliente. | Mixto     |

### 2.10. Gestión de precios

| ID     | Evento                           | Descripción                                                                                  | Situación |
| ------ | -------------------------------- | -------------------------------------------------------------------------------------------- | --------- |
| EV-051 | Cambio de costo identificado     | Se detecta una variación relevante en el costo de adquisición de un producto.                | Actual    |
| EV-052 | Precio de venta modificado       | Los propietarios establecen un nuevo precio de comercialización para uno o varios productos. | Actual    |
| EV-053 | Descuento excepcional autorizado | Se aprueba una condición especial de precio para una operación comercial determinada.        | Actual    |

## 3. Mantenimiento del catálogo

### Incorporación y modificación

Los eventos nuevos se incorporarán a su categoría correspondiente y recibirán el siguiente identificador global disponible, **sin renumerar los eventos existentes**.

Antes de añadir un evento se deberá comprobar que representa un hecho distinto, relevante y no cubierto por otro identificador.

La modificación de un evento deberá conservar su significado esencial. Si cambia sustancialmente el acontecimiento representado, se evaluará retirar el identificador anterior y asignar uno nuevo.

### Estado del catálogo

El catálogo contiene eventos de la operación actual de MIGAL y acontecimientos propuestos para su proceso rediseñado.

Las definiciones podrán ajustarse cuando se obtenga nueva evidencia de la operación empresarial o se aprueben cambios en los procesos, manteniendo la trazabilidad de los identificadores.
