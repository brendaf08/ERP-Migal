# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
import logging

from werkzeug.exceptions import BadRequest, Forbidden

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import content_disposition, request

_logger = logging.getLogger(__name__)

# Modelos con exportación XLSX legítima a través de /xlsx_report. Cualquier
# modelo fuera de esta lista se rechaza antes de resolver el método.
ALLOWED_XLSX_REPORT_MODELS = frozenset({
    "account.aged.trial.balance",
    "account.balance.report",
    "account.bank.book.report",
    "account.cash.book.report",
    "account.day.book.report",
    "account.print.journal",
    "account.report.general.ledger",
    "account.report.partner.ledger",
    "cash.flow.report",
    "financial.report",
    "kit.account.tax.report",
    "res.partner",
})

MAX_OPTIONS_BYTES = 2 * 1024 * 1024


class XLSXReportController(http.Controller):
    """Controller para reportes XLSX del kit contable."""

    @staticmethod
    def _json_error(message, status=400):
        # 'message' se incluye por compatibilidad con handlers JS que leen
        # error.data.message; 'error' mantiene un campo explícito y seguro.
        return request.make_json_response(
            {"error": message, "message": message}, status=status)

    @staticmethod
    def _validate_report_name(report_name):
        if not isinstance(report_name, str):
            raise BadRequest("Nombre de reporte inválido.")
        name = report_name.strip()
        if not name or len(name) > 120:
            raise BadRequest("Nombre de reporte inválido.")
        if any(ch in name for ch in ('\x00', '\n', '\r', '/', '\\')):
            raise BadRequest("Nombre de reporte inválido.")
        if '..' in name:
            raise BadRequest("Nombre de reporte inválido.")
        return name

    @staticmethod
    def _parse_options(options):
        if not isinstance(options, str):
            raise BadRequest("Opciones de reporte inválidas.")
        if len(options.encode("utf-8")) > MAX_OPTIONS_BYTES:
            raise BadRequest("Opciones de reporte demasiado grandes.")
        try:
            data = json.loads(options)
        except (TypeError, ValueError):
            raise BadRequest("Opciones de reporte inválidas.")
        if not isinstance(data, dict):
            raise BadRequest("Opciones de reporte inválidas.")
        return data

    def _resolve_report_model(self, model):
        if not isinstance(model, str) or model not in ALLOWED_XLSX_REPORT_MODELS:
            _logger.warning(
                "XLSX report rechazado: modelo no permitido (%s) para uid=%s",
                model, request.env.user.id,
            )
            raise Forbidden("Modelo de reporte no permitido.")

        try:
            report_obj = request.env[model]
        except KeyError:
            raise BadRequest("Modelo de reporte inválido.")

        if not hasattr(report_obj, "get_xlsx_report"):
            raise BadRequest("El modelo no soporta exportación XLSX.")

        try:
            report_obj.check_access('read')
        except AccessError:
            _logger.warning(
                "XLSX report rechazado: sin permiso de lectura en %s para uid=%s",
                model, request.env.user.id,
            )
            raise Forbidden("No tiene permisos para exportar este reporte.")

        return report_obj

    @http.route('/xlsx_report', type='http', auth='user', methods=['POST'])
    def get_report_xlsx(self, model, options, output_format, report_name,
                        report_action=None, **kwargs):
        """Genera y devuelve un reporte XLSX autorizado."""
        try:
            report_name = self._validate_report_name(report_name)
            data = self._parse_options(options)
            if output_format != 'xlsx':
                raise BadRequest("Formato de salida no soportado.")

            report_obj = self._resolve_report_model(model)
            response = request.make_response(
                None, headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', content_disposition(
                        report_name + '.xlsx'))])
            report_obj.get_xlsx_report(data, response)
            response.set_cookie('fileToken', 'dummy token')
            return response
        except (BadRequest, Forbidden) as exc:
            return self._json_error(exc.description, status=exc.code)
        except Exception:
            _logger.exception(
                "Error generando reporte XLSX model=%s uid=%s",
                model, request.env.user.id,
            )
            return self._json_error(
                "No se pudo generar el reporte XLSX.", status=500)
