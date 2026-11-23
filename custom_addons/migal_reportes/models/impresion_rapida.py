"""Descargas directas en formularios sin pasar por Ajustes ni el catálogo."""
from odoo import fields, models, _
from odoo.exceptions import UserError


def _vista_previa(registro, a4, ticket, titulo=None):
    return registro.env["migal.reportes.vista.previa"].abrir(registro, a4, ticket, titulo=titulo)


def _imprimir(registro, a4, ticket, formato):
    registro.ensure_one()
    registro.check_access("read")
    external_id = a4 if formato == "a4" else ticket
    return registro.env.ref("migal_reportes." + external_id).report_action(registro)


class MigalVentaReportes(models.Model):
    _inherit = "sale.order"

    def action_migal_imprimir(self):
        self.ensure_one()
        titulo = (_("Cotización %s") if self.state in ("draft", "sent") else _("Orden %s")) % self.name
        return _vista_previa(self, "action_cotizacion_a4", "action_cotizacion_58", titulo)

    def action_migal_descargar_a4(self):
        return _imprimir(self, "action_cotizacion_a4", "action_cotizacion_58", "a4")

    def action_migal_descargar_58(self):
        return _imprimir(self, "action_cotizacion_a4", "action_cotizacion_58", "58")


class MigalFacturaReportes(models.Model):
    _inherit = "account.move"

    def _migal_reportar(self, formato):
        self.ensure_one()
        if self.move_type not in ("out_invoice", "out_refund", "out_receipt"):
            raise UserError(_("Solo se imprimen facturas, boletas y notas de cliente."))
        if self.state != "posted":
            raise UserError(_("Primero contabiliza el documento. Este reporte es una vista comercial, no el CPE oficial."))
        return _imprimir(self, "action_comprobante_a4", "action_comprobante_58", formato)

    def action_migal_vista_previa(self):
        self.ensure_one()
        if self.move_type not in ("out_invoice", "out_refund", "out_receipt") or self.state != "posted":
            return self._migal_reportar("a4")  # muestra la validación correspondiente
        return _vista_previa(self, "action_comprobante_a4", "action_comprobante_58")

    def action_migal_descargar_a4(self):
        return self._migal_reportar("a4")

    def action_migal_descargar_58(self):
        return self._migal_reportar("58")


class MigalEntregaReportes(models.Model):
    _inherit = "stock.picking"

    def action_migal_vista_previa(self):
        return _vista_previa(self, "action_entrega_a4", "action_entrega_58")

    def action_migal_descargar_a4(self):
        return _imprimir(self, "action_entrega_a4", "action_entrega_58", "a4")

    def action_migal_descargar_58(self):
        return _imprimir(self, "action_entrega_a4", "action_entrega_58", "58")


class MigalPagoReportes(models.Model):
    _inherit = "account.payment"

    def action_migal_vista_previa(self):
        return _vista_previa(self, "action_recibo_a4", "action_recibo_58")

    def action_migal_descargar_a4(self):
        return _imprimir(self, "action_recibo_a4", "action_recibo_58", "a4")

    def action_migal_descargar_58(self):
        return _imprimir(self, "action_recibo_a4", "action_recibo_58", "58")


class MigalClienteReportes(models.Model):
    _inherit = "res.partner"

    def _migal_estado_rapido(self, formato):
        self.ensure_one()
        self.check_access("read")
        p = self.commercial_partner_id
        hoy = fields.Date.context_today(self)
        wiz = self.env["migal.agente.estado.cuenta.wizard"].create({
            "partner_id": p.id,
            "fecha_desde": hoy.replace(day=1),
            "fecha_hasta": hoy,
        })
        wiz.action_generar()  # Reutiliza permisos y bitácora del Agente MIGAL.
        if not wiz.generado:
            raise UserError(_("El estado de cuenta no pudo generarse; revisa el cliente o tus permisos."))
        if formato == "vista":
            return wiz.action_migal_vista_previa()
        if formato == "a4":
            return wiz.action_imprimir_migal_a4()
        return wiz.action_imprimir_migal_58()

    def action_migal_estado_vista(self):
        return self._migal_estado_rapido("vista")

    def action_migal_estado_a4(self):
        return self._migal_estado_rapido("a4")

    def action_migal_estado_58(self):
        return self._migal_estado_rapido("58")
