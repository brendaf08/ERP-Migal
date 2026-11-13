import base64
import json
from datetime import date

from odoo import fields, models
from odoo.tools import float_is_zero

from ..agent.guardrails import normalize


class MigalAgenteToolEstadoCuenta(models.AbstractModel):
    """Herramienta generar_estado_cuenta.

    Fuente de verdad: apuntes contables publicados de cuentas por cobrar
    (account.move.line, account_type = asset_receivable). Así se evita duplicar
    importes: una venta (Ventas o POS) solo forma parte del saldo cuando su
    factura o su cobro a cuenta del cliente está contabilizado. Las ventas sin
    facturar y las ventas POS pagadas en caja se informan aparte.
    """

    _name = "migal.agente.tool.estado.cuenta"
    _inherit = "migal.agente.tool.base"
    _description = "Herramienta de estado de cuenta del Agente MIGAL"

    # ------------------------------------------------------------------
    def _buscar_cliente(self, texto):
        Partner = self.env["res.partner"]
        texto = (texto or "").strip()
        exacto = Partner.search(["|", "|", ("vat", "=", texto), ("ref", "=", texto),
                                 ("name", "=ilike", texto)], limit=5)
        if exacto:
            candidatos = exacto
        else:
            norm = normalize(texto)
            palabras = [w for w in norm.split() if len(w) > 1]
            pool = Partner.search([], limit=5000)
            candidatos = pool.filtered(lambda p: all(w in normalize(p.display_name) for w in palabras))
        comerciales = candidatos.mapped("commercial_partner_id")
        return comerciales

    def _origen(self, line):
        """(tipo, referencia, origen) de un apunte de cuentas por cobrar.

        origen: «Ventas» (cotización/orden facturada), «Punto de Venta» (boleta/factura de POS o venta
        «a cuenta del cliente» contabilizada al cerrar la caja), «Cobranza» (pagos) u «Otros».
        """
        move = line.move_id.sudo()
        if move.move_type in ("out_invoice", "out_refund"):
            doc = move.l10n_latam_document_type_id if "l10n_latam_document_type_id" in move._fields else False
            tipo = doc.name if doc else ("Factura" if move.move_type == "out_invoice" else "Nota de crédito")
            pos = move.pos_order_ids if "pos_order_ids" in move._fields else False
            if pos:
                return tipo, "Ticket POS %s" % ", ".join(o.pos_reference or o.name for o in pos), "Punto de Venta"
            return tipo, ("Venta %s" % move.invoice_origin) if move.invoice_origin else (move.ref or ""), "Ventas"
        pago = move.origin_payment_id if "origin_payment_id" in move._fields else False
        pago = pago or line.payment_id
        if pago:
            return "Pago / abono", pago.memo or move.ref or "", "Cobranza"
        sesiones = move.pos_session_ids if "pos_session_ids" in move._fields else False
        if sesiones:
            tickets = self.env["pos.order"].sudo().search([
                ("session_id", "in", sesiones.ids),
                ("partner_id", "child_of", line.partner_id.commercial_partner_id.id),
                ("payment_ids.payment_method_id.split_transactions", "=", True),
                ("payment_ids.payment_method_id.journal_id", "=", False),
            ])
            ref = "Ticket(s) %s" % ", ".join(o.pos_reference or o.name for o in tickets) if tickets else sesiones[:1].name
            return ("Venta POS a cuenta" if line.debit else "Devolución POS a cuenta"), ref, "Punto de Venta"
        return ("Abono / ajuste" if line.credit else "Otro movimiento"), move.ref or line.name or "", "Otros"

    @staticmethod
    def _tipo_cliente(tipo):
        """Tipo simplificado para el cliente: Factura, Boleta o Pago (las notas de crédito se identifican aparte)."""
        if "Boleta" in tipo or tipo.startswith("Venta POS"):
            return "Boleta"
        if "Factura" in tipo:
            return "Factura"
        if tipo.startswith("Pago"):
            return "Pago"
        if "crédito" in tipo or tipo.startswith("Devolución"):
            return "Nota de crédito"
        return "Ajuste"

    @staticmethod
    def _fmt(fecha):
        return fecha.strftime("%d/%m/%Y") if fecha else ""

    def _plazo(self, line, hoy):
        """Situación de un documento impago frente al plazo acordado (condición de pago o fecha de vencimiento).

        Sin plazo acordado (vence el mismo día de emisión y sin condición de pago) se informa solo su antigüedad.
        """
        move = line.move_id
        emision = move.invoice_date or line.date
        vence = line.date_maturity or move.invoice_date_due
        termino = move.invoice_payment_term_id
        con_plazo = bool(termino) or bool(vence and emision and vence > emision)
        if con_plazo:
            dias = (hoy - vence).days
            plazo = termino.name if termino else "%s días (hasta el %s)" % ((vence - emision).days, self._fmt(vence))
            if dias < 0:
                estado = "Dentro del plazo · vence en %s día(s)" % -dias
            elif dias == 0:
                estado = "Vence hoy"
            else:
                estado = "Plazo excedido hace %s día(s)" % dias
            return {"con_plazo": True, "plazo": plazo, "estado_plazo": estado, "dias": dias,
                    "excedido": dias > 0, "vencimiento_txt": self._fmt(vence)}
        dias = (hoy - emision).days
        return {"con_plazo": False, "plazo": "Sin plazo acordado", "dias": dias, "excedido": False,
                "estado_plazo": "Pendiente desde hace %s día(s)" % dias if dias > 0 else "Emitida hoy",
                "vencimiento_txt": ""}

    def _metodos_pago(self):
        """Medios de pago configurados en Ajustes → Agente MIGAL (solo los que tienen datos)."""
        icp = self.env["ir.config_parameter"].sudo()
        g = lambda k: (icp.get_param("migal_agente.%s" % k) or "").strip()
        metodos = []
        if g("pago_yape"):
            metodos.append({"metodo": "Yape", "lineas": ["Celular: %s" % g("pago_yape")]})
        for banco, clave in (("BCP", "bcp"), ("BBVA", "bbva")):
            lineas = []
            if g("pago_%s_cuenta" % clave):
                lineas.append("Cuenta: %s" % g("pago_%s_cuenta" % clave))
            if g("pago_%s_cci" % clave):
                lineas.append("CCI: %s" % g("pago_%s_cci" % clave))
            if lineas:
                metodos.append({"metodo": "Transferencia %s" % banco, "lineas": lineas})
        return metodos, g("pago_titular")

    @staticmethod
    def _antiguedad(dias):
        if dias <= 0:
            return "Por vencer"
        if dias <= 30:
            return "1-30 días"
        if dias <= 60:
            return "31-60 días"
        if dias <= 90:
            return "61-90 días"
        return "Más de 90 días"

    # ------------------------------------------------------------------
    def generar(self, cliente, fecha_desde=None, fecha_hasta=None):
        partners = self._buscar_cliente(cliente)
        if not partners:
            return self._resultado(False, "error", "Estado de cuenta",
                                   "No encontré un cliente que coincida con «%s»." % cliente,
                                   datos={"cliente": cliente})
        if len(partners) > 1:
            opciones = ", ".join(p.display_name for p in partners[:5])
            return self._resultado(False, "ambiguo", "Estado de cuenta",
                                   "Hay varios clientes que coinciden con «%s»: %s. Indique el nombre completo o "
                                   "el RUC/DNI." % (cliente, opciones), datos={"cliente": cliente,
                                                                               "candidatos": partners[:5].mapped("display_name")})
        partner = partners
        hoy = self._hoy()
        hasta = fields.Date.to_date(fecha_hasta) if fecha_hasta else hoy
        desde = fields.Date.to_date(fecha_desde) if fecha_desde else date(hasta.year, hasta.month, 1)
        if desde > hasta:
            desde, hasta = hasta, desde

        company = self.env.company
        currency = company.currency_id
        base = [
            ("partner_id", "child_of", partner.id),
            ("account_id.account_type", "=", "asset_receivable"),
            ("parent_state", "=", "posted"),
            ("company_id", "=", company.id),
        ]
        AML = self.env["account.move.line"]
        anteriores = AML.search(base + [("date", "<", desde)])
        saldo_anterior = sum(anteriores.mapped("balance"))

        movimientos = []
        saldo = saldo_anterior
        for line in AML.search(base + [("date", ">=", desde), ("date", "<=", hasta)], order="date, move_name, id"):
            saldo += line.balance
            tipo, referencia, origen = self._origen(line)
            movimientos.append({
                "fecha": fields.Date.to_string(line.date),
                "fecha_txt": self._fmt(line.date),
                "documento": line.move_id.name,
                "referencia": referencia,
                "tipo": tipo,
                "tipo_cliente": self._tipo_cliente(tipo),
                "importe": line.balance,
                "origen": origen,
                "cargo": line.debit,
                "abono": line.credit,
                "saldo": saldo,
            })
        saldo_periodo = saldo

        # Saldo pendiente por operación (a la fecha de consulta).
        documentos = []
        abiertas = AML.search(base + [("reconciled", "=", False), ("amount_residual", ">", 0)], order="date_maturity, date")
        for line in abiertas:
            move = line.move_id
            vence = line.date_maturity or move.invoice_date_due or line.date
            tipo, referencia, origen = self._origen(line)
            dias = (hoy - vence).days if vence else 0
            documentos.append(dict(self._plazo(line, hoy), **{
                "documento": move.name,
                "tipo": tipo,
                "tipo_cliente": self._tipo_cliente(tipo),
                "fecha_txt": self._fmt(move.invoice_date or line.date),
                "origen": origen,
                "operacion": referencia,
                "antiguedad": self._antiguedad(dias),
                "fecha": fields.Date.to_string(move.invoice_date or line.date),
                "vencimiento": fields.Date.to_string(vence) if vence else "",
                "dias_vencido": max(dias, 0),
                "importe": line.balance,
                "pendiente": line.amount_residual,
            }))
        # Pagos/abonos registrados pendientes de aplicación o conciliación.
        sin_aplicar = []
        for line in AML.search(base + [("reconciled", "=", False), ("amount_residual", "<", 0)], order="date"):
            sin_aplicar.append({
                "documento": line.move_id.name,
                "fecha": fields.Date.to_string(line.date),
                "tipo": self._origen(line)[0],
                "referencia": self._origen(line)[1],
                "importe": -line.balance,
                "por_aplicar": -line.amount_residual,
            })
        total_documentos = sum(d["pendiente"] for d in documentos)
        total_sin_aplicar = sum(p["por_aplicar"] for p in sin_aplicar)
        total_pendiente = total_documentos - total_sin_aplicar
        # Vencido = plazo acordado excedido. Lo que no tiene plazo acordado se informa por antigüedad.
        vencido = sum(d["pendiente"] for d in documentos if d["excedido"])
        tramos = ["Por vencer", "1-30 días", "31-60 días", "61-90 días", "Más de 90 días"]
        antiguedad = [{"tramo": t, "importe": sum(d["pendiente"] for d in documentos if d["antiguedad"] == t)}
                      for t in tramos]
        por_origen = {}
        for d in documentos:
            por_origen[d["origen"]] = por_origen.get(d["origen"], 0.0) + d["pendiente"]

        # Información NO contable (no suma al saldo): evita duplicar ventas ya facturadas.
        # Se lee con sudo solo para totales del cliente consultado: el permiso de la herramienta
        # (FCO/GER) ya se verificó y FCO no necesita acceso operativo a Ventas o POS.
        informativo = []
        orders = self.env["sale.order"].sudo().search([
            ("partner_id", "child_of", partner.id), ("state", "=", "sale"),
            ("company_id", "=", company.id)])
        for so in orders:
            if not float_is_zero(so.amount_to_invoice, precision_rounding=so.currency_id.rounding):
                informativo.append({
                    "origen": "Ventas", "documento": so.name,
                    "fecha": fields.Date.to_string(fields.Datetime.context_timestamp(self, so.date_order).date()),
                    "importe": so.amount_to_invoice,
                    "nota": "Venta confirmada pendiente de facturar: no forma parte del saldo contable.",
                })
        pos_pagadas = self.env["pos.order"].sudo().search([
            ("partner_id", "child_of", partner.id), ("state", "in", ("paid", "done")),
            ("account_move", "=", False), ("company_id", "=", company.id),
            ("date_order", ">=", fields.Datetime.to_string(fields.Datetime.to_datetime(desde))),
            ("date_order", "<=", fields.Datetime.to_string(fields.Datetime.to_datetime(hasta).replace(hour=23, minute=59, second=59))),
        ]).filtered(
            # Solo lo cobrado en caja: los tickets pagados «a cuenta del cliente» (método sin diario) ya están en la
            # contabilidad del cliente y contarlos aquí duplicaría el importe.
            lambda o: not o.payment_ids.filtered(lambda p: p.payment_method_id.split_transactions
                                                 and not p.payment_method_id.journal_id))
        if pos_pagadas:
            informativo.append({
                "origen": "Punto de Venta", "documento": "%s ticket(s)" % len(pos_pagadas),
                "fecha": "", "importe": sum(pos_pagadas.mapped("amount_total")),
                "nota": "Ventas de mostrador pagadas en caja durante el período: no generan deuda.",
            })

        avisos = []
        if not movimientos and not documentos and not sin_aplicar:
            avisos.append("No hay facturas, notas ni pagos contabilizados para este cliente en la base.")
        if sin_aplicar:
            avisos.append("Hay %s pago(s) o abono(s) pendientes de aplicación/conciliación por %s %.2f: FCO debe "
                          "aplicarlos a las facturas correspondientes." % (len(sin_aplicar), currency.symbol, total_sin_aplicar))

        metodos_pago, pago_titular = self._metodos_pago()
        mensaje = ("Estado de cuenta de %s del %s al %s: saldo anterior %s %.2f, saldo al cierre del período %s %.2f. "
                   "Total pendiente a la fecha: %s %.2f (vencido %s %.2f)." % (
                       partner.display_name, desde.strftime("%d/%m/%Y"), hasta.strftime("%d/%m/%Y"),
                       currency.symbol, saldo_anterior, currency.symbol, saldo_periodo,
                       currency.symbol, total_pendiente, currency.symbol, vencido))
        return self._resultado(
            True, "generado", "Estado de cuenta - %s" % partner.display_name, mensaje,
            res=partner, reglas=["CT-004", "RN-014"], avisos=avisos,
            datos={
                "cliente": partner.display_name, "cliente_id": partner.id, "documento_identidad": partner.vat or "",
                "moneda": currency.name, "simbolo": currency.symbol,
                "fecha_desde": fields.Date.to_string(desde), "fecha_hasta": fields.Date.to_string(hasta),
                "fecha_consulta": fields.Date.to_string(hoy),
                "fecha_desde_txt": self._fmt(desde), "fecha_hasta_txt": self._fmt(hasta), "fecha_consulta_txt": self._fmt(hoy),
                "saldo_anterior": saldo_anterior, "movimientos": movimientos, "saldo_periodo": saldo_periodo,
                "documentos_pendientes": documentos, "pagos_sin_aplicar": sin_aplicar,
                "total_documentos": total_documentos, "total_sin_aplicar": total_sin_aplicar,
                "total_pendiente": total_pendiente, "total_vencido": vencido,
                "informativo": informativo, "antiguedad": antiguedad, "pendiente_por_origen": por_origen,
                "telefono": partner.phone or "",
                "metodos_pago": metodos_pago, "pago_titular": pago_titular,
            })

    # ------------------------------------------------------------------
    def compartir(self, cliente, fecha_desde=None, fecha_hasta=None):
        """Congela el estado de cuenta (24 h) y prepara QR + mensaje de WhatsApp para el cliente."""
        from .tool_whatsapp import E164_RE, normalizar_telefono

        res = self.generar(cliente, fecha_desde, fecha_hasta)
        if not res.get("ok"):
            return res
        d = res["datos"]
        partner = self.env["res.partner"].browse(d["cliente_id"])
        pub = self.env["migal.agente.estado.cuenta.publicacion"].sudo().create({
            "partner_id": partner.id, "user_id": self.env.uid,
            "fecha_desde": d["fecha_desde"], "fecha_hasta": d["fecha_hasta"],
            "total_pendiente": d["total_pendiente"],
            "datos_json": json.dumps(d, ensure_ascii=False, default=str),
        })
        wa = self.env["migal.agente.tool.whatsapp"]
        url = "%s/migal/estado-cuenta/%s" % (wa._base_publica(partner), pub.token)
        png = self.env["ir.actions.report"].barcode("QR", url, width=320, height=320, quiet=1)
        controles, avisos, local = wa._alcance(url)
        controles.insert(0, self._control(
            "Copia congelada del estado de cuenta", True,
            "El cliente verá exactamente lo revisado, con fecha de consulta %s." % d["fecha_consulta"]))
        expira = fields.Datetime.context_timestamp(self, pub.expira).strftime("%d/%m/%Y %H:%M")
        controles.append(self._control("Enlace con caducidad", True,
                                       "Solo lectura; deja de abrir el %s (o antes si se revoca)." % expira))
        telefono = normalizar_telefono(partner.phone)
        tel_ok = bool(E164_RE.match(telefono))
        controles.append(self._control(
            "Teléfono internacional", tel_ok,
            "Número %s." % telefono if tel_ok else
            "El cliente no tiene teléfono en formato internacional: puede usar el QR, pero no WhatsApp."))
        s = d["simbolo"]
        money = lambda v: "%s %s" % (s, "{:,.2f}".format(v or 0.0))
        partes = ["Hola %s, le saluda %s de Ferre & Inversiones MIGAL." % (partner.name, self.env.user.name),
                  "Le comparto su estado de cuenta al %s: total pendiente %s" % (
                      fields.Date.to_date(d["fecha_consulta"]).strftime("%d/%m/%Y"), money(d["total_pendiente"]))]
        partes[-1] += (", de los cuales %s tienen el plazo de pago excedido." % money(d["total_vencido"])) if d["total_vencido"] else "."
        if d["pagos_sin_aplicar"]:
            partes.append("Tenemos registrado un abono de %s pendiente de aplicar, ya considerado en el total."
                          % money(d["total_sin_aplicar"]))
        if d.get("metodos_pago"):
            partes.append("Puede abonar por %s; los datos están al final del PDF." % " o ".join(
                m["metodo"] for m in d["metodos_pago"]))
        partes.append("Le adjunto el PDF con el detalle. Quedamos atentos a cualquier consulta.")
        mensaje = " ".join(partes)
        return self._resultado(
            True, "compartible", "Estado de cuenta listo para compartir",
            "Copia de solo lectura creada (vence el %s). Muestre el QR o envíelo por WhatsApp adjuntando el PDF." % expira,
            controles=controles, avisos=avisos, res=partner, reglas=["CT-004"],
            datos={
                "cliente": partner.display_name, "publicacion_id": pub.id, "url": url, "accesible": not local,
                "qr_png_base64": base64.b64encode(png).decode(), "expira": expira,
                "telefono": telefono if tel_ok else "", "mensaje": mensaje,
                "total_pendiente": d["total_pendiente"], "simbolo": s,
                "pdf_url": "/report/pdf/migal_agente.report_estado_cuenta_publicado/%s" % pub.id,
            })
