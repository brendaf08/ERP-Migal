from odoo import fields, models


class MigalAgenteToolBase(models.AbstractModel):
    """Utilidades comunes de las herramientas del agente (solo lectura sobre Odoo)."""

    _name = "migal.agente.tool.base"
    _description = "Herramienta base del Agente MIGAL"

    def _resultado(self, ok, estado, titulo, mensaje, *, datos=None, controles=None, reglas=None,
                   escalar_a=None, res=None, avisos=None):
        """Estructura estándar que devuelven todas las herramientas."""
        return {
            "ok": ok,
            "estado": estado,
            "titulo": titulo,
            "mensaje": mensaje,
            "datos": datos or {},
            "controles": controles or [],
            "avisos": avisos or [],
            "reglas": reglas or [],
            "escalar_a": escalar_a or [],
            "res_model": res._name if res else False,
            "res_id": res.id if res else False,
        }

    def _buscar_cotizacion(self, ref):
        """Localiza una cotización por referencia, distinguiendo revisiones antiguas.

        Devuelve (order, vigente, error). ``vigente`` es la revisión actual cuando la
        referencia corresponde a una revisión reemplazada.
        """
        SO = self.env["sale.order"].with_context(active_test=False)
        ref = (ref or "").strip().upper()
        order = SO.search([("name", "=", ref)], limit=1)
        if not order:
            order = SO.search([("unrevisioned_name", "=", ref), ("active", "=", True)], limit=1)
        if not order:
            return SO.browse(), SO.browse(), "No encontré la cotización %s (o no tiene acceso a ella)." % ref
        vigente = order
        if not order.active or order.current_revision_id:
            vigente = order.current_revision_id or order
            while vigente.current_revision_id:
                vigente = vigente.current_revision_id
        return order, vigente, None

    def _control(self, nombre, ok, detalle):
        return {"control": nombre, "ok": bool(ok), "detalle": detalle}

    def _hoy(self):
        return fields.Date.context_today(self)
