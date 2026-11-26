from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    migal_llm_enabled = fields.Boolean(
        string="Usar IA en el chat", config_parameter="migal_agente.llm_enabled",
        help="El agente entiende mensajes escritos con libertad y redacta sus respuestas con IA.")
    migal_llm_data_ack = fields.Boolean(
        string="Autorizo enviar datos al proveedor de IA", config_parameter="migal_agente.llm_data_ack",
        help="Necesario para usar IA: el texto de la consulta (clientes, cotizaciones, saldos) o la foto de la "
             "lista escaneada se envían al proveedor elegido. Requiere aprobación de GER.")
    migal_llm_proveedor = fields.Selection(
        [("gemini", "Google Gemini"), ("anthropic", "Anthropic Claude")], string="Proveedor de IA",
        config_parameter="migal_agente.llm_proveedor", default="gemini",
        help="Google Gemini también se usa para leer las listas escaneadas (fotos y PDF).")
    migal_llm_api_key = fields.Char(string="Clave de API", config_parameter="migal_agente.llm_api_key")
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
    migal_llm_model = fields.Char(string="Modelo del chat", config_parameter="migal_agente.llm_model",
                                  help="Vacío: gemini-3.6-flash con Gemini, claude-opus-5-5 con Claude.")

    # Control de IA para OCR, independiente del agente.
    migal_ocr_llm_enabled = fields.Boolean(
        string="Usar IA en OCR (escaneo de listas)", config_parameter="migal_ocr.llm_enabled",
        help="Habilita el envío de fotos/PDF al proveedor de IA para transcribir listas. "
             "Es independiente del chat del agente: debe habilitarse explícitamente aunque el agente ya tenga IA activa.")
    migal_ocr_llm_data_ack = fields.Boolean(
        string="Autorizo enviar documentos OCR al proveedor de IA",
        config_parameter="migal_ocr.llm_data_ack",
        help="Consentimiento propio del OCR. Necesario para OCR con IA: la imagen/PDF de la lista se envía al proveedor configurado. "
             "No se hereda del consentimiento del agente; requiere aprobación responsable explícita.")
    migal_ocr_llm_api_key = fields.Char(
        string="Clave de API OCR", config_parameter="migal_ocr.llm_api_key",
        help="Vacía: usa la clave del Agente MIGAL cuando el proveedor es Gemini, solo si OCR está habilitado y con consentimiento OCR explícito.")
    migal_ocr_gemini_modelos = fields.Char(
        string="Modelos Gemini OCR", config_parameter="migal_ocr.gemini_modelos",
        help="Modelos separados por coma, en orden de preferencia. Vacío usa el valor por defecto del OCR.")
