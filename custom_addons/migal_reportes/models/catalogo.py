"""Catálogo de diseños, muestras explicativas y selección de registros reales."""
from datetime import date
from html import escape

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


DOCUMENTOS = [
    ("estado", "Estado de cuenta", "Cobranzas", "Cliente, movimientos, saldos y deuda vencida"),
    ("cotizacion", "Cotización / orden", "Ventas", "Productos, condiciones comerciales e importes"),
    ("comprobante", "Factura / boleta / notas", "Facturación", "Vista comercial; no reemplaza al CPE oficial"),
    ("entrega", "Resumen de entrega", "Inventario", "Movimientos y cantidades de la entrega"),
    ("recibo", "Constancia interna de pago", "Contabilidad", "Registro interno del pago; no es un CPE"),
]


def _settings(env):
    icp = env["ir.config_parameter"].sudo()
    return {
        "subtitulo": icp.get_param("migal_reportes.subtitulo", "Ferretería · Materiales para tus proyectos") or "",
        "pie_a4": icp.get_param("migal_reportes.pie_a4", "Documento generado por Ferre & Inversiones MIGAL.") or "",
        "pie_ticket": icp.get_param("migal_reportes.pie_ticket", "Gracias por confiar en MIGAL.") or "",
        "telefono": icp.get_param("migal_reportes.mostrar_telefono", "True") != "False",
        "correo": icp.get_param("migal_reportes.mostrar_correo", "True") != "False",
        "web": icp.get_param("migal_reportes.mostrar_web", "False") == "True",
        "logo_ticket": icp.get_param("migal_reportes.mostrar_logo_ticket", "True") != "False",
    }


