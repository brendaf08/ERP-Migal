# Continuidad de la cadena y relación entre mantenimiento y despacho

Este análisis identifica qué pedidos se afectan cuando un camión entra al taller o un equipo de carga deja de funcionar. Las prácticas de trabajo se basan en las [aclaraciones de la propietaria (FN-05)](../../fuentes/fuentes-negocio.md). Las capacidades y funciones por activo se detallan en el [catálogo de activos](../activos_mantenimiento/activos.md).

## 1. Preparación, transporte y entrega

La preparación comprende la descarga, el traslado dentro del establecimiento y la carga. Cuando falla la maquinaria de apoyo, el personal generalmente continúa con trabajo manual donde el material puede manejarse con seguridad. El vehículo eléctrico ayuda con cargas pequeñas y despachos cercanos de hasta 500 kg, siempre que la mercadería quepa y pueda sujetarse en la plataforma.

En el transporte, el camión de baranda tiene 2 500 kg de carga útil y atiende despachos generales. El volquete tiene 3 580 kg de carga útil y se usa principalmente para agregados, con descarga por volteo. Ante una urgencia, el volquete también puede llevar materiales que normalmente irían en la baranda, según el espacio, la sujeción de la carga y la necesidad de mantener las entregas de agregados.

## 2. Matriz de causa y efecto

| Escenario | Efecto inmediato | Cómo se mantiene el despacho | Efecto posible en el servicio |
| --- | --- | --- | --- |
| Camión de baranda fuera de servicio | Hay menos disponibilidad para el reparto general. | El volquete puede cubrir pedidos generales compatibles. Se reordena su ruta según los horarios comprometidos y los pedidos de agregados. | Se reprograman con el cliente los pedidos que quedan fuera de la jornada. |
| Volquete fuera de servicio | Se restringen los despachos de agregados que requieren descarga por volteo. | La baranda sigue atendiendo los despachos compatibles. Los pedidos que requieren volteo se evalúan por separado. | La restricción se concentra en los pedidos que necesitan esa modalidad de descarga. |
| Equipo de carga fuera de servicio | La preparación puede requerir más tiempo y personal. | Se continúa manualmente con cargas manejables. El equipo eléctrico puede apoyar los movimientos pequeños. | Se priorizan los pedidos que pueden salir y se reorganizan los que requieren izaje o mayor tiempo. |
| Vehículo eléctrico fuera de servicio | Se pierde capacidad para entregas pequeñas de cercanía. | Si hay espacio y tiempo, los pedidos se incorporan a la ruta de un camión. | Si la entrega queda fuera de la ruta, se acuerda otra fecha con el cliente. |

## 3. Decisión de continuidad

La dueña indica que las fallas de camiones son poco usuales. Tampoco confirmó un caso previo en que ambos se enviaran a mantenimiento al mismo tiempo. La práctica habitual es **alternar las visitas al taller para mantener un camión disponible**. Si uno queda fuera de servicio, el equipo revisa los pedidos comprometidos, reorganiza la carga y la ruta, y procura completar la mayor cantidad de despachos planificados para ese día. Cuando un pedido queda fuera de la jornada, se comunica con el cliente para acordar una nueva fecha.

Como propuesta de contingencia, Gerencia puede evaluar apoyo externo para pedidos que requieren un vehículo o equipo específico cuando la reorganización resulte insuficiente. La decisión depende de la carga, el plazo acordado, el costo y la aceptación de una fecha alternativa por parte del cliente.

## 4. Cómo medir el impacto

El [plan de mantenimiento](../activos_mantenimiento/mantenimiento.md) propone registrar las horas fuera de servicio, los pedidos afectados y el recurso alternativo utilizado. Para evaluar el servicio, se registran los pedidos programados, los entregados completos en la fecha inicialmente acordada y los reprogramados. Con estos datos se puede medir OTIF y estimar la capacidad diaria con un camión operativo, con carga manual o con apoyo del vehículo eléctrico.

La referencia de 40 toneladas por día y la meta de 90 % de OTIF permanecen en el [modelo de cadena](../p2p/cadena_suministro.md) como escenario y meta propuesta, respectivamente. La duración de una parada preventiva o correctiva puede ilustrar un escenario puntual. Su efecto sobre el año requiere registrar la frecuencia de las paradas y las horas de operación del período.
