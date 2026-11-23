"""Ticket térmico de 58 mm con alto según su contenido.

El formato de papel define un rollo de 200 mm. Sin este ajuste, una cotización de
una línea deja más de media hoja en blanco y una larga se parte en varias páginas.
Antes de llamar a wkhtmltopdf se estima el alto a partir de las líneas visibles del
HTML (con ajuste de línea a ~32 caracteres por renglón en 58 mm).
"""
import math
import re

from odoo import api, models

CARACTERES_POR_RENGLON = 32
MM_POR_RENGLON = 4.6
MM_MARGEN = 18
ALTO_MIN, ALTO_MAX = 90, 1200

_BLOQUE_RE = re.compile(r"<(?:div|tr|p|br|h[1-6]|li|table)\b[^>]*>", re.I)
_ETIQUETA_RE = re.compile(r"<[^>]+>")


def alto_ticket_mm(body):
    """Alto estimado en mm para el HTML de un ticket."""
    cuerpo = re.sub(r"(?is)<(style|script|head)\b.*?</\1>", "", body or "")
    renglones = 0
    for trozo in _BLOQUE_RE.split(cuerpo):
        texto = re.sub(r"\s+", " ", _ETIQUETA_RE.sub(" ", trozo)).strip()
        if texto:
            renglones += max(1, math.ceil(len(texto) / CARACTERES_POR_RENGLON))
    imagenes = len(re.findall(r"<img\b", cuerpo, re.I))
    alto = MM_MARGEN + renglones * MM_POR_RENGLON + imagenes * 16
    return int(min(ALTO_MAX, max(ALTO_MIN, alto)))


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _run_wkhtmltopdf(self, bodies, report_ref=False, header=None, footer=None, landscape=False,
                         specific_paperformat_args=None, set_viewport_size=False):
        ticket = self.env.ref("migal_reportes.paperformat_migal_ticket58", raise_if_not_found=False)
        report = self._get_report(report_ref) if report_ref else self.browse()
        if ticket and report and report.paperformat_id == ticket and bodies:
            alto = max(alto_ticket_mm(b) for b in bodies)
            self = self.with_context(migal_ticket_alto_mm=alto)
        return super()._run_wkhtmltopdf(
            bodies, report_ref=report_ref, header=header, footer=footer, landscape=landscape,
            specific_paperformat_args=specific_paperformat_args, set_viewport_size=set_viewport_size)

    @api.model
    def _build_wkhtmltopdf_args(self, paperformat_id, landscape, specific_paperformat_args=None,
                                set_viewport_size=False):
        args = super()._build_wkhtmltopdf_args(
            paperformat_id, landscape, specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size)
        alto = self.env.context.get("migal_ticket_alto_mm")
        if alto and "--page-height" in args:
            args[args.index("--page-height") + 1] = "%smm" % alto
        return args
