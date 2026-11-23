"""Agente de cadena de suministro. Responsable: Alejandro Flores.

Punto de partida real (ya funciona): cobertura, compras pendientes y estado de recepción.
Por hacer (ficha producto/agentes/suministro.md): consultar_baja_rotacion (la usa marketing; hoy responde el
simulador), sugerir reposición con las reglas de stock mínimo, borrador de orden de compra, comparar
proveedores, despachos pendientes y recepción con OCR de la guía.
"""
import logging
import re

from odoo import models
from odoo.tools import format_date

from odoo.addons.migal_agente.agent.contracts import DATE, ORDER_REF

_logger = logging.getLogger(__name__)

OC_REF = {"type": "string", "description": "Referencia de la orden de compra, p. ej. P00020.",
          "pattern": r"^[A-Za-z]{1,4}\d{3,}$", "maxLength": 20}


class AgenteSuministro(models.AbstractModel):
    _name = "migal.agente.suministro"
    _inherit = "migal.agente.especialista"
    _description = "Agente MIGAL · Cadena de suministro"
    _agente_codigo = "suministro"
    _agente_nombre = "Cadena de suministro"

    # ------------------------------------------------------------------
    # Contratos
    # ------------------------------------------------------------------
    def _herramientas(self):
        return {
            "evaluar_cobertura_preliminar": {
                "description": (
                    "Revisa por producto y cantidad si una cotización vigente puede cubrirse con el stock "
                    "disponible en tienda y las reposiciones previstas hasta la fecha solicitada. Aplica la "
                    "regla habitual para cementos, agregados, fierros y ladrillos. No reserva stock, no crea "
                    "SOV ni compras y no garantiza entregas."),
                "input_schema": {"type": "object", "properties": {"cotizacion": ORDER_REF, "fecha_requerida": DATE},
                                 "required": ["cotizacion"], "additionalProperties": False},
                "roles": ["VEN", "ALM", "CMP", "GER"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": ["RN-011", "RN-015"],
                "metodo": "evaluar_cobertura_preliminar",
            },
            "listar_compras_pendientes": {
                "description": "Órdenes de compra por aprobar, por recibir y atrasadas.",
                "input_schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
                "roles": ["CMP", "ALM", "GER"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": ["RN-012"],
                "metodo": "listar_compras_pendientes",
            },
            "consultar_recepcion": {
                "description": "Cantidades pedidas, recibidas y pendientes de una orden de compra.",
                "input_schema": {"type": "object", "properties": {"orden_compra": OC_REF},
                                 "required": ["orden_compra"], "additionalProperties": False},
                "roles": ["CMP", "ALM", "FCO", "GER"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": ["RN-013"],
                "metodo": "consultar_recepcion",
            },
        }

    def _eventos_escuchados(self):
        return {"EV-018": "_al_confirmarse_venta"}

    def _reconocer(self, texto):
        m = re.search(r"\b(recepcion|recibido|llego)\b.*\b(p\d{5})\b", texto)
        if m:
            return "consultar_recepcion", {"orden_compra": m.group(2).upper()}
        if re.search(r"\b(compras? pendientes?|ordenes? de compra|que falta recibir|por recibir|oc pendientes?)\b", texto):
            return "listar_compras_pendientes", {}
        return None

    def _acciones_widget(self, record):
        if record._name == "purchase.order" and record.state == "purchase":
            return [{"id": "consultar_recepcion", "label": "Estado de recepción", "icon": "fa-truck",
                     "descripcion": "Pedido, recibido y pendiente por producto", "principal": True}]
        return []

    def _argumentos_widget(self, accion, record, params):
        if accion == "consultar_recepcion":
            return {"orden_compra": record.name}
        return None

    # ------------------------------------------------------------------
    # Herramientas
    # ------------------------------------------------------------------
    def evaluar_cobertura_preliminar(self, cotizacion, fecha_requerida=None):
        return self.env["migal.agente.tool.cobertura"].evaluar(cotizacion, fecha_requerida)

    def listar_compras_pendientes(self):
        hoy = self._hoy()
        PO = self.env["purchase.order"]
        por_aprobar = PO.search([("state", "in", ("draft", "sent"))], order="date_order")
        por_recibir = PO.search([("state", "=", "purchase"), ("receipt_status", "in", ("pending", "partial"))],
                                order="date_planned")
        atrasadas = por_recibir.filtered(lambda o: o.date_planned and o.date_planned.date() < hoy)
        filas = []
        for po in por_aprobar:
            filas.append([po.name, po.partner_id.display_name, "Por aprobar (GER)", "-", "S/ {:,.2f}".format(po.amount_total)])
        for po in por_recibir:
            estado = "Atrasada" if po in atrasadas else ("Parcial" if po.receipt_status == "partial" else "Por recibir")
            filas.append([po.name, po.partner_id.display_name, estado,
                          format_date(self.env, po.date_planned) if po.date_planned else "-",
                          "S/ {:,.2f}".format(po.amount_total)])
        mensaje = "%s por aprobar, %s por recibir (%s atrasadas)." % (len(por_aprobar), len(por_recibir), len(atrasadas))
        avisos = ["Confirmar una orden de compra lo autoriza Gerencia (RN-012)."] if por_aprobar else []
        if atrasadas:
            avisos.append("Hay recepciones atrasadas: incumplimiento de abastecimiento (EV-024).")
        return self._resultado(True, "ok", "Compras pendientes", mensaje, reglas=["RN-012"], avisos=avisos, datos={
            "por_aprobar": por_aprobar.mapped("name"), "por_recibir": por_recibir.mapped("name"),
            "atrasadas": atrasadas.mapped("name"),
            "tabla": {"columnas": ["Orden", "Proveedor", "Estado", "Fecha prevista", "Total"], "filas": filas}})

    def consultar_recepcion(self, orden_compra):
        po = self.env["purchase.order"].search([("name", "=", orden_compra.upper())], limit=1)
        if not po:
            return self._resultado(False, "error", "Estado de recepción",
                                   "No encontré la orden de compra %s." % orden_compra)
        productos = []
        for linea in po.order_line.filtered(lambda l: l.product_id and not l.display_type):
            productos.append({"producto": linea.product_id.display_name, "pedido": linea.product_qty,
                              "recibido": linea.qty_received,
                              "pendiente": max(linea.product_qty - linea.qty_received, 0.0)})
        pendiente = sum(p["pendiente"] for p in productos)
        recibido = sum(p["recibido"] for p in productos)
        estado = "completa" if not pendiente else ("parcial" if recibido else "pendiente")
        texto = {"completa": "Recepción completa.", "parcial": "Recepción parcial: faltan %g unidades." % pendiente,
                 "pendiente": "Aún no se recibe nada."}[estado]
        return self._resultado(True, estado, "Recepción de %s" % po.name, "%s · %s" % (po.partner_id.display_name, texto),
                               res=po, reglas=["RN-013"], datos={
                                   "orden_compra": po.name, "estado_recepcion": estado, "productos": productos,
                                   "tabla": {"columnas": ["Producto", "Pedido", "Recibido", "Pendiente"],
                                             "filas": [["%s" % p["producto"], "{:g}".format(p["pedido"]),
                                                        "{:g}".format(p["recibido"]), "{:g}".format(p["pendiente"])]
                                                       for p in productos]}})

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def _al_confirmarse_venta(self, datos):
        """EV-018. Por hacer: preparar el despacho y revisar si la venta deja productos bajo el mínimo."""
        _logger.info("Agente suministro: EV-018 recibido para %s.", datos.get("orden"))
