"""Pruebas del orquestador multiagente: catálogo, registro, consultas, simulador, eventos y permisos."""
from odoo.tests import TransactionCase, new_test_user, tagged

from ..agent import catalogo, contracts


@tagged("post_install", "-at_install", "migal_agente")
class TestContratos(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("migal_agente.llm_enabled", "False")
        cls.ger = new_test_user(cls.env, login="ger_contratos",
                                groups="sales_team.group_sale_manager,account.group_account_manager")
        cls.Agente = cls.env["migal.agente"]

    # Catálogo -----------------------------------------------------------
    def test_catalogo_consistente(self):
        codigos = set(catalogo.AGENTES)
        for nombre, c in catalogo.CONSULTAS.items():
            self.assertIn(c["proveedor"], codigos, nombre)
            self.assertTrue(set(c["consumidores"]) <= codigos, nombre)
            self.assertNotIn(c["proveedor"], c["consumidores"], "Un agente no se consulta a sí mismo: %s" % nombre)
            salida = c["ejemplo_salida"]
            self.assertTrue({"ok", "estado", "titulo", "mensaje", "datos"} <= set(salida), nombre)
            for consumidor, campos in (c.get("campos_por_consumidor") or {}).items():
                self.assertIn(consumidor, c["consumidores"], nombre)
                self.assertTrue(set(campos) <= set(salida["datos"]), nombre)
        for codigo, e in catalogo.EVENTOS.items():
            self.assertRegex(codigo, r"^EV-\d{3}$")
            self.assertIn(e["emisor"], codigos, codigo)
            self.assertTrue(set(e["escuchan"]) <= codigos, codigo)
        for herramienta, dueno in catalogo.DUENO_HERRAMIENTAS_NUCLEO.items():
            self.assertIn(herramienta, contracts.TOOLS)
            self.assertIn(dueno, codigos)
        for a in catalogo.AGENTES.values():
            self.assertTrue(set(a["roles"]) <= set(catalogo.ROLES))

    def test_nombres_de_herramientas_unicos(self):
        vistos = {}
        for codigo, agente in self.Agente._agentes().items():
            for nombre in agente._herramientas():
                self.assertNotIn(nombre, contracts.TOOLS, "%s choca con una herramienta del núcleo" % nombre)
                self.assertNotIn(nombre, vistos, "%s definida por %s y %s" % (nombre, vistos.get(nombre), codigo))
                vistos[nombre] = codigo

    def test_herramientas_de_agentes_bien_declaradas(self):
        for codigo, agente in self.Agente._agentes().items():
            self.assertIn(codigo, catalogo.AGENTES, "Agente %s sin ficha en el catálogo" % codigo)
            for nombre, spec in agente._herramientas().items():
                self.assertRegex(nombre, r"^[a-z][a-z0-9_]{2,63}$")
                self.assertTrue(spec.get("description") or spec.get("descripcion"), nombre)
                self.assertEqual(spec["input_schema"]["type"], "object", nombre)
                self.assertFalse(spec["input_schema"].get("additionalProperties", True), nombre)
                self.assertTrue(spec["roles"] and set(spec["roles"]) <= set(catalogo.ROLES), nombre)
                self.assertTrue(hasattr(agente, spec["metodo"]), nombre)
            for evento, metodo in (agente._eventos_escuchados() or {}).items():
                self.assertIn(codigo, catalogo.EVENTOS[evento]["escuchan"],
                              "%s no figura como oyente de %s" % (codigo, evento))
                self.assertTrue(hasattr(agente, metodo))
        for nombre, c in catalogo.CONSULTAS.items():
            spec = self.Agente._spec(nombre)
            if spec:
                self.assertEqual(spec["agente"], c["proveedor"], "%s la implementa quien no es su dueño" % nombre)

    # Consultas ----------------------------------------------------------
    def test_consulta_no_acordada(self):
        res = self.Agente.with_user(self.ger).consultar("marketing", "resumen_obligaciones", {})
        self.assertFalse(res["ok"])
        self.assertEqual(res["estado"], "contrato")
        res = self.Agente.with_user(self.ger).consultar("ventas", "herramienta_inventada", {})
        self.assertEqual(res["estado"], "contrato")

    def test_consulta_queda_en_bitacora(self):
        self.Agente.with_user(self.ger).consultar("marketing", "consultar_cotizaciones_perdidas", {"dias": 30})
        log = self.env["migal.agente.log"].sudo().search([("canal", "=", "consulta")], order="id desc", limit=1)
        self.assertEqual(log.agente, "marketing")
        self.assertIn("consultar_cotizaciones_perdidas", log.input_prompt)

    def test_simulador_respeta_minimo_privilegio(self):
        # Fuerza el simulador: con otro dueño declarado, la implementación real no cuenta.
        contrato = catalogo.CONSULTAS["consultar_situacion_credito"]
        original = contrato["proveedor"]
        contrato["proveedor"] = "ventas"
        try:
            res = self.Agente.with_user(self.ger).consultar("marketing", "consultar_situacion_credito",
                                                            {"cliente": "x"})
        finally:
            contrato["proveedor"] = original
        self.assertTrue(res.get("simulado"))
        self.assertEqual(set(res["datos"]), {"cliente", "excluir"})

    # Eventos ------------------------------------------------------------
    def test_solo_el_dueno_emite(self):
        self.assertEqual(self.Agente.emitir("EV-018", {"orden": "S0"}, desde="marketing"), [])
        self.assertEqual(self.Agente.emitir("EV-999", {}), [])

    def test_evento_entregado_y_registrado(self):
        recibieron = self.Agente.emitir("EV-058", {"tipo": "prueba", "documento": "X", "detalle": "-"},
                                        desde="contabilidad")
        esperados = set(catalogo.EVENTOS["EV-058"]["escuchan"]) & set(self.Agente._agentes())
        self.assertEqual(set(recibieron), esperados)
        log = self.env["migal.agente.log"].sudo().search([("canal", "=", "evento")], order="id desc", limit=1)
        self.assertEqual(log.agente, "contabilidad")

    def test_oyente_que_falla_no_rompe(self):
        if "contabilidad" not in self.Agente._agentes():
            self.skipTest("Agente de contabilidad no instalado")
        clase = type(self.env["migal.agente.contabilidad"])
        original = clase._al_registrarse_documento

        def falla(modelo, datos):
            raise ValueError("falla de prueba")
        clase._al_registrarse_documento = falla
        try:
            recibieron = self.Agente.emitir("EV-055", {"pago": "P", "proveedor": "X", "monto": 1}, desde="pagos")
        finally:
            clase._al_registrarse_documento = original
        self.assertNotIn("contabilidad", recibieron)

    # Permisos y LLM -----------------------------------------------------
    def test_llm_solo_ve_herramientas_de_su_rol(self):
        sin_rol = new_test_user(self.env, login="base_contratos", groups="base.group_user")
        nombres = {t["name"] for t in self.Agente.with_user(sin_rol)._herramientas_para_usuario()}
        self.assertFalse(nombres & {"facturas_por_vencer", "pendientes_cierre", "resumen_cartera"})
        nombres = {t["name"] for t in self.Agente.with_user(self.ger)._herramientas_para_usuario()}
        self.assertTrue({"facturas_por_vencer", "pendientes_cierre", "clientes_inactivos"} <= nombres)

    def test_herramienta_inexistente(self):
        res = self.Agente.with_user(self.ger).ejecutar_herramienta("no_existe", {})
        self.assertFalse(res["ok"])