class MigalReportesCatalogo(models.Model):
    _name = "migal.reportes.catalogo"
    _description = "Catálogo de formatos de impresión MIGAL"
    _order = "secuencia, id"
    _rec_name = "nombre"

    nombre = fields.Char(required=True, readonly=True)
    codigo = fields.Selection([(r[0], r[1]) for r in DOCUMENTOS], required=True, readonly=True)
    area = fields.Char(readonly=True)
    descripcion = fields.Char(readonly=True)
    secuencia = fields.Integer(default=10, readonly=True)
    vista_a4 = fields.Html(string="Vista ilustrativa A4", compute="_compute_muestras", sanitize=False)
    vista_58 = fields.Html(string="Vista ilustrativa ticket 58 mm", compute="_compute_muestras", sanitize=False)

    @api.depends("codigo")
    def _compute_muestras(self):
        cfg = _settings(self.env)
        company = self.env.company
        nombre = escape(company.name or "Ferre & Inversiones MIGAL")
        ruc = escape(company.vat or "RUC de la empresa")
        subt = escape(cfg["subtitulo"])
        common = f"{nombre} · RUC {ruc}"
        if cfg["telefono"] and company.phone:
            common += " · " + escape(company.phone)
        if cfg["correo"] and company.email:
            common += " · " + escape(company.email)
        if cfg["web"] and company.website:
            common += " · " + escape(company.website)
        logo = "/migal_reportes/static/img/logo_migal.png"
        logo_bw = "/migal_reportes/static/img/logo_migal_bw.png"
        a4_foot = escape(cfg["pie_a4"])
        ticket_foot = escape(cfg["pie_ticket"])
        for rec in self:
            titulo = escape(rec.nombre or "Documento")
            # Muestras inventadas, claramente marcadas como ilustrativas; nunca contienen datos reales de clientes.
            lineas = {
                "estado": [("Saldo anterior", "S/ 150.00"), ("Factura de ejemplo", "S/ 120.00"), ("Abono de ejemplo", "− S/ 50.00")],
                "cotizacion": [("Producto de ejemplo × 2", "S/ 80.00"), ("Producto de ejemplo × 1", "S/ 45.00")],
                "comprobante": [("Producto de ejemplo × 1", "S/ 100.00"), ("Impuestos (ejemplo)", "S/ 18.00")],
                "entrega": [("Producto A", "2 un."), ("Producto B", "1 un.")],
                "recibo": [("Importe registrado", "S/ 125.00"), ("Método de pago", "Ejemplo")],
            }.get(rec.codigo, [])
            items_a4 = "".join("<tr><td style='padding:9px;border-bottom:1px solid #e5ebf1'>%s</td><td style='text-align:right;padding:9px;border-bottom:1px solid #e5ebf1'>%s</td></tr>" % (escape(k), escape(v)) for k,v in lineas)
            items_t = "".join("<div style='padding:5px 0;border-bottom:1px dotted #aaa;display:flex;justify-content:space-between;gap:8px'><span>%s</span><span style='white-space:nowrap'>%s</span></div>" % (escape(k),escape(v)) for k,v in lineas)
            rec.vista_a4 = f"""<div style="max-width:650px;background:#eef2f7;padding:18px">
  <div style="background:white;min-height:415px;padding:32px 32px 20px;border:1px solid #e2e9f1;box-shadow:0 3px 12px #cbd5e166;font-family:Arial,sans-serif;color:#29384c">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:14px;border-bottom:3px solid #073779;padding-bottom:18px">
      <img src="{logo}" style="width:185px;max-width:42%;height:auto" alt="Logo MIGAL"/>
      <div style="font-size:10px;color:#5e6c7d;text-align:right;overflow-wrap:anywhere">{common}<div>{subt}</div></div>
    </div>
    <div style="display:flex;justify-content:space-between;gap:12px;margin-top:27px">
      <div><div style="font-size:23px;font-weight:700;color:#073779">{titulo}</div><div style="font-size:11px;color:#6b7889;margin-top:5px">Cliente de ejemplo · Fecha de ejemplo</div></div>
      <div style="text-align:right;font-size:11px;color:#667" >FORMATO A4<br/>VISTA ILUSTRATIVA</div>
    </div>
    <table style="border-collapse:collapse;width:100%;margin-top:26px;font-size:12px"><thead><tr style="background:#ecf3fa;color:#073779"><th style="text-align:left;padding:9px">Concepto</th><th style="text-align:right;padding:9px">Importe / Cantidad</th></tr></thead><tbody>{items_a4}</tbody></table>
    <div style="text-align:right;margin-top:22px;font-size:17px;font-weight:bold;color:#073779">Resumen · S/ 125.00</div>
    <div style="margin-top:35px;padding-top:11px;border-top:1px solid #e3e8ee;font-size:10px;color:#667788">{a4_foot}</div>
  </div>
  <div style="margin-top:9px;color:#64748b;font-size:11px">Muestra de estilo. Para comprobar valores reales, usa «Imprimir con datos de Odoo».</div>
</div>"""
            logo_html = f'<img src="{logo_bw}" style="max-width:145px;width:100%;max-height:58px;object-fit:contain" alt="MIGAL"/>' if cfg["logo_ticket"] else '<b>MIGAL</b>'
            rec.vista_58 = f"""<div style="background:#f1f3f5;padding:18px;text-align:center">
  <div style="display:inline-block;background:white;vertical-align:top;text-align:left;width:215px;min-height:375px;padding:12px 10px;box-shadow:0 2px 10px #00000018;font-family:monospace;color:#111;font-size:10px;overflow-wrap:anywhere">
   <div style="text-align:center">{logo_html}<br/><b>{nombre}</b><br/>RUC {ruc}</div>
   <div style="margin:13px 0 8px;border-top:1px dashed #333"></div>
   <div style="text-align:center;font-size:12px;font-weight:bold">{titulo.upper()}</div>
   <div style="text-align:center;font-size:9px">VISTA ILUSTRATIVA · 58 mm</div>
   <div style="margin:13px 0 10px;border-top:1px dashed #333"></div>
   <div>Cliente: Ejemplo<br/>Fecha: --/--/----</div>
   <div style="margin:12px 0">{items_t}</div>
   <div style="text-align:right;border-top:1px dashed #333;padding-top:8px"><b>RESUMEN S/ 125.00</b></div>
   <div style="margin-top:18px;text-align:center;border-top:1px dashed #333;padding-top:10px">{ticket_foot}</div>
  </div>
  <div style="margin-top:9px;color:#64748b;font-size:11px">Muestra de estilo. No equivale a un PDF de impresión.</div>
</div>"""

    def action_imprimir_con_datos(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Imprimir con datos reales de Odoo"),
            "res_model": "migal.reportes.imprimir.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_documento_id": self.id},
        }

    def action_empresa(self):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(_("Solo un administrador puede modificar los datos oficiales de la empresa."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Datos de la empresa"),
            "res_model": "res.company",
            "view_mode": "form",
            "res_id": self.env.company.id,
            "target": "current",
        }

    def action_configurar(self):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(_("Solo un administrador puede cambiar la configuración de plantillas."))
        return self.env.ref("migal_reportes.action_migal_reportes_ajustes").read()[0]


class MigalReportesImprimirWizard(models.TransientModel):
    _name = "migal.reportes.imprimir.wizard"
    _description = "Impresión de un reporte MIGAL con datos reales"

    documento_id = fields.Many2one("migal.reportes.catalogo", required=True, default=lambda self: self.env["migal.reportes.catalogo"].search([], order="secuencia", limit=1))
    codigo = fields.Selection(related="documento_id.codigo", readonly=True)
    formato = fields.Selection([("a4", "A4"), ("58", "Ticket 58 mm")], required=True, default="a4")
    partner_id = fields.Many2one("res.partner", string="Cliente")
    sale_order_id = fields.Many2one("sale.order", string="Cotización / orden")
    account_move_id = fields.Many2one("account.move", string="Factura, boleta o nota")
    picking_id = fields.Many2one("stock.picking", string="Entrega")
    payment_id = fields.Many2one("account.payment", string="Pago")
    fecha_desde = fields.Date(default=lambda s: fields.Date.context_today(s).replace(day=1))
    fecha_hasta = fields.Date(default=fields.Date.context_today)

    def action_imprimir_venta_a4(self):
        self.ensure_one()
        accion = self.sale_order_id.action_migal_descargar_a4()
        accion["close_on_report_download"] = True
        return accion

    def action_imprimir_venta_58(self):
        self.ensure_one()
        accion = self.sale_order_id.action_migal_descargar_58()
        accion["close_on_report_download"] = True
        return accion

    def action_imprimir(self):
        self.ensure_one()
        codigo = self.codigo
        if not codigo:
            raise UserError(_("Selecciona un documento."))
        if codigo == "estado":
            if not self.partner_id:
                raise UserError(_("Selecciona un cliente."))
            if not self.fecha_desde or not self.fecha_hasta:
                raise UserError(_("Selecciona el período del estado de cuenta."))
            if self.fecha_desde > self.fecha_hasta:
                raise UserError(_("La fecha inicial debe ser anterior o igual a la fecha final."))
            wizard = self.env["migal.agente.estado.cuenta.wizard"].create({
                "partner_id": self.partner_id.id,
                "fecha_desde": self.fecha_desde,
                "fecha_hasta": self.fecha_hasta,
            })
            wizard.action_generar()  # Mantiene permisos, bitácora y cálculo del agente.
            if not wizard.generado:
                raise UserError(_("No se pudo generar el estado de cuenta. Verifica los permisos o datos del cliente."))
            return wizard.action_imprimir_migal_a4() if self.formato == "a4" else wizard.action_imprimir_migal_58()
        field = {"cotizacion":"sale_order_id", "comprobante":"account_move_id", "entrega":"picking_id", "recibo":"payment_id"}[codigo]
        record = self[field].exists()
        if not record:
            raise UserError(_("Selecciona un registro guardado de Odoo para imprimir."))
        record.check_access("read")
        xmlids = {
            "cotizacion": ("action_cotizacion_a4", "action_cotizacion_58"),
            "comprobante": ("action_comprobante_a4", "action_comprobante_58"),
            "entrega": ("action_entrega_a4", "action_entrega_58"),
            "recibo": ("action_recibo_a4", "action_recibo_58"),
        }
        xmlid = xmlids[codigo][0 if self.formato == "a4" else 1]
        return self.env.ref("migal_reportes.%s" % xmlid).report_action(record)
