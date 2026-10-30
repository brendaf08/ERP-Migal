# Riesgos y controles de la implementación

Este documento centraliza los riesgos identificados durante la implementación y operación de **ERP-MIGAL sobre Odoo 19 Community**, estableciendo controles, responsables y evidencias para prevenir o reducir sus consecuencias.

## 1. Identificación y gestión de riesgos

Este archivo constituye el **registro central de riesgos del proyecto** y deberá actualizarse durante el análisis, diseño, configuración, pruebas, implementación y operación.

Para incorporar un riesgo se debe:

- **Identificar:** reconocer una situación que podría afectar la seguridad, información, costos, procesos o continuidad de MIGAL.
- **Evaluar:** determinar sus posibles causas, señales tempranas e impacto.
- **Controlar:** proponer una medida viable, asignar un responsable y definir una evidencia verificable.
- **Registrar:** asignar un identificador consecutivo, evitando duplicar riesgos existentes.

Los riesgos identificados no representan necesariamente fallas ocurridas. Asimismo, los controles propuestos no se consideran implementados hasta que exista evidencia de su aplicación.

## 2. Matriz de riesgos y controles

| ID | Riesgo | Señal temprana | Impacto | Control propuesto | Responsable | Evidencia |
|---|---|---|---|---|---|---|
| **RSK-01** | **Ampliación no controlada del alcance.** | Solicitudes de automatizar KeyFacil, WhatsApp u otras funcionalidades no contempladas. | Retrasos, sobrecostos y entregables incompletos. | Evaluar los cambios frente al alcance aprobado y autorizar su incorporación antes de implementarlos. | GER / Equipo ERP-MIGAL | Solicitudes y decisiones de cambio. |
| **RSK-02** | **Datos maestros inconsistentes.** | Productos duplicados, variantes ambiguas, unidades incorrectas o contactos repetidos. | Errores de cotización, inventario y atención. | Depurar y normalizar los datos antes de importarlos; verificar muestras y corregir inconsistencias. | VEN / ALM / SIS | Reportes de validación e incidencias de datos. |
| **RSK-03** | **Diferencias entre inventario físico y registrado.** | Existencias de Odoo distintas de las observadas en tienda o almacenes. | Ventas no atendibles, faltantes y pérdida de confianza. | Realizar conteo inicial, conciliaciones periódicas y ajustes justificados; reservar a GER la autorización de ajustes extraordinarios. | ALM / GER | Conteos, diferencias y ajustes autorizados. |
| **RSK-04** | **Modificaciones comerciales no autorizadas.** | Descuentos, cambios de precio o condiciones de crédito sin aprobación identificable. | Pérdida de margen, créditos indebidos y conflictos comerciales. | Exigir autorización de GER para excepciones y registrar responsable, motivo y condiciones aprobadas. | VEN / GER / FCO | Historial de cambios y autorizaciones. |
| **RSK-05** | **Pedidos confirmados sin validación operativa.** | Una cotización aceptada pasa directamente a pedido confirmado sin revisar disponibilidad o condiciones. | Incumplimiento de entregas y compromisos inviables. | Verificar la transición CRM–ERP: solicitud de pedido, revalidación operativa y confirmación únicamente después de una respuesta aceptada. | VEN / ALM / GER | Casos de prueba y registros vinculados de solicitud y respuesta. |
| **RSK-06** | **Incumplimiento en la preparación y entrega de pedidos.** | Fechas prometidas sin confirmar, faltantes o responsabilidades logísticas indefinidas. | Retrasos, costos adicionales y reclamos. | Validar disponibilidad y viabilidad logística antes de confirmar compromisos; definir responsables de transporte, conformidad y documentación de entrega. | GER / ALM | Registros de preparación, entrega e incidencias. |
| **RSK-07** | **Inconsistencias entre Odoo y KeyFacil.** | Diferencias entre ventas, montos cobrados y comprobantes emitidos. | Descuadres de caja, duplicidades y errores administrativos o tributarios. | Establecer conciliación periódica de operaciones, comprobantes y pagos, con referencias verificables entre ambos sistemas y sin asumir integración automática. | FCO / GER | Reportes de conciliación y discrepancias corregidas. |
| **RSK-08** | **Gestión financiera o tributaria incompleta.** | Reportes faltantes, registros contables incorrectos o dificultades para obtener información tributaria. | Información financiera poco confiable e incumplimientos potenciales. | Validar las operaciones de Facturación, evaluar complementos OCA y comprobar los procedimientos tributarios aplicables antes de utilizarlos oficialmente. | FCO / SIS / GER | Pruebas contables, reportes y validaciones tributarias. |
| **RSK-09** | **Cuentas por cobrar incorrectas o no controladas.** | Pagos parciales no registrados, saldos inconsistentes o créditos otorgados sin aprobación. | Dificultades de cobranza y pérdidas económicas. | Conciliar pagos con saldos pendientes, revisar las cuentas de clientes y mantener la autorización de crédito bajo GER. | FCO / GER | Estados de cuenta y conciliaciones de pagos. |
| **RSK-10** | **Permisos excesivos o autorizaciones omitidas.** | Usuarios ejecutan operaciones ajenas a su responsabilidad o combinan privilegios incompatibles. | Cambios indebidos, errores y falta de responsabilidad identificable. | Configurar mínimo privilegio, verificar la matriz de permisos y probar las operaciones restringidas con usuarios representativos. | SIS / GER | Matriz validada y pruebas de autorización. |
| **RSK-11** | **Incompatibilidad de módulos y actualizaciones.** | Errores al instalar complementos OCA, modificar configuraciones o actualizar Odoo 19. | Pérdida de funcionalidades, interrupciones y retrabajo. | Comprobar versiones y dependencias en un entorno de pruebas, respaldar los datos y validar operaciones críticas antes de aplicar cambios en producción. | SIS | Registro de versiones, resultados de pruebas y respaldos previos. |
| **RSK-12** | **Interrupción del servicio.** | Fallas de conectividad, energía, servidor o acceso al ERP. | Imposibilidad temporal de registrar ventas y movimientos. | Definir un procedimiento de contingencia para operaciones indispensables, con registro posterior y conciliación al recuperar el servicio. | GER / SIS | Registro de incidentes y operaciones regularizadas. |
| **RSK-13** | **Pérdida o corrupción de información.** | Respaldos fallidos, eliminación accidental o errores en la base de datos. | Pérdida de registros comerciales, financieros e históricos. | Mantener respaldos periódicos protegidos y comprobar su recuperación mediante pruebas de restauración. | SIS | Historial de respaldos y pruebas de recuperación. |
| **RSK-14** | **Baja adopción por parte del personal.** | Ventas y movimientos continúan registrándose únicamente fuera del ERP o aparecen registros incompletos. | Información desactualizada y abandono progresivo del sistema. | Implementar capacitación práctica y adopción gradual; contrastar operaciones registradas con las realizadas, sin eliminar controles manuales antes de validar su sustitución. | GER / VEN / ALM | Registros de capacitación, pruebas de uso y seguimiento de operaciones. |
| **RSK-15** | **Falta de continuidad después del proyecto académico.** | Dependencia exclusiva de estudiantes, ausencia de procedimientos técnicos o falta de responsables disponibles. | Deterioro, abandono o imposibilidad de mantener el sistema. | Documentar instalación, administración y recuperación; transferir conocimientos y definir responsables o servicios de mantenimiento posteriores. | GER / SIS | Documentación operativa, entrega técnica y responsable designado. |
| **RSK-16** | **Acceso informático no autorizado o exposición de información.** | Intentos de acceso sospechosos, contraseñas compartidas, cuentas desconocidas o comportamientos anómalos. | Robo, modificación o divulgación de datos; afectación de las operaciones. | Utilizar cuentas individuales, contraseñas seguras, autenticación adicional cuando esté disponible y configuración segura de accesos; revisar eventos sospechosos y retirar credenciales innecesarias. | SIS / GER | Revisión de cuentas, configuraciones de seguridad y registro de incidentes. |
| **RSK-17** | **Rendimiento insuficiente del ERP.** | Lentitud en búsquedas, apertura de productos, confirmación de ventas o movimientos simultáneos. | Demoras en la atención, errores operativos y rechazo del sistema. | Ejecutar pruebas con el catálogo y una carga representativa de usuarios y transacciones; supervisar recursos del servidor y corregir cuellos de botella antes de ampliar el uso. | SIS | Resultados de pruebas de rendimiento y registros de recursos. |
| **RSK-18** | **Incompatibilidad con dispositivos periféricos.** | Impresoras de tickets, lectores de códigos de barras u otros equipos no funcionan correctamente con el POS. | Interrupciones en caja, atención lenta y trabajo manual adicional. | Verificar compatibilidad y conectividad de los dispositivos antes de adquirirlos o utilizarlos; probar impresión, lectura y recuperación ante fallas. | SIS / VEN | Inventario de equipos y resultados de pruebas. |
| **RSK-19** | **Precios de venta desactualizados o inconsistentes.** | Diferencias entre el precio registrado en Odoo, el costo de reposición y el precio indicado por los propietarios. | Pérdida de margen, ventas con importes incorrectos y dependencia de consultas manuales. | Establecer responsables y un procedimiento de revisión de precios ante cambios relevantes de costos; validar los precios con GER antes de aplicar modificaciones. | GER / VEN / CMP | Historial de revisión y cambios de precios autorizados. |
| **RSK-20** | **Dependencia de servicios y componentes externos.** | Cambios de condiciones, suspensión de servicios, abandono de complementos o pérdida de soporte de proveedores. | Costos imprevistos, funcionalidades indisponibles y dificultades de mantenimiento. | Mantener un inventario de dependencias externas, revisar condiciones y continuidad de soporte y disponer de procedimientos alternativos para servicios críticos. | SIS / GER | Inventario de dependencias, condiciones de servicio y revisiones de continuidad. |

