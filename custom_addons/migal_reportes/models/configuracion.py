"""Opciones globales de diseño; los datos legales siempre vienen de res.company."""
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    migal_reportes_subtitulo = fields.Char(
        string="Línea descriptiva del encabezado A4",
        config_parameter="migal_reportes.subtitulo",
        default="Ferretería · Materiales para tus proyectos",
    )
    migal_reportes_pie_a4 = fields.Char(
        string="Texto del pie A4",
        config_parameter="migal_reportes.pie_a4",
        default="Documento generado por Ferre & Inversiones MIGAL.",
    )
    migal_reportes_pie_ticket = fields.Char(
        string="Texto final del ticket",
        config_parameter="migal_reportes.pie_ticket",
        default="Gracias por confiar en MIGAL.",
    )
    migal_reportes_mostrar_telefono = fields.Boolean(
        string="Mostrar teléfono de la empresa",
        config_parameter="migal_reportes.mostrar_telefono", default=True,
    )
    migal_reportes_mostrar_correo = fields.Boolean(
        string="Mostrar correo de la empresa",
        config_parameter="migal_reportes.mostrar_correo", default=True,
    )
    migal_reportes_mostrar_web = fields.Boolean(
        string="Mostrar página web de la empresa",
        config_parameter="migal_reportes.mostrar_web", default=False,
    )
    migal_reportes_mostrar_logo_ticket = fields.Boolean(
        string="Mostrar logotipo en el ticket",
        config_parameter="migal_reportes.mostrar_logo_ticket", default=True,
    )
    migal_reportes_a4_compacto = fields.Boolean(
        string="Separación compacta en A4",
        help="Reduce ligeramente los espacios en blanco en los documentos A4 largos.",
        config_parameter="migal_reportes.a4_compacto", default=False,
    )

    migal_reportes_solo_migal = fields.Boolean(
        string="Mostrar solo reportes MIGAL en Imprimir",
        config_parameter="migal_reportes.solo_migal", default=True,
        help="Oculta del menú de impresión los reportes ajenos a MIGAL en ventas, entregas y pagos. "
             "No elimina informes. Los comprobantes fiscales oficiales de facturas y boletas se conservan."
    )
