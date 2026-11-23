from odoo import fields, models
from odoo.tools import format_date

ESTADOS_ABIERTOS = ("draft", "sent")


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

    # ------------------------------------------------------------------
    # Versiones de una cotización (familia = mismo unrevisioned_name)
    # ------------------------------------------------------------------
    def _familia(self, order):
        """Todas las versiones de la cotización, de la más reciente a la original."""
        if not order:
            return order
        return self.env["sale.order"].with_context(active_test=False).search([
            ("unrevisioned_name", "=", order.unrevisioned_name or order.name),
            ("company_id", "=", order.company_id.id),
        ], order="revision_number desc, id desc")

    def _versiones_disponibles(self, order):
        """Versiones que siguen abiertas (borrador/enviada y no archivadas), la más reciente primero.

        Una versión anterior sigue disponible hasta que vence su plazo de vigencia
        (ver ``sale.order._prepare_revision_data`` en este módulo).
        """
        return self._familia(order).filtered(lambda o: o.active and o.state in ESTADOS_ABIERTOS)

    def _control_version(self, order, vigente):
        """Control «Versión» común a WhatsApp, QR y cobertura.

        - La versión más reciente siempre pasa.
        - Una versión anterior pasa mientras siga abierta (no vencida ni cancelada), con aviso.
        - Una versión reemplazada y ya cerrada se bloquea, indicando la vigente.
        """
        if order == vigente:
            return True, "Es la versión más reciente."
        if order.active and order.state in ESTADOS_ABIERTOS:
            hasta = (" hasta el %s" % format_date(self.env, order.validity_date)) if order.validity_date else ""
            return True, ("Versión anterior: sigue disponible%s. La versión más reciente es %s."
                          % (hasta, vigente.name))
        return False, "%s fue reemplazada por %s y ya no está disponible; use %s." % (
            order.name, vigente.name, vigente.name)

    def _control(self, nombre, ok, detalle):
        return {"control": nombre, "ok": bool(ok), "detalle": detalle}

    def _hoy(self):
        return fields.Date.context_today(self)
