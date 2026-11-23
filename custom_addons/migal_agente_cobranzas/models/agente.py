"""Agente de cuentas por cobrar. Responsable: Gabriel Martínez.

Ficha y tareas: producto/agentes/cobranzas.md
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


class AgenteCobranzas(models.AbstractModel):
    _name = "migal.agente.cobranzas"
    _inherit = "migal.agente.especialista"
    _description = "Agente MIGAL · Cuentas por cobrar"
    _agente_codigo = "cobranzas"
    _agente_nombre = "Cuentas por cobrar"

    def _herramientas(self):
        return {
            "consultar_situacion_credito": {
                "description": "Deuda total y vencida de un cliente frente a su límite de crédito. No otorga ni modifica "
                               "crédito (RN-004).",
                "input_schema": {"type": "object", "properties": {"cliente": NOMBRE}, "required": ["cliente"],
                                 "additionalProperties": False},
                "roles": ["VEN", "FCO", "GER"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": ["RN-004"],
                "metodo": "consultar_situacion_credito",
            },
            "resumen_cartera": {
                "description": "Total por cobrar y vencido por tramos de antigüedad.",
                "input_schema": SIN_ENTRADA,
                "roles": ["FCO", "GER"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": [],
                "metodo": "resumen_cartera",
            },
        }

    def _eventos_escuchados(self):
        return {"EV-018": "_al_confirmarse_venta", "EV-058": "_al_detectarse_inconsistencia"}

    def _reconocer(self, texto):
        m = re.search(r"\b(?:situacion de credito|limite de credito|credito)\s+(?:de|del)\s+(?:cliente\s+)?(.+)$", texto)
        if m:
            return "consultar_situacion_credito", {"cliente": m.group(1).strip(" ?.!")}
        if re.search(r"\b(cartera|resumen de cobranzas?|cuanto nos deben)\b", texto):
            return "resumen_cartera", {}
        return None

    def _acciones_widget(self, record):
        if record._name == "res.partner" and record.customer_rank:
            return [{"id": "consultar_situacion_credito", "label": "Situación de crédito", "icon": "fa-credit-card",
                     "descripcion": "Deuda vencida frente al límite de crédito"}]
        return []

    def _argumentos_widget(self, accion, record, params):
        if accion == "consultar_situacion_credito":
            cliente = record.commercial_partner_id
            return {"cliente": cliente.vat or cliente.name}
        return None

    def _por_cobrar(self, partner=None):
        dominio = [("account_id.account_type", "=", "asset_receivable"), ("parent_state", "=", "posted"),
                   ("reconciled", "=", False), ("company_id", "=", self.env.company.id)]
        if partner:
            dominio.append(("partner_id", "child_of", partner.id))
        return self.env["account.move.line"].search(dominio).filtered(lambda l: l.amount_residual)

    def consultar_situacion_credito(self, cliente):
        partners = self.env["migal.agente.tool.estado.cuenta"]._buscar_cliente(cliente)
        if not partners:
            return self._resultado(False, "error", "Situación de crédito",
                                   "No encontré un cliente que coincida con «%s»." % cliente)
        if len(partners) > 1:
            return self._resultado(False, "ambiguo", "Situación de crédito",
                                   "Hay varios clientes que coinciden con «%s»." % cliente,
                                   datos={"cliente": cliente, "candidatos": partners[:8].mapped("display_name"),
                                          "candidatos_ids": partners[:8].ids})
        partner, hoy = partners, self._hoy()
        lineas = self._por_cobrar(partner)
        total = sum(lineas.mapped("amount_residual"))
        vencidas = lineas.filtered(lambda l: l.date_maturity and l.date_maturity < hoy)
        vencido = sum(vencidas.mapped("amount_residual"))
        dias = max([(hoy - l.date_maturity).days for l in vencidas], default=0)
        limite = partner.credit_limit if "credit_limit" in partner._fields else 0.0
        excede = bool(limite) and total > limite
        excluir = bool(vencido > 0 and dias > 30)
        partes = ["Debe %s" % _soles(total)]
        if vencido:
            partes.append("%s vencido (hasta %s días)" % (_soles(vencido), dias))
        if limite:
            partes.append("límite %s%s" % (_soles(limite), ", EXCEDIDO" if excede else ""))
        return self._resultado(
            True, "alerta" if (excede or dias > 30) else "ok", "Situación de crédito · %s" % partner.display_name,
            "; ".join(partes) + ".", res=partner, reglas=["RN-004"],
            avisos=["Cualquier crédito adicional lo decide Gerencia (RN-004)."] if (excede or vencido) else [],
            datos={"cliente": partner.display_name, "deuda_total": round(total, 2), "deuda_vencida": round(vencido, 2),
                   "dias_max_vencido": dias, "limite_credito": limite, "excede_limite": excede, "excluir": excluir})

    def resumen_cartera(self):
        hoy = self._hoy()
        tramos = {"por_vencer": 0.0, "0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "+90": 0.0}
        for linea in self._por_cobrar():
            dias = (hoy - linea.date_maturity).days if linea.date_maturity else 0
            clave = ("por_vencer" if dias <= 0 else "0-30" if dias <= 30 else "31-60" if dias <= 60
                     else "61-90" if dias <= 90 else "+90")
            tramos[clave] += linea.amount_residual
        por_cobrar = sum(tramos.values())
        vencido = por_cobrar - tramos["por_vencer"]
        return self._resultado(True, "ok", "Cartera por cobrar", "Por cobrar %s, vencido %s." % (
            _soles(por_cobrar), _soles(vencido)), datos={
            "por_cobrar": round(por_cobrar, 2), "vencido": round(vencido, 2),
            "tramos": {k: round(v, 2) for k, v in tramos.items()},
            "tabla": {"columnas": ["Tramo", "Monto"], "filas": [[k.replace("_", " "), _soles(v)] for k, v in tramos.items()]}})

    def _al_confirmarse_venta(self, datos):
        """EV-018. Por hacer: alertar si el cliente supera su límite de crédito con esta venta."""
        _logger.info("Agente cobranzas: EV-018 recibido para %s.", datos.get("orden"))

    def _al_detectarse_inconsistencia(self, datos):
        """EV-058. Por hacer: registrar la observación de contabilidad para revisarla."""
        _logger.info("Agente cobranzas: EV-058 recibido (%s).", datos.get("documento"))
