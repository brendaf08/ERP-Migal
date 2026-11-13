from odoo import fields, models


class MigalAgenteWhatsappEnvio(models.Model):
    """Registro de envíos de cotizaciones por WhatsApp confirmados por VEN."""

    _name = "migal.agente.whatsapp.envio"
    _description = "Envío de cotización por WhatsApp"
    _order = "fecha desc, id desc"
    _rec_name = "cotizacion"

    fecha = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
    order_id = fields.Many2one("sale.order", string="Cotización", required=True, readonly=True,
                               ondelete="cascade", index=True)
    cotizacion = fields.Char(string="Referencia enviada", required=True, readonly=True)
    revision_number = fields.Integer(string="N.º de revisión", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Destinatario", required=True, readonly=True)
    telefono = fields.Char(required=True, readonly=True)
    amount_total = fields.Monetary(string="Total enviado", readonly=True, currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", readonly=True)
    user_id = fields.Many2one("res.users", string="Enviado por", default=lambda s: s.env.user, readonly=True)
    mensaje = fields.Text(readonly=True)
