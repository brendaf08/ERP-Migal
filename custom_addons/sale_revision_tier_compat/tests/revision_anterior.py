# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Comprobación del estado de la versión anterior tras crear una revisión.

OCA (base_revision/sale_order_revision) cancela y archiva la versión anterior en
cuanto se crea otra. Si está instalado migal_agente, la versión anterior sigue
abierta hasta que vence su vigencia y apunta a la nueva (regla comercial MIGAL);
en ambos casos no se puede confirmar. Este módulo no depende de migal_agente: la
comprobación se adapta a la regla que esté instalada.
"""


def mantiene_versiones_vigentes(env):
    return hasattr(type(env["sale.order"]), "_migal_sigue_vigente")


def assert_version_anterior(test, anterior, nueva=None):
    anterior.invalidate_recordset()
    if mantiene_versiones_vigentes(anterior.env):
        test.assertIn(anterior.state, ("draft", "sent"))
        test.assertTrue(anterior.active)
        test.assertTrue(anterior.current_revision_id)
        if nueva:
            test.assertEqual(anterior.current_revision_id, nueva)
    else:
        test.assertEqual(anterior.state, "cancel")
        test.assertFalse(anterior.active)
