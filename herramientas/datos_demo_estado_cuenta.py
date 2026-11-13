"""Datos [SIM] para el estado de cuenta (Ventas + Punto de Venta) del Agente MIGAL.

    python odoo\\odoo-bin shell -c odoo.conf -d <base> < herramientas\\datos_demo_estado_cuenta.py

Cliente: «PRUEBA - Inversiones del Norte» (RUC de prueba válido). Crea, si no existen:
- Ventas: 3 órdenes facturadas en meses distintos (una pagada, una con pago parcial y nota de
  crédito, una abierta) y 1 orden confirmada pendiente de facturar.
- Un abono sin aplicar.
- Punto de Venta: caja «Caja MIGAL [SIM]» (Efectivo + Cuenta de cliente), una sesión con una venta
  pagada en efectivo y una venta «a cuenta del cliente»; al cerrar la sesión se contabiliza la deuda.
Todo lleva la marca [SIM-EC]. Es idempotente.
"""
from datetime import date, timedelta
from random import randint

from odoo import Command, fields

TAG = "[SIM-EC]"
hoy = fields.Date.context_today(env.user)
company = env.company
Move = env["account.move"]


def ruc_valido(base10):
    pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    r = 11 - sum(int(a) * b for a, b in zip(base10, pesos)) % 11
    return base10 + str({10: 0, 11: 1}.get(r, r))


RUC_DEMO = ruc_valido("2088888888")
cliente = env["res.partner"].search(["|", ("vat", "=", RUC_DEMO), ("name", "=", "PRUEBA - Inversiones del Norte")], limit=1)
if not cliente:
    # La base no trae el cliente de demostración: se crea (datos ficticios).
    cliente = env["res.partner"].create({"name": "PRUEBA - Inversiones del Norte", "phone": "+51 90000002",
                                         "street": "Calle Prueba 2", "city": "Lima",
                                         "country_id": env.ref("base.pe").id, "customer_rank": 1})
if not cliente.vat:
    vals = {"vat": ruc_valido("2088888888"), "is_company": True}
    ruc = env.ref("l10n_pe.it_RUC", raise_if_not_found=False)
    if ruc:
        vals["l10n_latam_identification_type_id"] = ruc.id
    cliente.write(vals)

vendedor = env["res.users"].search([("login", "=", "vendedor.pruebas@example.invalid")], limit=1)
journal_venta = env["account.journal"].search([("type", "=", "sale"), ("company_id", "=", company.id)], limit=1)
banco = env["account.journal"].search([("type", "=", "bank"), ("company_id", "=", company.id)], limit=1)
doc_factura = env["l10n_latam.document.type"].search([("code", "=", "01"), ("country_id.code", "=", "PE")], limit=1)
doc_nc = env["l10n_latam.document.type"].search([("code", "=", "07"), ("country_id.code", "=", "PE"),
                                                 ("name", "not ilike", "Boleta")], limit=1)
Prod = env["product.product"]


def prod(nombre, categoria=None):
    p = Prod.search([("name", "ilike", nombre), ("sale_ok", "=", True)], limit=1)
    if not p and categoria:
        p = Prod.search([("categ_id.name", "ilike", categoria), ("sale_ok", "=", True)], limit=1)
    assert p, "No encontré un producto para %s" % nombre
    return p


cemento = prod("CEMENTO", "Cemento")
fierro = prod("FIERRO", "Fierro")
ladrillo = prod("LADRILLO", "Ladrillo")
arena = prod("ARENA", "Agregado")


def venta(ref, lineas, fecha):
    so = env["sale.order"].search([("client_order_ref", "=", ref)], limit=1)
    if so:
        return so
    so = env["sale.order"].create({
        "partner_id": cliente.id, "client_order_ref": ref, "user_id": vendedor.id or env.uid,
        "date_order": fields.Datetime.to_datetime(fecha),
        "order_line": [Command.create({"product_id": p.id, "product_uom_qty": q}) for p, q in lineas],
    })
    so.action_confirm()
    so.date_order = fields.Datetime.to_datetime(fecha)
    return so


