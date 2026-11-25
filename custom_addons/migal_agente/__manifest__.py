{
    "name": "Agente MIGAL",
    "version": "19.0.2.0.0",
    "category": "Sales/Sales",
    "summary": "Orquestador multiagente de MIGAL: registro de agentes, contratos, consultas, eventos, chat y bitácora",
    "description": """
Agente MIGAL (PC3)
==================

Agente integrado en Odoo 19 Community para Ferre & Inversiones MIGAL.
Estructura de agente:

* **Interfaz**: chat con «Agente MIGAL» en Conversaciones y botones en
  cotizaciones y clientes.
* **Orquestador** (``migal.agente``): interpreta la solicitud, selecciona la
  herramienta, aplica guardarraíles y compone la respuesta.
* **Registro de agentes** (ADR-007): descubre los módulos ``migal_agente_<codigo>``
  instalados, media sus consultas y eventos según ``agent/catalogo.py``
  (INT-02) y simula las consultas que su dueño aún no implementa.
* **Herramientas** con contrato JSON Schema y permisos por rol:
  ``preparar_whatsapp_cotizacion``, ``registrar_envio_whatsapp``,
  ``generar_estado_cuenta``, ``buscar_cotizaciones`` y ``consultar_cotizacion``
  más las de cada agente instalado (la cobertura pasó a cadena de suministro).
* **Cotizaciones por cliente y versiones**: «cotización de Luis» lista las
  cotizaciones abiertas que coinciden y pide elegir (cotización y versión).
  Una versión anterior sigue vigente hasta que vence su plazo.
* **Guardarraíles deterministas**: vetan descuentos, confirmaciones,
  reservas, crédito y facturación (RN-004, RN-006, RN-015) y escalan a GER.
* **Bitácora** (``migal.agente.log``) con el contrato de ``audit_log.jsonl``.
* **LLM opcional** (desactivado por defecto): solo interpreta y redacta;
  nunca decide ni escribe.

El agente no confirma ventas, no reserva stock, no crea compras, no aplica
descuentos ni registra pagos. Sus únicas escrituras son su bitácora y el
registro de envíos de WhatsApp confirmados por VEN.
""",
    "author": "Grupo 1 GE703 - ERP MIGAL",
    "website": "https://github.com/brendaf08/ERP-Migal",
    "license": "LGPL-3",
    "depends": [
        "mail",
        "portal",
        "sale_management",
        "sale_stock",
        "account",
        "point_of_sale",
        "sale_order_request",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "data/agente_data.xml",
        "data/agente_cron.xml",
        "report/estado_cuenta_report.xml",
        "wizard/whatsapp_wizard_views.xml",
        "wizard/cobertura_wizard_views.xml",
        "wizard/estado_cuenta_wizard_views.xml",
        "views/agente_log_views.xml",
        "views/regla_cobertura_views.xml",
        "views/whatsapp_envio_views.xml",
        "views/sale_order_views.xml",
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "migal_agente/static/src/agente_widget/agente_widget.scss",
            "migal_agente/static/src/agente_widget/agente_widget.xml",
            "migal_agente/static/src/agente_widget/agente_widget.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": True,
    "auto_install": False,
}
