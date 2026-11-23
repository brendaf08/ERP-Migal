"""Cotizaciones por cliente, elección de cotización/versión y vigencia de versiones anteriores.

Casos:
- Varios clientes con el mismo nombre y un cliente con dos cotizaciones: el agente lista y pide elegir.
- Un único resultado: el agente actúa directamente.
- Versiones: la anterior sigue abierta hasta vencer, se puede consultar/enviar pero no confirmar;
  el cron la cierra al vencer y confirmar la más reciente cierra las demás.
"""
import json
from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user, tagged

from ..agent import intent


@tagged("post_install", "-at_install", "migal_agente")
class TestCotizacionesAgente(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hoy = fields.Date.context_today(cls.env.user)
        # Las pruebas nunca llaman a un servicio de IA real (aunque la base tenga una clave configurada).
        cls.env["ir.config_parameter"].sudo().set_param("migal_agente.llm_enabled", "False")
        cls.ven = new_test_user(cls.env, login="ven_cot_pc3",
                                groups="sales_team.group_sale_salesman_all_leads,stock.group_stock_user")
        cls.producto = cls.env["product.product"].create({"name": "PC3 Cemento Zeta", "list_price": 30.0})
        cls.perez = cls.env["res.partner"].create({"name": "Zuleta Pérez Quispe", "phone": "+51 911 111 111"})
        cls.gomez = cls.env["res.partner"].create({"name": "Zuleta Gómez Ríos", "phone": "+51 922 222 222"})
        cls.unico = cls.env["res.partner"].create({"name": "Xiomara Única", "phone": "+51 933 333 333"})

    def _cot(self, partner, qty=10, dias=15):
        return self.env["sale.order"].with_user(self.ven).create({
            "partner_id": partner.id,
            "user_id": self.ven.id,
            "validity_date": self.hoy + timedelta(days=dias),
            "order_line": [Command.create({"product_id": self.producto.id, "product_uom_qty": qty})],
        })

    def _chat(self, texto, session="cot-test"):
        return self.env["migal.agente"].with_user(self.ven).procesar_mensaje(texto, canal="prueba", session_id=session)

    # ------------------------------------------------------------------
    def test_intent_reconoce_cliente(self):
        self.assertEqual(intent.parse("Quiero saber la cotización de Luis"),
                         ("consultar_cotizacion", {"_cliente": "luis"}))
        self.assertEqual(intent.parse("whatsapp de la cotización de Luis por favor"),
                         ("preparar_whatsapp_cotizacion", {"_cliente": "luis"}))
        self.assertEqual(intent.parse("qr para el cliente Pérez"), ("generar_qr_cotizacion", {"_cliente": "perez"}))
        nombre, args = intent.parse("cobertura de la cotización de Luis para el 25/11/2026")
        self.assertEqual((nombre, args["_cliente"], args["fecha_requerida"]),
                         ("evaluar_cobertura_preliminar", "luis", "2026-11-25"))
        self.assertEqual(intent.parse("S00637-01"), ("consultar_cotizacion", {"cotizacion": "S00637-01"}))
        self.assertEqual(intent.parse("whatsapp S00573"), ("preparar_whatsapp_cotizacion", {"cotizacion": "S00573"}))

    def test_varios_clientes_y_cotizaciones_pide_elegir(self):
        a1 = self._cot(self.perez, 10)
        a2 = self._cot(self.perez, 20)
        b1 = self._cot(self.gomez, 5)
        res = self.env["migal.agente"].with_user(self.ven).ejecutar_herramienta(
            "buscar_cotizaciones", {"cliente": "zuleta"})
        self.assertTrue(res["ok"], res["mensaje"])
        refs = {o["ref"] for o in res["datos"]["opciones"]}
        self.assertEqual(refs, {a1.name, a2.name, b1.name})
        self.assertEqual(len(res["datos"]["clientes"]), 2)

        html, log = self._chat("quiero ver la cotización de Zuleta")
        self.assertIn("¿Cuál desea ver?", str(html))
        self.assertIn("Zuleta Pérez Quispe", str(html))
        self.assertIn("Zuleta Gómez Ríos", str(html))
        self.assertEqual(log.resultado, "ayuda")
        sel = self.env["migal.agente.seleccion"].sudo().search([("session_id", "=", "cot-test")])
        self.assertEqual(sel.etapa, "cotizacion")
        elegida = next(o for o in sel.opciones if o["ref"] == b1.name)

        html, log = self._chat(str(elegida["n"]))
        self.assertEqual(log.resultado, "ok")
        self.assertEqual((log.res_model, log.res_id), ("sale.order", b1.id))
        self.assertIn(b1.name, str(html))
        self.assertFalse(self.env["migal.agente.seleccion"].sudo().search([("session_id", "=", "cot-test")]))

    def test_filtra_por_nombre_completo_y_ordinal(self):
        self._cot(self.perez)
        p2 = self._cot(self.perez, 7)
        self._cot(self.gomez)
        html, _log = self._chat("whatsapp de la cotización de zuleta perez")
        self.assertNotIn("Gómez", str(html))
        self.assertIn("¿Cuál desea enviar por WhatsApp?", str(html))
        sel = self.env["migal.agente.seleccion"].sudo().search([("session_id", "=", "cot-test")])
        n = next(o["n"] for o in sel.opciones if o["ref"] == p2.name)
        html, log = self._chat({1: "la primera", 2: "la segunda"}[n])
        self.assertEqual(log.res_id, p2.id)
        self.assertIn("preparar_whatsapp_cotizacion", log.tools_invoked)
        self.assertIn("wa.me/51911111111", str(html))

    def test_un_solo_resultado_actua_directo(self):
        order = self._cot(self.unico)
        html, log = self._chat("cotización de Xiomara")
        self.assertEqual(log.resultado, "ok")
        self.assertEqual(log.res_id, order.id)
        self.assertIn("tiene una sola cotización abierta", str(html))

    def test_sin_resultados_y_otro_pedido_descarta_lista(self):
        html, log = self._chat("cotización de Nadie Inexistente")
        self.assertIn("No encontré cotizaciones abiertas", str(html))
        self._cot(self.perez)
        self._cot(self.gomez)
        self._chat("cotizaciones de zuleta")
        self.assertTrue(self.env["migal.agente.seleccion"].sudo().search([("session_id", "=", "cot-test")]))
        html, log = self._chat("hola")
        self.assertFalse(self.env["migal.agente.seleccion"].sudo().search([("session_id", "=", "cot-test")]))
        self.assertIn("Agente MIGAL", str(html))

    # ------------------------------------------------------------------
    # Versiones
    # ------------------------------------------------------------------
    def test_version_anterior_sigue_disponible_hasta_vencer(self):
        original = self._cot(self.unico, 10)
        original.action_quotation_sent()
        nueva = original.create_revision_preserving_tier()
        self.assertEqual(nueva.name, "%s-01" % original.name)
        self.assertEqual(original.state, "sent", "La versión anterior no se cancela al crear otra")
        self.assertTrue(original.active)
        self.assertEqual(original.current_revision_id, nueva)

        # «S00xxx» sin versión y con dos versiones disponibles: el agente pregunta cuál.
        html, log = self._chat("whatsapp %s" % original.name)
        self.assertIn("2 versiones disponibles", str(html))
        sel = self.env["migal.agente.seleccion"].sudo().search([("session_id", "=", "cot-test")])
        self.assertEqual(sel.etapa, "version")
        html, log = self._chat("versión 0")
        self.assertEqual(log.res_id, original.id)
        self.assertEqual(log.resultado, "ok", log.output_response)
        self.assertIn("Versión anterior: sigue disponible", str(html))

        # Referencia explícita de versión: sin pregunta.
        html, log = self._chat("cotización %s" % nueva.name)
        self.assertEqual((log.resultado, log.res_id), ("ok", nueva.id))
        self.assertIn(original.name, str(html), "El detalle muestra las otras versiones disponibles")

        # Por cliente con dos versiones: pide la versión directamente; «la más reciente».
        self._chat("cotización de Xiomara")
        html, log = self._chat("la más reciente")
        self.assertEqual(log.res_id, nueva.id)

        # La versión anterior no se puede confirmar (regla de sale_order_request).
        with self.assertRaises(UserError):
            original.action_confirm()

        # Vence la anterior: el cron la cierra (cancelada y archivada); la nueva sigue abierta.
        original.write({"validity_date": self.hoy - timedelta(days=1)})
        self.env["sale.order"]._cron_migal_vencer_versiones()
        self.assertEqual((original.state, original.active), ("cancel", False))
        self.assertEqual(nueva.state, "draft")
        res = self.env["migal.agente"].with_user(self.ven).ejecutar_herramienta(
            "preparar_whatsapp_cotizacion", {"cotizacion": original.name})
        self.assertFalse(res["ok"])
        self.assertIn("ya no está disponible", res["mensaje"])

    def test_confirmar_mas_reciente_cierra_las_demas(self):
        original = self._cot(self.unico)
        v1 = original.create_revision_preserving_tier()
        v2 = v1.create_revision_preserving_tier()
        self.assertEqual((original.current_revision_id, v1.current_revision_id), (v2, v2))
        v2.action_confirm()
        self.assertEqual(v2.state, "sale")
        for anterior in (original, v1):
            self.assertEqual((anterior.state, anterior.active), ("cancel", False))

    def test_nueva_version_desde_una_anterior(self):
        original = self._cot(self.unico, 10)
        v1 = original.create_revision_preserving_tier()
        # El cliente prefiere la propuesta original: se crea una versión nueva a partir de ella.
        v2 = original.create_revision_preserving_tier()
        self.assertEqual(v2.revision_number, 2)
        self.assertEqual(v2.order_line.product_uom_qty, 10)
        self.assertEqual((original.current_revision_id, v1.current_revision_id), (v2, v2))
        self.assertFalse(v2.current_revision_id)

    def test_sin_vigencia_se_cierra_como_oca(self):
        original = self._cot(self.unico)
        original.validity_date = False
        original.create_revision_preserving_tier()
        self.assertEqual((original.state, original.active), ("cancel", False))

    # ------------------------------------------------------------------
    # Lenguaje natural: errores, plurales, contexto y clientes ambiguos
    # ------------------------------------------------------------------
    def test_intent_tolera_errores_y_plurales(self):
        self.assertEqual(intent.parse("kiero ver las cotisaciones de luis"),
                         ("consultar_cotizacion", {"_cliente": "luis"}))
        self.assertEqual(intent.parse("mandale la coti a luis x wasap"),
                         ("preparar_whatsapp_cotizacion", {"_cliente": "luis"}))
        self.assertEqual(intent.parse("el kr de la cotizacion de Luis"), ("generar_qr_cotizacion", {"_cliente": "luis"}))
        self.assertEqual(intent.parse("hay stok para la cotizacion de luis?")[0], "evaluar_cobertura_preliminar")
        nombre, args = intent.parse("histrial de pagos de luis de octubre")
        self.assertEqual((nombre, args["cliente"]), ("generar_estado_cuenta", "luis"))
        self.assertTrue(args["fecha_desde"].endswith("-10-01") and args["fecha_hasta"].endswith("-10-31"))
        self.assertEqual(intent.parse("deudas de luis"), ("generar_estado_cuenta", {"cliente": "luis"}))

    def test_contexto_de_la_conversacion(self):
        order = self._cot(self.unico)
        self._chat("cotización de Xiomara")
        html, log = self._chat("el qr de esa")
        self.assertEqual((log.res_id, log.resultado), (order.id, "ok"))
        self._chat("whatsapp")
        html, log = self._chat("ya la envié")
        self.assertIn("registrar_envio_whatsapp", log.tools_invoked)
        self.assertEqual(len(self.env["migal.agente.whatsapp.envio"].search([("order_id", "=", order.id)])), 1)

    def test_nombre_mal_escrito(self):
        order = self._cot(self.unico)
        html, log = self._chat("cotizacion de Xiomarra")
        self.assertEqual(log.res_id, order.id)

    def test_estado_de_cuenta_cliente_ambiguo_pide_elegir(self):
        ger = new_test_user(self.env, login="ger_cot_pc3",
                            groups="sales_team.group_sale_manager,account.group_account_manager")
        agente = self.env["migal.agente"].with_user(ger)
        html, log = agente.procesar_mensaje("cuanto debe zuleta", canal="prueba", session_id="cot-ec")
        self.assertIn("2 clientes", str(html))
        html, log = agente.procesar_mensaje("gomez", canal="prueba", session_id="cot-ec")
        self.assertIn("generar_estado_cuenta", log.tools_invoked)
        self.assertIn("Zuleta Gómez Ríos", str(html))

    def test_chat_con_gemini_simulado(self):
        """Proveedor Gemini: function calling sobre las mismas herramientas protegidas."""
        from unittest.mock import patch
        from ..agent import llm
        order = self._cot(self.unico)
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("migal_agente.llm_enabled", "True")
        icp.set_param("migal_agente.llm_data_ack", "True")
        icp.set_param("migal_agente.llm_proveedor", "gemini")
        icp.set_param("migal_agente.llm_api_key", "clave-de-prueba")
        respuestas = [
            {"candidates": [{"content": {"role": "model", "parts": [
                {"functionCall": {"name": "consultar_cotizacion", "args": {"cotizacion": order.name}}}]}}]},
            {"candidates": [{"content": {"role": "model", "parts": [{"text": "Aquí está la cotización."}]}}]},
        ]
        enviados = []

        def falso(api_key, model, cuerpo, timeout=45):
            enviados.append((model, cuerpo))
            return respuestas.pop(0)

        with patch.object(llm, "_gemini_post", side_effect=falso):
            html, log = self._chat("muéstrame la cotización de Xiomara")
        self.assertEqual(log.modo, "llm")
        self.assertEqual(log.res_id, order.id)
        self.assertIn("Aquí está la cotización.", str(html))
        self.assertEqual(enviados[0][0], llm.GEMINI_MODELO_POR_DEFECTO.split(",")[0])
        declaraciones = enviados[0][1]["tools"][0]["functionDeclarations"]
        self.assertNotIn("additionalProperties", json.dumps(declaraciones))