def facturar(so, fecha, vence, numero):
    if so.invoice_ids.filtered(lambda m: m.state == "posted"):
        return so.invoice_ids.filtered(lambda m: m.state == "posted")[:1]
    inv = so._create_invoices()
    vals = {"invoice_date": fecha, "ref": "%s %s" % (TAG, so.name)}
    if journal_venta.l10n_latam_use_documents:
        vals.update({"l10n_latam_document_type_id": doc_factura.id, "l10n_latam_document_number": numero})
    inv.write(vals)
    inv.invoice_payment_term_id = False
    inv.invoice_date_due = vence
    inv.action_post()
    return inv


def pagar(inv, monto, fecha, memo):
    wiz = env["account.payment.register"].with_context(active_model="account.move", active_ids=inv.ids).create({
        "amount": monto, "payment_date": fecha, "journal_id": banco.id, "communication": "%s %s" % (TAG, memo)})
    return wiz._create_payments()


m0 = date(hoy.year, hoy.month, 1)
if not Move.search([("ref", "like", TAG), ("partner_id", "=", cliente.id)], limit=1):
    # Septiembre: pagada completa
    so1 = venta("%s obra Los Olivos" % TAG, [(cemento, 40), (fierro, 20)], m0 - timedelta(days=55))
    f1 = facturar(so1, m0 - timedelta(days=55), m0 - timedelta(days=25), "F001-00000911")
    pagar(f1, f1.amount_total, m0 - timedelta(days=30), "pago %s" % f1.name)
    # Octubre: pago parcial + nota de crédito por devolución
    so2 = venta("%s obra Comas" % TAG, [(ladrillo, 500), (cemento, 30)], m0 - timedelta(days=20))
    f2 = facturar(so2, m0 - timedelta(days=20), hoy - timedelta(days=6), "F001-00000912")
    pagar(f2, round(f2.amount_total * 0.5, 2), m0 - timedelta(days=5), "abono 50%% %s" % f2.name)
    nc = Move.create({
        "move_type": "out_refund", "partner_id": cliente.id, "journal_id": journal_venta.id,
        "invoice_date": hoy - timedelta(days=9), "reversed_entry_id": f2.id, "ref": "%s devolución %s" % (TAG, f2.name),
        "invoice_origin": so2.name,
        "invoice_line_ids": [Command.create({"product_id": ladrillo.id, "name": "%s Devolución 50 ladrillos" % TAG,
                                             "quantity": 50, "price_unit": so2.order_line.filtered(
                                                 lambda l: l.product_id == ladrillo).price_unit,
                                             "tax_ids": [Command.set(ladrillo.taxes_id.ids)]})],
        **({"l10n_latam_document_type_id": doc_nc.id, "l10n_latam_document_number": "F001-00000951"}
           if journal_venta.l10n_latam_use_documents and doc_nc else {}),
    })
    nc.action_post()
    (f2 | nc).line_ids.filtered(lambda l: l.account_id.account_type == "asset_receivable" and not l.reconciled).reconcile()
    # Noviembre: abierta (vence en 15 días)
    so3 = venta("%s obra Puente Piedra" % TAG, [(fierro, 35), (arena, 10)], hoy - timedelta(days=4))
    facturar(so3, hoy - timedelta(days=4), hoy + timedelta(days=15), "F001-00000913")
    # Confirmada sin facturar (informativo)
    venta("%s obra Carabayllo (por facturar)" % TAG, [(cemento, 25)], hoy - timedelta(days=1))
    # Abono sin aplicar
    libre = env["account.payment"].create({
        "payment_type": "inbound", "partner_type": "customer", "partner_id": cliente.id, "amount": 200.0,
        "date": hoy - timedelta(days=2), "journal_id": banco.id, "memo": "%s abono a cuenta sin aplicar" % TAG})
    libre.action_post()
    print("Ventas y facturas creadas para", cliente.display_name)
