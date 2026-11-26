import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Inicializa los controles de OCR de forma independiente.

    Decisión funcional: el consentimiento del agente NO equivale al consentimiento OCR.
    Para instalaciones existentes sin parámetros OCR, se inicializa OCR IA deshabilitado
    y sin consentimiento explícito, sin copiar configuración del agente.
    Si ya existen parámetros OCR, se conservan sin sobrescribirlos.
    """
    ICP = env["ir.config_parameter"].sudo()

    # Si ya existe configuración OCR, no sobrescribir nada.
    if ICP.get_param("migal_ocr.llm_enabled", default=None) is not None:
        return

    # Instalación/upgrade sin parámetros OCR previos: seguro por defecto, consentimiento explícito.
    ICP.set_param("migal_ocr.llm_enabled", "False")
    ICP.set_param("migal_ocr.llm_data_ack", "False")

    # No copiar consentimiento/clave del agente. Solo completar defaults no sensibles si faltan.
    if not ICP.get_param("migal_ocr.gemini_modelos"):
        ICP.set_param(
            "migal_ocr.gemini_modelos",
            "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.6-flash",
        )

    _logger.info(
        "migal_ocr: parámetros de OCR inicializados como deshabilitados y sin consentimiento explícito."
    )
