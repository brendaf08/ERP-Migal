# Copyright 2018-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import Command
from odoo.fields import Domain
from odoo.orm.model_classes import add_to_registry
from odoo.tests import TransactionCase, new_test_user

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class CommonTierValidation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # BaseCommon-like setup with Odoo 19 res.partner.autopost_bills compatibility.
        cls.env = cls.env["base"].with_context(**DISABLED_MAIL_CONTEXT).env

        cls.env.user.group_ids += cls.env.ref("base.group_user")

        cls.company = cls.env.company
        cls.currency = cls.env.company.currency_id

        partner_vals = {"name": "Test Partner"}
        Partner = cls.env["res.partner"]
        if "autopost_bills" in Partner._fields:
            partner_vals["autopost_bills"] = "ask"
        else:
            # Compatibility for DBs where autopost_bills column is required but
            # the ORM field is not available in this test setup.
            cls.env.cr.execute(
                "ALTER TABLE res_partner ALTER COLUMN autopost_bills SET DEFAULT 'ask'"
            )
            cls.addClassCleanup(
                cls.env.cr.execute,
                "ALTER TABLE res_partner ALTER COLUMN autopost_bills DROP DEFAULT",
            )
        cls.partner = Partner.create(partner_vals)

        # Compatibility for res.company required columns without ORM/defaults in
        # this test environment (e.g. fiscal/account fields in validation DB).
        cls.env.cr.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name='res_company'
              AND is_nullable='NO'
              AND column_default IS NULL
              AND column_name NOT IN ('id')
            """
        )
        for col, data_type in cls.env.cr.fetchall():
            if data_type in ("integer", "smallint", "bigint", "numeric", "double precision", "real"):
                default = 0
            elif data_type == "boolean":
                default = False
            elif data_type in ("json", "jsonb"):
                continue
            else:
                default = ""
            try:
                with cls.env.cr.savepoint():
                    cls.env.cr.execute(
                        f"ALTER TABLE res_company ALTER COLUMN {col} SET DEFAULT %s",
                        (default,),
                    )
                cls.addClassCleanup(
                    cls.env.cr.execute,
                    f"ALTER TABLE res_company ALTER COLUMN {col} DROP DEFAULT",
                )
            except Exception:
                pass

        cls.group_portal = cls.env.ref("base.group_portal")
        cls.group_user = cls.env.ref("base.group_user")
        cls.group_system = cls.env.ref("base.group_system")
        from .tier_validation_tester import (
            TierDefinition,
            TierValidationTester,
            TierValidationTester2,
            TierValidationTesterComputed,
        )

        cls.TierValidationTester = TierValidationTester
        cls.TierValidationTester2 = TierValidationTester2
        cls.TierValidationTesterComputed = TierValidationTesterComputed
        model_defs = (
            TierValidationTester,
            TierValidationTester2,
            TierValidationTesterComputed,
            TierDefinition,
        )
        for model_def in model_defs:
            add_to_registry(cls.registry, model_def)

        model_names = [
            "tier.validation.tester",
            "tier.validation.tester2",
            "tier.validation.tester.computed",
            "tier.definition",
        ]
        cls.registry._setup_models__(cls.env.cr, model_names)
        cls.registry.init_models(
            cls.env.cr,
            model_names[:-1],
            {"models_to_check": True},
        )
        for model_name in model_names[:-1]:
            cls.addClassCleanup(cls.registry.__delitem__, model_name)

    def _create_tier_definition(self, **values):
        return self.tier_def_obj.create(values)

    def _setup_tier_definitions(self):
        self.definition_1 = self.tier_definition = self._create_tier_definition(
            model_id=self.tester_model.id,
            review_type="individual",
            reviewer_id=self.test_user_1.id,
            definition_domain="[('test_field', '=', 1.0)]",
            sequence=30,
        )
        self.definition_2 = self._create_tier_definition(
            model_id=self.tester_model.id,
            review_type="individual",
            reviewer_id=self.test_user_1.id,
            definition_domain="[('test_field', '>', 3.0)]",
            approve_sequence=True,
            notify_on_pending=False,
            sequence=20,
            name="Definition for test 19 - sequence - user 1",
        )
        self.definition_3 = self._create_tier_definition(
            model_id=self.tester_model.id,
            review_type="individual",
            reviewer_id=self.test_user_2.id,
            definition_domain="[('test_field', '>', 3.0)]",
            approve_sequence=True,
            notify_on_pending=True,
            sequence=10,
            name="Definition for test 19 - sequence - user 2",
        )
        self.definition_4 = self._create_tier_definition(
            model_id=self.tester_model.id,
            review_type="individual",
            reviewer_id=self.test_user_1.id,
            definition_domain="[('test_field', '=', 0.9)]",
            approve_sequence=False,
            notify_on_pending=True,
            sequence=10,
            name="Definition for test 20 - no sequence -  user 1 - no sequence",
        )
        self.definition_5 = self._create_tier_definition(
            model_id=self.tester_model_computed.id,
            review_type="individual",
            reviewer_id=self.test_user_1.id,
            definition_domain="[]",
            approve_sequence=True,
            notify_on_pending=False,
            sequence=20,
            name="Definition for computed model",
        )
        self.definition_6 = self._create_tier_definition(
            model_id=self.tester_model_2.id,
            review_type="individual",
            reviewer_id=self.test_user_1.id,
            definition_domain="[('test_field', '>=', 1.0)]",
            approve_sequence=True,
            notify_on_pending=False,
            sequence=30,
            name="Definition for test 30 - sequence - user 1 - main company",
            company_id=self.main_company.id,
        )
        self.definition_7 = self._create_tier_definition(
            model_id=self.tester_model_2.id,
            review_type="individual",
            reviewer_id=self.test_user_3_multi_company.id,
            definition_domain="[('test_field', '>=', 1.0)]",
            approve_sequence=True,
            notify_on_pending=False,
            sequence=20,
            name="Definition for test 30 - sequence - user 3 - main company",
            company_id=self.main_company.id,
        )
        self.definition_8 = self._create_tier_definition(
            model_id=self.tester_model_2.id,
            review_type="individual",
            reviewer_id=self.test_user_3_multi_company.id,
            definition_domain="[('test_field', '>=', 1.0)]",
            approve_sequence=True,
            notify_on_pending=False,
            sequence=30,
            name="Definition for test 30 - sequence - user 3 - other company",
            company_id=self.other_company.id,
        )

    def setUp(self):
        super().setUp()
        self.test_model = self.env[self.TierValidationTester._name]
        self.test_model_2 = self.env[self.TierValidationTester2._name]
        self.test_model_computed = self.env[self.TierValidationTesterComputed._name]

        self.tester_model = self.env["ir.model"].search(
            Domain("model", "=", "tier.validation.tester")
        )
        self.tester_model_2 = self.env["ir.model"].search(
            Domain("model", "=", "tier.validation.tester2")
        )
        self.tester_model_computed = self.env["ir.model"].search(
            Domain("model", "=", "tier.validation.tester.computed")
        )
        # Create a multi-company
        self.main_company = self.env.ref("base.main_company")
        company_vals = {"name": f"My Company {self._testMethodName}"}
        Company = self.env["res.company"]
        if "fiscalyear_last_day" in Company._fields:
            company_vals.setdefault("fiscalyear_last_day", 31)
        if "fiscalyear_last_month" in Company._fields:
            company_vals.setdefault("fiscalyear_last_month", "12")
        self.other_company = Company.create(company_vals)

        models = (
            self.tester_model,
            self.tester_model_2,
            self.tester_model_computed,
        )
        for model in models:
            # Access record:
            self.env["ir.model.access"].create(
                {
                    "name": f"access {model.name}",
                    "model_id": model.id,
                    "perm_read": 1,
                    "perm_write": 1,
                    "perm_create": 1,
                    "perm_unlink": 1,
                }
            )

            # Define views to avoid automatic views with all fields.
            self.env["ir.ui.view"].create(
                {
                    "model": model.model,
                    "name": f"Demo view for {model}",
                    "arch": """<form>
                    <header>
                        <button name="action_confirm" type="object" string="Confirm" />
                        <field name="state" widget="statusbar" />
                    </header>
                    <sheet>
                        <field name="test_field" />
                    </sheet>
                    </form>""",
                }
            )

        # Create users:
        self.test_user_1 = new_test_user(
            self.env, name="John", login="test1", groups="base.group_system"
        )
        self.test_user_2 = new_test_user(self.env, name="Mike", login="test2")
        self.test_user_3_multi_company = new_test_user(
            self.env,
            name="Jane",
            login="test3",
            company_ids=[Command.set([self.main_company.id, self.other_company.id])],
        )
        # Create groups
        self.test_group = self.env["res.groups"].create(
            {
                "name": "TestGroup",
                "user_ids": [
                    Command.link(self.test_user_1.id),
                    Command.link(self.test_user_2.id),
                ],
            }
        )
        # Create tier definitions:
        self.tier_def_obj = self.env["tier.definition"]
        self._setup_tier_definitions()

        self.test_record = self.test_model.create({"test_field": 1.0})
        self.test_record_2 = self.test_model_2.create({"test_field": 1.0})
        self.test_record_computed = self.test_model_computed.create({"test_field": 1.0})
