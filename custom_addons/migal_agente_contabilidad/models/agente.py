"""Agente de contabilidad. Responsable: César Joaquín.

Ficha y tareas: producto/agentes/contabilidad.md
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


class AgenteContabilidad(models.AbstractModel):
    _name = "migal.agente.contabilidad"
    _inherit = "migal.agente.especialista"
    _description = "Agente MIGAL · Contabilidad"
    _agente_codigo = "contabilidad"
    _agente_nombre = "Contabilidad"

    def _herramientas(self):
        return {
            "pendientes_cierre": {
                "description": "Revisión de cierre del mes: documentos en borrador, pagos sin conciliar, facturas de "
                               "proveedor sin orden de compra, IGV referencial del mes y saldos por cobrar y por pagar.",
                "input_schema": SIN_ENTRADA,
                "roles": ["FCO", "GER"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": ["RN-009", "RN-014"],
                "metodo": "pendientes_cierre",
            },
        }

    def _eventos_escuchados(self):
        return {"EV-038": "_al_registrarse_documento", "EV-040": "_al_registrarse_documento",
                "EV-043": "_al_registrarse_documento", "EV-055": "_al_registrarse_documento"}

    def _reconocer(self, texto):
        if re.search(r"\b(pendientes de cierre|cierre (de|del) mes|como va la contabilidad|resumen contable|igv del mes)\b", texto):
            return "pendientes_cierre", {}
        return None

    def pendientes_cierre(self):
        hoy = self._hoy()
        inicio = hoy.replace(day=1)
        Move = self.env["account.move"]
        tipos = ("out_invoice", "out_refund", "in_invoice", "in_refund")
        borradores = Move.search_count([("move_type", "in", tipos), ("state", "=", "draft")])
        pagos = self.env["account.payment"].search([("state", "not in", ("draft", "canceled", "cancel"))])
        sin_conciliar = len(pagos.filtered(lambda p: "is_reconciled" in p._fields and not p.is_reconciled))
        compras = Move.search([("move_type", "=", "in_invoice"), ("state", "=", "posted")])
        sin_oc = len(compras.filtered(lambda f: not f.invoice_line_ids.purchase_line_id))
        del_mes = Move.search([("move_type", "in", tipos), ("state", "=", "posted"), ("invoice_date", ">=", inicio)])
        igv_ventas = sum(del_mes.filtered(lambda m: m.move_type.startswith("out")).mapped("amount_tax_signed"))
        igv_compras = -sum(del_mes.filtered(lambda m: m.move_type.startswith("in")).mapped("amount_tax_signed"))
        cartera = self._consultar("resumen_cartera", {})
        obligaciones = self._consultar("resumen_obligaciones", {})
        filas = [
            ["Documentos en borrador", borradores, "Revisar" if borradores else "OK"],
            ["Pagos sin conciliar", sin_conciliar, "Revisar" if sin_conciliar else "OK"],
            ["Facturas de proveedor sin orden de compra", sin_oc, "Revisar" if sin_oc else "OK"],
            ["IGV ventas del mes (referencial)", _soles(igv_ventas), ""],
            ["IGV compras del mes (referencial)", _soles(igv_compras), ""],
            ["Por cobrar / vencido", "%s / %s" % (_soles((cartera.get("datos") or {}).get("por_cobrar")),
                                                  _soles((cartera.get("datos") or {}).get("vencido"))),
             "Simulado" if cartera.get("simulado") else ""],
            ["Por pagar / vencido", "%s / %s" % (_soles((obligaciones.get("datos") or {}).get("por_pagar")),
                                                 _soles((obligaciones.get("datos") or {}).get("vencido"))),
             "Simulado" if obligaciones.get("simulado") else ""],
        ]
        revisar = sum(1 for f in filas if f[2] == "Revisar")
        return self._resultado(True, "alerta" if revisar else "ok", "Pendientes de cierre",
                               "%s puntos por revisar antes del cierre del mes." % revisar,
                               avisos=["KeyFacil conserva la emisión fiscal; el IGV mostrado es referencial (RN-009)."],
                               datos={"borradores": borradores, "pagos_sin_conciliar": sin_conciliar,
                                      "facturas_sin_oc": sin_oc, "igv_ventas": round(igv_ventas, 2),
                                      "igv_compras": round(igv_compras, 2),
                                      "tabla": {"columnas": ["Revisión", "Valor", "Estado"], "filas": filas}})

    def _al_registrarse_documento(self, datos):
        """EV-038/040/043/055. Por hacer: acumular el movimiento para la conciliación del cierre."""
        _logger.info("Agente contabilidad: documento recibido %s.", datos.get("factura") or datos.get("pago"))
