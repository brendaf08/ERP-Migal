"""Pruebas del agente de cadena de suministro (caso normal, borde, permiso y evento)."""
from odoo import Command
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install", "migal_agente", "migal_agente_suministro")
class TestAgenteSuministro(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("migal_agente.llm_enabled", "False")
        cls.cmp = new_test_user(cls.env, login="cmp_sum", groups="purchase.group_purchase_user,stock.group_stock_user")
        cls.ven = new_test_user(cls.env, login="ven_sum", groups="sales_team.group_sale_salesman")
        cls.proveedor = cls.env["res.partner"].create({"name": "Proveedor prueba suministro"})
        cls.producto = cls.env["product.product"].create({"name": "Producto prueba suministro", "is_storable": True,
                                                           "purchase_ok": True})
        cls.po = cls.env["purchase.order"].create({"partner_id": cls.proveedor.id, "order_line": [
            Command.create({"product_id": cls.producto.id, "product_qty": 10})]})
        cls.po.button_confirm()

    def _agente(self, user):
        return self.env["migal.agente"].with_user(user)

    def test_registro_y_herramientas(self):
        self.assertIn("suministro", self.env["migal.agente"]._agentes())
        spec = self.env["migal.agente"]._spec("evaluar_cobertura_preliminar")
        self.assertEqual(spec["agente"], "suministro", "La cobertura pertenece a cadena de suministro")

    def test_compras_pendientes_y_recepcion(self):
        res = self._agente(self.cmp).ejecutar_herramienta("listar_compras_pendientes", {})
        self.assertTrue(res["ok"])
        self.assertIn(self.po.name, res["datos"]["por_recibir"])
        res = self._agente(self.cmp).ejecutar_herramienta("consultar_recepcion", {"orden_compra": self.po.name})
        self.assertEqual(res["estado"], "pendiente")

    def test_recepcion_parcial_emite_ev027(self):
        picking = self.po.picking_ids
        picking.move_ids.quantity = 6
        accion = picking.button_validate()
        if isinstance(accion, dict) and accion.get("res_model") == "stock.backorder.confirmation":
            self.env["stock.backorder.confirmation"].with_context(accion["context"]).create({}).process()
        res = self._agente(self.cmp).ejecutar_herramienta("consultar_recepcion", {"orden_compra": self.po.name})
        self.assertEqual(res["estado"], "parcial")
        self.assertEqual(res["datos"]["productos"][0]["pendiente"], 4)
        log = self.env["migal.agente.log"].sudo().search([("canal", "=", "evento"), ("input_prompt", "like", "EV-027")],
                                                          order="id desc", limit=1)
        self.assertTrue(log, "La recepción validada emite EV-027")

    def test_permiso_por_rol(self):
        res = self._agente(self.ven).ejecutar_herramienta("listar_compras_pendientes", {})
        self.assertEqual(res["estado"], "sin_permiso")

    def test_chat_reconoce_frase(self):
        html, log = self._agente(self.cmp).procesar_mensaje("que compras pendientes hay", canal="prueba")
        self.assertIn("listar_compras_pendientes", log.tools_invoked)
        self.assertEqual(log.agente, "suministro")

    def test_disponibilidad_producto_por_ubicacion(self):
        almacen = self.po.picking_type_id.warehouse_id
        principal = almacen.lot_stock_id
        auxiliar = self.env["stock.location"].create({
            "name": "[PRUEBA] Auxiliar disponibilidad",
            "usage": "internal",
            "location_id": principal.id,
            "company_id": principal.company_id.id,
        })
        producto = self.env["product.product"].create({
            "name": "[PRUEBA] Disponibilidad suministro",
            "default_code": "PRUEBA-SUM-DISP-TEST",
            "is_storable": True,
        })
        quant = self.env["stock.quant"]
        quant._update_available_quantity(producto, principal, 60)
        movimiento = self.env["stock.move"].create({
            "product_id": producto.id,
            "product_uom_qty": 20,
            "product_uom": producto.uom_id.id,
            "location_id": principal.id,
            "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            "picking_type_id": almacen.out_type_id.id,
            "company_id": almacen.company_id.id,
        })
        movimiento._action_confirm(merge=False)
        movimiento._action_assign()
        quant._update_available_quantity(producto, auxiliar, 30)

        resultado = self._agente(self.ven).ejecutar_herramienta(
            "consultar_disponibilidad_producto", {"producto": "prueba-sum-disp-test"},
        )
        self.assertTrue(resultado["ok"], resultado["mensaje"])
        filas = {fila[0]: fila[1:] for fila in resultado["datos"]["tabla"]["filas"]}
        self.assertEqual(filas, {
            principal.complete_name: ["60", "20", "40"],
            auxiliar.complete_name: ["30", "0", "30"],
        })

    def test_disponibilidad_producto_restringe_rol(self):
        usuario = new_test_user(self.env, login="sin_rol_disponibilidad", groups="base.group_user")
        resultado = self._agente(usuario).ejecutar_herramienta(
            "consultar_disponibilidad_producto", {"producto": self.producto.name},
        )
        self.assertEqual(resultado["estado"], "sin_permiso")

    def test_chat_disponibilidad_producto(self):
        html, log = self._agente(self.ven).procesar_mensaje(
            f"disponibilidad de {self.producto.name}", canal="prueba",
        )
        self.assertIn("Disponibilidad por ubicación", html)
        self.assertIn("consultar_disponibilidad_producto", log.tools_invoked)
        self.assertEqual(log.agente, "suministro")