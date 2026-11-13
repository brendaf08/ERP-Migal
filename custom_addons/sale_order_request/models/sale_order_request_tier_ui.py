# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models


class SaleOrderRequest(models.Model):
    _inherit = "sale.order.request"

    def _add_tier_validation_buttons(self, node, params):
        """Override para usar plantilla sin botones Request/Restart Validation.

        Renderiza solo el campo validation_status oculto, necesario para el
        mecanismo de readonly dinámico de OCA. Los botones Request Validation
        y Restart Validation se omiten deliberadamente (D-UI-06-A′).
        """
        str_element = self.env["ir.qweb"]._render(
            "sale_order_request.tier_validation_buttons", params
        )
        new_node = etree.fromstring(str_element)
        return new_node
