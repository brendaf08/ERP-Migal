# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged, HttpCase
import json


@tagged('post_install', '-at_install', 'p2_r07')
class TestP2R07CoordinatedRevision(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company_2 = cls.env['res.company'].create({'name': 'Empresa R07'})
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente R07'})

        def _user(login, groups):
            return cls.env['res.users'].create({
                'name': login, 'login': login,
                'group_ids': [(6, 0, [cls.env.ref(g).id for g in groups])],
                'company_id': cls.company.id,
                'company_ids': [(6, 0, [cls.company.id])],
            })

        cls.user_coord = _user('r07_coord', [
            'base.group_user', 'sale_order_request.group_sale_order_request_coordinator'])
        cls.user_no_coord = _user('r07_nocoord', ['base.group_user'])
        cls.user_coord_c2 = cls.env['res.users'].create({
            'name': 'r07_coord_c2', 'login': 'r07_coord_c2',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('sale_order_request.group_sale_order_request_coordinator').id])],
            'company_id': cls.company_2.id,
            'company_ids': [(6, 0, [cls.company_2.id])],
        })

        cls.product = cls.env['product.product'].create({'name': 'Prod R07', 'type': 'consu'})
        cls.user_sales = _user('r07_sales', [
            'base.group_user', 'sales_team.group_sale_salesman',
            'sale_order_request.group_sale_order_request_salesperson'])
        cls.order = cls.env['sale.order'].with_user(cls.user_sales).create({
            'partner_id': cls.partner.id,
            'company_id': cls.company.id,
            'order_line': [(0, 0, {'product_id': cls.product.id, 'product_uom_qty': 1, 'price_unit': 10})],
        })
        cls.order.with_user(cls.user_sales).action_mark_sale_request_subject()
        cls.request = cls.env['sale.order.request'].with_user(cls.user_sales).create({
            'sale_order_id': cls.order.id,
            'sale_order_revision_id': cls.order.id,
            'unrevisioned_name': cls.order.unrevisioned_name,
            'company_id': cls.company.id,
            'delivery_mode': 'pickup',
            'requester_id': cls.user_sales.id,
            'line_ids': [(0, 0, {
                'sale_order_line_id': cls.order.order_line[0].id,
                'product_id': cls.product.id,
                'product_uom_id': cls.order.order_line[0].product_uom_id.id,
                'qty': 1.0,
            })],
        })
        cls.env.cr.execute("UPDATE sale_order_request SET state='approved' WHERE id=%s", (cls.request.id,))
        cls.request.invalidate_recordset()

    def test_coordinator_authorized_same_company_ok(self):
        res = self.request.with_user(self.user_coord).action_coordinated_revision()
        self.assertEqual(res.get('res_model'), 'sale.order.request')
        self.request.invalidate_recordset()
        self.assertEqual(self.request.state, 'superseded')

    def test_user_without_coordinator_group_denied(self):
        with self.assertRaises(UserError):
            self.request.with_user(self.user_no_coord).action_coordinated_revision()

    def test_coordinator_without_company_access_denied(self):
        with self.assertRaises(UserError):
            self.request.with_user(self.user_coord_c2).action_coordinated_revision()

    def test_invalid_state_denied_no_mutation(self):
        order = self.env['sale.order'].with_user(self.user_sales).create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 1, 'price_unit': 10})],
        })
        order.with_user(self.user_sales).action_mark_sale_request_subject()
        req = self.env['sale.order.request'].with_user(self.user_sales).create({
            'sale_order_id': order.id,
            'sale_order_revision_id': order.id,
            'unrevisioned_name': order.unrevisioned_name,
            'company_id': self.company.id,
            'delivery_mode': 'pickup',
            'requester_id': self.user_sales.id,
            'line_ids': [(0, 0, {
                'sale_order_line_id': order.order_line[0].id,
                'product_id': self.product.id,
                'product_uom_id': order.order_line[0].product_uom_id.id,
                'qty': 1.0,
            })],
        })
        # req queda en draft por defecto
        with self.assertRaises(UserError):
            req.with_user(self.user_coord).action_coordinated_revision()
        self.assertEqual(req.state, 'draft')

    def test_new_revision_other_family_denied(self):
        other = self.env['sale.order'].with_user(self.user_sales).create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 1, 'price_unit': 10})],
        })
        other.with_user(self.user_sales).action_mark_sale_request_subject()
        with self.assertRaises(UserError):
            self.request.with_user(self.user_coord)._check_coordinated_revision_access(new_revision=other)


    # ------------------------------------------------------------------
    # Pruebas adicionales de la revisión coordinada
    # ------------------------------------------------------------------
    def test_mark_superseded_helper_rejects_no_coordinator(self):
        """Helper interno no puede omitir autorización de coordinador."""
        req = self._new_approved_request("R07-HLP-NOCOORD")
        with self.assertRaises(UserError):
            req.with_user(self.user_no_coord)._mark_superseded_coordinated()
        req.invalidate_recordset()
        self.assertEqual(req.state, "approved")

    def test_mark_superseded_helper_rejects_other_company(self):
        req = self._new_approved_request("R07-HLP-COMP")
        with self.assertRaises(UserError):
            req.with_user(self.user_coord_c2)._mark_superseded_coordinated()
        req.invalidate_recordset()
        self.assertEqual(req.state, "approved")

    def test_mark_superseded_helper_rejects_other_family(self):
        req = self._new_approved_request("R07-HLP-FAM")
        other = self.env['sale.order'].with_user(self.user_sales).create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 1, 'price_unit': 10})],
        })
        other.with_user(self.user_sales).action_mark_sale_request_subject()
        # Simular inconsistencia de familia por corrupción/manipulación directa en DB.
        self.env.cr.execute(
            "UPDATE sale_order_request SET sale_order_revision_id=%s WHERE id=%s",
            (other.id, req.id),
        )
        req.invalidate_recordset()
        with self.assertRaises(UserError):
            req.with_user(self.user_coord)._mark_superseded_coordinated()
        self.env.cr.execute(
            "UPDATE sale_order_request SET sale_order_revision_id=%s WHERE id=%s",
            (req.sale_order_id.id, req.id),
        )
        req.invalidate_recordset()
        self.assertEqual(req.state, "approved")

    def test_mark_superseded_no_authorized_bypass_param(self):
        """No existe un parámetro booleano authorized=True que permita omitir las validaciones."""
        req = self._new_approved_request("R07-HLP-BYPASS")
        with self.assertRaises(TypeError):
            req.with_user(self.user_coord)._mark_superseded_coordinated(authorized=True)
        req.invalidate_recordset()
        self.assertEqual(req.state, "approved")

    def test_coordinated_revision_full_flow_creates_new_request(self):
        req = self._new_approved_request("R07-FULL")
        old_revision = req.sale_order_revision_id
        res = req.with_user(self.user_coord).action_coordinated_revision()
        self.assertEqual(res.get('res_model'), 'sale.order.request')
        new_req = self.env['sale.order.request'].browse(res.get('res_id'))
        self.assertTrue(new_req.exists())
        self.assertNotEqual(new_req.id, req.id)
        self.assertEqual(new_req.state, 'draft')
        self.assertEqual(new_req.unrevisioned_name, req.unrevisioned_name)
        self.assertEqual(new_req.company_id, req.company_id)
        self.assertNotEqual(new_req.sale_order_revision_id.id, old_revision.id)
        req.invalidate_recordset()
        self.assertEqual(req.state, 'superseded')
        # nueva revisión marcada como sujeta
        self.assertTrue(new_req.sale_order_revision_id.sale_request_subject)

    def test_coordinated_revision_preserves_tier_reviews(self):
        """La revisión coordinada debe preservar revisiones Tier de la orden anterior."""
        req = self._new_approved_request("R07-TIER")
        order = req.sale_order_revision_id
        TierDef = self.env['tier.definition']
        model = self.env['ir.model']._get('sale.order')
        tier_def = TierDef.search([('model_id', '=', model.id)], limit=1)
        if not tier_def:
            tier_def = TierDef.create({
                'name': 'Tier R07 Test',
                'model_id': model.id,
                'review_type': 'individual',
                'reviewer_id': self.user_coord.id,
                'definition_domain': '[]',
            })
        review = self.env['tier.review'].with_context(skip_validation_check=True).create({
            'model': 'sale.order',
            'res_id': order.id,
            'definition_id': tier_def.id,
            'requested_by': self.user_coord.id,
            'review_type': tier_def.review_type or 'individual',
            'status': 'approved',
            'sequence': 10,
        })
        self.assertTrue(review.exists())

        res = req.with_user(self.user_coord).action_coordinated_revision()
        new_req = self.env['sale.order.request'].browse(res.get('res_id'))
        new_order = new_req.sale_order_revision_id
        self.assertNotEqual(new_order.id, order.id)
        # Preservación real: la review sigue en la orden anterior (no eliminada por revisión).
        old_reviews = self.env['tier.review'].with_context(active_test=False).search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', order.id),
            ('definition_id', '=', tier_def.id),
        ])
        self.assertTrue(old_reviews, "Las revisiones Tier deben preservarse en la orden anterior")
        self.assertEqual(set(old_reviews.mapped('status')), {'approved'})

    def test_helper_mark_subject_denied_without_coordinator(self):
        req = self._new_approved_request("R07-MSUBJ")
        new_order = req.sale_order_id.copy()
        with self.assertRaises(UserError):
            new_order.with_user(self.user_no_coord)._sale_request_mark_subject_coordinated()

    def test_helper_create_revision_denied_without_coordinator(self):
        req = self._new_approved_request("R07-CREV")
        with self.assertRaises(UserError):
            req.sale_order_revision_id.with_user(self.user_no_coord)._sale_request_create_revision_preserving_tier_coordinated()

    def _new_approved_request(self, label):
        order = self.env['sale.order'].with_user(self.user_sales).create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'client_order_ref': label,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 1, 'price_unit': 10})],
        })
        order.with_user(self.user_sales).action_mark_sale_request_subject()
        req = self.env['sale.order.request'].with_user(self.user_sales).create({
            'sale_order_id': order.id,
            'sale_order_revision_id': order.id,
            'unrevisioned_name': order.unrevisioned_name,
            'company_id': self.company.id,
            'delivery_mode': 'pickup',
            'requester_id': self.user_sales.id,
            'line_ids': [(0, 0, {
                'sale_order_line_id': order.order_line[0].id,
                'product_id': self.product.id,
                'product_uom_id': order.order_line[0].product_uom_id.id,
                'qty': 1.0,
            })],
        })
        self.env.cr.execute("UPDATE sale_order_request SET state='approved' WHERE id=%s", (req.id,))
        req.invalidate_recordset()
        return req


