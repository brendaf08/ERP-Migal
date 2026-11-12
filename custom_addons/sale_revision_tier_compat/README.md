Sale Revision Tier Compatibility
================================

Addon tecnico generico y reutilizable para Odoo 19 Community que permite
usar conjuntamente:

- OCA ``base_revision`` y ``sale_order_revision`` (versionado de cotizaciones)
- Odoo ``base_tier_validation`` y ``sale_tier_validation`` (aprobaciones en etapas)

Problema
--------
Al crear una revision de cotizacion con OCA Revision sobre un documento que
tiene registros ``tier.review``, Tier Validation elimina fisicamente las
aprobaciones anteriores cuando la orden pasada pasa a ``state='cancel'``.

Solucion
--------
Este addon sobresobre unicamente ``_allow_to_remove_reviews()`` en
``sale.order`` para respetar el contexto ``preserve_tier_reviews_on_revision``.
Cuando ese contexto esta activo, el metodo devuelve ``False``, impidiendo que
Tier Validation elimine los registros de aprobacion de la orden anterior.

El alcance del contexto se limita estrictamente a la creacion de revisiones
mediante el metodo publico ``create_revision_preserving_tier()``, que ademas
usa ``skip_validation_check=True`` solo para la escritura tecnica necesaria.

No se modifica el codigo fuente de Odoo, OCA o Tier Validation.

Instalacion
-----------
1. Copiar la carpeta ``sale_revision_tier_compat`` al directorio de addons
   personalizados.
2. Actualizar la lista de modulos en Odoo.
3. Buscar e instalar el modulo "sale_revision_tier_compat".

Uso tecnico
-----------
Desde Python o desde un modulo superior:

    orden.create_revision_preserving_tier()

Esto crea la nueva revision de OCA y conserva el historial
``tier.review`` de la revision anterior.

Licencia
--------
AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
