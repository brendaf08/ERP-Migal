"""Datos de demostración [SIM] para el Agente MIGAL (PC3).

Se ejecuta con el shell de Odoo sobre la base indicada:

    python odoo\\odoo-bin shell -c odoo.conf -d <base> < herramientas\\datos_demo_agente.py

Crea (solo si no existen; es idempotente por referencias [SIM]):
1. Cotización de cobertura para «PRUEBA - Proyectos Urbanos» con cuatro casos:
   stock suficiente, reposición prevista, regla habitual (cemento) y faltante.
2. Recepción prevista (no validada) que alimenta la reposición.
3. Facturas, pagos aplicados y un pago sin aplicar para «PRUEBA - Constructora Andina»
   (estado de cuenta). Todos con referencia [SIM].

No toca cotizaciones ni ventas existentes.
"""
from datetime import date, timedelta

from odoo import Command, fields

TAG = "[SIM-PC3]"
hoy = fields.Date.context_today(env.user)
company = env.company


def producto(nombre_like=None, categoria=None, sin_stock=True):
    P = env["product.product"]
    dom = [("is_storable", "=", True), ("sale_ok", "=", True)]
    if nombre_like:
        dom.append(("name", "ilike", nombre_like))
    if categoria:
        dom.append(("categ_id.name", "=", categoria))
    for p in P.search(dom, order="id"):
        if not sin_stock or p.qty_available <= 0:
            return p
    return P.browse()


# ---------------------------------------------------------------------------
# 1-2. Cobertura preliminar
# ---------------------------------------------------------------------------
cliente_cob = env["res.partner"].search([("name", "=", "PRUEBA - Proyectos Urbanos")], limit=1)
cot = env["sale.order"].search([("client_order_ref", "=", TAG + " cobertura")], limit=1)
if cliente_cob and not cot:
    arena = producto("ARENA FINA", sin_stock=False)
    cemento = producto(categoria="Cemento y aglomerantes")
    tubo = producto(categoria="Tuberías y conexiones")
    pintura = producto(categoria="Pinturas")
    warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)

    # Recepción prevista del tubo (12 und. dentro de 2 días), confirmada pero no validada.
    proveedor = env["res.partner"].search([("name", "=", TAG + " Proveedor demo")], limit=1) or \
        env["res.partner"].create({"name": TAG + " Proveedor demo", "supplier_rank": 1})
    fecha_rec = fields.Datetime.to_datetime(hoy + timedelta(days=2))
    picking = env["stock.picking"].create({
        "picking_type_id": warehouse.in_type_id.id,
        "partner_id": proveedor.id,
        "origin": TAG + " reposición prevista",
        "scheduled_date": fecha_rec,
        "location_id": env.ref("stock.stock_location_suppliers").id,
        "location_dest_id": warehouse.lot_stock_id.id,
        "move_ids": [Command.create({
            "product_id": tubo.id, "product_uom_qty": 12, "product_uom": tubo.uom_id.id,
            "location_id": env.ref("stock.stock_location_suppliers").id,
            "location_dest_id": warehouse.lot_stock_id.id, "date": fecha_rec,
        })],
    })
    picking.action_confirm()

    cot = env["sale.order"].create({
        "partner_id": cliente_cob.id,
        "client_order_ref": TAG + " cobertura",
        "validity_date": hoy + timedelta(days=30),
        "commitment_date": fields.Datetime.to_datetime(hoy + timedelta(days=5)),
        "warehouse_id": warehouse.id,
        "order_line": [
            Command.create({"product_id": arena.id, "product_uom_qty": 20}),
            Command.create({"product_id": tubo.id, "product_uom_qty": 10}),
            Command.create({"product_id": cemento.id, "product_uom_qty": 50}),
            Command.create({"product_id": pintura.id, "product_uom_qty": 5}),
        ],
    })
    print("Cotización de cobertura:", cot.name, "| recepción prevista:", picking.name)
else:
    print("Cotización de cobertura ya existente:", cot.name if cot else "(cliente no encontrado)")

