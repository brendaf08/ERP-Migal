"""Herramientas buscar_cotizaciones y consultar_cotizacion (solo lectura)."""
import difflib
import re

from odoo import models
from odoo.tools import format_date

from ..agent.guardrails import normalize
from .tool_base import ESTADOS_ABIERTOS

# Palabras que no identifican al cliente.
PALABRAS_VACIAS = {
    "de", "del", "la", "el", "los", "las", "y", "e", "cliente", "clienta", "senor", "senora", "sr", "sra",
    "srta", "don", "dona", "empresa", "sac", "srl", "eirl", "sa",
}


def _tokens(texto):
    return [t for t in re.split(r"[^a-z0-9]+", normalize(texto)) if len(t) > 1 and t not in PALABRAS_VACIAS]


def coincide_aproximado(texto, tokens, corte=0.8):
    """Todas las palabras buscadas aparecen (por prefijo o con un error de tipeo) en ``texto``."""
    palabras = [p for p in re.split(r"[^a-z0-9]+", normalize(texto)) if p]
    def una(t):
        return any(p.startswith(t) or (len(t) >= 4 and difflib.SequenceMatcher(None, t, p).ratio() >= corte)
                   for p in palabras)
    return bool(tokens) and all(una(t) for t in tokens)


class MigalAgenteToolCotizacion(models.AbstractModel):
    _name = "migal.agente.tool.cotizacion"
    _inherit = "migal.agente.tool.base"
    _description = "Herramienta de consulta de cotizaciones del Agente MIGAL"

    # ------------------------------------------------------------------
    # Datos de una versión / familia
    # ------------------------------------------------------------------
    def _estado_txt(self, order):
        return dict(order._fields["state"]._description_selection(self.env)).get(order.state, order.state)

    def _resumen_lineas(self, order, maximo=3):
        lineas = order.order_line.filtered(lambda l: not l.display_type and l.product_id)
        partes = ["%s × %g" % (l.product_id.name, l.product_uom_qty) for l in lineas[:maximo]]
        if len(lineas) > maximo:
            partes.append("y %s más" % (len(lineas) - maximo))
        return ", ".join(partes)

    def _datos_version(self, order, ultima):
        hoy = self._hoy()
        return {
            "ref": order.name,
            "order_id": order.id,
            "revision_number": order.revision_number,
            "es_ultima": order == ultima,
            "estado": self._estado_txt(order),
            "fecha": format_date(self.env, order.date_order),
            "total": order.amount_total,
            "simbolo": order.currency_id.symbol or "S/",
            "vigencia": format_date(self.env, order.validity_date) if order.validity_date else "",
            "vencida": bool(order.validity_date and order.validity_date < hoy),
            "productos": self._resumen_lineas(order),
            "n_lineas": len(order.order_line.filtered(lambda l: not l.display_type and l.product_id)),
        }

    def datos_familia(self, order):
        """Versiones disponibles de la cotización de ``order`` (la más reciente primero)."""
        familia = self._familia(order)
        ultima = familia[:1]
        disponibles = familia.filtered(lambda o: o.active and o.state in ESTADOS_ABIERTOS)
        return {
            "base": order.unrevisioned_name or order.name,
            "cliente": order.partner_id.display_name,
            "versiones": [self._datos_version(o, ultima) for o in disponibles],
        }

    # ------------------------------------------------------------------
    # buscar_cotizaciones
    # ------------------------------------------------------------------
    def _coincide(self, partner, tokens):
        return coincide_aproximado(" ".join(filter(None, [
            partner.display_name, partner.commercial_partner_id.name, partner.vat, partner.ref])), tokens)

    def buscar(self, cliente):
        tokens = _tokens(cliente)
        if not tokens:
            return self._resultado(False, "entrada_invalida", "Buscar cotizaciones",
                                   "Indique el nombre, RUC/DNI o referencia del cliente.")
        SO = self.env["sale.order"]
        abiertas = SO.search([("state", "in", ESTADOS_ABIERTOS)], order="date_order desc, id desc")
        abiertas = abiertas.filtered(lambda o: self._coincide(o.partner_id, tokens))
        # Una entrada por cotización (familia); se presenta su versión más reciente disponible.
        familias, vistas = [], set()
        for order in abiertas:
            base = (order.unrevisioned_name or order.name, order.company_id.id)
            if base in vistas:
                continue
            vistas.add(base)
            familias.append(self.datos_familia(order))
        confirmadas = len(SO.search([("state", "=", "sale")]).filtered(
            lambda o: self._coincide(o.partner_id, tokens)))
        if not familias:
            extra = (" Tiene %s venta(s) ya confirmada(s), que no son cotizaciones abiertas." % confirmadas
                     if confirmadas else "")
            return self._resultado(
                False, "sin_resultados", "Sin cotizaciones abiertas",
                "No encontré cotizaciones abiertas de clientes que coincidan con «%s».%s" % (cliente, extra),
                datos={"cliente_buscado": cliente, "opciones": [], "confirmadas": confirmadas})
        # Vigentes primero; dentro de cada grupo, la más reciente primero (orden de búsqueda).
        familias.sort(key=lambda f: f["versiones"][0]["vencida"])
        opciones = []
        for n, fam in enumerate(familias, 1):
            v = fam["versiones"][0]
            opciones.append(dict(fam, n=n, ref=v["ref"], order_id=v["order_id"]))
        clientes = sorted({f["cliente"] for f in familias})
        return self._resultado(
            True, "ok", "Cotizaciones abiertas",
            "Encontré %s cotización(es) abierta(s) de %s cliente(s) que coinciden con «%s»." % (
                len(opciones), len(clientes), cliente),
            datos={"cliente_buscado": cliente, "opciones": opciones, "clientes": clientes,
                   "confirmadas": confirmadas})

    # ------------------------------------------------------------------
    # consultar_cotizacion
    # ------------------------------------------------------------------
    def consultar(self, cotizacion):
        order, vigente, error = self._buscar_cotizacion(cotizacion)
        if error:
            return self._resultado(False, "error", "Consultar cotización", error, datos={"cotizacion": cotizacion})
        ok_version, detalle_version = self._control_version(order, vigente)
        familia = self.datos_familia(order)
        hoy = self._hoy()
        vencida = bool(order.validity_date and order.validity_date < hoy)
        simbolo = order.currency_id.symbol or "S/"
        lineas = [{
            "producto": l.product_id.display_name,
            "cantidad": l.product_uom_qty,
            "uom": l.product_uom_id.name,
            "precio": l.price_unit,
            "descuento": l.discount,
            "subtotal": l.price_subtotal,
        } for l in order.order_line.filtered(lambda l: not l.display_type and l.product_id)]
        controles = [
            self._control("Revisión vigente", ok_version, detalle_version),
            self._control("Vigencia", not vencida,
                          ("Válida hasta %s." % format_date(self.env, order.validity_date)) if order.validity_date
                          and not vencida else ("Sin fecha de vencimiento registrada." if not order.validity_date
                                                else "Venció el %s." % format_date(self.env, order.validity_date))),
        ]
        avisos = []
        if order.state in ESTADOS_ABIERTOS and order != vigente:
            avisos.append("Para aceptar esta propuesta debe confirmarse la versión más reciente: cree una nueva "
                          "versión a partir de esta si el cliente la prefiere.")
        return self._resultado(
            True, "ok", "Cotización %s" % order.name,
            "%s · %s · %s" % (order.partner_id.display_name, self._estado_txt(order),
                              "versión %s de la cotización %s" % (order.revision_number, familia["base"])),
            datos={
                "detalle_cotizacion": True,
                "cotizacion": order.name,
                "base": familia["base"],
                "cliente": order.partner_id.display_name,
                "documento": order.partner_id.vat or "",
                "vendedor": order.user_id.name or "",
                "estado": self._estado_txt(order),
                "fecha": format_date(self.env, order.date_order),
                "vigencia": format_date(self.env, order.validity_date) if order.validity_date else "",
                "vencida": vencida,
                "simbolo": simbolo,
                "lineas_cotizacion": lineas,
                "base_imponible": order.amount_untaxed,
                "impuestos": order.amount_tax,
                "total": order.amount_total,
                "versiones": familia["versiones"],
                "es_ultima": order == vigente,
                "disponible": order.active and order.state in ESTADOS_ABIERTOS,
                "url": "/odoo/sale.order/%s" % order.id,
            },
            controles=controles, avisos=avisos, res=order)
