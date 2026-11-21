# -*- coding: utf-8 -*-
###############################################################################
# Módulo: partner_relation_multi
# Autor: Custom Development
# Licencia: AGPL-3
###############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    related_contact_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='partner_relation_multi_rel',
        column1='partner_id',
        column2='related_partner_id',
        string='Contactos asociados',
        help='Contactos a los que se puede recurrir desde esta ficha.',
    )

    @api.constrains('related_contact_ids')
    def _check_no_self_relation(self):
        """Impide que un contacto se asocie consigo mismo."""
        for partner in self:
            if partner in partner.related_contact_ids:
                raise ValidationError(
                    _('Un contacto no puede estar asociado a sí mismo.')
                )
