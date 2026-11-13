# -*- coding: utf-8 -*-
"""Inspección del estado actual de PRUEBAS para validación manual."""

from odoo.tests import TransactionCase


class TestInspeccionManual(TransactionCase):
    def test_inspeccion(self):
        print("\n" + "=" * 60)
        print("INSPECCIÓN DE PRUEBAS PARA VALIDACIÓN MANUAL")
        print("=" * 60)

        # Usuarios existentes
        User = self.env["res.users"]
        print("\n--- USUARIOS ---")
        for u in User.search([], order="id"):
            grupos = [g.name for g in u.group_ids]
            print(f"ID={u.id} login={u.login} name={u.name} company_id={u.company_id.id}")
            print(f"  Grupos: {grupos}")

        # Grupos 
        print("\n--- GRUPOS  ---")
        for xml_id in ["sale_order_request.group_sale_order_request_salesperson",
                       "sale_order_request.group_sale_order_request_supply",
                       "sale_order_request.group_sale_order_request_transport"]:
            try:
                g = self.env.ref(xml_id)
                print(f"{xml_id}: ID={g.id} name={g.name} usuarios={[u.login for u in g.users]}")
            except Exception as e:
                print(f"{xml_id}: NO ENCONTRADO - {e}")

        # Compañías
        print("\n--- COMPAÑÍAS ---")
        for c in self.env["res.company"].search([]):
            print(f"ID={c.id} name={c.name}")

        # Productos almacenables
        print("\n--- PRODUCTOS ALMACENABLES ---")
        for p in self.env["product.product"].search([("product_tmpl_id.type", "=", "consu"), ("product_tmpl_id.is_storable", "=", True)], limit=20):
            tmpl = p.product_tmpl_id
            print(f"ID={p.id} name={p.name} type={tmpl.type} is_storable={tmpl.is_storable} company={p.company_id.id if p.company_id else None}")
            print(f"  free_qty={p.free_qty} virtual_available={p.virtual_available} qty_available={p.qty_available}")

        # Clientes
        print("\n--- CLIENTES ---")
        for p in self.env["res.partner"].search([("customer_rank", ">", 0)], limit=10):
            print(f"ID={p.id} name={p.name} ref={p.ref} company={p.company_id.id if p.company_id else None}")

        # Cotizaciones
        print("\n--- COTIZACIONES ---")
        for o in self.env["sale.order"].search([], limit=20):
            print(f"ID={o.id} name={o.name} client_order_ref={o.client_order_ref} state={o.state} company={o.company_id.id if o.company_id else None} sale_request_applicable={o.sale_request_applicable} sale_request_subject={o.sale_request_subject}")
            for l in o.order_line:
                if l.display_type == False:
                    print(f"  Línea: product={l.product_id.name if l.product_id else None} qty={l.product_uom_qty}")

        # Solicitudes 
        print("\n--- SOLICITUDES  ---")
        for s in self.env["sale.order.request"].search([], limit=20):
            print(f"ID={s.id} name={s.name} state={s.state} sale_order={s.sale_order_id.name if s.sale_order_id else None} delivery_mode={s.delivery_mode} company={s.company_id.id if s.company_id else None}")

        # Almacenes
        print("\n--- ALMACENES ---")
        for w in self.env["stock.warehouse"].search([]):
            print(f"ID={w.id} name={w.name} code={w.code} company={w.company_id.id if w.company_id else None}")
            print(f"  lot_stock_id={w.lot_stock_id.id} ({w.lot_stock_id.name})")

        self.assertTrue(True)
