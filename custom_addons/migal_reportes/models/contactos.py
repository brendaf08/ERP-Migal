from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain

from odoo.addons.migal_agente.models.tool_whatsapp import E164_RE, normalizar_telefono


_POS_CONTACTOS = [
    ("type", "=", "contact"),
    ("parent_id", "=", False),
    ("migal_marcador_contacto", "!=", "obra"),
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    migal_marcador_contacto = fields.Selection(
        [
            ("migal", "MIGAL"),
            ("fraternidad_amical", "Fraternidad Amical"),
            ("maestro", "Maestro de obra"),
            ("cliente", "Cliente"),
            ("obra", "Obra"),
        ],
        string="Clasificación",
    )

    migal_pos_contacto_elegible = fields.Boolean(compute="_compute_migal_pos_contacto_elegible")

    @api.depends("type", "parent_id", "migal_marcador_contacto")
    def _compute_migal_pos_contacto_elegible(self):
        elegibles = self.filtered_domain(_POS_CONTACTOS)
        for partner in self:
            partner.migal_pos_contacto_elegible = partner in elegibles

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        context = self.env.context
        if (
            not context.get("migal_contact_defaults")
            or values.get("parent_id", context.get("default_parent_id"))
            or values.get("type", context.get("default_type") or "contact") != "contact"
        ):
            return values

        peru = self.env.ref("base.pe")
        country_id = values.get("country_id") or context.get("default_country_id")
        if country_id != peru.id and (country_id or "default_country_id" in context):
            return values
        if "country_id" in fields_list and not country_id:
            values["country_id"] = peru.id
        if (
            {"city", "city_id"}.issubset(fields_list)
            and not values.get("city")
            and not values.get("city_id")
            and "default_city" not in context
            and "default_city_id" not in context
        ):
            lima = self.env.ref("l10n_pe.city_pe_1501")
            values.update(city=lima.name, city_id=lima.id)
            if "state_id" in fields_list and "default_state_id" not in context:
                values.setdefault("state_id", lima.state_id.id)
        if (
            "l10n_latam_identification_type_id" in fields_list
            and "default_l10n_latam_identification_type_id" not in context
        ):
            company_type = values.get("company_type") or context.get("default_company_type")
            is_company = company_type == "company" if company_type else values.get(
                "is_company", context.get("default_is_company", False)
            )
            values["l10n_latam_identification_type_id"] = self._migal_pe_document_type(is_company).id
        return values

    def _migal_pe_document_type(self, is_company):
        return self.env.ref("l10n_pe.it_RUC" if is_company else "l10n_pe.it_DNI")

    def _migal_suggest_pe_document_type(self):
        for partner in self:
            if (
                partner._origin
                or partner.parent_id
                or partner.type != "contact"
                or partner.vat
                or partner.country_id.code != "PE"
            ):
                continue
            current = partner.l10n_latam_identification_type_id
            standard = (
                self._migal_pe_document_type(False)
                | self._migal_pe_document_type(True)
                | self.env.ref("l10n_latam_base.it_vat")
            )
            if not current or current in standard:
                partner.l10n_latam_identification_type_id = self._migal_pe_document_type(
                    partner.is_company
                )

    @api.onchange("company_type")
    def onchange_company_type(self):
        result = super().onchange_company_type()
        self._migal_suggest_pe_document_type()
        return result

    @api.onchange("country_id")
    def _onchange_country_id(self):
        result = super()._onchange_country_id()
        self._migal_suggest_pe_document_type()
        return result

    @api.model
    def _load_pos_data_fields(self, config):
        return [*super()._load_pos_data_fields(config), "migal_pos_contacto_elegible"]

    @api.model
    def get_new_partner(self, config_id, domain, offset):
        if domain:
            domain = list(Domain.AND([domain, _POS_CONTACTOS]))
        return super().get_new_partner(config_id, domain, offset)

    def action_migal_contacto_whatsapp(self):
        self.ensure_one()
        self.check_access("read")
        telefono = normalizar_telefono(self.phone)
        if not E164_RE.fullmatch(telefono):
            raise UserError(_("Registra un teléfono internacional válido para abrir WhatsApp."))
        return {
            "type": "ir.actions.act_url",
            "url": f"https://wa.me/{telefono[1:]}",
            "target": "new",
        }
