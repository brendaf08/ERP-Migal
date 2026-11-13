# -*- coding: utf-8 -*-
"""Diagnóstico de datos existentes en PRUEBAS para B6."""

from odoo.tests import TransactionCase


class TestDiagnosticoB6(TransactionCase):
    def test_datos_existentes(self):
        print("\n" + "=" * 60)
        print("DIAGNÓSTICO B6: Datos existentes en PRUEBAS")
        print("=" * 60)

        # Usuarios B4
        User = self.env["res.users"]
        for login in ["user_b4_sales_c1", "user_b4_abast_c1", "user_b4_trans_c1",
                      "user_b4_plain_c1", "user_b4_sales_c2"]:
            u = User.search([("login", "=", login)], limit=1)
            if u:
                print(f"Usuario: {u.login} | company_id={u.company_id.id} | company_ids={[c.id for c in u.company_ids]}")
                grupos = [g.name for g in u.group_ids]
                print(f"  Grupos: {grupos}")
            else:
                print(f"Usuario NO ENCONTRADO: {login}")

        # Productos B4
        Product = self.env["product.product"]
        for nombre in ["Producto B4 Recojo", "Producto B4 Despacho", "Producto B4 Insuficiente"]:
            p = Product.search([("name", "=", nombre)], limit=1)
            if p:
                tmpl = p.product_tmpl_id
                print(f"Producto: {p.name} | type={tmpl.type} | is_storable={tmpl.is_storable} | company={p.company_id.id if p.company_id else None}")
                print(f"  free_qty={p.free_qty} virtual_available={p.virtual_available} qty_available={p.qty_available}")
            else:
                print(f"Producto NO ENCONTRADO: {nombre}")

        # Compañías
        Company = self.env["res.company"]
        for c in Company.search([]):
            print(f"Compañía: ID={c.id} name={c.name}")

        # Almacenes
        Warehouse = self.env["stock.warehouse"]
        for w in Warehouse.search([]):
            print(f"Almacén: ID={w.id} name={w.name} company={w.company_id.id if w.company_id else None}")
            print(f"  lot_stock_id={w.lot_stock_id.id} ({w.lot_stock_id.name})")

        # Ubicaciones internas
        Location = self.env["stock.location"]
        for l in Location.search([("usage", "=", "internal")]):
            print(f"Ubicación: ID={l.id} name={l.name} company={l.company_id.id if l.company_id else None}")

        # Grupos 
        Group = self.env["res.groups"]
        for xml_id in ["sale_order_request.group_sale_order_request_salesperson",
                       "sale_order_request.group_sale_order_request_supply",
                       "sale_order_request.group_sale_order_request_transport"]:
            try:
                g = self.env.ref(xml_id)
                print(f"Grupo: {xml_id} | ID={g.id} | name={g.name}")
            except Exception as e:
                print(f"Grupo NO ENCONTRADO: {xml_id} | {e}")

        self.assertTrue(True)
