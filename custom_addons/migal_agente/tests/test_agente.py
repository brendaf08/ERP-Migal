"""Casos CP3-AI-01 (normal), CP3-AI-02 (borde) y CP3-AI-03 (excepción) del Agente MIGAL.

Cada prueba crea sus propios datos sintéticos y se revierte al terminar.
"""
from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
import json

from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged

from ..agent import llm


@tagged("post_install", "-at_install", "migal_agente")
class TestAgenteMigal(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hoy = fields.Date.context_today(cls.env.user)
        cls.ven = new_test_user(cls.env, login="ven_pc3", groups="sales_team.group_sale_salesman,stock.group_stock_user")
        cls.fco = new_test_user(cls.env, login="fco_pc3", groups="account.group_account_invoice,sales_team.group_sale_salesman")
        cls.ger = new_test_user(cls.env, login="ger_pc3", groups="sales_team.group_sale_manager,account.group_account_manager")
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)

        cls.categ_cemento = cls.env["product.category"].create({"name": "PC3 Cemento"})
        cls.categ_otros = cls.env["product.category"].create({"name": "PC3 Otros"})
        cls.env["migal.agente.regla.cobertura"].create(
            {"categ_id": cls.categ_cemento.id, "plazo_dias": 3, "faltante_max_pct": 100.0})

        def prod(nombre, categ, stock=0.0):
            p = cls.env["product.product"].create({
                "name": nombre, "is_storable": True, "categ_id": categ.id, "list_price": 10.0})
            if stock:
                cls.env["stock.quant"]._update_available_quantity(p, cls.warehouse.lot_stock_id, stock)
            return p

        cls.p_stock = prod("PC3 Arena con stock", cls.categ_otros, 100)
        cls.p_cemento = prod("PC3 Cemento sin stock", cls.categ_cemento)
        cls.p_tubo = prod("PC3 Tubo con reposición", cls.categ_otros)
        cls.p_pintura = prod("PC3 Pintura sin stock", cls.categ_otros)

        cls.cliente = cls.env["res.partner"].create({"name": "PC3 Cliente Demo", "phone": "+51 987 654 321"})
        cls.cliente_sin_tel = cls.env["res.partner"].create({"name": "PC3 Cliente Sin Teléfono", "phone": "987654321"})

    def _cotizacion(self, lineas, partner=None, **vals):
        return self.env["sale.order"].with_user(self.ven).create(dict({
            "partner_id": (partner or self.cliente).id,
            "user_id": self.ven.id,
            "validity_date": self.hoy + timedelta(days=15),
            "order_line": [Command.create({"product_id": p.id, "product_uom_qty": q}) for p, q in lineas],
        }, **vals))

    def _agente(self, user):
        return self.env["migal.agente"].with_user(user)

    # ------------------------------------------------------------------
    # CP3-AI-01 — caso normal
    # ------------------------------------------------------------------
    def test_cp3_ai_01_normal(self):
        order = self._cotizacion([(self.p_stock, 20)])
        html, log = self._agente(self.ven).procesar_mensaje("cobertura %s" % order.name, canal="prueba")
        self.assertEqual(log.resultado, "ok")
        res = self._agente(self.ven).ejecutar_herramienta("evaluar_cobertura_preliminar", {"cotizacion": order.name})
        self.assertEqual(res["estado"], "cubierta")
        self.assertEqual(res["datos"]["lineas"][0]["estado"], "stock")
        self.assertEqual(order.state, "draft", "La consulta no debe confirmar la cotización")
        self.assertFalse(order.picking_ids, "La consulta no debe crear entregas ni reservas")

        res = self._agente(self.ven).ejecutar_herramienta("preparar_whatsapp_cotizacion", {"cotizacion": order.name})
        self.assertTrue(res["ok"], res["mensaje"])
        self.assertTrue(res["datos"]["enlace_whatsapp"].startswith("https://wa.me/51987654321?text="))
        self.assertIn(order.name, res["datos"]["mensaje"])

        html, log = self._agente(self.ven).procesar_mensaje("registrar envío %s" % order.name, canal="prueba")
        self.assertEqual(log.resultado, "ok")
        envio = self.env["migal.agente.whatsapp.envio"].search([("order_id", "=", order.id)])
        self.assertEqual(len(envio), 1)
        self.assertEqual((envio.telefono, envio.user_id), ("+51987654321", self.ven))
        self.assertIn("registrar_envio_whatsapp", log.tools_invoked)

    # ------------------------------------------------------------------
    # CP3-AI-02 — casos borde de cobertura
    # ------------------------------------------------------------------
    def test_cp3_ai_02_borde_cobertura(self):
        # Reposición prevista del tubo en 2 días.
        sup = self.env.ref("stock.stock_location_suppliers")
        fecha_rec = fields.Datetime.to_datetime(self.hoy + timedelta(days=2))
        picking = self.env["stock.picking"].create({
            "picking_type_id": self.warehouse.in_type_id.id, "location_id": sup.id,
            "location_dest_id": self.warehouse.lot_stock_id.id, "scheduled_date": fecha_rec,
            "move_ids": [Command.create({
                "product_id": self.p_tubo.id, "product_uom_qty": 12, "product_uom": self.p_tubo.uom_id.id,
                "location_id": sup.id, "location_dest_id": self.warehouse.lot_stock_id.id, "date": fecha_rec})],
        })
        picking.action_confirm()
        order = self._cotizacion([(self.p_stock, 20), (self.p_tubo, 10), (self.p_cemento, 50), (self.p_pintura, 5)])
        agente = self._agente(self.ven)

        fecha_ok = fields.Date.to_string(self.hoy + timedelta(days=5))
        res = agente.ejecutar_herramienta("evaluar_cobertura_preliminar",
                                          {"cotizacion": order.name, "fecha_requerida": fecha_ok})
        estados = {l["producto"].split("] ")[-1]: l["estado"] for l in res["datos"]["lineas"]}
        self.assertEqual(estados["PC3 Arena con stock"], "stock")
        self.assertEqual(estados["PC3 Tubo con reposición"], "reposicion")
        self.assertEqual(estados["PC3 Cemento sin stock"], "regla")
        self.assertEqual(estados["PC3 Pintura sin stock"], "faltante")
        self.assertEqual(res["estado"], "faltantes")
        self.assertIn("RN-011", res["reglas"])

        # Hoy: la reposición (en 2 días) no llega y el plazo habitual (3 días) no se cumple.
        res = agente.ejecutar_herramienta("evaluar_cobertura_preliminar",
                                          {"cotizacion": order.name, "fecha_requerida": fields.Date.to_string(self.hoy)})
        estados = {l["producto"].split("] ")[-1]: l["estado"] for l in res["datos"]["lineas"]}
        self.assertEqual(estados["PC3 Tubo con reposición"], "faltante")
        self.assertEqual(estados["PC3 Cemento sin stock"], "faltante")
        self.assertEqual(order.state, "draft")
        self.assertFalse(self.env["stock.quant"].search([("product_id", "=", self.p_stock.id),
                                                         ("reserved_quantity", ">", 0)]),
                         "La evaluación no debe reservar stock")

    def test_cp3_ai_02_whatsapp_bloqueos(self):
        sin_tel = self._cotizacion([(self.p_stock, 1)], partner=self.cliente_sin_tel)
        res = self._agente(self.ven).ejecutar_herramienta("preparar_whatsapp_cotizacion", {"cotizacion": sin_tel.name})
        self.assertFalse(res["ok"])
        self.assertIn("formato internacional", res["mensaje"])

        vencida = self._cotizacion([(self.p_stock, 1)], validity_date=self.hoy - timedelta(days=1))
        res = self._agente(self.ven).ejecutar_herramienta("preparar_whatsapp_cotizacion", {"cotizacion": vencida.name})
        self.assertFalse(res["ok"])
        self.assertIn("venció", res["mensaje"])
        self.assertFalse(self.env["migal.agente.whatsapp.envio"].search([("order_id", "in", (sin_tel | vencida).ids)]))

    # ------------------------------------------------------------------
    # CP3-AI-03 — excepción prioritaria y escalamiento
    # ------------------------------------------------------------------
    def test_cp3_ai_03_veto_descuento_y_confirmacion(self):
        order = self._cotizacion([(self.p_stock, 5)])
        total = order.amount_total
        html, log = self._agente(self.ven).procesar_mensaje(
            "El cliente pide 10%% de descuento y que confirmes la venta %s" % order.name, canal="prueba")
        self.assertEqual(log.resultado, "bloqueado")
        self.assertIn("RN-004", log.rule_triggered)
        self.assertIn("RN-006", log.rule_triggered)
        self.assertTrue(log.escalation_flag)
        self.assertIn("GER", log.escalated_to)
        self.assertEqual(log.tools_invoked, "[]", "Un veto no ejecuta herramientas")
        self.assertEqual((order.state, order.amount_total), ("draft", total))
        self.assertFalse(any(order.order_line.mapped("discount")))

    def test_cp3_ai_03_permiso_estado_cuenta(self):
        html, log = self._agente(self.ven).procesar_mensaje("estado de cuenta de PC3 Cliente Demo", canal="prueba")
        self.assertEqual(log.resultado, "bloqueado")
        self.assertIn("AUT-ROL", log.rule_triggered)
        res = self._agente(self.fco).ejecutar_herramienta("generar_estado_cuenta", {"cliente": "PC3 Cliente Demo"})
        self.assertTrue(res["ok"], res["mensaje"])

    # ------------------------------------------------------------------
    # Estado de cuenta (contabilidad como fuente de verdad)
    # ------------------------------------------------------------------
    def test_estado_cuenta_saldos(self):
        journal = self.env["account.journal"].search([("type", "=", "sale"), ("company_id", "=", self.env.company.id)], limit=1)
        banco = self.env["account.journal"].search([("type", "=", "bank"), ("company_id", "=", self.env.company.id)], limit=1)
        cliente = self.env["res.partner"].create({"name": "PC3 Cliente Contable", "vat": "20999999981", "is_company": True,
                                                  "l10n_latam_identification_type_id": self.env.ref("l10n_pe.it_RUC").id})
        doc = self.env["l10n_latam.document.type"].search([("code", "=", "01"), ("country_id.code", "=", "PE")], limit=1)
        inv = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": cliente.id, "journal_id": journal.id,
            "invoice_date": self.hoy - timedelta(days=10), "invoice_date_due": self.hoy - timedelta(days=1),
            "l10n_latam_document_type_id": doc.id, "l10n_latam_document_number": "F001-00009999",
            "invoice_line_ids": [Command.create({"name": "PC3", "quantity": 1, "price_unit": 1000.0, "tax_ids": False})],
        })
        inv.invoice_payment_term_id = False
        inv.invoice_date_due = self.hoy - timedelta(days=1)
        inv.action_post()
        self.env["account.payment.register"].with_context(active_model="account.move", active_ids=inv.ids).create(
            {"amount": 400.0, "payment_date": self.hoy - timedelta(days=5), "journal_id": banco.id})._create_payments()

        res = self._agente(self.fco).ejecutar_herramienta("generar_estado_cuenta", {
            "cliente": "20999999981", "fecha_desde": fields.Date.to_string(self.hoy - timedelta(days=30)),
            "fecha_hasta": fields.Date.to_string(self.hoy)})
        self.assertTrue(res["ok"], res["mensaje"])
        d = res["datos"]
        self.assertAlmostEqual(d["saldo_anterior"], 0.0)
        self.assertAlmostEqual(d["total_pendiente"], 600.0)
        self.assertAlmostEqual(d["total_vencido"], 600.0)
        self.assertEqual(len(d["documentos_pendientes"]), 1)
        self.assertAlmostEqual(d["saldo_periodo"], 600.0)

    # ------------------------------------------------------------------
    # Capa LLM: nunca evita los controles
    # ------------------------------------------------------------------
    def _activar_llm(self):
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("migal_agente.llm_enabled", "True")
        icp.set_param("migal_agente.llm_data_ack", "True")
        icp.set_param("migal_agente.llm_api_key", "clave-de-prueba")

    def test_llm_no_disponible_vuelve_a_reglas(self):
        self._activar_llm()
        order = self._cotizacion([(self.p_stock, 1)])
        with patch.object(llm, "run", side_effect=llm.LLMUnavailable("sin conexión")):
            html, log = self._agente(self.ven).procesar_mensaje("cobertura %s" % order.name, canal="prueba")
        self.assertEqual(log.modo, "reglas")
        self.assertEqual(log.resultado, "ok")
        self.assertIn("LLM no disponible", str(html))

    def test_llm_no_puede_saltar_permisos_ni_contrato(self):
        self._activar_llm()

        def llm_falso(texto, *, api_key, model, ejecutar_herramienta, history=None):
            r1 = ejecutar_herramienta("generar_estado_cuenta", {"cliente": "PC3 Cliente Demo"})
            r2 = ejecutar_herramienta("confirmar_venta", {"cotizacion": "S00001"})
            return "Resumen", [("generar_estado_cuenta", {}, r1), ("confirmar_venta", {}, r2)]

        with patch.object(llm, "run", side_effect=llm_falso):
            html, log = self._agente(self.ven).procesar_mensaje("dame la deuda del cliente demo", canal="prueba")
        self.assertEqual(log.modo, "llm")
        self.assertEqual(log.resultado, "bloqueado")
        self.assertIn("no está autorizado", str(html))
        self.assertIn("no autorizada", str(html))

    def test_llm_guardarrail_antes_del_llm(self):
        self._activar_llm()
        with patch.object(llm, "run") as run:
            html, log = self._agente(self.ven).procesar_mensaje("aplica 15% de descuento a la S00001", canal="prueba")
        run.assert_not_called()
        self.assertEqual(log.resultado, "bloqueado")

    # ------------------------------------------------------------------
    # Asistente flotante: mismos controles, presentados como pasos
    # ------------------------------------------------------------------
    def test_widget_procesar_cotizacion(self):
        order = self._cotizacion([(self.p_stock, 3), (self.p_pintura, 2)])
        agente = self._agente(self.ven)
        ctx = agente.widget_contexto("sale.order", order.id)
        self.assertEqual([a["id"] for a in ctx["acciones"]], ["procesar_cotizacion", "qr", "cobertura"])
        res = agente.widget_ejecutar("procesar_cotizacion", "sale.order", order.id, {"incluir_disponibilidad": True})
        self.assertTrue(res["ok"], res["final"])
        titulos = " | ".join(p["titulo"] for p in res["pasos"])
        self.assertIn("Revisión vigente", titulos)
        self.assertIn("Agregando la disponibilidad", titulos)
        self.assertIn("Algunos productos requieren confirmar", res["whatsapp"]["mensaje"])
        self.assertEqual(res["whatsapp"]["telefono"], "+51987654321")
        self.assertTrue(res["pdf_url"].endswith("/%s" % order.id))
        res = agente.widget_ejecutar("registrar_envio", "sale.order", order.id, {"mensaje": "Hola, editado"})
        self.assertTrue(res["registrado"])
        self.assertEqual(self.env["migal.agente.whatsapp.envio"].search([("order_id", "=", order.id)]).mensaje, "Hola, editado")

    def test_widget_estado_cuenta_por_rol(self):
        ctx = self._agente(self.ven).widget_contexto("res.partner", self.cliente.id)
        self.assertTrue(ctx["acciones"][0]["bloqueada"])
        res = self._agente(self.ven).widget_ejecutar("estado_cuenta", "res.partner", self.cliente.id, {})
        self.assertFalse(res["ok"])
        res = self._agente(self.fco).widget_ejecutar("estado_cuenta", "res.partner", self.cliente.id, {})
        self.assertTrue(res["ok"], res["final"])
        self.assertIn("/report/pdf/migal_agente.report_estado_cuenta/", res["pdf_url"])

    def test_widget_mensaje_usa_la_cotizacion_abierta(self):
        order = self._cotizacion([(self.p_stock, 1)])
        res = self._agente(self.ven).widget_mensaje("cobertura", "sale.order", order.id)
        self.assertEqual(res["resultado"], "ok", "%s | %s" % (order.name, res["html"][:300]))
        self.assertIn(order.name, res["html"])

    def test_qr_presencial(self):
        order = self._cotizacion([(self.p_stock, 2)], partner=self.cliente_sin_tel)
        self.assertFalse(order.access_token)
        res = self._agente(self.ven).widget_ejecutar("qr", "sale.order", order.id, {})
        self.assertTrue(res["ok"], res["final"])
        self.assertTrue(order.access_token, "El QR necesita el token de acceso del portal")
        self.assertIn("report_type=pdf", res["qr"]["url"], "Versión de solo lectura: sin aceptar ni pagar")
        self.assertIn("access_token=%s" % order.access_token, res["qr"]["url"])
        self.assertTrue(res["qr"]["imagen"].startswith("data:image/png;base64,"))
        self.assertEqual((order.state, order.amount_total > 0), ("draft", True))
        html, log = self._agente(self.ven).procesar_mensaje("muéstrale el qr de %s al cliente" % order.name, canal="prueba")
        self.assertEqual(log.resultado, "ok")
        self.assertIn("generar_qr_cotizacion", log.tools_invoked)
        self.assertNotIn("qr_png_base64", log.tools_invoked)

    def test_qr_bloquea_cotizacion_vencida(self):
        vencida = self._cotizacion([(self.p_stock, 1)], validity_date=self.hoy - timedelta(days=1))
        res = self._agente(self.ven).ejecutar_herramienta("generar_qr_cotizacion", {"cotizacion": vencida.name})
        self.assertFalse(res["ok"])
        self.assertFalse(vencida.access_token)

    def test_qr_usa_tunel_activo_y_no_en_whatsapp(self):
        from odoo.addons.migal_agente.models.tool_whatsapp import MigalAgenteToolWhatsapp
        order = self._cotizacion([(self.p_stock, 1)])
        tunel = "https://prueba-demo.trycloudflare.com"
        with patch.object(MigalAgenteToolWhatsapp, "_tunel_activo", return_value=tunel):
            res = self._agente(self.ven).ejecutar_herramienta("generar_qr_cotizacion", {"cotizacion": order.name})
            self.assertTrue(res["datos"]["url"].startswith(tunel + "/my/orders/%s?access_token=" % order.id))
            self.assertIn("Publicación temporal activa", [c["control"] for c in res["controles"]])
            wa = self._agente(self.ven).ejecutar_herramienta("preparar_whatsapp_cotizacion", {"cotizacion": order.name})
            self.assertNotIn("trycloudflare", wa["datos"]["mensaje"], "El mensaje no debe llevar un enlace temporal")

    # ------------------------------------------------------------------
    # Estado de cuenta: compartir con el cliente
    # ------------------------------------------------------------------
    def test_compartir_estado_cuenta_roles_y_copia(self):
        res = self._agente(self.ven).ejecutar_herramienta("compartir_estado_cuenta", {"cliente": "PC3 Cliente Demo"})
        self.assertEqual(res["estado"], "sin_permiso")
        Pub = self.env["migal.agente.estado.cuenta.publicacion"].sudo()
        antes = Pub.search_count([])
        res = self._agente(self.fco).ejecutar_herramienta("compartir_estado_cuenta", {"cliente": "PC3 Cliente Demo"})
        self.assertTrue(res["ok"], res["mensaje"])
        pub = Pub.browse(res["datos"]["publicacion_id"])
        self.assertEqual(Pub.search_count([]), antes + 1)
        self.assertIn("/migal/estado-cuenta/%s" % pub.token, res["datos"]["url"])
        self.assertTrue(pub.vigente)
        self.assertEqual(res["datos"]["telefono"], "+51987654321")
        self.assertIn("total pendiente", res["datos"]["mensaje"])
        self.assertEqual(pub.get_datos()["cliente"], "PC3 Cliente Demo")
        html, log = self._agente(self.fco).procesar_mensaje("comparte el estado de cuenta de PC3 Cliente Demo por whatsapp",
                                                            canal="prueba")
        self.assertEqual(log.resultado, "ok")
        self.assertIn("compartir_estado_cuenta", log.tools_invoked)

    def test_widget_compartir_y_registrar_envio_estado(self):
        res = self._agente(self.fco).widget_ejecutar("estado_cuenta_compartir", "res.partner", self.cliente.id, {})
        self.assertTrue(res["ok"], res["final"])
        self.assertEqual(res["whatsapp"]["accion_registro"], "registrar_envio_estado")
        self.assertTrue(res["qr"]["imagen"].startswith("data:image/png;base64,"))
        res = self._agente(self.fco).widget_ejecutar("registrar_envio_estado", "res.partner", self.cliente.id, {})
        self.assertTrue(res["registrado"])
        res = self._agente(self.ven).widget_ejecutar("registrar_envio_estado", "res.partner", self.cliente.id, {})
        self.assertFalse(res["ok"])

    def test_estado_cuenta_metodos_pago(self):
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("migal_agente.pago_yape", "900 000 000")
        icp.set_param("migal_agente.pago_bcp_cci", "002-000-000000000000-00")
        for clave in ("pago_bcp_cuenta", "pago_bbva_cuenta", "pago_bbva_cci"):
            icp.set_param("migal_agente.%s" % clave, "")
        res = self._agente(self.fco).ejecutar_herramienta("generar_estado_cuenta", {"cliente": "PC3 Cliente Demo"})
        metodos = {m["metodo"]: m["lineas"] for m in res["datos"]["metodos_pago"]}
        self.assertEqual(metodos["Yape"], ["Celular: 900 000 000"])
        self.assertEqual(metodos["Transferencia BCP"], ["CCI: 002-000-000000000000-00"])
        self.assertNotIn("Transferencia BBVA", metodos, "Un banco sin datos no se muestra")
        res = self._agente(self.fco).ejecutar_herramienta("compartir_estado_cuenta", {"cliente": "PC3 Cliente Demo"})
        self.assertIn("Yape o Transferencia BCP", res["datos"]["mensaje"])

    def test_cobertura_comprometido_y_fecha_estimada(self):
        # Otra venta confirmada compromete 90 de las 100 unidades en stock.
        otra = self.env["sale.order"].create({
            "partner_id": self.cliente_sin_tel.id,
            "order_line": [Command.create({"product_id": self.p_stock.id, "product_uom_qty": 90})]})
        otra.action_confirm()
        order = self._cotizacion([(self.p_stock, 20)])
        agente = self._agente(self.ven)
        hoy = fields.Date.to_string(self.hoy)
        res = agente.ejecutar_herramienta("evaluar_cobertura_preliminar", {"cotizacion": order.name, "fecha_requerida": hoy})
        linea = res["datos"]["lineas"][0]
        self.assertEqual((linea["comprometido"], linea["disponible"], linea["estado"]), (90, 10, "faltante"))
        self.assertFalse(res["datos"]["fecha_atencion"], "Sin reposición prevista no hay fecha estimada")
        self.assertIn("confirmar su abastecimiento", res["datos"]["mensaje_cliente"])
        # Llega una reposición en 4 días: la fecha estimada pasa a ser esa.
        sup = self.env.ref("stock.stock_location_suppliers")
        llegada = fields.Datetime.to_datetime(self.hoy + timedelta(days=4)).replace(hour=15)
        rec = self.env["stock.picking"].create({
            "picking_type_id": self.warehouse.in_type_id.id, "location_id": sup.id,
            "location_dest_id": self.warehouse.lot_stock_id.id, "scheduled_date": llegada,
            "move_ids": [Command.create({"product_id": self.p_stock.id, "product_uom_qty": 15,
                                         "product_uom": self.p_stock.uom_id.id, "location_id": sup.id,
                                         "location_dest_id": self.warehouse.lot_stock_id.id, "date": llegada})]})
        rec.action_confirm()
        res = agente.ejecutar_herramienta("evaluar_cobertura_preliminar", {"cotizacion": order.name, "fecha_requerida": hoy})
        esperada = fields.Date.to_string(self.hoy + timedelta(days=4))
        self.assertEqual(res["datos"]["lineas"][0]["fecha_posible"], esperada)
        self.assertEqual(res["datos"]["fecha_atencion"], esperada)
        self.assertIn("desde el", res["datos"]["mensaje_cliente"])
        res = agente.widget_ejecutar("cobertura", "sale.order", order.id, {"fecha": esperada})
        self.assertEqual(res["pasos"][-1]["titulo"][:30], "Fecha estimada para atender to")
        self.assertIn("sugerencia", res)


