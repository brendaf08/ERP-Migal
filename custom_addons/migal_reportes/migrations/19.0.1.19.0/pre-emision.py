def migrate(cr, version):
    if not version:
        return

    # Los estados anteriores no identificaban un tipo pendiente de emisión.
    cr.execute("""
        UPDATE sale_order
           SET migal_comprobante_externo = 'order'
         WHERE migal_comprobante_externo IN ('pending', 'none', 'not_required')
    """)
