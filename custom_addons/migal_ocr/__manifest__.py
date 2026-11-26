{
    "name": "MIGAL · Escanear lista de productos (OCR + coincidencias)",
    "version": "19.0.1.1.0",
    "category": "Sales/Sales",
    "summary": "Lee una lista de productos (foto, PDF o texto), la vincula al catálogo con % de coincidencia "
               "y la agrega a una cotización",
    "description": """
Escanear lista de productos
===========================

1. En una cotización, pulse **Escanear lista** (o Ventas › Escanear lista).
2. Suba la foto o el PDF de la lista, o pegue el texto.
3. **Leer lista**: Gemini transcribe cada línea y su cantidad; el sistema propone el producto
   del catálogo con su porcentaje de coincidencia y hasta dos alternativas.
4. Revise o cambie el producto de cada línea y pulse **Agregar a la cotización**.

La IA solo transcribe; el producto lo propone el emparejador (normalizador ferretero +
similitud difusa) y lo confirma la persona. Solo se crean borradores: nada se confirma.
Origen: OCR y fuzzy matching de MIGAL SmartOps (ADR-011/ADR-012).
""",
    "author": "Grupo 1 GE703 - ERP MIGAL",
    "website": "https://github.com/brendaf08/ERP-Migal",
    "license": "LGPL-3",
    "depends": ["sale_management", "stock", "migal_agente"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "data/sinonimos.xml",
        "data/catalogo_fierros.xml",
        "views/documento_views.xml",
        "views/sinonimo_views.xml",
        "views/sale_order_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": ["migal_ocr/static/src/archivo_lista_field.js"],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
