"""Agente de cuentas por pagar. Responsable: Diego Pinedo.

Ficha y tareas: producto/agentes/pagos.md
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


class AgentePagos(models.AbstractModel):
    _name = "migal.agente.pagos"
    _inherit = "migal.agente.especialista"
    _description = "Agente MIGAL · Cuentas por pagar"
    _agente_codigo = "pagos"
    _agente_nombre = "Cuentas por pagar"

    def _herramientas(self):
        return {
            "facturas_por_vencer": {
                "description": "Facturas de proveedor sin pagar que vencen en los próximos días o ya vencieron.",
                "input_schema": {"type": "object", "properties": {"dias": DIAS, "proveedor": NOMBRE}, "required": [],
                                 "additionalProperties": False},
                "roles": ["FCO", "GER"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": ["RN-014"],
                "metodo": "facturas_por_vencer",
            },
            "resumen_obligaciones": {
                "description": "Total por pagar a proveedores, vencido y por vencer en 7 días.",
                "input_schema": SIN_ENTRADA,
                "roles": ["FCO", "GER"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": [],
                "metodo": "resumen_obligaciones",
            },
        }

    def _eventos_escuchados(self):
        return {"EV-027": "_al_validarse_recepcion", "EV-058": "_al_detectarse_inconsistencia"}

    def _reconocer(self, texto):
        if re.search(r"\b(facturas? por vencer|cuentas por pagar|que debemos|deudas? con proveedores|facturas? de proveedor)\b", texto):
            return "facturas_por_vencer", {}
        return None

    def _acciones_widget(self, record):
        if record._name == "res.partner" and record.supplier_rank:
            return [{"id": "facturas_por_vencer", "label": "Facturas por vencer", "icon": "fa-calendar",
                     "descripcion": "Facturas de este proveedor sin pagar"}]
        return []

    def _argumentos_widget(self, accion, record, params):
        if accion == "facturas_por_vencer":
            return {"proveedor": record.commercial_partner_id.name, "dias": 60}
        return None

    def _por_pagar(self):
        return self.env["account.move"].search([
            ("move_type", "=", "in_invoice"), ("state", "=", "posted"),
            ("payment_state", "in", ("not_paid", "partial")), ("company_id", "=", self.env.company.id)],
            order="invoice_date_due")

    def facturas_por_vencer(self, dias=7, proveedor=None):
        hoy = self._hoy()
        facturas = self._por_pagar().filtered(lambda f: f.invoice_date_due and f.invoice_date_due <= hoy + timedelta(days=dias))
        if proveedor:
            facturas = facturas.filtered(lambda f: proveedor.lower() in (f.partner_id.display_name or "").lower())
        vencidas = facturas.filtered(lambda f: f.invoice_date_due < hoy)
        filas = [[f.name, f.partner_id.display_name, format_date(self.env, f.invoice_date_due), _soles(f.amount_residual),
                  "Vencida" if f in vencidas else "Por vencer"] for f in facturas]
        return self._resultado(True, "ok", "Facturas de proveedor por vencer",
                               "%s facturas (%s vencidas) por %s." % (len(facturas), len(vencidas),
                                                                      _soles(sum(facturas.mapped("amount_residual")))),
                               reglas=["RN-014"], avisos=["Los pagos los ejecuta FCO; el agente solo propone (RN-014)."],
                               datos={"facturas": facturas.mapped("name"), "vencidas": vencidas.mapped("name"), "tabla": {
                                   "columnas": ["Factura", "Proveedor", "Vence", "Saldo", "Estado"], "filas": filas}})

    def resumen_obligaciones(self):
        hoy = self._hoy()
        facturas = self._por_pagar()
        por_pagar = sum(facturas.mapped("amount_residual"))
        vencido = sum(facturas.filtered(lambda f: f.invoice_date_due and f.invoice_date_due < hoy).mapped("amount_residual"))
        proximos = sum(facturas.filtered(lambda f: f.invoice_date_due and hoy <= f.invoice_date_due <= hoy + timedelta(days=7))
                       .mapped("amount_residual"))
        return self._resultado(True, "ok", "Obligaciones con proveedores", "Por pagar %s, vencido %s." % (
            _soles(por_pagar), _soles(vencido)), datos={"por_pagar": round(por_pagar, 2), "vencido": round(vencido, 2),
                                                        "proximos_7_dias": round(proximos, 2)})

    def _al_validarse_recepcion(self, datos):
        """EV-027. Por hacer: preparar el cruce con la factura del proveedor cuando llegue."""
        _logger.info("Agente pagos: EV-027 recibido (%s, %s).", datos.get("recepcion"), datos.get("orden_compra"))

    def _al_detectarse_inconsistencia(self, datos):
        """EV-058. Por hacer: registrar la observación de contabilidad para revisarla."""
        _logger.info("Agente pagos: EV-058 recibido (%s).", datos.get("documento"))
