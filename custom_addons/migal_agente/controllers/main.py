import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# R-04: rate limiting conservador para endpoint público. Ventana fija por IP.
ESTADO_CUENTA_RATE_LIMIT = 15
ESTADO_CUENTA_RATE_WINDOW_SECONDS = 60


class MigalAgentePublico(http.Controller):

    def _estado_cuenta_ip(self):
        """IP de origen confiable. No confiar ciegamente en X-Forwarded-For:
        Odoo/werkzeug resuelve remote_addr según proxy_mode y proxies confiables.
        """
        remote = (request.httprequest.remote_addr or "").strip()
        return remote or "unknown"

    @http.route("/migal/estado-cuenta/<string:token>", type="http", auth="public", methods=["GET"], sitemap=False)
    def estado_cuenta_publico(self, token, **kwargs):
        """PDF de solo lectura de un estado de cuenta compartido (token UUID, caduca a las 24 h)."""
        ip = self._estado_cuenta_ip()
        rl = request.env["migal.agente.rate.limit"].sudo()
        allowed, retry_after = rl.check_and_hit(
            f"estado_cuenta:{ip}", ESTADO_CUENTA_RATE_LIMIT, ESTADO_CUENTA_RATE_WINDOW_SECONDS)
        if not allowed:
            _logger.warning(
                "Rate limit estado-cuenta público excedido ip=%s retry_after=%s", ip, retry_after)
            return request.make_response(
                "Too Many Requests",
                status=429,
                headers=[
                    ("Content-Type", "text/plain; charset=utf-8"),
                    ("Retry-After", str(retry_after)),
                    ("Cache-Control", "no-store, private"),
                    ("X-Robots-Tag", "noindex, nofollow, noarchive"),
                ],
            )

        pub = request.env["migal.agente.estado.cuenta.publicacion"].sudo()._buscar_vigente(token)
        if not pub:
            raise request.not_found()
        pub._registrar_vista(ip=ip)
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
