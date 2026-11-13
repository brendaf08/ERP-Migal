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
        string='Contactos Asociados',
        help='Contactos o empresas asociados a este contacto. La relación es '
             'simétrica: se ve desde las dos fichas y funciona tanto para '
             'personas como para empresas. Es independiente de la empresa '
             'matriz (parent_id).',
    )

    @api.constrains('related_contact_ids')
    def _check_no_self_relation(self):
        """Impide que un contacto se asocie consigo mismo."""
        for partner in self:
            if partner in partner.related_contact_ids:
                raise ValidationError(
                    _('Un contacto no puede estar asociado a sí mismo.')
                )

    def _sync_related_contact_ids(self, pairs_to_add, pairs_to_remove):
        """Mantiene la relación simétrica en la tabla relacional.

        Odoo guarda una sola fila por cada escritura de un Many2many
        (``partner_id`` -> ``related_partner_id``). Para que la relación se
        vea desde las dos fichas se guarda también la fila inversa. Así la
        misma relación lógica existe en ambos sentidos sin tocar los campos
        estándar ``parent_id`` / ``child_ids``.

        ``pairs_to_add`` / ``pairs_to_remove`` contienen pares
        ``(partner_id, related_partner_id)``; aquí se reflejan en la fila
        inversa ``(related_partner_id, partner_id)``.
        """
        relation = 'partner_relation_multi_rel'
        cr = self.env.cr

        reverse_pairs = [
            (related_id, partner_id)
            for partner_id, related_id in pairs_to_remove
            if partner_id != related_id
        ]
        if reverse_pairs:
            cr.executemany(
                "DELETE FROM %s WHERE partner_id = %%s "
                "AND related_partner_id = %%s" % relation,
                reverse_pairs,
            )

        reverse_pairs = [
            (related_id, partner_id)
            for partner_id, related_id in pairs_to_add
            if partner_id != related_id
        ]
        if reverse_pairs:
            cr.executemany(
                "INSERT INTO %s (partner_id, related_partner_id) "
                "VALUES (%%s, %%s) ON CONFLICT DO NOTHING" % relation,
                reverse_pairs,
            )

        if pairs_to_add or pairs_to_remove:
            self.env['res.partner'].invalidate_model(['related_contact_ids'])

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        pairs = []
        for vals, partner in zip(vals_list, records):
            if vals.get('related_contact_ids'):
                pairs.extend(
                    (partner.id, related.id)
                    for related in partner.related_contact_ids
                    if related.id != partner.id
                )
        if pairs:
            self._sync_related_contact_ids(pairs, [])
        return records

    def write(self, vals):
        if 'related_contact_ids' not in vals:
            return super().write(vals)

        previous = {
            partner.id: set(partner.related_contact_ids.ids)
            for partner in self
        }
        result = super().write(vals)

        pairs_to_add = []
        pairs_to_remove = []
        for partner in self:
            current = set(partner.related_contact_ids.ids)
            added = current - previous[partner.id]
            removed = previous[partner.id] - current
            pairs_to_add.extend((partner.id, related_id) for related_id in added)
            pairs_to_remove.extend(
                (partner.id, related_id) for related_id in removed
            )

        self._sync_related_contact_ids(pairs_to_add, pairs_to_remove)
        return result
