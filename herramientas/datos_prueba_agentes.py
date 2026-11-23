"""Datos [PRUEBA] para desarrollar y probar los agentes de MIGAL.

    .\\infra\\odoo\\cargar_datos_demo.ps1        (o: odoo shell -d <base> < herramientas/datos_prueba_agentes.py)

Todos los registros llevan el prefijo «[PRUEBA]» (nombres, referencias u orígenes) y son ficticios.
Las fechas se calculan desde el día de la carga. Idempotente: si ya existe el proveedor marcador,
no vuelve a crear nada.

Qué crea y para qué agente:
- Cadena de suministro: 5 proveedores, precios y plazos por producto (product.supplierinfo), reglas de
  stock mínimo con disparo MANUAL (RN-011: sin órdenes automáticas) y órdenes de compra en todos los
  estados: solicitud por aprobar (GER, RN-012), enviada, confirmada por recibir, recepción atrasada
  (EV-024), recibida completa y recibida parcial (RN-013).
- Cuentas por pagar: facturas de proveedor que cuadran, facturada de más frente a lo recibido, con precio
  distinto al pedido (CT-007), vencida sin pagar (EV-044) y pagada (EV-046/EV-055).
- Marketing / CRM: clientes por segmento (frecuente, revendedor, ocasional, inactivo), oportunidades en
  cada etapa con canal de origen, ganadas, perdidas con motivo y actividades pendientes (RN-001).
- Cuentas por cobrar: ventas facturadas con antigüedad 0-30, 31-60, 61-90 y más de 90 días, pagos
  parciales y un límite de crédito.
"""
from datetime import timedelta

from odoo import Command, fields

TAG = "[PRUEBA]"
admin = env["res.users"].search([("login", "=", "administrador@migal.test")], limit=1) or env.user
env = env(user=admin.id, context=dict(env.context, tz=admin.tz or "America/Lima", tracking_disable=True,
                                       mail_create_nolog=True, mail_notrack=True))
hoy = fields.Date.context_today(env.user)
company = env.company
P = env["product.product"]
Partner = env["res.partner"]
resumen = []


def dia(delta):
    return hoy + timedelta(days=delta)


def momento(delta, hora=10):
    return fields.Datetime.to_datetime(dia(delta)).replace(hour=hora)


def producto(*nombres):
    for nombre in nombres:
        p = P.search([("sale_ok", "=", True), ("name", "ilike", nombre)], limit=1)
        if p:
            return p
    return P.browse()


def ruc(base):
    """RUC ficticio de 11 dígitos con dígito verificador válido (empresa, prefijo 20)."""
    cuerpo = "20%08d" % base
    suma = sum(int(d) * w for d, w in zip(cuerpo, (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)))
    verificador = 11 - suma % 11
    return cuerpo + str({10: 0, 11: 1}.get(verificador, verificador))


def contacto(nombre, **vals):
    p = Partner.search([("name", "=", nombre)], limit=1)
    return p or Partner.create(dict({"name": nombre, "country_id": env.ref("base.pe").id}, **vals))


if Partner.search_count([("name", "=", "%s Distribuidora de Aceros Lima" % TAG)]):
    print("Datos %s ya cargados: no se repiten." % TAG)