else:
    print("Ventas [SIM-EC] ya existentes")

# ---------------------------------------------------------------------------
# Punto de Venta
# ---------------------------------------------------------------------------
# El Punto de Venta se opera con un usuario cajero real (el administrador), no con el superusuario técnico.
admin = env["res.users"].search([("login", "=", "administrador@migal.test")], limit=1) or env.user
env = env(user=admin.id)
PosOrder = env["pos.order"]
if not PosOrder.search([("partner_id", "=", cliente.id)], limit=1):
    caja_journal = env["account.journal"].search([("code", "=", "CAJA"), ("company_id", "=", company.id)], limit=1) or \
        env["account.journal"].create({"name": "Caja tienda %s" % TAG, "code": "CAJA", "type": "cash"})
    PM = env["pos.payment.method"]
    efectivo = PM.search([("name", "=", "Efectivo %s" % TAG)], limit=1) or \
        PM.create({"name": "Efectivo %s" % TAG, "journal_id": caja_journal.id})
    a_cuenta = PM.search([("name", "=", "Cuenta de cliente %s" % TAG)], limit=1) or \
        PM.create({"name": "Cuenta de cliente %s" % TAG, "split_transactions": True})
    config = env["pos.config"].search([("name", "=", "Caja MIGAL [SIM]")], limit=1) or \
        env["pos.config"].create({"name": "Caja MIGAL [SIM]",
                                  "payment_method_ids": [Command.set([efectivo.id, a_cuenta.id])]})
    config.open_ui()
    session = config.current_session_id
    session.set_opening_control(0, None)
    pricelist = config.pricelist_id
    fpos = config.default_fiscal_position_id

    def orden_pos(lineas, metodo):
        lines, total, base = [], 0.0, 0.0
        for p, q in lineas:
            precio = pricelist._get_product_price(p, q) if pricelist else p.lst_price
            taxes = fpos.map_tax(p.taxes_id) if fpos else p.taxes_id
            tv = taxes.compute_all(precio, session.currency_id, q) if taxes else {"total_excluded": precio * q, "total_included": precio * q}
            total += tv["total_included"]
            base += tv["total_excluded"]
            lines.append(Command.create({"id": randint(1, 10 ** 6), "product_id": p.id, "qty": q, "price_unit": precio,
                                         "price_subtotal": tv["total_excluded"], "price_subtotal_incl": tv["total_included"],
                                         "tax_ids": [Command.set(taxes.ids)], "pack_lot_ids": []}))
        uid = "sim-ec-%s" % randint(10 ** 6, 10 ** 7)
        data = {
            "amount_paid": total, "amount_return": 0, "amount_tax": total - base, "amount_total": total,
            "date_order": fields.Datetime.to_string(fields.Datetime.now()), "fiscal_position_id": fpos.id,
            "pricelist_id": pricelist.id, "name": "Order %s" % uid, "last_order_preparation_change": "{}",
            "lines": lines, "partner_id": cliente.id, "session_id": session.id, "uuid": uid, "user_id": env.uid,
            "payment_ids": [Command.create({"amount": total, "name": fields.Datetime.now(), "payment_method_id": metodo.id})],
            "to_invoice": False,
        }
        PosOrder.sync_from_ui([data])
        return total

    t1 = orden_pos([(arena, 2), (cemento, 3)], efectivo)
    t2 = orden_pos([(fierro, 6), (ladrillo, 100)], a_cuenta)
    session.post_closing_cash_details(session.cash_register_balance_end) if hasattr(session, "post_closing_cash_details") else None
    session.action_pos_session_closing_control()
    print("POS: venta en efectivo %.2f y venta a cuenta %.2f; sesión %s %s" % (t1, t2, session.name, session.state))
else:
    print("Ventas POS del cliente ya existentes")

env.cr.commit()
print("OK datos [SIM-EC] listos")
