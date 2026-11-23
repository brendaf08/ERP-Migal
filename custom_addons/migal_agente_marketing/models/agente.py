"""Agente de marketing. Responsable: Brenda Mirano.

Ficha y tareas: producto/agentes/marketing.md
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


class AgenteMarketing(models.AbstractModel):
    _name = "migal.agente.marketing"
    _inherit = "migal.agente.especialista"
    _description = "Agente MIGAL · Marketing"
    _agente_codigo = "marketing"
    _agente_nombre = "Marketing"

    def _herramientas(self):
        return {
            "clientes_inactivos": {
                "description": "Clientes que compraron antes pero no en los últimos días, indicando si conviene excluirlos "
                               "de una campaña por morosidad.",
                "input_schema": {"type": "object", "properties": {"dias": DIAS}, "required": [], "additionalProperties": False},
                "roles": ["GER", "VEN"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": ["RN-022"],
                "metodo": "clientes_inactivos",
            },
            "productos_para_promocion": {
                "description": "Productos con stock y baja rotación, candidatos a promoción (dato de cadena de suministro).",
                "input_schema": {"type": "object", "properties": {"dias": DIAS}, "required": [], "additionalProperties": False},
                "roles": ["GER", "VEN"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": ["RN-022"],
                "metodo": "productos_para_promocion",
            },
        }

    def _reconocer(self, texto):
        if re.search(r"\b(clientes? inactivos?|clientes? que no compran|clientes? dormidos?)\b", texto):
            return "clientes_inactivos", {}
        if re.search(r"\b(baja rotacion|productos? para promocion|que promocionar|que productos promocionar)\b", texto):
            return "productos_para_promocion", {}
        return None

    def clientes_inactivos(self, dias=60):
        hoy = self._hoy()
        limite = hoy - timedelta(days=dias)
        ventas = self.env["sale.order"].search([("state", "=", "sale")])
        ultima = {}
        for orden in ventas:
            cliente = orden.partner_id.commercial_partner_id
            fecha = orden.date_order.date() if orden.date_order else None
            if fecha and (cliente not in ultima or fecha > ultima[cliente]):
                ultima[cliente] = fecha
        inactivos = sorted([(c, f) for c, f in ultima.items() if f < limite], key=lambda x: x[1])
        filas, excluidos = [], 0
        for cliente, fecha in inactivos:
            credito = self._consultar("consultar_situacion_credito", {"cliente": cliente.vat or cliente.name})
            excluir = bool((credito.get("datos") or {}).get("excluir"))
            excluidos += excluir
            filas.append([cliente.display_name, format_date(self.env, fecha), (hoy - fecha).days,
                          "Sí (morosidad)" if excluir else "No"])
        return self._resultado(True, "ok", "Clientes inactivos",
                               "%s clientes sin compras en %s días; %s conviene excluirlos por morosidad." % (
                                   len(inactivos), dias, excluidos),
                               avisos=["Una campaña a estos clientes requiere la aprobación de Gerencia (RN-022)."],
                               datos={"clientes": [c.display_name for c, _f in inactivos], "tabla": {
                                   "columnas": ["Cliente", "Última compra", "Días", "Excluir"], "filas": filas}})

    def productos_para_promocion(self, dias=90):
        res = self._consultar("consultar_baja_rotacion", {"dias": dias})
        res["titulo"] = "Productos para promoción"
        return res
