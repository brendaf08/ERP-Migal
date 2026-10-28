# Seguridad y autorización

Esta carpeta contiene la documentación de **seguridad, roles funcionales, autorización y control de acceso** del sistema de información de **Ferre & Inversiones MIGAL**, basado en Odoo 18 Community.

Su propósito es establecer las responsabilidades de los usuarios, los permisos previstos y las restricciones necesarias para proteger las operaciones comerciales, operativas, contables y financieras de la empresa.

Los documentos representan un diseño funcional y técnico sujeto a validación. Su existencia no demuestra que los roles o permisos correspondientes ya estén configurados en Odoo.

## 1. Contenido de la carpeta

| Archivo                                                        | Descripción                                                                                                                |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| [modelo-autorizacion.md](modelo-autorizacion.md)               | Define los roles, permisos generales, restricciones, autorizaciones y asignación funcional de usuarios.                    |
| [revision-roles-funcionales.md](revision-roles-funcionales.md) | Analiza las responsabilidades operativas por actividad, diferenciando preparación, autorización, ejecución y verificación. |
| [matriz-permisos.xlsx](matriz-permisos.xlsx)                   | Documento previsto para detallar los permisos específicos por usuario o rol, aplicación, operación y tipo de acceso.       |

## 2. Alcance funcional de seguridad

El modelo considera seis roles:

- **GER:** Gerencia.
- **VEN:** Atención y Ventas.
- **ALM:** Almacén y Despacho.
- **CMP:** Compras y Abastecimiento.
- **FCO:** Facturación, Contabilidad y Cobros.
- **SIS:** Administración del Sistema.

Las responsabilidades abarcan CRM, Contactos, Ventas, Punto de Venta, Inventario, Compras y Facturación.

**Contabilidad y Finanzas** se considera un área funcional atendida mediante las capacidades de Facturación de Odoo Community. No se plantea una aplicación contable independiente dentro de esta definición de seguridad.

## 3. Criterios de control

Las decisiones de autorización se fundamentan en los siguientes principios:

1. **Mínimo privilegio:** los usuarios acceden únicamente a las funciones necesarias para sus responsabilidades.
2. **Segregación de funciones:** las operaciones sensibles deben contar con controles de aprobación o revisión.
3. **Autorización por responsabilidad:** las decisiones comerciales, financieras y operativas restringidas corresponden a los roles designados.
4. **Trazabilidad:** las operaciones relevantes deben permitir identificar al responsable y, cuando corresponda, al autorizador.
5. **Validación técnica:** los permisos propuestos deberán comprobarse en Odoo antes de considerarse implementados.

La asignación de varios roles a una misma persona no elimina la necesidad de controlar las operaciones sensibles.

## 4. Relación entre los documentos

El [modelo de autorización](modelo-autorizacion.md) constituye la referencia principal para establecer quién puede consultar, ejecutar y autorizar las operaciones.

La [revisión de roles funcionales](revision-roles-funcionales.md) desarrolla estas responsabilidades por actividad y permite identificar posibles conflictos entre preparación, ejecución, autorización y verificación.

La [matriz de permisos](matriz-permisos.xlsx) deberá traducir esas definiciones a permisos específicos y servir como referencia para las pruebas de seguridad.

Las decisiones sobre selección de aplicaciones, módulos técnicos y complementos de Odoo se documentan en la arquitectura del sistema, no en esta carpeta.

## 5. Implementación y validación

La definición documental de los roles no implica que los permisos estén configurados o probados.

Antes de considerar implementado el modelo de seguridad, se deberá:

- Contrastar los roles propuestos con los grupos de acceso reales de Odoo 18 Community.
- Verificar los permisos por aplicación y operación.
- Comprobar las restricciones relacionadas con compras, descuentos, créditos, inventario y operaciones financieras.
- Evaluar los efectos de combinar varios roles en un mismo usuario.
- Validar los accesos de FCO y GER a las operaciones contables y financieras correspondientes.
- Ejecutar pruebas con usuarios representativos y conservar las evidencias.

Los permisos que no puedan restringirse directamente mediante la configuración estándar deberán evaluarse para determinar los controles o ajustes necesarios.


