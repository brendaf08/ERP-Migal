/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { session } from "@web/session";
import { NavBar } from "@web/webclient/navbar/navbar";

const appKey = (app) => app.xmlid || String(app.id);

class MigalConfigurarApps extends Component {
    static template = "migal_reportes.ConfigurarApps";
    static components = { Dialog };
    static props = {
        apps: Array,
        hidden: Array,
        onSave: Function,
        close: Function,
    };

    setup() {
        this.state = useState({ hidden: [...this.props.hidden] });
    }

    setVisible(key, visible) {
        const hidden = this.state.hidden.filter((id) => id !== key);
        this.state.hidden = visible ? hidden : [...hidden, key];
    }

    mostrarTodas() {
        this.state.hidden = [];
    }

    guardar() {
        this.props.onSave([...this.state.hidden]);
        this.props.close();
    }
}

patch(NavBar.prototype, {
    setup() {
        super.setup(...arguments);
        this.migalDialog = useService("dialog");
        this.migalAppsPreferenceKey = `migal.apps.hidden.${session.db || "odoo"}.${user.userId}`;
        let hidden = [];
        try {
            const saved = JSON.parse(browser.localStorage.getItem(this.migalAppsPreferenceKey) || "[]");
            if (Array.isArray(saved)) {
                hidden = saved.filter((id) => typeof id === "string");
            }
        } catch {
            // Un navegador con almacenamiento bloqueado mantiene la selección solo en esta sesión.
        }
        this.migalAppsPreference = useState({ hidden });
    },

    get migalAppsVisibles() {
        return this.menuService.getApps().filter(
            (app) => !this.migalAppsPreference.hidden.includes(appKey(app))
        );
    },

    migalEditarAplicaciones() {
        this._closeAppMenuSidebar();
        this.migalDialog.add(MigalConfigurarApps, {
            apps: this.menuService.getApps().map((app) => ({ key: appKey(app), name: app.name })),
            hidden: [...this.migalAppsPreference.hidden],
            onSave: (hidden) => {
                this.migalAppsPreference.hidden = hidden;
                try {
                    browser.localStorage.setItem(this.migalAppsPreferenceKey, JSON.stringify(hidden));
                } catch {
                    // La selección sigue aplicada hasta que se recargue la página.
                }
            },
        });
    },
});
