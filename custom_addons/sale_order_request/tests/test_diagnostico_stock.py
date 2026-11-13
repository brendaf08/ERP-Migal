# -*- coding: utf-8 -*-
"""Diagnóstico B3: Verificar ubicaciones y sus compañías"""

from odoo.tests import TransactionCase


class TestDiagnosticoStock(TransactionCase):
    def test_diagnostico_stock(self):
        print("\n" + "=" * 60)
        print("DIAGNÓSTICO B3: Ubicaciones y compañías")
        print("=" * 60)

        Location = self.env["stock.location"]
        locs = Location.search([("usage", "=", "internal")])
        print(f"\nUbicaciones internas: {len(locs)}")
        for l in locs:
            print(f"  ID={l.id} name={l.name} company_id={l.company_id.id if l.company_id else None} "
                  f"usage={l.usage}")

        # También mostrar TODAS las ubicaciones para ver las compañías
        all_locs = Location.search([])
        print(f"\nTodas las ubicaciones: {len(all_locs)}")
        for l in all_locs:
            print(f"  ID={l.id} name={l.name} usage={l.usage} company_id={l.company_id.id if l.company_id else None}")

        # Verificar almacenes
        Warehouse = self.env["stock.warehouse"]
        whs = Warehouse.search([])
        print(f"\nAlmacenes: {len(whs)}")
        for w in whs:
            print(f"  ID={w.id} name={w.name} company={w.company_id.id if w.company_id else None}")
            print(f"    lot_stock_id={w.lot_stock_id.id} ({w.lot_stock_id.name}) company={w.lot_stock_id.company_id.id if w.lot_stock_id.company_id else None}")
            print(f"    lot_input_id={w.lot_input_id.id} ({w.lot_input_id.name}) company={w.lot_input_id.company_id.id if w.lot_input_id.company_id else None}")
            print(f"    lot_output_id={w.lot_output_id.id} ({w.lot_output_id.name}) company={w.lot_output_id.company_id.id if w.lot_output_id.company_id else None}")

        # Compañías existentes
        Company = self.env["res.company"]
        comps = Company.search([])
        print(f"\nCompañías: {len(comps)}")
        for c in comps:
            print(f"  ID={c.id} name={c.name}")

        # Ahora probar: crear quant en ubicación de company 1
        print("\n" + "=" * 60)
        print("Probando quant en ubicación de company 1")
        print("=" * 60)

        # Buscar ubicación con company_id=1
        loc_c1 = Location.search([("usage", "=", "internal"), ("company_id", "=", 1)], limit=1)
        if loc_c1:
            print(f"Ubicación company 1: ID={loc_c1.id} name={loc_c1.name}")
        else:
            print("NO se encontró ubicación interna con company_id=1")
            # Crear una ubicación con company_id=1 bajo el almacén de company 1
            wh_c1 = Warehouse.search([("company_id", "=", 1)], limit=1)
            if wh_c1:
                print(f"Almacén company 1: ID={wh_c1.id} name={wh_c1.name}")
                # La ubicación de stock del almacén debería tener company 1
                loc_c1 = wh_c1.lot_stock_id
                print(f"  lot_stock_id: ID={loc_c1.id} company={loc_c1.company_id.id}")

        # Crear producto con company_id=1
        template = self.env["product.template"].create({
            "name": "Producto Test C1",
            "type": "consu",
            "is_storable": True,
            "sale_ok": True,
            "company_id": 1,
        })
        product = template.product_variant_ids[0]

        # Crear quant en ubicación de company 1
        if loc_c1:
            quant = self.env["stock.quant"].create({
                "product_id": product.id,
                "location_id": loc_c1.id,
                "quantity": 50.0,
            })
            print(f"Quant: company_id={quant.company_id.id}, quantity={quant.quantity}")

            self.env.invalidate_all()
            product = self.env["product.product"].browse(product.id)

            print(f"\nSin contexto de compañía: free_qty={product.free_qty}")
            env_ctx = self.env(context={"company": 1, "allowed_company_ids": [1]})
            p_ctx = env_ctx["product.product"].browse(product.id)
            print(f"Con company_ctx=1: free_qty={p_ctx.free_qty} virtual_available={p_ctx.virtual_available}")
        else:
            print("No se pudo crear quant sin ubicación de company 1")

        self.assertTrue(True)
