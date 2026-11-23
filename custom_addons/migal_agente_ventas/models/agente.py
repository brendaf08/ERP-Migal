"""Agente de ventas. Responsable: Brenda Mirano.

Ficha y tareas: producto/agentes/ventas.md
"""
import logging
import re
from datetime import timedelta

from odoo import models
from odoo.tools import format_date

_logger = logging.getLogger(__name__)

SIN_ENTRADA = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
DIAS = {"type": "integer", "description": "Días de la ventana de análisis.", "minimum": 1, "maximum": 730}
NOMBRE = {"type": "string", "minLength": 2, "maxLength": 120, "description": "Nombre, RUC/DNI o referencia."}


def _soles(valor):
    return "S/ {:,.2f}".format(valor or 0.0)


class AgenteVentas(models.AbstractModel):
    _name = "migal.agente.ventas"
    _inherit = "migal.agente.especialista"
    _description = "Agente MIGAL · Ventas"
    _agente_codigo = "ventas"
    _agente_nombre = "Ventas"

    def _herramientas(self):
        return {
            "cotizaciones_por_vencer": {
                "description": "Cotizaciones abiertas cuya vigencia vence en los próximos días (para hacer seguimiento).",
                "input_schema": {"type": "object", "properties": {"dias": DIAS}, "required": [], "additionalProperties": False},
                "roles": ["VEN", "GER"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": ["RN-002"],
                "metodo": "cotizaciones_por_vencer",
            },
        }

    def _eventos_escuchados(self):
        return {"EV-027": "_al_validarse_recepcion", "EV-057": "_al_aprobarse_campana"}

    def _reconocer(self, texto):
        if re.search(r"\b(cotizaciones? por vencer|que cotizaciones vencen|vencen pronto|por caducar)\b", texto):
            return "cotizaciones_por_vencer", {}
        return None

    def cotizaciones_por_vencer(self, dias=7):
        hoy = self._hoy()
        ordenes = self.env["sale.order"].search([
            ("state", "in", ("draft", "sent")), ("validity_date", ">=", hoy),
            ("validity_date", "<=", hoy + timedelta(days=dias))], order="validity_date")
        filas = [[o.name, o.partner_id.display_name, format_date(self.env, o.validity_date), _soles(o.amount_total)]
                 for o in ordenes]
        return self._resultado(True, "ok", "Cotizaciones por vencer",
                               "%s cotizaciones vencen en los próximos %s días." % (len(ordenes), dias),
                               reglas=["RN-002"], datos={"cotizaciones": ordenes.mapped("name"), "tabla": {
                                   "columnas": ["Cotización", "Cliente", "Vence", "Total"], "filas": filas}})

    def _al_validarse_recepcion(self, datos):
        """EV-027. Por hacer: avisar al vendedor de las cotizaciones abiertas que esperaban estos productos."""
        _logger.info("Agente ventas: EV-027 recibido (%s).", datos.get("recepcion"))

    def _al_aprobarse_campana(self, datos):
        """EV-057. Por hacer: mostrar la promoción vigente a los vendedores."""
        _logger.info("Agente ventas: EV-057 recibido (%s).", datos.get("campana"))
