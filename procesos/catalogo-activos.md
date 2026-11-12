# Catálogo de activos de ERP-MIGAL: función, criticidad y disponibilidad

**Estado:** catálogo de trabajo. Identifica los activos físicos y tecnológicos que sostienen [O2C](o2c/flujo.md), [P2P](p2p/flujo.md) e [inventario](inventario/flujo.md), y asigna a cada uno una criticidad y una disponibilidad de referencia. La función y la criticidad son interpretaciones del equipo. Los valores de MTBF y MTTR son **supuestos de trabajo**: MIGAL no conserva un registro de fallas que permita calcularlos. Las fotografías se declaran como [FN-04](../fuentes/fuentes-negocio.md).

## 1. Dieciséis activos con cinco de criticidad alta

El catálogo reúne 16 activos: 5 de criticidad alta, 6 de media y 5 de baja. Los de criticidad alta son los dos camiones, el montacargas, los teléfonos celulares de los propietarios y el servicio KeyFacil. La disponibilidad inherente de referencia varía entre 89,29 % (minicargador frontal) y 99,95 % (escalera de tijera). Los tres equipos con menor disponibilidad tienen motor de combustión: el minicargador, el camión volquete y el camión de baranda.

La criticidad se evalúa sobre la operación propuesta con Odoo 19 Community, no sobre el uso actual. El mantenimiento de cada activo se define en el [plan de mantenimiento](plan-mantenimiento.md), que usa este catálogo como entrada.

## 2. Criterios de criticidad y cálculo de disponibilidad

La criticidad resulta de dos preguntas: qué ocurre con el proceso cuando el activo se detiene y qué alternativa existe en ese momento.

| Criticidad | Criterio |
|---|---|
| Alta | La parada detiene una operación de O2C, P2P o inventario, y la alternativa disponible es nula o cubre la operación solo en parte. |
| Media | La parada degrada la operación (más tiempo, más trabajo manual o menor exactitud) o detiene una operación secundaria que otro medio cubre por completo. |
| Baja | La parada no afecta la continuidad de las operaciones en el corto plazo. |

La disponibilidad se expresa con tres indicadores:

- **MTBF:** horas promedio de funcionamiento entre dos fallas.
- **MTTR:** horas promedio desde la falla hasta la reposición del servicio, incluidos diagnóstico, espera de repuesto y reparación.
- **Disponibilidad (%):** MTBF / (MTBF + MTTR) × 100. Es una disponibilidad inherente: no descuenta las paradas planificadas de mantenimiento preventivo.

Como no existe historial de fallas, los valores de MTBF y MTTR se fijaron por clase de equipo, según antigüedad aparente, intensidad de uso y entorno de polvo y carga:

- Vehículos y maquinaria con motor de combustión: MTBF de 200 a 300 h y MTTR de 16 a 24 h.
- Equipos de izaje y de traslado eléctricos: MTBF de 400 a 800 h y MTTR de 8 h.
- Equipos electrónicos y de comunicaciones: MTBF de 1 000 a 4 000 h y MTTR de 4 a 48 h. El sistema de videovigilancia recibe el MTBF más bajo de su clase porque la fotografía del monitor muestra canales sin señal.
- Herramientas y equipos de apoyo manuales: MTBF de 5 000 a 8 000 h y MTTR de 4 a 8 h.

Estos valores se reemplazan por datos reales cuando los propietarios aporten el historial de fallas y reparaciones.

## 3. Tabla maestra de activos

La tabla presenta, por activo, su función en el proceso, su criticidad y sus indicadores de disponibilidad.

