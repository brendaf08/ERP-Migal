# Validación observada — 13/11/2026

- Windows 11, Docker Desktop con motor Linux 29.7.2 y PostgreSQL 16.
- Construcción de la imagen: correcta, qifparse 0.5 instalado.
- Restauración completa ejecutada con restaurar.ps1: correcta; PostgreSQL healthy, filestore extraído y Odoo iniciado.
- Parámetros comprobados por SQL: web.base.url y report.url = http://127.0.0.1:8069; web.base.url.freeze = True; migal_agente.llm_enabled = False. Ausentes url_publica y llm_api_key.
- Inicio de sesión real en navegador con el administrador y su nueva contraseña de demo: correcto.
- Menú Agente MIGAL y avatar flotante: visibles.
- S00586 → avatar → Disponibilidad → Cobertura preliminar: funciona; calcula faltante para el 16/11/2026 y atención completa estimada para el 19/11/2026. También se comprobó el botón superior de cobertura.
- Estado de cuenta de cliente PRUEBA existente: generado desde el agente. PDF descargado del endpoint local y renderizado con Poppler; una página, tablas, colores, encabezado y pie visibles con estilos. La empresa conserva el logo genérico de la base de pruebas.
- Pruebas en contenedor aislado del servidor web: `0 failed, 0 error(s) of 29 tests when loading database 'ferre_inversiones_migal'` (salida 0).
- Sintaxis de restaurar.sh comprobada con bash -n; sintaxis PowerShell comprobada y restauración Windows ejecutada. No se ejecutó restauración en un host Linux/macOS.
- 649 archivos de addons comparados byte a byte con el origen, sin diferencias. No se modificó el núcleo ni los addons. Se conservaron sus finales de línea y espacios existentes.
- Staging revisado: respaldo, ZIP, .env real, filestore y credenciales excluidos; odoo.conf versionado es únicamente la plantilla nueva sin secretos. Se buscaron coincidencias con secretos conocidos y patrones de claves privadas/tokens sin hallazgos reales.

## Incidencias resueltas y límites

1. Docker Desktop estaba detenido: iniciado desde su instalación de usuario. El CLI desktop start no localizaba su clave de registro.
2. Puerto 8069 ocupado por Odoo local: se identificó odoo-bin y se detuvo antes de iniciar Docker. La base PostgreSQL local original no fue modificada.
3. La primera ejecución de tests coincidió con la generación de assets del servidor web: SerializationFailure y cero tests. Se corrigió el procedimiento deteniendo el servicio y ejecutando un contenedor temporal; después se reinició Odoo.
4. `os.path.dirname(odoo.__file__)` falla en esta imagen namespace. `list(odoo.__path__)` devuelve `/usr/lib/python3/dist-packages/odoo`; addons confirma `/usr/lib/python3/dist-packages/odoo/addons`.
5. El nombre Constructora Andina del script antiguo no existe en esta copia: se verificó el estado de cuenta con PRUEBA - Constructora Joaquin, presente en la base. No se alteraron datos para forzar esa coincidencia.
6. QR público/cloudflared y envío de WhatsApp no ejecutados. La UI informó correctamente que el enlace es local sin publicador activo. No se envió ningún mensaje externo.
7. Las etiquetas de imágenes son móviles: la reproducción usa las versiones disponibles al construir. Digests observados abajo; fijarlos en FROM/image permite congelarlas.

## Imágenes observadas

- odoo:19: `sha256:49c9d2a9935f07f15e2404ce8649a84c4f0d4e70a880f7209ad27a19ab415f77`
- postgres:16: `sha256:11a9d238fbb48bab14599c57e41123254452b1a2d93c6c8595bce96f346bd082`

La evidencia completa y el paquete permanecen fuera de Git. El paquete fue generado antes de las pruebas y contiene solo la copia saneada; los tests y verificaciones posteriores afectan exclusivamente el volumen Docker de demostración.
