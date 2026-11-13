# -*- coding: utf-8 -*-
###############################################################################
# Módulo: partner_relation_multi
# Autor: Custom Development
# Licencia: AGPL-3
###############################################################################


def _mirror_existing_relations(cr):
    """Duplica las relaciones existentes para que sean simétricas.

    Las instalaciones anteriores guardaban una sola fila por relación
    (``partner_id`` -> ``related_partner_id``). Aquí se crea la fila inversa
    de las relaciones que aún no la tengan.
    """
    cr.execute(
        """
        INSERT INTO partner_relation_multi_rel (partner_id, related_partner_id)
        SELECT related_partner_id, partner_id
        FROM partner_relation_multi_rel
        ON CONFLICT DO NOTHING
        """
    )


def post_init_hook(env):
    _mirror_existing_relations(env.cr)
