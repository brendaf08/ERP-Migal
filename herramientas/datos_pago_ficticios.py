# Datos de pago FICTICIOS para la demo (no corresponden a cuentas reales de MIGAL)
datos = {
    "pago_titular": "Ferre & Inversiones MIGAL S.A.C.",
    "pago_yape": "912 345 678",
    "pago_bcp_cuenta": "191-2345678-0-12",
    "pago_bcp_cci": "002-191-002345678012-58",
    "pago_bbva_cuenta": "0011-0123-0201234567",
    "pago_bbva_cci": "011-123-000201234567-89",
}
icp = env["ir.config_parameter"].sudo()
for k, v in datos.items():
    icp.set_param("migal_agente.%s" % k, v)
env.cr.commit()
print("ok", env.cr.dbname)
