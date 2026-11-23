/** @odoo-module **/
/**
 * Campo «Foto o PDF de la lista»: apenas se sube el archivo, se guarda y se lee
 * (Gemini + emparejamiento) sin pulsar otro botón.
 */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { BinaryField, binaryField } from "@web/views/fields/binary/binary_field";

export class ArchivoListaField extends BinaryField {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.ui = useService("ui");
    }

    async update({ data, name }) {
        await super.update({ data, name });
        if (!data) {
            return;
        }
        const record = this.props.record;
        this.ui.block();
        this.notification.add(_t("Leyendo la lista y buscando cada producto en el catálogo…"), { type: "info" });
        try {
            await record.save();
            await this.orm.call("migal.ocr.documento", "action_leer", [[record.resId]], {
                context: record.context,
            });
        } finally {
            this.ui.unblock();
            await record.load();
        }
    }
}

registry.category("fields").add("migal_ocr_archivo", {
    ...binaryField,
    component: ArchivoListaField,
});
