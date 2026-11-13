from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    migal_llm_enabled = fields.Boolean(
        string="Activar capa LLM", config_parameter="migal_agente.llm_enabled",
        help="El agente usará un LLM para interpretar lenguaje libre y redactar. Las decisiones siguen "
             "siendo de las reglas deterministas.")
    migal_llm_data_ack = fields.Boolean(
        string="Autorizo enviar datos al proveedor LLM", config_parameter="migal_agente.llm_data_ack",
        help="Obligatorio para activar el LLM: los datos de la consulta (clientes, cotizaciones, saldos) "
             "se envían al servicio externo. Requiere revisión de privacidad y aprobación de GER.")
    migal_llm_api_key = fields.Char(string="API key del LLM", config_parameter="migal_agente.llm_api_key")
    migal_url_publica = fields.Char(
        string="URL pública para clientes", config_parameter="migal_agente.url_publica",
        help="Dirección con la que el celular del cliente llega a Odoo (por ejemplo http://192.168.1.50:8069 en la "
             "red de la tienda, o un dominio). Se usa en el QR y en los enlaces. Si se deja vacía se usa web.base.url.")
    # Métodos de pago que se imprimen en el estado de cuenta (vacío = no se muestra)
    migal_pago_titular = fields.Char(string="Titular de las cuentas", config_parameter="migal_agente.pago_titular")
    migal_pago_yape = fields.Char(string="Yape (celular)", config_parameter="migal_agente.pago_yape")
    migal_pago_bcp_cuenta = fields.Char(string="BCP - N.º de cuenta", config_parameter="migal_agente.pago_bcp_cuenta")
    migal_pago_bcp_cci = fields.Char(string="BCP - CCI", config_parameter="migal_agente.pago_bcp_cci")
    migal_pago_bbva_cuenta = fields.Char(string="BBVA - N.º de cuenta", config_parameter="migal_agente.pago_bbva_cuenta")
    migal_pago_bbva_cci = fields.Char(string="BBVA - CCI", config_parameter="migal_agente.pago_bbva_cci")
    migal_llm_model = fields.Char(string="Modelo LLM", config_parameter="migal_agente.llm_model",
                                  default="claude-opus-5-5")
