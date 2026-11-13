"""Datos [SIM-COB] para la cobertura preliminar del Agente MIGAL.

    python odoo\\odoo-bin shell -c odoo.conf -d <base> < herramientas\\datos_demo_cobertura.py

Crea (idempotente):
- Ajustes de inventario para que haya stock real en tienda de cemento, fierro, ladrillo,
  piedra chancada y una conexión sanitaria (las ventas confirmadas existentes quedan como
  «comprometido»).
- Recepciones previstas (confirmadas, no validadas) de cemento (+2 días), fierro (+4 días)
  y la conexión sanitaria (+6 días).
- La cotización «[SIM-COB] Obra Pinedo» para «PRUEBA - Servicios Generales Lima», con fecha
  comprometida en 3 días y un caso de cada tipo: stock, reposición, regla habitual y faltante
  que se cubriría en una fecha posterior.
"""
from datetime import timedelta

from odoo import Command, fields

TAG = "[SIM-COB]"
admin = env["res.users"].search([("login", "=", "administrador@migal.test")], limit=1) or env.user
env = env(user=admin.id, context=dict(env.context, tz=admin.tz or "America/Lima"))
hoy = fields.Date.context_today(env.user)
company = env.company
warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
stock = warehouse.lot_stock_id
proveedores = env.ref("stock.stock_location_suppliers")
P = env["product.product"]


def producto(*nombres, categoria=None, excluir=()):
    base = [("is_storable", "=", True), ("sale_ok", "=", True), ("id", "not in", [p.id for p in excluir])]
    for nombre in nombres:
        p = P.search(base + [("name", "ilike", nombre)], limit=1)
        if p:
            return p
    if categoria:
        p = P.search(base + [("categ_id.name", "ilike", categoria)], limit=1)
        if p:
            return p
    raise ValueError("No encontré ninguno de %s (categoría %s)" % (nombres, categoria))


cemento = producto("CEMENTO ANDINO ROJO", "CEMENTO", categoria="Cemento")
fierro = producto("FIERRO CORRUGADO", "MALLA CUADRADA SPRATT", "ALAMBRE #16", categoria="Fierro")
ladrillo = producto("LADRILLO KK18", "LADRILLO", categoria="Ladrillo")
piedra = producto("PIEDRA CHANCADA", categoria="Agregado")
yee = producto("YEE SANITARIA", "CODO", "TEE", categoria="Tuber")
arena = producto("ARENA FINA", "ARENA", categoria="Agregado", excluir=(piedra,))

cot = env["sale.order"].search([("client_order_ref", "=", "%s Obra Pinedo" % TAG)], limit=1)
if not cot:
    # 1. Stock en tienda (ajuste de inventario con movimiento trazable)
    objetivo = {cemento: 150, fierro: 40, ladrillo: 1200, piedra: 30, yee: 15}
    Quant = env["stock.quant"].with_context(inventory_mode=True)
    for prod, cantidad in objetivo.items():
        quant = Quant.search([("product_id", "=", prod.id), ("location_id", "=", stock.id)], limit=1)
        if not quant:
            quant = Quant.create({"product_id": prod.id, "location_id": stock.id})
        quant.inventory_quantity = cantidad
        quant.action_apply_inventory()

    # 2. Reposiciones previstas
    proveedor = env["res.partner"].search([("name", "=", "%s Proveedor de materiales" % TAG)], limit=1) or \
        env["res.partner"].create({"name": "%s Proveedor de materiales" % TAG, "supplier_rank": 1})
    for prod, cantidad, dias in ((cemento, 100, 2), (fierro, 50, 4), (yee, 40, 6)):
        fecha = fields.Datetime.to_datetime(hoy + timedelta(days=dias)).replace(hour=15)
        picking = env["stock.picking"].create({
            "picking_type_id": warehouse.in_type_id.id, "partner_id": proveedor.id,
            "origin": "%s reposición %s" % (TAG, prod.name[:30]), "scheduled_date": fecha,
            "location_id": proveedores.id, "location_dest_id": stock.id,
            "move_ids": [Command.create({
                "product_id": prod.id, "product_uom_qty": cantidad, "product_uom": prod.uom_id.id,
                "location_id": proveedores.id, "location_dest_id": stock.id, "date": fecha})],
        })
        picking.action_confirm()

    # 3. Cotización con todos los casos
    cliente = env["res.partner"].search([("name", "=", "PRUEBA - Servicios Generales Lima")], limit=1) or \
        env["res.partner"].create({"name": "PRUEBA - Servicios Generales Lima", "phone": "+51 90000003",
                                   "street": "Calle Prueba 3", "city": "Lima",
                                   "country_id": env.ref("base.pe").id, "customer_rank": 1})
    vendedor = env["res.users"].search([("login", "=", "vendedor.pruebas@example.invalid")], limit=1)
    cot = env["sale.order"].create({
        "partner_id": cliente.id, "client_order_ref": "%s Obra Pinedo" % TAG,
        "user_id": vendedor.id or env.uid, "warehouse_id": warehouse.id,
        "validity_date": hoy + timedelta(days=30),
        "commitment_date": fields.Datetime.to_datetime(hoy + timedelta(days=3)).replace(hour=15),
        "order_line": [Command.create({"product_id": p.id, "product_uom_qty": q}) for p, q in (
            (arena, 5), (cemento, 120), (fierro, 60), (ladrillo, 1000), (piedra, 15), (yee, 25))],
    })
    env.cr.commit()
    print("Cotización de cobertura creada:", cot.name)
else:
    print("Ya existe la cotización de cobertura:", cot.name)
print("OK datos [SIM-COB] listos")
