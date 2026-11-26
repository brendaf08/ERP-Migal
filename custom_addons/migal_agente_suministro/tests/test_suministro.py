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

    def test_baja_rotacion_excluye_salida_pos(self):
        almacen = self.po.picking_type_id.warehouse_id
        ubicacion = almacen.lot_stock_id
        productos = self.env["product.product"].create([
            {"name": "[PRUEBA] Sin ventas", "is_storable": True},
            {"name": "[PRUEBA] Vendido por POS", "is_storable": True},
            {"name": "[PRUEBA] Sin existencias", "is_storable": True},
        ])
        sin_ventas, vendido_pos, sin_stock = productos
        quant = self.env["stock.quant"]
        quant._update_available_quantity(sin_ventas, ubicacion, 10)
        quant._update_available_quantity(vendido_pos, ubicacion, 10)

        caja = self.env["pos.config"].create({"name": "[PRUEBA] Caja baja rotación"})
        sesion = self.env["pos.session"].create({"config_id": caja.id})
        destino = self.env.ref("stock.stock_location_customers")
        picking = self.env["stock.picking"].create({
            "picking_type_id": almacen.out_type_id.id,
            "location_id": ubicacion.id,
            "location_dest_id": destino.id,
            "pos_session_id": sesion.id,
        })
        movimiento = self.env["stock.move"].create({
            "product_id": vendido_pos.id,
            "product_uom_qty": 2,
            "product_uom": vendido_pos.uom_id.id,
            "location_id": ubicacion.id,
            "location_dest_id": destino.id,
            "picking_id": picking.id,
        })
        picking.action_confirm()
        picking.action_assign()
        movimiento.quantity = 2
        movimiento.picked = True
        picking._action_done()
        self.assertEqual(movimiento.state, "done")
        self.assertEqual(vendido_pos.qty_available, 8)

        resultado = self._agente(self.ven).consultar("marketing", "consultar_baja_rotacion", {})
        self.assertTrue(resultado["ok"], resultado["mensaje"])
        self.assertFalse(resultado.get("simulado"))
        self.assertEqual(resultado["datos"]["dias"], 90)
        filas = {p["producto"]: p for p in resultado["datos"]["productos"]}
        self.assertEqual(filas[sin_ventas.display_name]["stock"], 10)
        self.assertEqual(filas[sin_ventas.display_name]["vendido"], 0)
        self.assertNotIn(vendido_pos.display_name, filas)
        self.assertNotIn(sin_stock.display_name, filas)

    def test_baja_rotacion_chat_con_ventana(self):
        html, log = self._agente(self.ven).procesar_mensaje("inventario sin ventas en 30 días", canal="prueba")
        self.assertIn("en 30 días", html)
        self.assertIn("consultar_baja_rotacion", log.tools_invoked)
        self.assertEqual(log.agente, "suministro")

    def test_baja_rotacion_restringe_rol(self):
        usuario = new_test_user(self.env, login="sin_rol_rotacion", groups="base.group_user")
        resultado = self._agente(usuario).ejecutar_herramienta("consultar_baja_rotacion", {})
        self.assertEqual(resultado["estado"], "sin_permiso")


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