@tagged("post_install", "-at_install", "migal_agente")
class TestEstadoCuentaPublico(HttpCase):
    """La ruta pública solo entrega PDFs de copias vigentes; todo lo demás es 404."""

    def test_ruta_publica(self):
        partner = self.env["res.partner"].create({"name": "PC3 Cliente Público"})
        Pub = self.env["migal.agente.estado.cuenta.publicacion"].sudo()
        datos = {"cliente": partner.name, "simbolo": "S/", "fecha_desde": "2026-11-01", "fecha_hasta": "2026-11-13",
                 "fecha_consulta": "2026-11-13", "saldo_anterior": 0, "movimientos": [], "saldo_periodo": 0,
                 "documentos_pendientes": [], "pagos_sin_aplicar": [], "total_pendiente": 0, "total_vencido": 0,
                 "informativo": [], "antiguedad": []}
        pub = Pub.create({"partner_id": partner.id, "datos_json": json.dumps(datos)})
        r = self.url_open("/migal/estado-cuenta/%s" % pub.token)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Content-Type"], "application/pdf")
        self.assertIn("no-store", r.headers["Cache-Control"])
        self.assertEqual(pub.vistas, 1)
        self.assertEqual(self.url_open("/migal/estado-cuenta/00000000-0000-0000-0000-000000000000").status_code, 404)
        pub.expira = fields.Datetime.now() - timedelta(minutes=1)
        self.assertEqual(self.url_open("/migal/estado-cuenta/%s" % pub.token).status_code, 404)
        pub.write({"expira": fields.Datetime.now() + timedelta(hours=1), "activo": False})
        self.assertEqual(self.url_open("/migal/estado-cuenta/%s" % pub.token).status_code, 404)

