from datetime import datetime, time, timedelta

import pytz

from odoo import fields, models
from odoo.tools import float_compare, format_date

ESTADOS = {
    "stock": "Cubierto con stock",
    "reposicion": "Cubierto con reposición prevista",
    "regla": "Regla habitual de abastecimiento",
    "faltante": "Faltante sin cobertura prevista",
    "no_inventariable": "No inventariable (servicio)",
}


class MigalAgenteToolCobertura(models.AbstractModel):
    """Herramienta evaluar_cobertura_preliminar (no reserva, no crea SOV ni compras).

    Por producto:
      libre = stock en tienda − entregas pendientes de otras ventas confirmadas hasta la fecha
      llega = recepciones previstas (no validadas) hasta la fecha requerida
    y, si no alcanza, la regla habitual por categoría o la primera llegada posterior que lo cubriría.
    """

    _name = "migal.agente.tool.cobertura"
    _inherit = "migal.agente.tool.base"
    _description = "Herramienta de cobertura preliminar del Agente MIGAL"

    def evaluar(self, cotizacion, fecha_requerida=None):
        order, vigente, error = self._buscar_cotizacion(cotizacion)
        if error:
            return self._resultado(False, "error", "Cobertura preliminar", error, datos={"cotizacion": cotizacion})

        hoy = self._hoy()
        controles, bloqueos = [], []

        def add(nombre, ok, detalle):
            controles.append(self._control(nombre, ok, detalle))
            if not ok:
                bloqueos.append(detalle)

        add("Revisión vigente", order == vigente,
            "Es la revisión vigente." if order == vigente else
            "%s fue reemplazada por %s; evalúe la revisión vigente." % (order.name, vigente.name))
        add("Cotización abierta", order.state in ("draft", "sent"),
            "Cotización enviada/en borrador, aún no aceptada." if order.state in ("draft", "sent") else
            "La cotización ya no está abierta (estado «%s»). La evaluación formal se registra en la "
            "Solicitud de Orden de Venta." % dict(order._fields["state"]._description_selection(self.env)).get(order.state))
        vencida = bool(order.validity_date and order.validity_date < hoy)
        add("Vigencia", not vencida,
            "Vigente." if not vencida else "La cotización venció el %s." % format_date(self.env, order.validity_date))
        if bloqueos:
            return self._resultado(False, "bloqueado", "Cobertura preliminar no disponible",
                                   " ".join(bloqueos), controles=controles, res=order,
                                   datos={"cotizacion": order.name})

        # Fecha requerida: argumento > fecha comprometida de la cotización > hoy.
        if fecha_requerida:
            fecha = fields.Date.to_date(fecha_requerida)
            origen_fecha = "indicada por el usuario"
        elif order.commitment_date:
            fecha = fields.Datetime.context_timestamp(self, order.commitment_date).date()
            origen_fecha = "fecha comprometida de la cotización"
        else:
            fecha = hoy
            origen_fecha = "sin fecha solicitada: se evalúa para hoy"
        if fecha < hoy:
            fecha, origen_fecha = hoy, "la fecha indicada ya pasó: se evalúa para hoy"

        warehouse = order.warehouse_id or self.env["stock.warehouse"].search(
            [("company_id", "=", order.company_id.id)], limit=1)
        Regla = self.env["migal.agente.regla.cobertura"]

        # Agrupar cantidades por producto en su unidad de medida base.
        requeridos = {}
        for line in order.order_line.filtered(lambda l: not l.display_type and l.product_id):
            product = line.product_id
            qty = line.product_uom_id._compute_quantity(line.product_uom_qty, product.uom_id) \
                if line.product_uom_id else line.product_uom_qty
            requeridos.setdefault(product, 0.0)
            requeridos[product] += qty

        lineas = []
        ctx = {"warehouse_id": warehouse.id} if warehouse else {}
        hasta = self._fin_dia_utc(fecha)
        for product, qty in requeridos.items():
            uom = product.uom_id
            item = {
                "producto": product.display_name, "producto_id": product.id,
                "categoria": product.categ_id.complete_name, "cantidad": qty, "uom": uom.name,
                "fisico": 0.0, "comprometido": 0.0, "disponible": 0.0, "reposicion": 0.0, "faltante": 0.0,
                "llegadas": "", "fecha_posible": "", "estado": "", "detalle": "",
            }
            if not product.is_storable:
                item.update(estado="no_inventariable", detalle="Servicio o producto no inventariable.",
                            fecha_posible=fields.Date.to_string(hoy))
                lineas.append(item)
                continue
            fisico = max(product.with_context(**ctx).qty_available, 0.0)
            # Entregas pendientes de otras ventas confirmadas (reservadas o no) hasta la fecha evaluada.
            comprometido = max(product.with_context(to_date=hasta, **ctx).outgoing_qty, 0.0)
            libre = max(fisico - comprometido, 0.0)
            llegadas = self._llegadas(product, warehouse)
            llega = sum(q for f, q in llegadas if f <= fecha)
            faltante_stock = max(qty - libre, 0.0)
            faltante = max(qty - libre - llega, 0.0)
            item.update(fisico=fisico, comprometido=comprometido, disponible=libre, reposicion=llega,
                        faltante=faltante,
                        llegadas=", ".join("%g el %s" % (q, f.strftime("%d/%m")) for f, q in llegadas[:3]))
            rounding = uom.rounding
            base = "%g libres en tienda" % libre + (
                " (%g en stock, %g comprometidas en otras ventas)" % (fisico, comprometido) if comprometido else "")
            if float_compare(faltante_stock, 0.0, precision_rounding=rounding) <= 0:
                item.update(estado="stock", fecha_posible=fields.Date.to_string(hoy), detalle="Hay stock: %s." % base)
            elif float_compare(faltante, 0.0, precision_rounding=rounding) <= 0:
                fecha_cubre = self._fecha_cubre(llegadas, qty - libre) or fecha
                item.update(estado="reposicion", fecha_posible=fields.Date.to_string(fecha_cubre),
                            detalle="%s; con la reposición del %s alcanza (prevista, no garantizada)." % (
                                base[0].upper() + base[1:], fecha_cubre.strftime("%d/%m")))
            else:
                regla = Regla._regla_para_producto(product)
                posterior = self._fecha_cubre(llegadas, qty - libre)
                if regla:
                    pct = faltante / qty * 100 if qty else 0.0
                    dentro_limite = pct <= regla.faltante_max_pct + 1e-9 and (
                        not regla.faltante_max_qty or faltante <= regla.faltante_max_qty)
                    fecha_regla = hoy + timedelta(days=regla.plazo_dias)
                    if dentro_limite and fecha >= fecha_regla:
                        item.update(estado="regla", fecha_posible=fields.Date.to_string(fecha_regla), detalle=(
                            "%s. Faltan %g: se espera cubrir por el proceso habitual de %s hacia el %s (plazo %s días). "
                            "No es entrega garantizada." % (base[0].upper() + base[1:], faltante,
                                                            product.categ_id.name.lower(),
                                                            fecha_regla.strftime("%d/%m"), regla.plazo_dias)))
                    else:
                        motivo = ("la fecha requerida no deja el plazo habitual de %s días (sería hacia el %s)"
                                  % (regla.plazo_dias, fecha_regla.strftime("%d/%m"))
                                  if fecha < fecha_regla else "el faltante supera el límite de la regla habitual")
                        opciones = [d for d in (posterior, fecha_regla if dentro_limite else None) if d]
                        item.update(estado="faltante",
                                    fecha_posible=fields.Date.to_string(min(opciones)) if opciones else "",
                                    detalle="%s. Faltan %g: %s." % (base[0].upper() + base[1:], faltante, motivo))
                else:
                    item.update(
                        estado="faltante", fecha_posible=fields.Date.to_string(posterior) if posterior else "",
                        detalle="%s. Faltan %g sin reposición prevista hasta el %s.%s" % (
                            base[0].upper() + base[1:], faltante, fecha.strftime("%d/%m"),
                            (" Se cubriría con la llegada del %s." % posterior.strftime("%d/%m")) if posterior else ""))
            lineas.append(item)

        conteo = {k: sum(1 for l in lineas if l["estado"] == k) for k in ESTADOS}
        faltantes = [l for l in lineas if l["estado"] == "faltante"]
        sin_fecha = [l for l in faltantes if not l["fecha_posible"]]
        fechas_posibles = [fields.Date.to_date(l["fecha_posible"]) for l in lineas if l["fecha_posible"]]
        fecha_atencion = max(fechas_posibles) if fechas_posibles and not sin_fecha else None
        if not lineas:
            estado, resumen = "sin_lineas", "La cotización no tiene productos para evaluar."
        elif faltantes:
            estado = "faltantes"
            if sin_fecha:
                resumen = ("%s de %s productos no tienen cobertura prevista. Cuando el cliente esté listo para aceptar, "
                           "la Solicitud de Orden de Venta pedirá la evaluación puntual de Abastecimiento."
                           % (len(sin_fecha), len(lineas)))
            else:
                resumen = ("Para el %s faltan %s producto(s); el pedido completo podría atenderse desde el %s "
                           "(estimado)." % (fecha.strftime("%d/%m/%Y"), len(faltantes),
                                            fecha_atencion.strftime("%d/%m/%Y")))
        elif conteo["regla"] or conteo["reposicion"]:
            estado = "cubierta_condicionada"
            resumen = ("Se puede atender completo para el %s con stock, reposiciones previstas y la regla habitual "
                       "(%s producto(s) dependen de ellas). No es una entrega garantizada."
                       % (fecha.strftime("%d/%m/%Y"), conteo["regla"] + conteo["reposicion"]))
        else:
            estado = "cubierta"
            resumen = "El stock disponible en tienda cubre todos los productos de la cotización."

        cliente = order.partner_id.name
        if estado in ("cubierta", "cubierta_condicionada"):
            mensaje_cliente = ("Hola %s, según nuestro stock y las reposiciones previstas podríamos atender su pedido "
                               "completo para el %s. Se lo confirmamos al aceptar la cotización."
                               % (cliente, fecha.strftime("%d/%m/%Y")))
        elif fecha_atencion:
            mensaje_cliente = ("Hola %s, para el %s no llegamos con todo el pedido; según nuestras reposiciones "
                               "previstas podríamos atenderlo completo desde el %s (fecha estimada). Si lo necesita "
                               "antes, lo consultamos con nuestro almacén."
                               % (cliente, fecha.strftime("%d/%m/%Y"), fecha_atencion.strftime("%d/%m/%Y")))
        elif lineas:
            mensaje_cliente = ("Hola %s, la mayor parte de su pedido está disponible; algunos productos requieren "
                               "confirmar su abastecimiento y le daremos la fecha al aceptar la cotización." % cliente)
        else:
            mensaje_cliente = ""

        return self._resultado(
            True, estado, "Cobertura preliminar de %s" % order.name, resumen,
            controles=controles, reglas=["RN-015"] + (["RN-011"] if conteo["regla"] else []), res=order,
            avisos=["Consulta informativa: no reserva stock, no crea la SOV, no inicia compras y no garantiza "
                    "la entrega (RN-015)."],
            datos={
                "cotizacion": order.name, "cliente": order.partner_id.display_name,
                "almacen": warehouse.display_name if warehouse else "",
                "fecha_requerida": fields.Date.to_string(fecha), "origen_fecha": origen_fecha,
                "fecha_atencion": fields.Date.to_string(fecha_atencion) if fecha_atencion else "",
                "mensaje_cliente": mensaje_cliente, "lineas": lineas, "conteo": conteo,
            })

    # ------------------------------------------------------------------
    def _fin_dia_utc(self, fecha):
        """Fin del día local (zona del usuario) en UTC, para comparar con las fechas de los movimientos."""
        tz = pytz.timezone(self.env.user.tz or self.env.context.get("tz") or "America/Lima")
        local = tz.localize(datetime.combine(fecha, time(23, 59, 59)))
        return fields.Datetime.to_string(local.astimezone(pytz.utc).replace(tzinfo=None))

    def _llegadas(self, product, warehouse):
        """Recepciones previstas (no validadas) hacia el almacén: [(fecha_local, cantidad)] ordenadas."""
        if not warehouse:
            return []
        internas = self.env["stock.location"].sudo().search([("id", "child_of", warehouse.view_location_id.id)])
        moves = self.env["stock.move"].sudo().search([
            ("product_id", "=", product.id),
            ("state", "in", ("waiting", "confirmed", "assigned", "partially_available")),
            ("location_dest_id", "in", internas.ids),
            ("location_id", "not in", internas.ids),
        ], order="date")
        res = {}
        for m in moves:
            dia = fields.Datetime.context_timestamp(self, m.date).date()
            res[dia] = res.get(dia, 0.0) + m.product_qty
        return sorted(res.items())

    @staticmethod
    def _fecha_cubre(llegadas, necesario):
        """Primera fecha en que las llegadas acumuladas alcanzan la cantidad necesaria."""
        acumulado = 0.0
        for dia, qty in llegadas:
            acumulado += qty
            if acumulado + 1e-9 >= necesario:
                return dia
        return None