# La cotización de demo pertenece al vendedor de pruebas (regla «solo mis documentos» de VEN).
vendedor = env["res.users"].search([("login", "=", "vendedor.pruebas@example.invalid")], limit=1)
if cot and vendedor and cot.user_id != vendedor:
    cot.user_id = vendedor

# ---------------------------------------------------------------------------
# 3. Estado de cuenta
# ---------------------------------------------------------------------------
cliente_ec = env["res.partner"].search([("name", "=", "PRUEBA - Constructora Andina")], limit=1)
Move = env["account.move"]
ya = Move.search([("ref", "like", TAG), ("partner_id", "=", cliente_ec.id)], limit=1)
if cliente_ec and not ya:
    if not cliente_ec.vat:
        ruc = env.ref("l10n_pe.it_RUC", raise_if_not_found=False)
        vals = {"vat": "20999999990", "is_company": True}
        if ruc:
            vals["l10n_latam_identification_type_id"] = ruc.id
        cliente_ec.write(vals)
    journal = env["account.journal"].search([("type", "=", "sale"), ("company_id", "=", company.id)], limit=1)
    banco = env["account.journal"].search([("type", "=", "bank"), ("company_id", "=", company.id)], limit=1)
    tax = env["account.tax"].search([("type_tax_use", "=", "sale"), ("amount", "=", 18),
                                     ("company_id", "=", company.id)], limit=1)
    doc_factura = env["l10n_latam.document.type"].search([("code", "=", "01"), ("country_id.code", "=", "PE")], limit=1)
    prod = producto("ARENA FINA", sin_stock=False)

    def factura(fecha, vence, base, origen, n):
        vals = {
            "move_type": "out_invoice", "partner_id": cliente_ec.id, "journal_id": journal.id,
            "invoice_date": fecha, "invoice_date_due": vence, "ref": "%s factura %s" % (TAG, n),
            "invoice_origin": origen,
            "invoice_line_ids": [Command.create({
                "product_id": prod.id, "name": "%s Materiales de construcción" % TAG, "quantity": 1,
                "price_unit": base, "tax_ids": [Command.set(tax.ids)]})],
        }
        if journal.l10n_latam_use_documents and doc_factura:
            vals["l10n_latam_document_type_id"] = doc_factura.id
            vals["l10n_latam_document_number"] = "F001-%08d" % (900 + n)
        inv = Move.create(vals)
        inv.invoice_payment_term_id = False
        inv.invoice_date_due = vence
        inv.action_post()
        return inv

    def pagar(inv, monto, fecha):
        wiz = env["account.payment.register"].with_context(active_model="account.move", active_ids=inv.ids).create({
            "amount": monto, "payment_date": fecha, "journal_id": banco.id,
            "communication": "%s pago %s" % (TAG, inv.name)})
        return wiz._create_payments()

    a = date(hoy.year, hoy.month, 1)
    f1 = factura(a - timedelta(days=47), a - timedelta(days=17), 1000.0, "S-OBRA-01", 1)   # 1 180,00
    pagar(f1, 680.0, a - timedelta(days=32))
    f2 = factura(a - timedelta(days=22), hoy - timedelta(days=4), 2000.0, "S-OBRA-02", 2)  # 2 360,00
    pagar(f1, 500.0, a - timedelta(days=12))
    pagar(f2, 1000.0, hoy - timedelta(days=11))
    f3 = factura(hoy - timedelta(days=8), hoy + timedelta(days=22), 500.0, "S-OBRA-03", 3)  # 590,00
    libre = env["account.payment"].create({
        "payment_type": "inbound", "partner_type": "customer", "partner_id": cliente_ec.id,
        "amount": 300.0, "date": hoy - timedelta(days=3), "journal_id": banco.id,
        "memo": "%s abono sin aplicar" % TAG,
    })
    libre.action_post()
    print("Facturas:", (f1 | f2 | f3).mapped("name"), "| pago sin aplicar:", libre.name, libre.state)
else:
    print("Datos de estado de cuenta ya existentes" if ya else "Cliente PRUEBA - Constructora Andina no encontrado")

env.cr.commit()
print("OK datos [SIM] listos")
