"""Agente de cadena de suministro. Responsable: Alejandro Flores.

Punto de partida real (ya funciona): cobertura, compras pendientes y estado de recepción.
Por hacer (ficha producto/agentes/suministro.md): consultar_baja_rotacion (la usa marketing; hoy responde el
simulador), sugerir reposición con las reglas de stock mínimo, borrador de orden de compra, comparar
proveedores, despachos pendientes y recepción con OCR de la guía.
"""
from collections import defaultdict
import logging
import re

from markupsafe import Markup

from odoo import fields, models
from odoo.tools import format_date
from odoo.tools.float_utils import float_round

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
            "diagnosticar_faltantes": {
                "description": "Evalúa faltantes de una cotización abierta para una fecha y propone traslados.",
                "input_schema": {
                    "type": "object",
                    "properties": {"cotizacion": ORDER_REF, "fecha_requerida": DATE},
                    "required": ["cotizacion", "fecha_requerida"],
                    "additionalProperties": False,
                },
                "roles": ["VEN", "ALM", "CMP", "GER"],
                "escritura": "Ninguna (solo bitácora).",
                "reglas": ["RN-011", "RN-015", "RN-016"],
                "metodo": "diagnosticar_faltantes",
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
        m = re.fullmatch(
            r"diagnostico de ([a-z]{1,4}\d{3,}(?:-\d+)?) para (\d{4}-\d{2}-\d{2})",
            texto.rstrip(" ?"),
        )
        if m:
            return "diagnosticar_faltantes", {"cotizacion": m.group(1).upper(), "fecha_requerida": m.group(2)}
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

    def diagnosticar_faltantes(self, cotizacion, fecha_requerida):
        titulo = "Diagnóstico de faltantes"
        try:
            fecha = fields.Date.to_date(fecha_requerida)
        except ValueError:
            return self._resultado(False, "error", titulo, "Indica una fecha válida en formato AAAA-MM-DD.")

        hoy = self._hoy()
        if not fecha or fecha < hoy:
            return self._resultado(False, "error", titulo, "Indica una fecha requerida igual o posterior a hoy.")

        orden, vigente, error = self._buscar_cotizacion(cotizacion)
        if error:
            return self._resultado(False, "error", titulo, error)

        revision_valida, detalle = self._control_version(orden, vigente)
        if not revision_valida:
            return self._resultado(False, "bloqueado", titulo, detalle)
        if not orden.active or orden.state not in ("draft", "sent") or (
            orden.validity_date and orden.validity_date < hoy
        ):
            return self._resultado(False, "bloqueado", titulo, "Indica una cotización abierta y vigente.")

        origen = orden.warehouse_id.lot_stock_id
        if not origen:
            return self._resultado(False, "error", titulo, "La cotización necesita un almacén de atención.")

        requeridos = defaultdict(float)
        for linea in orden.order_line:
            producto = linea.product_id
            if producto.is_storable and not linea.display_type and linea.product_uom_qty > 0:
                requeridos[producto] += linea.product_uom_id._compute_quantity(
                    linea.product_uom_qty, producto.uom_id, round=False,
                )
        if not requeridos:
            return self._resultado(
                False, "error", titulo,
                "Agrega un producto del catálogo con inventario y cantidad positiva, y guarda la cotización.",
            )

        compania = orden.company_id
        almacenes = self.env["stock.warehouse"].search([("company_id", "=", compania.id)])
        ubicaciones = self.env["stock.location"].search([
            ("id", "child_of", almacenes.lot_stock_id.ids),
            ("company_id", "=", compania.id),
            ("usage", "=", "internal"),
        ])
        ids_productos = [p.id for p in requeridos]
        libres = defaultdict(dict)
        for producto, ubicacion, stock, reservada in self.env["stock.quant"]._read_group(
            [
                ("company_id", "=", compania.id),
                ("product_id", "in", ids_productos),
                ("location_id", "in", ubicaciones.ids),
                ("owner_id", "=", False),
            ],
            groupby=["product_id", "location_id"],
            aggregates=["quantity:sum", "reserved_quantity:sum"],
        ):
            libres[producto][ubicacion] = max(stock - reservada, 0.0)

        limite = self.env["migal.agente.tool.cobertura"]._fin_dia_utc(fecha)
        recepciones = dict(self.env["stock.move"]._read_group(
            [
                ("company_id", "=", compania.id),
                ("product_id", "in", ids_productos),
                ("location_id.usage", "=", "supplier"),
                ("location_dest_id", "=", origen.id),
                ("purchase_line_id", "!=", False),
                ("state", "in", ("waiting", "confirmed", "assigned", "partially_available")),
                ("date", ">=", fields.Datetime.now()),
                ("date", "<=", limite),
            ],
            groupby=["product_id"],
            aggregates=["product_qty:sum"],
        ))

        lineas, filas = [], []
        for producto, pedido in requeridos.items():
            precision = producto.uom_id.rounding
            libre = libres[producto].get(origen, 0.0)
            previsto = recepciones.get(producto, 0.0)
            sin_traslado = float_round(
                max(pedido - libre - previsto, 0.0), precision_rounding=precision,
            )

            saldo = sin_traslado
            traslados = []
            otras = sorted(libres[producto].items(), key=lambda item: item[0].complete_name)
            for ubicacion, stock in otras:
                if ubicacion == origen or stock <= 0 or saldo <= 0:
                    continue
                cantidad = min(stock, saldo)
                traslados.append({"ubicacion": ubicacion.complete_name, "cantidad": cantidad})
                saldo = float_round(max(saldo - cantidad, 0.0), precision_rounding=precision)

            lineas.append({
                "producto": producto.display_name,
                "unidad": producto.uom_id.name,
                "pedido": pedido,
                "libre_origen": libre,
                "recepcion_en_plazo": previsto,
                "saldo_sin_traslado": sin_traslado,
                "traslados": traslados,
                "saldo_si_traslado": saldo,
            })
            alternativas = ", ".join(f"{t['cantidad']:g} desde {t['ubicacion']}" for t in traslados) or "—"
            datos_producto = [
                ("Pedido", f"{pedido:g} {producto.uom_id.name}"),
                ("Libre en origen", f"{libre:g}"),
                ("Recepción en plazo", f"{previsto:g}"),
                ("Saldo sin traslado", f"{sin_traslado:g}"),
                ("Traslado posible", alternativas),
                ("Saldo si se traslada", f"{saldo:g}"),
            ]
            detalle = Markup("").join(
                Markup("<div><strong>%s</strong> %s</div>") % dato for dato in datos_producto
            )
            filas.append([
                Markup('<div class="text-break" style="overflow-wrap: anywhere"><strong>%s</strong>%s</div>')
                % (producto.display_name, detalle),
            ])

        return self._resultado(
            True, "alerta" if any(l["saldo_sin_traslado"] > 0 for l in lineas) else "ok",
            titulo, f"{orden.name} · Fecha requerida {format_date(self.env, fecha)} · Origen {origen.complete_name}.",
            reglas=["RN-011", "RN-015", "RN-016"], res=orden,
            avisos=[
                "El stock libre refleja las reservas registradas. Confirma las recepciones y traslados antes de comprometer la fecha.",
            ],
            datos={
                "cotizacion": orden.name,
                "fecha_requerida": fields.Date.to_string(fecha),
                "ubicacion_origen": origen.complete_name,
                "detalle_faltantes": lineas,
                "tabla": {"columnas": ["Producto"], "filas": filas},
            },
        )

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
