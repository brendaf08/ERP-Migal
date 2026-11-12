# Plan de mantenimiento por activo de ERP-MIGAL

**Estado:** plan propuesto, sujeto a aprobación de GER. Asigna a cada activo del [catálogo de activos](catalogo-activos.md) un enfoque de mantenimiento, una frecuencia o disparador y una acción principal. Las frecuencias y duraciones son propuestas de planificación, no recomendaciones del fabricante: los manuales de los equipos no se han consultado. Los valores de disponibilidad provienen de supuestos de trabajo (MTBF y MTTR) y no de un historial de fallas.

## 1. Once activos con mantenimiento preventivo y once con correctivo

El plan cubre los 22 activos del catálogo, uno por fila. Aplica mantenimiento preventivo a los 6 activos de criticidad alta y a 5 de los 6 de criticidad media. Los 11 activos restantes (el terminal Culqi, la tablet, el compresor, el cortapernos, la escalera y los seis componentes de la videovigilancia) reciben mantenimiento correctivo. No se adopta mantenimiento predictivo en esta etapa (sección 5).

Cuatro activos no alcanzan la meta de disponibilidad propuesta: los dos camiones, el montacargas y el minicargador. El plan los atiende con inspección diaria y servicio periódico, y suma 122 h de parada planificada al año, de las cuales 88 h corresponden a esos cuatro activos (sección 4).

## 2. Criterios para elegir el enfoque de mantenimiento

El enfoque se deriva de la criticidad del catálogo, con una condición adicional para los activos de criticidad media.

| Criticidad | Enfoque | Condición |
|---|---|---|
| Alta | Preventivo | Siempre. Cuando el servicio es externo, el plan cubre las acciones que corresponden a MIGAL. |
| Media | Preventivo | Si la parada o su causa puede afectar la seguridad de las personas, la exactitud de los importes o la integridad de los datos, o si el activo no cumple su meta de disponibilidad. |
| Media | Correctivo | En los demás casos. |
| Baja | Correctivo | Siempre. Las rutinas de operación del usuario (purga, revisión visual) no se consideran intervención de mantenimiento. |

Definiciones aplicadas:

- **Preventivo:** intervención programada por tiempo o por uso, antes de que ocurra la falla.
- **Correctivo:** intervención posterior a la falla, disparada por ella.
- **Predictivo:** intervención decidida a partir de la medición de la condición del activo. No se adopta (sección 5).

## 3. Plan de mantenimiento por activo

La tabla vincula cada ID del catálogo con su enfoque, su frecuencia o disparador y su acción principal.

