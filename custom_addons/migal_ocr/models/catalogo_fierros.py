"""Fierro corrugado del catálogo MIGAL.

Las notas de venta reales de MIGAL (Documentos-Escanear) piden sobre todo fierro corrugado
(Ø 5/8, 1/2, 3/8, 3/4, 8 mm y 1/4), que no estaba en el catálogo del respaldo. Se crean al instalar
el módulo con los precios de esas notas, solo si aún no existen (no se duplican ni se modifican).
"""
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

FIERROS = [
    ("829", 'FIERRO CORRUGADO 5/8" X 9 M', 55.0),
    ("830", 'FIERRO CORRUGADO 1/2" X 9 M', 35.5),
    ("831", 'FIERRO CORRUGADO 3/8" X 9 M', 19.8),
    ("832", 'FIERRO CORRUGADO 3/4" X 9 M', 75.0),
    ("833", "FIERRO CORRUGADO 8 MM X 9 M", 14.3),
    ("834", 'FIERRO 1/4" X 9 M', 8.0),
]


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _migal_ocr_crear_fierros(self):
        Categoria = self.env["product.category"]
        categoria = Categoria.search([("name", "=", "Fierro y acero de construcción")], limit=1)
        if not categoria:
            padre = Categoria.search([("name", "=", "Materiales de construcción")], limit=1)
            categoria = Categoria.create({"name": "Fierro y acero de construcción",
                                          "parent_id": padre.id or False})
        impuesto = self.env["account.tax"].search([("type_tax_use", "=", "sale"), ("name", "=", "IGV 18%"),
                                                   ("company_id", "=", self.env.company.id)], limit=1) \
            or self.env.company.account_sale_tax_id
        unidades = self.env.ref("uom.product_uom_unit")
        creados = 0
        for codigo, nombre, precio in FIERROS:
            if self.with_context(active_test=False).search_count([("name", "=", nombre)]):
                continue
            ocupado = self.with_context(active_test=False).search_count([("default_code", "=", codigo)])
            self.create({
                "name": nombre, "default_code": False if ocupado else codigo, "list_price": precio,
                "categ_id": categoria.id, "uom_id": unidades.id, "type": "consu", "is_storable": True,
                "sale_ok": True, "purchase_ok": True, "taxes_id": [(6, 0, impuesto.ids)],
            })
            creados += 1
        _logger.info("MIGAL OCR: %s productos de fierro corrugado creados.", creados)
        return creados
