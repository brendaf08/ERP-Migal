/** @odoo-module **/

import { registry } from "@web/core/registry";

// Los enlaces guardados a la antigua pantalla de Inicio abren Cotizaciones.
registry.category("actions").add("migal_reportes.inicio_ventas", (env) =>
    env.services.action.loadAction("sale.action_quotations_with_onboarding")
);
