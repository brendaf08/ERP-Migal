/** @odoo-module **/

import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";

patch(PartnerList.prototype, {
    getPartners(partners) {
        const independientes = partners.filter((partner) => partner.migal_pos_contacto_elegible);
        return super.getPartners(independientes);
    },
});