| ID | Activo | Función en el proceso | Criticidad | MTBF (h) | MTTR (h) | Disponibilidad (%) |
|---|---|---|---|---|---|---|
| ACT-01 | Camión de baranda (placa C4W-921) | Transporta materiales a obras y entre tienda y almacenes en el despacho de O2C y en los traslados de inventario. | Alta | 300 | 24 | 92,59 |
| ACT-02 | Camión volquete (placa F5E-844) | Transporta agregados y material a granel hacia las obras en el despacho de O2C. | Alta | 250 | 24 | 91,24 |
| ACT-03 | Montacargas de combustión | Descarga la mercadería del proveedor en la recepción de P2P, mueve parihuelas y sacos dentro del almacén y carga los pedidos. | Alta | 300 | 16 | 94,94 |
| ACT-04 | Minicargador frontal con cuchara | Carga agregados a los camiones en la preparación del despacho. | Media | 200 | 24 | 89,29 |
| ACT-05 | Tecle eléctrico con monorriel y balancín de izaje | Levanta y carga paquetes de fierro en la preparación del despacho. | Media | 800 | 8 | 99,01 |
| ACT-06 | Carretilla eléctrica de plataforma | Traslada mercadería entre la tienda y los almacenes y apoya el despacho. | Media | 400 | 8 | 98,04 |
| ACT-07 | Balanza electrónica de plataforma | Pesa la mercadería vendida por peso y calcula precio unitario e importe en la venta de mostrador. | Media | 2 000 | 4 | 99,80 |
| ACT-08 | Terminal de pago Culqi | Cobra con tarjeta en la venta de mostrador. | Media | 3 000 | 24 | 99,21 |
| ACT-09 | Computadora All-in-One | Equipo informático fijo de la tienda; punto previsto de acceso a Odoo para registrar ventas, inventario y compras. | Media | 4 000 | 12 | 99,70 |
| ACT-10 | Teléfonos celulares de los propietarios (2) | Reciben listas, consultas y cotizaciones por WhatsApp y llamadas, y coordinan pedidos y entregas. | Alta | 3 000 | 24 | 99,21 |
| ACT-11 | Tablet | Dispositivo para consulta y registro de operaciones; el uso específico está pendiente de definir. | Baja | 3 000 | 24 | 99,21 |
| ACT-12 | Sistema de videovigilancia (cámaras, DVR de 16 canales y monitor) | Vigila la tienda y los almacenes y aporta evidencia visual ante pérdidas o incidencias. | Baja | 1 000 | 48 | 95,42 |
| ACT-13 | Compresor de aire Bauker | Suministra aire comprimido en la tienda; el uso específico está pendiente de confirmar. | Baja | 1 500 | 16 | 98,94 |
| ACT-14 | Servicio KeyFacil | Emite las boletas y facturas electrónicas, operado por los propietarios. | Alta | 2 000 | 4 | 99,80 |
| ACT-15 | Cortapernos manual | Corta alambre y varillas delgadas para fraccionar la mercadería vendida por longitud; el uso específico está pendiente de confirmar. | Baja | 5 000 | 8 | 99,84 |
| ACT-16 | Escalera de tijera de cuatro peldaños | Permite alcanzar los estantes altos de la tienda para sacar y reponer mercadería. | Baja | 8 000 | 4 | 99,95 |

## 4. Efecto de la parada y alternativa de cada activo

La tabla justifica la criticidad con los dos criterios de la sección 2. Las alternativas son interpretaciones del equipo y requieren confirmación con los propietarios.

| ID | Efecto de la parada | Alternativa existente | Criticidad |
|---|---|---|---|
| ACT-01 | Detiene el despacho de materiales largos y paquetes. | El volquete no transporta ese tipo de carga. | Alta |
| ACT-02 | Detiene el transporte de agregados y material a granel. | El camión de baranda no descarga por volteo. | Alta |
| ACT-03 | Detiene la descarga y el movimiento de carga en parihuelas. | Ningún otro equipo levanta parihuelas; el tecle solo iza fierro. | Alta |
| ACT-04 | La carga de agregados pasa a hacerse a mano, con más tiempo y personal. | Carga manual. | Media |
| ACT-05 | La carga de fierro pasa a hacerse a mano, con más tiempo y personal. | Carga manual. | Media |
| ACT-06 | Los traslados internos pasan a hacerse a mano, con más tiempo. | Traslado manual. | Media |
| ACT-07 | La venta por peso se cotiza con peso teórico o estimado y pierde exactitud. | Peso teórico o estimado. | Media |
| ACT-08 | Se pierde la venta con tarjeta; el cobro continúa. | Los demás medios de pago vigentes. | Media |
| ACT-09 | El registro en el ERP continúa con menor comodidad. | Tablet o teléfono; contingencia de [RSK-018](../arquitectura/riesgos-y-controles.md). | Media |
| ACT-10 | Detiene los pedidos por WhatsApp del propietario afectado y deja sin acceso a los contactos y al historial guardados en el equipo. | El teléfono del otro propietario cubre la comunicación, no los contactos del primero. | Alta |
| ACT-11 | Sin efecto sobre las operaciones. | La computadora All-in-One y los teléfonos. | Baja |
| ACT-12 | Sin efecto sobre la continuidad; reduce la seguridad y la evidencia ante pérdidas. | Revisión presencial. | Baja |
| ACT-13 | Sin efecto sobre O2C, P2P ni inventario. | No requerida. | Baja |
| ACT-14 | Detiene la emisión de comprobantes. | Ninguna registrada: el [alcance](../arquitectura/alcance.md) mantiene KeyFacil como único emisor. | Alta |
| ACT-15 | Sin efecto sobre la continuidad en el corto plazo. | Otra herramienta de corte, por confirmar. | Baja |
| ACT-16 | Sin efecto sobre la continuidad en el corto plazo. | Otro medio de acceso a los estantes, por confirmar. | Baja |

## 5. Marca, modelo y datos verificados en cada activo

Esta tabla separa lo que se lee en las fotografías de lo que queda por confirmar. Los datos referenciales no están verificados.