@tagged('post_install', '-at_install', 'p2_r07')
class TestP2R07RpcPrivate(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente R07 RPC'})
        cls.product = cls.env['product.product'].create({'name': 'Prod R07 RPC', 'type': 'consu'})
        coord_grp = cls.env.ref('sale_order_request.group_sale_order_request_coordinator')
        sales_grp = cls.env.ref('sales_team.group_sale_salesman')
        req_grp = cls.env.ref('sale_order_request.group_sale_order_request_salesperson')
        cls.user_sales = cls.env['res.users'].create({
            'name': 'r07rpc_sales', 'login': 'r07rpc_sales', 'password': 'r07rpc_sales',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, sales_grp.id, req_grp.id])],
            'company_id': cls.company.id, 'company_ids': [(6, 0, [cls.company.id])],
        })
        cls.user_coord = cls.env['res.users'].create({
            'name': 'r07rpc_coord', 'login': 'r07rpc_coord', 'password': 'r07rpc_coord',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, coord_grp.id])],
            'company_id': cls.company.id, 'company_ids': [(6, 0, [cls.company.id])],
        })
        order = cls.env['sale.order'].with_user(cls.user_sales).create({
            'partner_id': cls.partner.id, 'company_id': cls.company.id,
            'order_line': [(0, 0, {'product_id': cls.product.id, 'product_uom_qty': 1, 'price_unit': 10})],
        })
        order.with_user(cls.user_sales).action_mark_sale_request_subject()
        req = cls.env['sale.order.request'].with_user(cls.user_sales).create({
            'sale_order_id': order.id, 'sale_order_revision_id': order.id,
            'unrevisioned_name': order.unrevisioned_name, 'company_id': cls.company.id,
            'delivery_mode': 'pickup', 'requester_id': cls.user_sales.id,
            'line_ids': [(0, 0, {
                'sale_order_line_id': order.order_line[0].id, 'product_id': cls.product.id,
                'product_uom_id': order.order_line[0].product_uom_id.id, 'qty': 1.0,
            })],
        })
        cls.env.cr.execute("UPDATE sale_order_request SET state='approved' WHERE id=%s", (req.id,))
        req.invalidate_recordset()
        cls.req_id = req.id

    def _jsonrpc(self, model, method, args=None, kwargs=None):
        payload = {
            "jsonrpc": "2.0", "method": "call",
            "params": {"model": model, "method": method, "args": args or [], "kwargs": kwargs or {}},
            "id": 1,
        }
        resp = self.url_open('/web/dataset/call_kw/%s/%s' % (model, method),
                             data=json.dumps(payload), headers={"Content-Type": "application/json"})
        return resp

    def test_rpc_private_helpers_rejected(self):
        self.authenticate('r07rpc_coord', 'r07rpc_coord')
        # Odoo RPC rechaza métodos privados (inician con _)
        for method in ['_mark_superseded_coordinated', '_check_coordinated_revision_access']:
            resp = self._jsonrpc('sale.order.request', method, args=[[self.req_id]])
            # puede ser 404/200 con error RPC; lo importante es que no ejecute exitosamente
            self.assertNotEqual(resp.status_code, 500)
            body = resp.text
            self.assertNotIn('"result"', body.replace('"result": null', ''))
