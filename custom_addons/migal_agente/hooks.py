"""Inicialización: reglas de cobertura para las cuatro categorías de la regla habitual.

Las categorías de producto ya existen en la base de MIGAL (no tienen xmlid propio),
por lo que se buscan por nombre. Los límites y plazos sembrados son valores
[SIM] de ejercicio, pendientes de definición por MIGAL (GER/ALM).
"""

CATEGORIAS_REGLA_HABITUAL = [
    "Agregados",
    "Cemento y aglomerantes",
    "Fierro y acero de construcción",
    "Ladrillos y bloques",
]


def post_init_hook(env):
    Regla = env["migal.agente.regla.cobertura"]
    Categ = env["product.category"]
    for nombre in CATEGORIAS_REGLA_HABITUAL:
        categ = Categ.search([("name", "=", nombre)], limit=1)
        if not categ or Regla.search_count([("categ_id", "=", categ.id)]):
            continue
        Regla.create({
            "categ_id": categ.id,
            "plazo_dias": 3,
            "faltante_max_pct": 100.0,
            "nota": "[SIM] Regla habitual de reposición propuesta para la PC3. "
                    "Plazo y límite pendientes de validación por MIGAL (GER/ALM).",
        })