| ID | Marca y modelo | Verificado en la fotografía o el contexto | Referencial o por confirmar |
|---|---|---|---|
| ACT-01 | No legibles. | Placa C4W-921; peso neto 2 830 kg, carga útil 2 500 kg y peso bruto 5 330 kg; carrocería de baranda. | Marca, modelo y año, con la tarjeta de propiedad. |
| ACT-02 | No legibles. | Placa F5E-844; carga útil 3 580 kg, peso seco 3 700 kg y peso bruto 7 280 kg; tolva volcable. | Marca, modelo y año, con la tarjeta de propiedad. |
| ACT-03 | No legibles; la calcomanía está borrada. | Mástil con horquillas, neumáticos y motor de combustión. | Capacidad aparente de 2 a 3 t; combustible (GLP o diésel) por confirmar. |
| ACT-04 | No legibles. | Cabina abierta, brazos hidráulicos y cuchara. | Posible conversión de un chasis de montacargas. No figura en el [contexto de la empresa](../arquitectura/contexto-empresa.md). |
| ACT-05 | No legibles. | Tecle eléctrico de cadena sobre viga carril, con balancín de cadenas. | Capacidad, que consta en la placa del tecle. |
| ACT-06 | No legibles. | Triciclo con plataforma de baranda baja, manubrio, asiento y tres ruedas. | Tensión de batería y capacidad de carga. |
| ACT-07 | Sin marca legible. | Indicador con tres visores (peso, precio unitario e importe) y plataforma de acero. | Capacidad máxima, que consta en la placa. |
| ACT-08 | Culqi (rótulo visible). | Rótulos Culqi y Visa; pantalla táctil, teclado numérico, lector sin contacto e impresora. | Fabricante y modelo del terminal. |
| ACT-09 | Sin fotografía. | Descrita en el [contexto](../arquitectura/contexto-empresa.md), apartado 1.2. | Marca y modelo. |
| ACT-10 | Sin fotografía. | Dos equipos, uno por propietario, según el contexto, apartado 1.2. | Marca y modelo de cada equipo. |
| ACT-11 | Sin fotografía. | Descrita en el contexto, apartado 1.2. | Marca y modelo. |
| ACT-12 | Hikvision (cámara bullet), TP-Link Tapo (cámara giratoria) y Sony (monitor), según los rótulos visibles; otras dos cámaras fijas sin marca legible. | Cuatro cámaras fotografiadas (bullet de interior, giratoria, bullet de exterior con visera deteriorada y cámara compacta sobre caja de paso) y un mosaico de 16 canales, con un canal en «NO LINK» y otro en «NO VIDEO». | Modelos de cámara y DVR; la Tapo parece una C200. El contexto indica unas 10 cámaras. |
| ACT-13 | Bauker (rótulo visible); modelo no legible. | Tanque horizontal, motor eléctrico, dos manómetros y presostato. | Capacidad del tanque, que consta en la placa. |
| ACT-14 | Servicio externo. | Descrito en el contexto, apartado 9.1. | Plan contratado y disponibilidad pactada. |
| ACT-15 | No legibles. | Cortapernos de dos mangos con mordazas y empuñaduras de goma, sobre un rollo de alambre. | Longitud y capacidad de corte. |
| ACT-16 | No legibles. | Escalera de tijera de cuatro peldaños, con tapones en las patas y barandilla superior. | Altura y capacidad de carga. |

## 6. Elementos fotografiados o previstos que no se catalogan

- **Altavoz Amazon Echo Dot:** no tiene función verificada en los procesos. Se incorpora si los propietarios le asignan un uso operativo.
- **Parihuelas de madera:** son material de manipulación consumible y no admiten mantenimiento por unidad.
- **Instancia de Odoo 19 Community:** el alojamiento no está definido. Se cataloga cuando se decida dónde se ejecuta.
- **Escáner de códigos QR:** su compra no se ha realizado, según el [contexto](../arquitectura/contexto-empresa.md), apartado 1.2.

## 7. Diferencias con el contexto vigente y validaciones pendientes

El contexto de la empresa mantiene el montacargas y el vehículo eléctrico como pendientes de corroboración (FN-02). Las fotografías de FN-04 corresponden a ACT-03 y ACT-06, pero no establecen propiedad ni uso: el contexto se actualiza cuando los propietarios confirmen ambos recursos.

El minicargador, el tecle con monorriel, la balanza, el terminal Culqi y el compresor no figuran en el apartado 1 del contexto. El terminal Culqi implica un cobro con tarjeta que el [alcance](../arquitectura/alcance.md) no describe ni concilia. El monitor muestra 16 canales con fallas visibles, frente a las 10 cámaras que indica el contexto; la cantidad operativa de cámaras está por verificar.

Las validaciones quedan registradas en el [registro de pendientes](../producto/registro-pendientes.md):

- PEN-021: validar con los propietarios la lista, la cantidad y el estado de los activos, y los valores de MTBF y MTTR.
- PEN-022: definir el tratamiento del terminal Culqi en el cobro de O2C y en la conciliación.
