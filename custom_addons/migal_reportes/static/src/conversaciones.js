/** @odoo-module **/

import "@mail/chatter/web/form_compiler";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { FormCompiler } from "@web/views/form/form_compiler";

patch(FormCompiler.prototype, {
    compile(key, params = {}) {
        const compiled = super.compile(key, params);
        if (params.isSubView) {
            return compiled;
        }
        const renderer = compiled.firstElementChild;
        if (
            !renderer?.classList.contains("o_form_renderer") ||
            !renderer.querySelector(".o-mail-Form-chatter") ||
            renderer.querySelector(".o_migal_toggle_chatter")
        ) {
            return compiled;
        }

        const doc = renderer.ownerDocument;
        const label = _t("Mensajes y actividad");
        const control = doc.createElement("div");
        control.setAttribute("class", "o_migal_chatter_control");
        control.setAttribute("t-if", "!__comp__.env.inDialog");

        const toggle = doc.createElement("details");
        toggle.setAttribute("class", "o_migal_toggle_chatter");
        toggle.setAttribute("t-key", "__comp__.props.record.resId || 'new'");

        const summary = doc.createElement("summary");
        summary.setAttribute("title", label);
        const icon = doc.createElement("i");
        icon.setAttribute("class", "fa fa-comments-o");
        icon.setAttribute("aria-hidden", "true");
        const accessibleLabel = doc.createElement("span");
        accessibleLabel.setAttribute("class", "visually-hidden");
        accessibleLabel.textContent = label;
        summary.append(icon, accessibleLabel);
        toggle.append(summary);
        control.append(toggle);

        const sheet = renderer.querySelector(":scope > .o_form_sheet_bg > .o_form_sheet");
        const header = sheet?.querySelector(":scope > .o_migal_encabezado");
        (header || sheet || renderer).prepend(control);
        return compiled;
    },
});