else:
    plazo30 = env.ref("account.account_payment_term_30days", raise_if_not_found=False)

    # ------------------------------------------------------------------
    # 1. Proveedores
    # ------------------------------------------------------------------
    tipo_ruc = env.ref("l10n_pe.it_RUC", raise_if_not_found=False)
    tipo_factura = env["l10n_latam.document.type"].search([("country_id.code", "=", "PE"), ("code", "=", "01")], limit=1)

    def proveedor(nombre, n):
        extra = {"vat": ruc(90000000 + n), "l10n_latam_identification_type_id": tipo_ruc.id} if tipo_ruc else {}
        return contacto("%s %s" % (TAG, nombre), is_company=True, supplier_rank=1, city="Lima", **extra,
                        phone="+51 900 100 %03d" % n, email="proveedor%s@example.invalid" % n,
                        property_supplier_payment_term_id=plazo30.id if plazo30 else False)

    aceros = proveedor("Distribuidora de Aceros Lima", 1)
    cementos = proveedor("Cementos y Agregados del Centro", 2)
    ladrillera = proveedor("Ladrillera San Martín", 3)
    mayorista = proveedor("Ferretería Mayorista Industrial", 4)
    electricos = proveedor("Importaciones Eléctricas Norte", 5)
    resumen.append("5 proveedores")

    # ------------------------------------------------------------------
    # 2. Productos con proveedor, precio de compra y plazo de entrega
    # ------------------------------------------------------------------
    catalogo = [  # (nombres a buscar, proveedor, días de entrega, segundo proveedor con días)
        (('FIERRO CORRUGADO 5/8"',), aceros, 3, (mayorista, 1)),
        (('FIERRO CORRUGADO 1/2"',), aceros, 3, (mayorista, 1)),
        (('FIERRO CORRUGADO 3/8"',), aceros, 3, None),
        (('FIERRO CORRUGADO 3/4"',), aceros, 3, None),
        (("FIERRO CORRUGADO 8 MM",), aceros, 3, None),
        (('FIERRO 1/4"',), aceros, 3, None),
        (("ALAMBRE #16",), aceros, 2, None),
        (("ALAMBRE #08",), aceros, 2, None),
        (("CLAVO DE ALBAÑIL",), aceros, 2, None),
        (("CEMENTO SOL",), cementos, 2, (mayorista, 1)),
        (("CEMENTO ANDINO ROJO",), cementos, 2, None),
        (("ARENA GRUESA",), cementos, 1, None),
        (("ARENA FINA",), cementos, 1, None),
        (("PIEDRA CHANCADA",), cementos, 1, None),
        (("LADRILLO KK18",), ladrillera, 4, None),
        (("LADRILLO PANDERETA",), ladrillera, 4, None),
        (("LADRILLO TECHO",), ladrillera, 5, None),
        (("AMOLADORA",), mayorista, 5, None),
        (("WINCHA",), mayorista, 5, None),
        (("CINTA TEMFLEX",), mayorista, 5, None),
        (("CABLE MELLIZO",), electricos, 7, None),
        (("DICROICO LED OPALUX WHITE",), electricos, 7, None),
        (("CAJA OCTOGONAL",), electricos, 7, None),
    ]
    prod = {}
    for nombres, prov, dias, segundo in catalogo:
        p = producto(*nombres)
        if not p:
            continue
        prod[nombres[0]] = p
        tmpl = p.product_tmpl_id
        costo = round((tmpl.list_price or 10.0) * 0.78, 2)
        vals = [{"partner_id": prov.id, "product_tmpl_id": tmpl.id, "price": costo, "delay": dias, "min_qty": 1}]
        if segundo:
            vals.append({"partner_id": segundo[0].id, "product_tmpl_id": tmpl.id, "price": round(costo * 1.06, 2),
                         "delay": segundo[1], "min_qty": 1})
        env["product.supplierinfo"].create(vals)
        if not tmpl.standard_price:
            tmpl.standard_price = costo
    resumen.append("%s productos con proveedor" % len(prod))

    # ------------------------------------------------------------------
    # 3. Reglas de stock mínimo (disparo manual: sugieren, no compran solas)
    # ------------------------------------------------------------------
    warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
    minimos = {'FIERRO CORRUGADO 5/8"': (40, 150), 'FIERRO CORRUGADO 1/2"': (40, 150),
               'FIERRO CORRUGADO 3/8"': (60, 200), "CEMENTO SOL": (120, 400), "LADRILLO KK18": (1500, 6000),
               "ALAMBRE #16": (50, 200), "ARENA GRUESA": (10, 40), "PIEDRA CHANCADA": (10, 40)}
    reglas = 0
    for clave, (minimo, maximo) in minimos.items():
        p = prod.get(clave)
        if p and not env["stock.warehouse.orderpoint"].search_count([("product_id", "=", p.id)]):
            env["stock.warehouse.orderpoint"].create({
                "product_id": p.id, "warehouse_id": warehouse.id, "location_id": warehouse.lot_stock_id.id,
                "product_min_qty": minimo, "product_max_qty": maximo, "trigger": "manual"})
            reglas += 1
    resumen.append("%s reglas de stock mínimo" % reglas)

    # ------------------------------------------------------------------
    # 4. Órdenes de compra en todos los estados + facturas de proveedor
    # ------------------------------------------------------------------
    def orden(prov, lineas, ref, planificada):
        po = env["purchase.order"].create({
            "partner_id": prov.id, "partner_ref": "%s %s" % (TAG, ref), "origin": "%s %s" % (TAG, ref),
            "order_line": [Command.create({"product_id": prod[k].id, "product_qty": q, "date_planned": momento(planificada)})
                           for k, q in lineas if k in prod],
        })
        return po

    def recibir(po, fraccion=1.0, hace=0):
        for picking in po.picking_ids.filtered(lambda p: p.state not in ("done", "cancel")):
            for move in picking.move_ids:
                move.quantity = round(move.product_uom_qty * fraccion, 2)
            res = picking.button_validate()
            if isinstance(res, dict) and res.get("res_model") == "stock.backorder.confirmation":
                env["stock.backorder.confirmation"].with_context(res.get("context", {})).create({}).process()
            picking.date_done = momento(-hace, 15)

    def facturar(po, numero, hace, ajuste_precio=0.0, cantidad=None, pagar=False):
        accion = po.action_create_invoice()
        factura = env["account.move"].browse(accion.get("res_id")) or po.invoice_ids[-1:]
        datos = {"ref": "%s F001-%08d" % (TAG, numero), "invoice_date": dia(-hace),
                 "invoice_payment_term_id": plazo30.id if plazo30 else False}
        if "l10n_latam_document_number" in factura._fields:
            datos.update(l10n_latam_document_number="F001-%08d" % numero,
                         l10n_latam_document_type_id=tipo_factura.id or factura.l10n_latam_document_type_id.id)
        factura.write(datos)
        for linea in factura.invoice_line_ids:
            if ajuste_precio:
                linea.price_unit = round(linea.price_unit * (1 + ajuste_precio), 2)
            if cantidad:
                linea.quantity = cantidad
        if not plazo30:
            factura.invoice_date_due = dia(-hace + 30)
        factura.action_post()
        if pagar:
            env["account.payment.register"].with_context(active_model="account.move", active_ids=factura.ids).create(
                {"payment_date": dia(-max(hace - 10, 0))})._create_payments()
        return factura

    ordenes = []
    # 4.1 Solicitud de presupuesto por aprobar (CMP preparó; falta que GER confirme)
    ordenes.append(orden(aceros, [('FIERRO CORRUGADO 5/8"', 120), ('FIERRO CORRUGADO 1/2"', 100)], "OC por aprobar", 3))
    # 4.2 Solicitud enviada al proveedor (comparación de ofertas)
    po = orden(ladrillera, [("LADRILLO KK18", 5000), ("LADRILLO PANDERETA", 2000)], "Cotización solicitada", 5)
    po.write({"state": "sent"})
    ordenes.append(po)
    # 4.3 Confirmada, por recibir en 3 días (reposición prevista para la cobertura)
    po = orden(cementos, [("CEMENTO SOL", 200), ("ARENA GRUESA", 20)], "Reposición cemento", 3)
    po.button_confirm()
    ordenes.append(po)
    # 4.4 Confirmada, recepción atrasada 2 días (incumplimiento de abastecimiento EV-024)
    po = orden(electricos, [("CABLE MELLIZO", 300), ("DICROICO LED OPALUX WHITE", 50)], "Pedido eléctrico atrasado", -2)
    po.button_confirm()
    ordenes.append(po)
    # 4.5 Recibida completa hace 10 días, factura que cuadra, vence en 20 días
    po = orden(aceros, [('FIERRO CORRUGADO 3/8"', 150), ("ALAMBRE #16", 100)], "Fierro y alambre", -10)
    po.button_confirm(); recibir(po, hace=10); facturar(po, 1201, 10)
    ordenes.append(po)
    # 4.6 Recibida parcial (80 %) y facturada completa: facturado de más frente a lo recibido
    po = orden(ladrillera, [("LADRILLO TECHO", 1000)], "Ladrillo techo parcial", -6)
    po.button_confirm(); recibir(po, fraccion=0.8, hace=6); facturar(po, 3307, 5, cantidad=1000)
    ordenes.append(po)
    # 4.7 Recibida completa, factura con precio 8 % mayor al pedido
    po = orden(mayorista, [("AMOLADORA", 6), ("WINCHA", 20)], "Herramientas", -8)
    po.button_confirm(); recibir(po, hace=8); facturar(po, 4410, 7, ajuste_precio=0.08)
    ordenes.append(po)
    # 4.8 Recibida hace 40 días, factura vencida sin pagar
    po = orden(cementos, [("PIEDRA CHANCADA", 15), ("ARENA FINA", 10)], "Agregados", -40)
    po.button_confirm(); recibir(po, hace=40); facturar(po, 1188, 38)
    ordenes.append(po)
    # 4.9 Recibida, facturada y pagada
    po = orden(aceros, [("CLAVO DE ALBAÑIL", 40), ("ALAMBRE #08", 60)], "Clavos y alambre", -25)
    po.button_confirm(); recibir(po, hace=25); facturar(po, 1150, 24, pagar=True)
    ordenes.append(po)
    resumen.append("%s órdenes de compra (5 con factura de proveedor)" % len(ordenes))

    # ------------------------------------------------------------------
    # 5. Clientes por segmento, ventas facturadas y cobranzas
    # ------------------------------------------------------------------
    def cliente(nombre, n, empresa=True, **vals):
        return contacto("%s %s" % (TAG, nombre), is_company=empresa, customer_rank=1, city="Lima",
                        phone="+51 900 200 %03d" % n, email="cliente%s@example.invalid" % n,
                        property_payment_term_id=plazo30.id if plazo30 else False, **vals)

    constructora = cliente("Constructora Los Andes", 1, credit_limit=15000)
    revendedor = cliente("Ferretería El Progreso", 2, credit_limit=8000)
    maestro = cliente("Juan Quispe (maestro de obra)", 3, empresa=False)
    inactiva = cliente("Rosa Huamán", 4, empresa=False)
    inmobiliaria = cliente("Inmobiliaria Pacífico", 5)

    def venta(partner, lineas, hace, pagado=0.0):
        so = env["sale.order"].create({
            "partner_id": partner.id, "client_order_ref": "%s venta" % TAG,
            "order_line": [Command.create({"product_id": prod[k].id, "product_uom_qty": q}) for k, q in lineas if k in prod],
        })
        so.action_confirm()
        so.date_order = momento(-hace)
        factura = so._create_invoices()
        factura.invoice_date = dia(-hace)
        factura.action_post()
        if pagado:
            env["account.payment.register"].with_context(active_model="account.move", active_ids=factura.ids).create(
                {"payment_date": dia(-max(hace - 5, 0)), "amount": round(factura.amount_total * pagado, 2)})._create_payments()
        return so

    ventas = [
        venta(constructora, [('FIERRO CORRUGADO 1/2"', 60), ("CEMENTO SOL", 80)], 12),               # 0-30, por vencer
        venta(constructora, [("LADRILLO KK18", 3000), ("ARENA GRUESA", 6)], 45, pagado=0.5),          # 31-60, pago parcial
        venta(constructora, [('FIERRO CORRUGADO 3/8"', 40)], 70, pagado=1.0),                         # pagada
        venta(revendedor, [("WINCHA", 12), ("CINTA TEMFLEX", 30), ("CAJA OCTOGONAL", 40)], 20, pagado=1.0),
        venta(revendedor, [("CABLE MELLIZO", 150), ("DICROICO LED OPALUX WHITE", 24)], 75),          # 61-90 vencida
        venta(maestro, [("CEMENTO SOL", 10), ("ALAMBRE #16", 8)], 35),                                 # 31-60 vencida
        venta(inactiva, [("CEMENTO ANDINO ROJO", 5), ("ARENA FINA", 2)], 120, pagado=1.0),           # inactiva
        venta(inmobiliaria, [("PIEDRA CHANCADA", 12)], 100),                                           # más de 90
    ]
    resumen.append("5 clientes por segmento y %s ventas facturadas con antigüedad variada" % len(ventas))

    # ------------------------------------------------------------------
    # 6. CRM: oportunidades por etapa, canal, ganadas, perdidas y actividades
    # ------------------------------------------------------------------
    Lead = env["crm.lead"]
    etapas = env["crm.stage"].search([], order="sequence, id")
    abiertas = etapas.filtered(lambda s: not s.is_won)

    def etiqueta(nombre):
        return env["crm.tag"].search([("name", "=", nombre)], limit=1) or env["crm.tag"].create({"name": nombre})

    def origen(nombre):
        return env["utm.source"].search([("name", "=", nombre)], limit=1) or env["utm.source"].create({"name": nombre})

    def motivo(nombre):
        return env["crm.lost.reason"].search([("name", "=", nombre)], limit=1) or \
            env["crm.lost.reason"].create({"name": nombre})

    seg = {k: etiqueta(k) for k in ("Constructora", "Revendedor", "Maestro de obra", "Particular", "Obra grande")}
    canal = {k: origen(k) for k in ("WhatsApp", "Referido", "Mostrador", "Llamada")}
    oportunidades = [  # (nombre, cliente, monto, etapa, segmento, canal, días de cierre, estado)
        ("Estructura edificio 5 pisos", constructora, 48000, 2, "Obra grande", "Referido", 15, "abierta"),
        ("Reposición mensual fierro", constructora, 12500, 3, "Constructora", "WhatsApp", 7, "abierta"),
        ("Pedido mensual eléctrico", revendedor, 6400, 1, "Revendedor", "Llamada", 10, "abierta"),
        ("Ampliación de vivienda", maestro, 3200, 0, "Maestro de obra", "Mostrador", 20, "abierta"),
        ("Cerco perimétrico", inmobiliaria, 22000, 2, "Obra grande", "WhatsApp", 12, "abierta"),
        ("Techado de segundo piso", inactiva, 2800, 1, "Particular", "WhatsApp", 30, "abierta"),
        ("Tarrajeo de fachada", maestro, 1500, 0, "Maestro de obra", "WhatsApp", 25, "abierta"),
        ("Losa aligerada", constructora, 18000, 3, "Constructora", "Referido", -5, "ganada"),
        ("Instalación eléctrica local", revendedor, 4200, 2, "Revendedor", "Llamada", -12, "ganada"),
        ("Condominio etapa 1", inmobiliaria, 65000, 2, "Obra grande", "Referido", -20, "perdida:Precio"),
        ("Muro de contención", maestro, 5400, 1, "Maestro de obra", "Mostrador", -15, "perdida:Sin stock a tiempo"),
        ("Baño y cocina", inactiva, 1900, 1, "Particular", "WhatsApp", -40, "perdida:Eligió a la competencia"),
    ]
    creadas = 0
    for nombre, partner, monto, etapa, segmento, fuente, cierre, estado in oportunidades:
        lead = Lead.create({
            "name": "%s %s" % (TAG, nombre), "type": "opportunity", "partner_id": partner.id,
            "expected_revenue": monto, "stage_id": abiertas[min(etapa, len(abiertas) - 1)].id if abiertas else False,
            "tag_ids": [Command.set([seg[segmento].id])], "source_id": canal[fuente].id,
            "date_deadline": dia(cierre), "user_id": admin.id,
        })
        if estado == "ganada":
            lead.action_set_won()
        elif estado.startswith("perdida"):
            lead.action_set_lost(lost_reason_id=motivo(estado.split(":", 1)[1]).id)
        elif etapa <= 1:
            lead.activity_schedule("mail.mail_activity_data_call", date_deadline=dia(2 if etapa else -1),
                                   summary="Llamar para confirmar cantidades", user_id=admin.id)
        creadas += 1
    for nombre, fuente in (("Consulta precio cemento por mayor", "WhatsApp"),
                           ("Pide lista de precios de fierro", "Llamada"),
                           ("Interesado en ladrillo para obra", "Mostrador")):
        Lead.create({"name": "%s %s" % (TAG, nombre), "type": "lead", "source_id": canal[fuente].id,
                     "contact_name": "Interesado %s" % TAG, "user_id": admin.id})
        creadas += 1
    resumen.append("%s oportunidades y contactos iniciales en CRM" % creadas)

    env.cr.commit()
    print("Datos %s cargados: %s." % (TAG, "; ".join(resumen)))
