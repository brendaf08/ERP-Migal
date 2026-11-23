def migrate(cr, version):
    if not version:
        return

    cr.execute("ALTER TABLE sale_order ALTER COLUMN migal_comprobante_externo DROP NOT NULL")

    # Quita la elección automática anterior solo de las cotizaciones sin comprobante.
    cr.execute("""
        UPDATE sale_order
           SET migal_comprobante_externo = NULL
         WHERE state IN ('draft', 'sent')
           AND migal_comprobante_externo = 'order'
    """)