| ID | Activo | Enfoque | Frecuencia o disparador | Acción principal |
|---|---|---|---|---|
| ACT-01 | Camión de baranda | Preventivo | Inspección antes de cada salida; servicio cada 5 000 km o 3 meses, lo que ocurra primero. | Revisar neumáticos, frenos, luces y niveles; cambiar aceite y filtros; engrasar. |
| ACT-02 | Camión volquete | Preventivo | Inspección antes de cada salida; servicio cada 5 000 km o 3 meses, lo que ocurra primero. | Las acciones del camión de baranda, más la revisión de mangueras y cilindro de volteo. |
| ACT-03 | Montacargas de combustión | Preventivo | Inspección al iniciar cada jornada; servicio cada 250 h de motor o cada 3 meses (solo por tiempo si no hay horómetro). | Verificar mástil, cadenas, horquillas, frenos y fugas hidráulicas; cambiar aceite y filtros. |
| ACT-04 | Minicargador frontal con cuchara | Preventivo | Inspección al iniciar cada jornada; servicio cada 2 meses. | Lubricar las articulaciones del brazo y la cuchara; revisar mangueras y cilindros; cambiar aceite y filtros. |
| ACT-05 | Tecle eléctrico con monorriel y balancín de izaje | Preventivo | Inspección visual antes de cada uso; lubricación e inspección mensual; inspección técnica anual. | Revisar cadena, gancho, freno y finales de carrera; lubricar la cadena; verificar que la carga no exceda la capacidad de la placa. |
| ACT-06 | Carretilla eléctrica de plataforma | Preventivo | Revisión mensual. | Revisar batería, bornes, frenos, dirección y neumáticos. |
| ACT-07 | Balanza electrónica de plataforma | Preventivo | Verificación semanal del cero; calibración cada 6 meses. | Contrastar con pesas patrón y calibrar; limpiar la plataforma; revisar el cable y la alimentación. |
| ACT-08 | Terminal de pago Culqi | Correctivo | Falla del equipo, rechazo reiterado de transacciones o pérdida de conexión. | Solicitar al proveedor la reparación o reposición; cobrar por los demás medios vigentes mientras tanto. |
| ACT-09 | Computadora All-in-One | Preventivo | Revisión trimestral. | Aplicar actualizaciones, verificar el respaldo y limpiar el equipo. |
| ACT-10 | Teléfono celular de la propietaria | Preventivo | Respaldo mensual de contactos y conversaciones; revisión trimestral de batería y almacenamiento. | Respaldar la información, actualizar el sistema, verificar la batería y mantener identificado un equipo de reemplazo. |
| ACT-11 | Tablet | Correctivo | Falla del equipo. | Reparar o reponer y restablecer las aplicaciones. |
| ACT-12 | Grabador de video DVR | Correctivo | Falla del equipo, pérdida de las imágenes de todas las cámaras o disco sin grabación. La verificación mensual de que existe una grabación reciente es rutina de operación. | Reparar o reponer el DVR y su disco, y comprobar que se reanuda la grabación. |
| ACT-13 | Compresor de aire Bauker | Correctivo | Falla del equipo. La purga semanal del condensado del tanque es rutina de operación. | Reparar o reponer; revisar el presostato y el manómetro antes de reutilizarlo. |
| ACT-14 | Servicio KeyFacil | Preventivo | Verificación mensual. | Comprobar el acceso y la vigencia de las credenciales, conservar copia de los comprobantes emitidos y atender los avisos de mantenimiento del proveedor. |
| ACT-15 | Cortapernos manual | Correctivo | Filo desgastado, mordazas desalineadas o mango roto. La revisión del filo y del pasador antes de cada uso es rutina de operación. | Afilar o reponer las mordazas, o reponer la herramienta. |
| ACT-16 | Escalera de tijera de cuatro peldaños | Correctivo | Pata, peldaño, remache o tapón dañado. La revisión visual antes de cada uso es rutina de operación. | Retirar la escalera de uso y repararla o reponerla. |
| ACT-17 | Monitor Sony de videovigilancia | Correctivo | Falla del equipo o pantalla sin imagen. | Reparar o reponer el monitor y verificar la conexión con el DVR. |
| ACT-18 | Cámara bullet Hikvision | Correctivo | Canal en «NO LINK» o «NO VIDEO», o cámara sin imagen. La revisión mensual de los canales en el monitor es rutina de operación. | Reconectar o reemplazar el cable o la cámara. |
| ACT-19 | Cámara giratoria TP-Link Tapo | Correctivo | Canal en «NO LINK» o «NO VIDEO», o cámara sin imagen. La revisión mensual de los canales en el monitor es rutina de operación. | Reconectar o reemplazar el cable, el adaptador o la cámara. |
| ACT-20 | Cámara bullet con visera deteriorada | Correctivo | Canal en «NO LINK» o «NO VIDEO», cámara sin imagen o visera rota. La revisión mensual de los canales en el monitor es rutina de operación. | Reponer la visera o la cámara y reconectar el cable. |
| ACT-21 | Cámara compacta fija | Correctivo | Canal en «NO LINK» o «NO VIDEO», o cámara sin imagen. La revisión mensual de los canales en el monitor es rutina de operación. | Reconectar o reemplazar el cable o la cámara. |
| ACT-22 | Teléfono celular del propietario | Preventivo | Respaldo mensual de contactos y conversaciones; revisión trimestral de batería y almacenamiento. | Respaldar la información, actualizar el sistema, verificar la batería y mantener identificado un equipo de reemplazo. |

## 4. Paradas planificadas, metas de disponibilidad y responsables

Las metas de disponibilidad son una propuesta por nivel de criticidad: 95 % para la alta, 92 % para la media y 90 % para la baja. La columna «MTBF requerido» indica las horas entre fallas que alcanzarían la meta con el MTTR del catálogo, según la relación MTBF = meta / (1 − meta) × MTTR.

