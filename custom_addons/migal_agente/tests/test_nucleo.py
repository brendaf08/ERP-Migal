"""Pruebas del núcleo independiente de Odoo: intérprete, contrato y guardarraíles."""
from odoo.tests import BaseCase, tagged

from ..agent import contracts, guardrails, intent


@tagged("post_install", "-at_install", "migal_agente")
class TestNucleo(BaseCase):

    def test_intent_whatsapp(self):
        self.assertEqual(intent.parse("Prepárame el WhatsApp de la S00573"),
                         ("preparar_whatsapp_cotizacion", {"cotizacion": "S00573"}))

    def test_intent_qr(self):
        self.assertEqual(intent.parse("el cliente está presencial, muéstrale el QR de la S00576"),
                         ("generar_qr_cotizacion", {"cotizacion": "S00576"}))

    def test_intent_compartir_estado(self):
        nombre, args = intent.parse("Comparte el estado de cuenta de Inversiones del Norte por WhatsApp")
        self.assertEqual(nombre, "compartir_estado_cuenta")
        self.assertEqual(args["cliente"], "inversiones del norte")

    def test_intent_registrar(self):
        self.assertEqual(intent.parse("registrar envío S00573")[0], "registrar_envio_whatsapp")

    def test_intent_cobertura_con_fecha(self):
        nombre, args = intent.parse("¿alcanza el stock para la S00577 para el 20/11/2026?")
        self.assertEqual(nombre, "evaluar_cobertura_preliminar")
        self.assertEqual(args, {"cotizacion": "S00577", "fecha_requerida": "2026-11-20"})

    def test_intent_estado_cuenta(self):
        nombre, args = intent.parse("Estado de cuenta de Constructora Andina del 01/10/2026 al 13/11/2026")
        self.assertEqual(nombre, "generar_estado_cuenta")
        self.assertEqual(args["cliente"], "constructora andina")
        self.assertEqual((args["fecha_desde"], args["fecha_hasta"]), ("2026-10-01", "2026-11-13"))

    def test_intent_ayuda(self):
        self.assertEqual(intent.parse("hola")[0], "ayuda")
        self.assertEqual(intent.parse("cuéntame un chiste")[0], "ayuda")

    def test_contrato_rechaza_parametros(self):
        with self.assertRaises(contracts.ToolInputError):
            contracts.validate_args("evaluar_cobertura_preliminar", {"cotizacion": "S1; DROP TABLE"})
        with self.assertRaises(contracts.ToolInputError):
            contracts.validate_args("evaluar_cobertura_preliminar", {"cotizacion": "S00573", "reservar": True})
        with self.assertRaises(contracts.ToolInputError):
            contracts.validate_args("generar_estado_cuenta", {})
        with self.assertRaises(contracts.ToolInputError):
            contracts.validate_args("crear_venta", {"x": 1})

    def test_guardarrailes(self):
        casos = {
            "dale 10% de descuento a la S00573": "RN-004",
            "confirma la venta S00573": "RN-006",
            "resérvame 20 bolsas de cemento": "RN-015",
            "dale crédito a 30 días al cliente": "RN-004",
            "registra el pago de la factura F001-1": "RN-014",
            "emite la factura de la S00573": "RN-009",
        }
        for texto, regla in casos.items():
            self.assertIn(regla, [h["regla"] for h in guardrails.check_request(texto)], texto)
        for texto in ("whatsapp S00573", "cobertura S00573", "estado de cuenta de Andina", "registrar envío S00573"):
            self.assertFalse(guardrails.check_request(texto), texto)