## 3. Aplicación y seguimiento

### 3.1. Responsabilidades

Los responsables indicados corresponden a los roles funcionales definidos para ERP-MIGAL:

- **GER:** supervisa riesgos empresariales, aprueba decisiones sensibles y determina medidas correctivas.
- **VEN, ALM, CMP y FCO:** aplican controles relacionados con sus operaciones y comunican incidencias.
- **SIS:** gestiona controles técnicos, accesos, respaldos, seguridad y mantenimiento.
- **Equipo ERP-MIGAL:** evalúa riesgos asociados con cambios de alcance y decisiones de implementación.

La asignación funcional no garantiza que los permisos o controles técnicos estén configurados. Su aplicación deberá comprobarse conforme al [modelo de autorización](seguridad/modelo-autorizacion.md).

Las responsabilidades logísticas aún no definidas deberán validarse con Gerencia.

### 3.2. Verificación de controles

Los controles deberán comprobarse mediante pruebas, revisiones operativas o evidencias documentadas, según corresponda.

Cuando dependan de una configuración, un módulo o un procedimiento todavía no implementado, **no se considerarán efectivos hasta su validación**.

Las incidencias detectadas deberán registrar su impacto, causa conocida, acción correctiva y responsable de atención.

### 3.3. Seguimiento y actualización

Los riesgos se mantienen centralizados en este documento. Las actividades concretas para resolver sus causas o implementar controles se gestionan en el [registro de pendientes](../producto/registro-pendientes.md).

La matriz se actualizará cuando:

- Se identifiquen nuevos riesgos durante el análisis, implementación, pruebas u operación.
- Cambien el alcance, los procesos, la arquitectura o las dependencias técnicas.
- Se produzcan incidentes que revelen riesgos previamente desconocidos.
- Se determine que un control existente es insuficiente o necesita modificarse.

Los nuevos riesgos recibirán identificadores consecutivos (`RSK-21`, `RSK-22`, etc.), conservando la trazabilidad de los registros anteriores.