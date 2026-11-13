from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MigalAgenteReglaCobertura(models.Model):
    """Regla habitual de abastecimiento por categoría (cementos, agregados, fierros, ladrillos).

    Si el faltante de un producto de estas categorías cumple el límite y el plazo,
    el agente informa a VEN que se espera cubrirlo por el proceso habitual, sin pedir
    una evaluación individual a Abastecimiento. Nunca se presenta como entrega garantizada.
    """

    _name = "migal.agente.regla.cobertura"
    _description = "Regla habitual de cobertura (Agente MIGAL)"
    _order = "categ_id"

    active = fields.Boolean(default=True)
    categ_id = fields.Many2one("product.category", string="Categoría", required=True, ondelete="cascade")
    incluir_subcategorias = fields.Boolean(default=True)
    plazo_dias = fields.Integer(
        string="Plazo habitual (días)", default=3, required=True,
        help="Días que necesita el proceso habitual de reposición. Si la fecha requerida es anterior "
             "a hoy + plazo, el faltante no se considera cubierto por la regla.")
    faltante_max_pct = fields.Float(
        string="Faltante máximo cubierto (%)", default=100.0,
        help="Porcentaje máximo de la cantidad solicitada que puede faltar para aplicar la regla.")
    faltante_max_qty = fields.Float(
        string="Faltante máximo (unidades)", default=0.0,
        help="Límite absoluto opcional en unidades del producto. 0 = sin límite.")
    nota = fields.Text(string="Fundamento / estado de validación")

    @api.constrains("plazo_dias", "faltante_max_pct", "faltante_max_qty")
    def _check_valores(self):
        for rec in self:
            if rec.plazo_dias < 0 or not 0 <= rec.faltante_max_pct <= 100 or rec.faltante_max_qty < 0:
                raise ValidationError("Valores de la regla fuera de rango.")

    def _regla_para_producto(self, product):
        """Devuelve la regla activa aplicable a la categoría del producto (o vacío)."""
        categ = product.categ_id
        for regla in self.search([]):
            if categ == regla.categ_id or (regla.incluir_subcategorias and categ.parent_path
                                           and categ.parent_path.startswith(regla.categ_id.parent_path)):
                return regla
        return self.browse()
