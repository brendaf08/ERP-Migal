"""El asistente flotante del Agente MIGAL ofrece «Escanear lista» en las cotizaciones abiertas."""
from odoo import api, models

ACCION_ESCANEAR = {
    "id": "escanear_lista",
    "label": "Escanear lista del cliente",
    "icon": "fa-camera",
    "descripcion": "Sube la foto o pega la lista: te propongo cada producto con su % de coincidencia",
    "principal": True,
    "abrir": True,
}


class MigalAgenteOcr(models.AbstractModel):
    _inherit = "migal.agente"

    @api.model
    def widget_contexto(self, res_model=False, res_id=False):
        ctx = super().widget_contexto(res_model, res_id)
        if res_model != "sale.order" or not res_id:
            return ctx
        order = self.env["sale.order"].browse(res_id).exists()
        if not order or order.state not in ("draft", "sent") or not self.env.user.has_group(
                "sales_team.group_sale_salesman"):
            return ctx
        accion = dict(ACCION_ESCANEAR)
        if ctx.get("pestanas"):
            ctx["pestanas"].append({"id": "productos", "label": "Agregar productos", "icon": "fa-camera",
                                    "acciones": [accion]})
            ctx["acciones"] = ctx.get("acciones", []) + [accion]
        else:
            # Cotización recién creada, aún sin productos: la lista del cliente es el primer paso.
            ctx["acciones"] = [accion] + ctx.get("acciones", [])
            ctx["subtitulo"] = "%s · Aún no tiene productos. ¿Te dio una lista? Puedo leerla por ti." % (
                order.partner_id.display_name)
        return ctx

    def _widget_abrir(self, accion, record, params=None):
        if accion == "escanear_lista" and record._name == "sale.order":
            return record.action_migal_escanear_lista()
        return super()._widget_abrir(accion, record, params=params)
