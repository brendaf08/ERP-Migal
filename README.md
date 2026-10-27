
# Ferre & Inversiones MIGAL — Sistema Integrado Empresarial

Repositorio académico del **Grupo 1**, desarrollado para el curso **GE703 · Sistemas Integrados Empresariales**, de la Facultad de Ingeniería Industrial y de Sistemas de la Universidad Nacional de Ingeniería (UNI).

El proyecto tiene como finalidad proponer una arquitectura empresarial integrada para **Ferre & Inversiones MIGAL**, que permita articular procesos, datos, aplicaciones y controles, fortaleciendo la trazabilidad de sus operaciones comerciales y administrativas.

## 1. Contexto y propósito

Ferre & Inversiones MIGAL es una empresa del sector ferretero dedicada a la comercialización de materiales de construcción. Su operación comprende atención presencial, consultas y pedidos mediante WhatsApp, llamadas y referidos.

Actualmente, parte de la información del negocio se encuentra distribuida entre registros manuales, conocimiento de los propietarios y sistemas no integrados. Esta situación dificulta el seguimiento de pedidos, inventarios, precios, entregas y cobros.

Como respuesta, se propone utilizar **Odoo 18 Community** como plataforma integrada, diferenciando dos responsabilidades funcionales:

- **CRM:** gestión de interesados, oportunidades, cotizaciones, negociación y seguimiento comercial.
- **ERP:** validación y confirmación de pedidos, inventario, abastecimiento documental, entregas y registros económicos.

Se mantiene **KeyFacil** para la emisión de comprobantes electrónicos y **WhatsApp** como canal externo de comunicación, sin asumir integraciones automáticas.

La propuesta busca mejorar la consistencia de la información y el control operativo, de acuerdo con las capacidades y restricciones de MIGAL.

**Referencia:** [Contexto de la empresa](arquitectura/contexto-empresa.md).

## 2. Alcance y estado del proyecto

El proyecto se desarrolla de manera **incremental y acumulativa**, comprendiendo la arquitectura CRM–ERP y los siguientes procesos empresariales:

- **Order to Cash (O2C):** desde la necesidad comercial hasta la entrega, el cobro y el cierre de la operación.
- **Inventario:** control de existencias, ubicaciones, movimientos, reservas y ajustes.
- **Procure to Pay (P2P):** modelado documental del abastecimiento, recepción y obligaciones con proveedores.

La solución se documenta mediante modelos de procesos, decisiones arquitectónicas, reglas de negocio, una especificación funcional de la transición CRM–ERP, datos, diagramas y casos de prueba.

**Estado actual:** diseño funcional y arquitectónico sujeto a validación técnica. La presencia de documentos, modelos o casos de prueba no acredita por sí misma una implementación operativa en Odoo.

El alcance no presupone integraciones automáticas con KeyFacil o WhatsApp ni la utilización del módulo de Compras (`purchase`) de Odoo.

**Referencia:** [Alcance de la solución](arquitectura/alcance.md).

## 3. Estructura del repositorio

El repositorio se organiza conforme a las áreas documentales establecidas para el curso.

| Elemento | Propósito |
|---|---|
| `README.md` | Propósito, alcance, integrantes y pasos de reproducción. |
| `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE` | Convenciones de colaboración, historial de cambios y condiciones de uso. |
| `arquitectura/` | Vistas, interfaces, decisiones y versiones. |
| `procesos/` | Modelos, reglas, eventos y controles. |
| `datos/` | Diccionario, fuentes, datos de prueba y tratamiento de datos sensibles. |
| `producto/` | Código, automatizaciones, configuraciones o evidencias equivalentes. |
| `pruebas/` | Casos, resultados, incidencias y criterios de aceptación. |
| `fuentes/` | Bibliografía, licencias, atribución y declaración de uso de IA. |

### Documentación principal

| Tema | Ubicación |
|---|---|
| Alcance y arquitectura | [Alcance](arquitectura/alcance.md) |
| Decisiones arquitectónicas | [ADR](arquitectura/decisiones/) |
| Diagramas y vistas | [Vistas](arquitectura/vistas/) |
| Transición CRM–ERP | [INT-01](arquitectura/integraciones/INT-01-CRM-ERP.md) |
| Flujo comercial | [CRM](procesos/comercial-crm/flujo-comercial.md) |
| Proceso Order to Cash | [O2C](procesos/o2c/flujo.md) |
| Reglas y controles | [Catálogo de reglas](procesos/catalogo-reglas.md) |
| Diccionario de datos | [Datos](datos/diccionario-datos.md) |
| Casos de prueba | [Pruebas](pruebas/) |
| Bibliografía y uso de IA | [Fuentes](fuentes/) |

Cada documento desarrolla un propósito específico. Este README constituye el punto de entrada del proyecto y no sustituye la documentación especializada.

## 4. Consulta y reproducción de evidencias

Para revisar la documentación y reproducir las evidencias disponibles:

1. Clonar o descargar el repositorio y consultar este README.
2. Revisar el alcance, las decisiones y las vistas en `arquitectura/`.
3. Examinar los recorridos empresariales en `procesos/` y contrastarlos con las reglas y controles correspondientes.
4. Consultar el diccionario y los datos sintéticos en `datos/`, junto con los casos definidos en `pruebas/`.
5. Contrastar los supuestos y afirmaciones relevantes con las referencias disponibles en `fuentes/`.

Los diagramas se organizan mediante dos directorios complementarios:

- `.../fuentes/`: archivos editables de los diagramas, como `.puml` y `.bpm`.
- `.../render/`: representaciones exportadas para su consulta, principalmente `.png`.

Los archivos `.puml` pueden reproducirse mediante PlantUML y los `.bpm` mediante una herramienta compatible con su formato.

La consulta de diagramas, datos sintéticos y casos documentados permite revisar el diseño propuesto, pero **no equivale a ejecutar pruebas funcionales en Odoo**.

## 5. Integrantes

| Integrante | Rol de trabajo |
|---|---|
| Alejandro Flores | Facilitación |
| Brenda Mirano | Producto |
| César Joaquín | Procesos |
| Diego Pinedo | Arquitectura |
| Gabriel Martínez | Datos |
| Luis Núñez | Validación |

Los roles organizan el trabajo colaborativo. Las contribuciones deben poder verificarse mediante commits, Pull Requests, revisiones, documentos, modelos o evidencias.

## 6. Colaboración y licencia

El desarrollo del proyecto se gestiona mediante ramas de trabajo y Pull Requests hacia `main`, siguiendo convenciones comunes de nomenclatura, revisión y trazabilidad.

- [CONTRIBUTING.md](CONTRIBUTING.md): normas de colaboración y calidad documental.
- [CHANGELOG.md](CHANGELOG.md): registro de cambios relevantes del proyecto.
- [LICENSE](LICENSE): condiciones de uso del repositorio.
