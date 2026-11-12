# -*- coding: utf-8 -*-
###############################################################################
# Módulo: partner_relation_multi
# Autor: Custom Development
# Licencia: AGPL-3
###############################################################################


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        INSERT INTO partner_relation_multi_rel (partner_id, related_partner_id)
        SELECT related_partner_id, partner_id
        FROM partner_relation_multi_rel
        ON CONFLICT DO NOTHING
        """
    )
