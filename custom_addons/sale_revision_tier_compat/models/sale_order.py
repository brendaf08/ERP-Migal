# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""
Extensiones de sale.order para compatibilidad entre OCA Revision y Tier
Validation.

El addon sobrescribe unicamente _allow_to_remove_reviews() para respetar el
contexto preserve_tier_reviews_on_revision, impidiendo que Tier Validation elimine
los registros tier.review durante la cancelacion tecnica que OCA aplica a la
orden anterior al crear una revision.

No se modifica codigo de base_revision, sale_order_revision,
base_tier_validation ni sale_tier_validation.
"""

import ast
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # ---------------------------------------------------------------------
    # Metodo publico para crear revision preservando el historial Tier
    # ---------------------------------------------------------------------
    def create_revision_preserving_tier(self):
        """Crea una nueva revision de la orden conservando el historial
        tier.review de la revision anterior.

        Usa dos contextos de forma limitada y controlada:

        - ``skip_validation_check=True``: evita que Tier Validation bloquee
          la escritura tecnica de current_revision_id en la orden anterior
          durante la creacion de la revision.
        - ``preserve_tier_reviews_on_revision=True``: impide que
          _allow_to_remove_reviews() devuelva True cuando la orden anterior
          pasa a state='cancel', evitando el unlink de sus revisiones Tier.

        El alcance de ambos contextos se limita exclusivamente a la llamada a
        create_revision(); no afectan otras operaciones del sistema.

        Devuelve el registro de la nueva revision (no el action dict de
        create_revision()).
        """
        self.ensure_one()
        action = self.with_context(
            skip_validation_check=True,
            preserve_tier_reviews_on_revision=True,
        ).create_revision()
        # create_revision() devuelve un action dict cuya domain contiene
        # los IDs de las nuevas revisiones. Extraemos el primero.
        domain = ast.literal_eval(action["domain"])
        new_id = domain[0][2][0]
        return self.env[self._name].browse(new_id)

    # ---------------------------------------------------------------------
    # Override limitado de _allow_to_remove_reviews
    # ---------------------------------------------------------------------
    def _allow_to_remove_reviews(self, values):
        """Decide si es necesario eliminar las revisiones Tier de un
        registro.

        La implementacion estandar devuelve True cuando el estado cambia a
        cancel. Con el contexto preserve_tier_reviews_on_revision forzamos el
        retorno False para conservar el historial de aprobaciones de la
        orden anterior durante la creacion de una revision.

        En cualquier otro contexto se delega completamente en la
        implementacion de Tier Validation, sin alterar su comportamiento.
        """
        if self.env.context.get("preserve_tier_reviews_on_revision"):
            return False
        return super()._allow_to_remove_reviews(values)
