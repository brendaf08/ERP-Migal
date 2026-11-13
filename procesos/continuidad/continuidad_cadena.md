# Continuidad de la Cadena y Relación Mantenimiento-Disponibilidad

**Estado:** Documento de análisis. Este archivo modela un escenario crítico de interrupción logística en Ferre & Inversiones MIGAL, analiza el impacto de la falla de un activo en la cadena de suministro (P2P y O2C) y sustenta la decisión principal de mitigación para asegurar el nivel de servicio. Los valores cuantitativos marcados con `[SIM]` son datos sintéticos formulados para el escenario.

## 1. Relación Mantenimiento - Disponibilidad - Servicio

La continuidad de las operaciones de despacho de MIGAL depende de una infraestructura logística pequeña y centralizada. Como se identificó en el [catálogo de activos](../activos_mantenimiento/activos.md), los equipos críticos operan con motores de combustión y presentan tiempos medios de reparación (MTTR) elevados. 

El mantenimiento preventivo actúa como el principal sostén de la **Disponibilidad**:
* Un mantenimiento correctivo (falla imprevista) inmoviliza un equipo crítico entre 16 y 24 horas (MTTR).
* Un mantenimiento preventivo programado representa una parada controlada de 4 a 6 horas (según el [plan de mantenimiento](../activos_mantenimiento/mantenimiento.md)), minimizando el impacto en los despachos diarios y acercando la disponibilidad a la meta del **95 %**.

## 2. Matriz Causa-Efecto (Escenario de Falla)

Se modela el escenario de falla imprevista del activo **ACT-03 (Montacargas de combustión)** o el **ACT-01 (Camión de baranda)** durante la temporada alta (noviembre a febrero).

| Etapa del Impacto | Descripción en el Escenario |
| :--- | :--- |
| **1. Paro del Activo (Causa)** | Falla mecánica imprevista del montacargas (único equipo capaz de levantar parihuelas pesadas) o del camión de baranda. |
| **2. Caída de Disponibilidad** | El activo queda inoperativo por un MTTR de 16 a 24 horas (1 a 2 jornadas laborales completas perdidas). La disponibilidad operativa cae por debajo del 92 %. |
| **3. Quiebre en la Cadena** | La Capacidad de Despacho (cuello de botella logístico) se reduce a más de la mitad (cayendo de las 40 toneladas/día nominales **[SIM]** a menos de 20 toneladas/día). |
| **4. Efecto en el Cliente** | Se incumplen las programaciones de entrega a las obras. La métrica de Nivel de Servicio OTIF (*On Time In Full*) cae por debajo de la alerta del 90 % **[SIM]**. |

## 3. Escenario Analizado: Problemas, Efectos y Decisión

Para evitar el quiebre de la cadena de suministro por indisponibilidad de activos críticos, se formula el siguiente análisis para la Gerencia (GER).

### A. Problemas
* **Alta dependencia de activos únicos:** La empresa depende de un solo montacargas para estiba pesada y una flota muy reducida. No existe redundancia de equipos.
* **Tiempos prolongados de inactividad:** Las fallas mecánicas correctivas tienen un MTTR proyectado de hasta 24 horas, lo que paraliza la operación de P2P (recepción) y O2C (despachos).

### B. Efectos Operativos y Comerciales
* **Entregas parciales o retrasadas:** Forzar el despacho manual o en vehículos no adecuados aumenta los tiempos de estiba, generando cuellos de botella en la tienda y almacenes.
* **Pérdida de fidelidad:** Los retrasos en obra generan sobrecostos a los clientes (albañiles paralizados), lo que debilita la recomendación "boca a boca" de los maestros de obra, que es el principal canal de captación de MIGAL.

### C. Decisión Principal de Mitigación
Para sostener la continuidad de la cadena de suministro, se toma la siguiente **decisión principal sustentada**:

> **Decisión:** Implementar un régimen estricto de **mantenimiento preventivo basado en tiempo/uso** (inspecciones diarias y servicios cada 250h/5000km) para asegurar la meta del 95 % de disponibilidad, combinado con un **protocolo logístico de contingencia (Outsourcing Spot)**.

**Sustento de la decisión:**
1. **Sustento Cuantitativo:** Cambiar las paradas por fallas (MTTR de 24h) a paradas planificadas (4h a 6h) reduce la indisponibilidad en un 75 %, asegurando que la capacidad de despacho se mantenga cerca de las 40 toneladas/día **[SIM]**.
2. **Protocolo de contingencia:** Dado que el mantenimiento preventivo no elimina el 100 % de las fallas, se establece como regla de negocio que ante cualquier falla de un activo de criticidad Alta (camión o montacargas) cuyo diagnóstico supere las 6 horas, GER autorizará el alquiler temporal (*outsourcing spot*) de un equipo de reemplazo para evitar que el indicador OTIF caiga por debajo del 90 %.