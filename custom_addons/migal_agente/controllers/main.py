from odoo import http
from odoo.http import request


class MigalAgentePublico(http.Controller):

    @http.route("/migal/estado-cuenta/<string:token>", type="http", auth="public", methods=["GET"], sitemap=False)
    def estado_cuenta_publico(self, token, **kwargs):
        """PDF de solo lectura de un estado de cuenta compartido (token UUID, caduca a las 24 h)."""
        pub = request.env["migal.agente.estado.cuenta.publicacion"]._buscar_vigente(token)
        if not pub:
            raise request.not_found()
        pub.sudo().vistas += 1
        pdf, _ = request.env["ir.actions.report"].sudo()._render_qweb_pdf(
            "migal_agente.report_estado_cuenta_publicado", pub.ids)
        return request.make_response(pdf, headers=[
            ("Content-Type", "application/pdf"),
            ("Content-Length", str(len(pdf))),
            ("Content-Disposition", 'inline; filename="Estado-de-cuenta-MIGAL.pdf"'),
            ("Cache-Control", "no-store, private"),
            ("X-Robots-Tag", "noindex, nofollow, noarchive"),
            ("Referrer-Policy", "no-referrer"),
        ])