| ID | Criticidad | Disponibilidad de referencia (%) | Meta (%) | Resultado | MTBF requerido (h) | Parada planificada anual (h) | Responsables |
|---|---|---|---|---|---|---|---|
| ACT-01 | Alta | 92,59 | 95 | Brecha de 2,41 puntos | 456 | 24 (4 × 6 h) | ALM programa y registra; CMP gestiona repuestos; GER autoriza el gasto. |
| ACT-02 | Alta | 91,24 | 95 | Brecha de 3,76 puntos | 456 | 24 (4 × 6 h) | ALM programa y registra; CMP gestiona repuestos; GER autoriza el gasto. |
| ACT-03 | Alta | 94,94 | 95 | Brecha de 0,06 puntos | 304 | 16 (4 × 4 h) | ALM programa y registra; CMP gestiona repuestos; GER autoriza el gasto. |
| ACT-04 | Media | 89,29 | 92 | Brecha de 2,71 puntos | 276 | 24 (6 × 4 h) | ALM programa y registra; CMP gestiona repuestos; GER autoriza el gasto. |
| ACT-05 | Media | 99,01 | 92 | Cumple | No aplica | 16 (12 × 1 h y 1 × 4 h) | ALM programa y registra; GER autoriza la inspección técnica anual. |
| ACT-06 | Media | 98,04 | 92 | Cumple | No aplica | 12 (12 × 1 h) | ALM programa y registra; GER autoriza el gasto. |
| ACT-07 | Media | 99,80 | 92 | Cumple | No aplica | 2 (2 × 1 h) | ALM programa y registra; GER autoriza el gasto. |
| ACT-08 | Media | 99,21 | 92 | Cumple | No aplica | 0 | VEN reporta la falla; GER autoriza la reposición. |
| ACT-09 | Media | 99,70 | 92 | Cumple | No aplica | 4 (4 × 1 h) | SIS ejecuta; GER autoriza la reposición. |
| ACT-10 | Alta | 99,21 | 95 | Cumple | No aplica | 0 (el respaldo no detiene el equipo) | SIS ejecuta; GER autoriza la reposición. |
| ACT-11 | Baja | 99,21 | 90 | Cumple | No aplica | 0 | SIS ejecuta; GER autoriza la reposición. |
| ACT-12 | Baja | 99,40 | 90 | Cumple | No aplica | 0 | ALM revisa; GER autoriza la reparación. |
| ACT-13 | Baja | 98,94 | 90 | Cumple | No aplica | 0 | ALM opera; GER autoriza la reposición. |
| ACT-14 | Alta | 99,80 | 95 | Cumple | No aplica | 0 (sin parada en MIGAL) | GER, como operador del servicio. |
| ACT-15 | Baja | 99,84 | 90 | Cumple | No aplica | 0 | ALM opera; GER autoriza la reposición. |
| ACT-16 | Baja | 99,95 | 90 | Cumple | No aplica | 0 | ALM opera; GER autoriza la reposición. |
| ACT-17 | Baja | 99,70 | 90 | Cumple | No aplica | 0 | ALM revisa; GER autoriza la reparación. |
| ACT-18 | Baja | 99,21 | 90 | Cumple | No aplica | 0 | ALM revisa; GER autoriza la reparación. |
| ACT-19 | Baja | 99,21 | 90 | Cumple | No aplica | 0 | ALM revisa; GER autoriza la reparación. |
| ACT-20 | Baja | 98,43 | 90 | Cumple | No aplica | 0 | ALM revisa; GER autoriza la reparación. |
| ACT-21 | Baja | 99,21 | 90 | Cumple | No aplica | 0 | ALM revisa; GER autoriza la reparación. |
| ACT-22 | Alta | 99,21 | 95 | Cumple | No aplica | 0 (el respaldo no detiene el equipo) | SIS ejecuta; GER autoriza la reposición. |

Las horas de parada planificada se restan de la disponibilidad operativa, y la disponibilidad de referencia no las descuenta. La relación entre estas horas, la mejora esperada del MTBF y la continuidad del despacho se modela en el análisis de continuidad de la cadena, pendiente de documentación. Los códigos de rol proceden del [modelo de autorización](../arquitectura/seguridad/modelo-autorizacion.md).

## 5. Mantenimiento predictivo no adoptado y registro de intervenciones

El mantenimiento predictivo exige medir la condición de los equipos (vibración, temperatura, análisis de aceite) y comparar esas mediciones con un historial. MIGAL no tiene instrumentos ni historial, y el catálogo parte de supuestos de MTBF y MTTR. El plan lo reconsidera cuando existan al menos doce meses de registro de intervenciones.

Cada intervención, preventiva o correctiva, deja un registro con estos datos: ID del activo, fecha, tipo, duración de la parada, causa de la falla (si hubo), repuestos y costo, y responsable. Con ese registro se calculan MTBF y MTTR reales y se sustituyen los supuestos del catálogo. Hasta que se evalúe una herramienta de registro en Odoo 19, el registro se lleva en una hoja controlada por ALM. La falla de un activo de despacho se relaciona con los riesgos [RSK-014](../arquitectura/riesgos-y-controles.md) (incumplimiento en preparación y entrega) y [RSK-018](../arquitectura/riesgos-y-controles.md) (interrupción del servicio).

## 6. Validaciones pendientes

El [registro de pendientes](../producto/registro-pendientes.md) conserva estas validaciones:

- PEN-021: confirmar con los propietarios el catálogo y los valores de MTBF y MTTR de los que depende la disponibilidad de referencia.
- PEN-023: aprobar con GER las metas de disponibilidad, las frecuencias, las duraciones de parada y los responsables, y contrastar las frecuencias con los manuales de los equipos y con un taller.
- PEN-024: verificar si Odoo 19 Community ofrece una aplicación de mantenimiento utilizable para registrar intervenciones.
