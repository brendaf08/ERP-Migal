"""Escanear lista: lectura (texto y Gemini simulado), coincidencias y creación de la cotización."""
import base64
import json
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user, tagged

from ..lib import lectura, matcher

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=")


class _RespuestaFalsa:
    def __init__(self, cuerpo):
        self._cuerpo = json.dumps(cuerpo).encode()

    def read(self):
        return self._cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@tagged("post_install", "-at_install", "migal_ocr")
class TestEscanearLista(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ven = new_test_user(cls.env, login="ven_ocr", groups="sales_team.group_sale_salesman_all_leads")
        P = cls.env["product.product"]
        # Catálogo aislado para la prueba (se revierte al terminar).
        P.search([("sale_ok", "=", True)]).write({"sale_ok": False})
        cls.cemento = P.create({"name": "CEMENTO SOL TIPO I 42.5 KG", "sale_ok": True, "list_price": 30})
        cls.fierro12 = P.create({"name": "FIERRO CORRUGADO 1/2\" X 9 M", "sale_ok": True, "list_price": 40})
        cls.fierro38 = P.create({"name": "FIERRO CORRUGADO 3/8\" X 9 M", "sale_ok": True, "list_price": 25})
        cls.wincha = P.create({"name": "WINCHA 5 M STANLEY", "sale_ok": True, "list_price": 25})
        cls.cliente = cls.env["res.partner"].create({"name": "Cliente OCR"})

    def _doc(self, **vals):
        return self.env["migal.ocr.documento"].with_user(self.ven).create(dict({"partner_id": self.cliente.id}, **vals))

    def test_lectura_de_texto(self):
        filas = lectura.leer_texto("10 bls cemento sol\nfierro 1/2 x 20\n- huincha stanley 5m : 2\nalgo raro")
        self.assertEqual(filas[0], ("bls cemento sol", 10.0))
        self.assertEqual(filas[1], ("fierro 1/2", 20.0))
        self.assertEqual(filas[2], ("huincha stanley 5m", 2.0))
        self.assertEqual(filas[3], ("algo raro", None))

    def test_medidas_distintas_no_se_confunden(self):
        cands = matcher.preparar_catalogo([(1, "FIERRO CORRUGADO 1/2\" X 9 M"), (2, "FIERRO CORRUGADO 3/8\" X 9 M")])
        _n, cs, _c = matcher.coincidencias("20 varillas fierro 3/8", cands)
        self.assertEqual(cs[0].producto_id, 2)
        self.assertTrue(len(cs) == 1 or cs[1].confianza < cs[0].confianza * 0.5)

    def test_texto_a_cotizacion(self):
        doc = self._doc(texto_lista="10 bls cemento sol\nfierro 1/2 x 20\nhuincha stanley - 2\nxyz qwerty")
        doc.action_leer()
        self.assertEqual(doc.estado, "leido")
        por_texto = {l.texto_crudo: l for l in doc.linea_ids}
        self.assertEqual(por_texto["bls cemento sol"].product_id, self.cemento)
        self.assertEqual(por_texto["fierro 1/2"].product_id, self.fierro12)
        self.assertEqual(por_texto["huincha stanley"].product_id, self.wincha, "huincha = wincha")
        self.assertGreaterEqual(por_texto["bls cemento sol"].coincidencia, 60)
        self.assertFalse(por_texto["xyz qwerty"].product_id)
        self.assertEqual(por_texto["xyz qwerty"].nivel, "ninguna")

        accion = doc.action_agregar_a_cotizacion()
        order = self.env["sale.order"].browse(accion["res_id"])
        self.assertEqual(order.state, "draft")
        self.assertEqual(order.partner_id, self.cliente)
        self.assertEqual(sorted(order.order_line.mapped("product_uom_qty")), [2.0, 10.0, 20.0])
        self.assertEqual(doc.estado, "aplicado")

    def test_agrega_a_cotizacion_existente(self):
        order = self.env["sale.order"].with_user(self.ven).create({"partner_id": self.cliente.id})
        accion = order.action_migal_escanear_lista()
        doc = self.env["migal.ocr.documento"].with_user(self.ven).with_context(accion["context"]).create(
            {"texto_lista": "3 cemento sol"})
        self.assertEqual(doc.partner_id, self.cliente)
        doc.action_leer()
        doc.action_agregar_a_cotizacion()
        self.assertEqual(order.order_line.product_id, self.cemento)

    def test_sinonimo_editable(self):
        self.env["migal.ocr.sinonimo"].create({"termino": "metrito", "equivale": "wincha"})
        doc = self._doc(texto_lista="2 metrito stanley")
        doc.action_leer()
        self.assertEqual(doc.linea_ids.product_id, self.wincha)

    def test_foto_sin_clave_explica_que_hacer(self):
        self.env["ir.config_parameter"].sudo().set_param("migal_agente.llm_api_key", "")
        doc = self._doc(archivo=base64.b64encode(PNG_1PX))
        with patch.object(lectura, "urlopen", side_effect=AssertionError("La prueba no debe llamar a Gemini")),                 self.assertRaises(UserError) as err:
            doc.action_leer()
        self.assertIn("clave de Gemini", str(err.exception))

    def test_foto_con_gemini_simulado(self):
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("migal_agente.llm_proveedor", "gemini")
        icp.set_param("migal_agente.llm_api_key", "clave-de-prueba")
        icp.set_param("migal_agente.llm_data_ack", "True")
        salida = {"legible": True, "lineas": [{"textoCrudo": "Cem. Sol 42,5 kg", "cantidadLeida": 8},
                                              {"textoCrudo": "F° 3/8\"", "cantidadLeida": 15}]}
        respuesta = {"candidates": [{"content": {"parts": [{"text": json.dumps(salida)}]}}]}
        enviado = {}

        def falso(req, timeout=None):
            enviado["url"] = req.full_url
            enviado["clave"] = req.get_header("X-goog-api-key")
            enviado["cuerpo"] = json.loads(req.data)
            return _RespuestaFalsa(respuesta)

        doc = self._doc(archivo=base64.b64encode(PNG_1PX))
        with patch.object(lectura, "urlopen", side_effect=falso):
            doc.action_leer()
        self.assertIn("generativelanguage.googleapis.com", enviado["url"])
        self.assertEqual(enviado["clave"], "clave-de-prueba")
        self.assertNotIn("CEMENTO", json.dumps(enviado["cuerpo"]), "El catálogo nunca se envía a la IA")
        self.assertEqual(doc.origen, "ia")
        productos = {l.cantidad: l.product_id for l in doc.linea_ids}
        self.assertEqual(productos[8.0], self.cemento)
        self.assertEqual(productos[15.0], self.fierro38)

    def test_lineas_reales_de_notas_de_venta(self):
        """Transcripciones de Gemini sobre notas de venta manuscritas reales de MIGAL (Documentos-Escanear)."""
        P = self.env["product.product"]
        alambre16 = P.create({"name": "ALAMBRE #16", "sale_ok": True})
        chancada = P.create({"name": "PIEDRA CHANCADA", "sale_ok": True})
        P.create({"name": "PIEDRA CHANCADA - BOLSA", "sale_ok": True})
        arena_fina = P.create({"name": "ARENA FINA", "sale_ok": True})
        doc = self._doc(texto_lista="x")
        doc._emparejar([
            ("Ø 5/8", 96.0), ("φ 3/8", 25.0), ("fierra 1/2", 20.0), ("Kg alambre 16", 50.0),
            ("f° alambre 16", 20.0), ("Com sal.", 60.0), ("30 cemento sol", 30.0), ("Mt de fina", 2.0),
            ("mtrs piedra chancada", 20.0), ("tubo 4\"", 2.0),
        ])
        l = {x.texto_crudo: x for x in doc.linea_ids}
        self.assertEqual(l["φ 3/8"].product_id, self.fierro38)
        self.assertEqual(l["fierra 1/2"].product_id, self.fierro12)
        self.assertEqual(l["Kg alambre 16"].product_id, alambre16)
        self.assertEqual(l["f° alambre 16"].product_id, alambre16, "«f°» delante de alambre es «kg», no fierro")
        self.assertEqual(l["Com sal."].product_id, self.cemento)
        self.assertEqual(l["cemento sol"].cantidad, 30.0, "La cantidad repetida en el texto se quita")
        self.assertEqual(l["cemento sol"].product_id, self.cemento)
        self.assertEqual(l["Mt de fina"].product_id, arena_fina)
        self.assertEqual(l["mtrs piedra chancada"].product_id, chancada, "metros cúbicos: granel, no bolsa")
        self.assertFalse(l["tubo 4\""].product_id, "Un producto que no está en el catálogo no se inventa")

    def test_widget_ofrece_escanear_lista(self):
        order = self.env["sale.order"].with_user(self.ven).create({"partner_id": self.cliente.id})
        agente = self.env["migal.agente"].with_user(self.ven)
        ctx = agente.widget_contexto("sale.order", order.id)
        self.assertEqual(ctx["acciones"][0]["id"], "escanear_lista", "Sin productos: escanear es la primera opción")
        accion = agente.widget_abrir("escanear_lista", "sale.order", order.id)
        self.assertEqual(accion["res_model"], "migal.ocr.documento")
        self.assertEqual(accion["context"]["default_order_id"], order.id)
        order.write({"order_line": [(0, 0, {"product_id": self.cemento.id, "product_uom_qty": 1})]})
        ctx = agente.widget_contexto("sale.order", order.id)
        self.assertIn("productos", [p["id"] for p in ctx["pestanas"]])

    def test_productos_repetidos_se_suman(self):
        """Ø 5/8 en dos filas (96 + 20) -> una sola línea de 116; si ya estaba en la cotización, se suma ahí."""
        order = self.env["sale.order"].with_user(self.ven).create({
            "partner_id": self.cliente.id,
            "order_line": [(0, 0, {"product_id": self.fierro12.id, "product_uom_qty": 4})],
        })
        doc = self._doc(order_id=order.id, texto_lista="96 fierro 3/8\n10 cemento sol\n20 fierro 3/8\n6 fierro 1/2")
        doc.action_leer()
        doc.action_agregar_a_cotizacion()
        lineas = {l.product_id: l for l in order.order_line}
        self.assertEqual(len(order.order_line), 3, "Sin líneas duplicadas")
        self.assertEqual(lineas[self.fierro38].product_uom_qty, 116.0)
        self.assertEqual(lineas[self.fierro12].product_uom_qty, 10.0, "4 que ya estaban + 6 de la lista")
        self.assertEqual(lineas[self.cemento].product_uom_qty, 10.0)
        self.assertAlmostEqual(lineas[self.fierro38].price_subtotal, 116 * lineas[self.fierro38].price_unit, places=2)
