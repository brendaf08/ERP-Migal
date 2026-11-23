from odoo import fields, models


class MigalOcrSinonimo(models.Model):
    """Jerga ferretera editable: cómo llama la gente a un producto -> cómo figura en el catálogo."""

    _name = "migal.ocr.sinonimo"
    _description = "Sinónimo ferretero para escanear listas"
    _order = "termino"

    termino = fields.Char("Cómo lo escriben", required=True, help="Por ejemplo «huincha», «terokal», «bls».")
    equivale = fields.Char("Equivale a", required=True, help="Palabra del catálogo, por ejemplo «wincha».")
    active = fields.Boolean(default=True)

    _termino_unico = models.Constraint("unique(termino)", "Ese término ya está registrado.")
