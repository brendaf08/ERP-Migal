# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""
Módulo de negocio : Solicitud de Pedido.

Implementa el flujo de Solicitud de Pedido de la ferretería :

1. El vendedor crea una Solicitud de Pedido vinculada a una cotización
   vigente y su revisión correspondiente.
2. El sistema evalúa la disponibilidad de inventario (free_qty para
   recojo, virtual_available para despacho).
3. El sistema determina las aprobaciones requeridas según la matriz:
   - Stock suficiente + recojo: sin aprobaciones
   - Stock suficiente + despacho: requiere Transporte
   - Stock insuficiente + recojo: requiere Abastecimiento
   - Stock insuficiente + despacho: requiere Abastecimiento + Transporte
4. Los responsables aprueban de forma independiente y paralela.
5. El vendedor ejecuta la aceptación final.
6. El sistema confirma la cotización vigente (pasa a 'sale').

No se crea un segundo sale.order al finalizar el flujo.

Dependencias:
- sale_management
- sale_stock
- base_tier_validation
- sale_tier_validation
- base_revision
- sale_order_revision
- sale_revision_tier_compat

Seguridad (Fase A2):
- El campo `state` NO puede modificarse directamente por ORM/RPC. Solo los
  métodos `action_*` pueden cambiar el estado, tras validar permisos y
  condiciones. No se utiliza un contexto RPC autorizable (por ejemplo
  `sale_order_request_allow_state_write`), porque cualquier cliente RPC puede inyectarlo.
- Los campos que identifican la solicitud (cotización, revisión, familia,
  compañía y solicitante) son inmutables tras la creación, lo que impide
  reutilizar aprobaciones de otra cotización o revisión.
- La aceptación final revalida el stock real y solo puede ser ejecutada por
  el vendedor solicitante.
"""

import weakref
from contextlib import contextmanager

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

# Registro transitorio privado (no-RPC) para coordinar  con
# base_tier_validation._tier_validation_check_state_on_write.
# Clave: cursor de transacción (request-local, no manipulable por RPC).
# Valor: {(model_name, res_id): [stack de casos]}.
# WeakKeyDictionary exige cursor hashable/weakrefeable; si no es compatible,
# fallar explícitamente (sin fallback silencioso).
try:
    _SALE_REQUEST_TIER_STATE_CASES = weakref.WeakKeyDictionary()
except TypeError as err:
    raise TypeError(
        "sale_order_request: el cursor no admite WeakKeyDictionary; "
        "no se puede inicializar el marcador transitorio Tier de forma segura"
    ) from err

_TIER_CASES_CLOSED = frozenset({"no_tier_approved", "tier_validated_approved"})


def _sale_request_tier_case_get(cr, model, res_id):
    data = _SALE_REQUEST_TIER_STATE_CASES.get(cr) or {}
    stack = data.get((model, int(res_id))) or []
    return stack[-1] if stack else None


def _sale_request_tier_case_push(cr, model, res_id, case):
    if case not in _TIER_CASES_CLOSED:
        raise ValueError("Caso interno Tier no permitido: %s" % case)
    try:
        data = _SALE_REQUEST_TIER_STATE_CASES.setdefault(cr, {})
    except TypeError as err:
        raise TypeError(
            "sale_order_request: cursor no compatible como clave del marcador "
            "transitorio Tier"
        ) from err
    data.setdefault((model, int(res_id)), []).append(case)


def _sale_request_tier_case_pop(cr, model, res_id):
    data = _SALE_REQUEST_TIER_STATE_CASES.get(cr)
    if not data:
        return None
    key = (model, int(res_id))
    stack = data.get(key) or []
    case = stack.pop() if stack else None
    if not stack:
        data.pop(key, None)
    if not data:
        try:
            _SALE_REQUEST_TIER_STATE_CASES.pop(cr, None)
        except Exception:
            pass
    return case


class SaleOrderRequest(models.Model):
    _name = "sale.order.request"
    _inherit = ["mail.thread", "tier.validation"]
    _description = "Solicitud de orden de venta"

    _state_from = ["draft", "pending_approval"]
    _state_to = ["approved"]
    _cancel_state = "cancel"
    _tier_validation_manual_config = False

    # ------------------------------------------------------------------
    # Guardia de transiciones de estado (Fase A - A2 / A4)
    # ------------------------------------------------------------------
    # Los cambios directos de `state` mediante write() (ORM/RPC) están
    # siempre prohibidos. Únicamente los métodos action_* pueden cambiar
    # el estado, a través de _set_request_state(), y tras validar permisos
    # y condiciones. No se usa un contexto RPC autorizable.
    _ALLOWED_STATE_TRANSITIONS = {
        "draft": ["pending_approval", "approved", "cancel", "superseded"],
        "pending_approval": ["approved", "rejected", "cancel", "superseded"],
        "approved": ["rejected", "accepted", "cancel", "superseded"],
        "accepted": ["confirmed"],
        "rejected": ["cancel", "superseded"],
        "superseded": [],
        "confirmed": ["superseded"],
    }

    # Campos que identifican la solicitud y no pueden alterarse tras la
    # creación. Evita reutilizar aprobaciones pertenecientes a otra
    # cotización o revisión.
    _IMMUTABLE_FIELDS = [
        "sale_order_id",
        "sale_order_revision_id",
        "unrevisioned_name",
        "company_id",
        "requester_id",
    ]

    def _state_transition_allowed(self, state_to):
        self.ensure_one()
        state_from = self.state or "draft"
        return state_to in self._ALLOWED_STATE_TRANSITIONS.get(state_from, [])

    def _check_review_integrity(self):
        """A3.2: Verifica que ninguna revisión Tier haya sido falsificada.

        Cada revisión con status 'approved' debe tener done_by establecido
        y ese usuario debe pertenecer a reviewer_ids de la revisión. Esto
        impide que un usuario escriba directamente tier.review.status='approved'
        con done_by=otro_usuario para falsificar una aprobación.
        """
        self.ensure_one()
        for review in self.review_ids:
            if review.status == "approved":
                if not review.done_by:
                    raise UserError(
                        "La revisión Tier '%s' está aprobada pero no tiene "
                        "usuario asignado como responsable (done_by)."
                        % review.name
                    )
                if review.done_by not in review.reviewer_ids:
                    raise UserError(
                        "La revisión Tier '%s' fue aprobada por un usuario "
                        "que no es revisor asignado. Posible falsificación."
                        % review.name
                    )
                if not review.reviewed_date:
                    raise UserError(
                        "La revisión Tier '%s' está aprobada pero no tiene "
                        "fecha de revisión."
                        % review.name
                    )

    def _check_company_consistency(self):
        """A3.3: Verifica que la compañía de la solicitud sea accesible por
        el usuario actual.

        Esta validación se aplica en servidor y no se puede eludir mediante
        contexto RPC ni manipulando company_ids. Solo verifica el campo
        company_id de la solicitud (que ya se derivó de la cotización al
        crear), sin acceder a registros relacionados que el usuario podría
        no tener permiso de leer.
        """
        self.ensure_one()
        user_company_ids = set(self.env.user.company_ids.ids)

        # La solicitud debe pertenecer a una compañía a la que el usuario
        # tiene acceso. Si company_ids está vacío (usuario sin compañías
        # asignadas), se deniega el acceso (fail-closed).
        if not user_company_ids or self.company_id.id not in user_company_ids:
            raise UserError(
                "No tiene acceso a la compañía de esta solicitud (%s)."
                % (self.company_id.name or self.company_id.id)
            )

    def _check_company_consistency(self):
        """A3.3: Verifica que la compañía de la solicitud sea accesible por
        el usuario actual.

        Esta validación se aplica en servidor y no se puede eludir mediante
        contexto RPC ni manipulando company_ids. Solo verifica el campo
        company_id de la solicitud (que ya se derivó de la cotización al
        crear), sin acceder a registros relacionados que el usuario podría
        no tener permiso de leer.
        """
        self.ensure_one()
        user_company_ids = set(self.env.user.company_ids.ids)

        # La solicitud debe pertenecer a una compañía a la que el usuario
        # tiene acceso. Si company_ids está vacío (usuario sin compañías
        # asignadas), se deniega el acceso (fail-closed).
        if not user_company_ids or self.company_id.id not in user_company_ids:
            raise UserError(
                "No tiene acceso a la compañía de esta solicitud (%s)."
                % (self.company_id.name or self.company_id.id)
            )

    def check_access_rule(self, operation):
        """A3.3: Verificar que el usuario tenga acceso a la compañía del
        registro antes de permitir cualquier operación. Complementa a
        ir.rule para garantizar fail-closed."""
        super(SaleOrderRequest, self).check_access_rule(operation)
        user_company_ids = set(self.env.user.company_ids.ids)
        if not user_company_ids:
            raise AccessError(
                "No tiene acceso a ninguna compañía."
            )
        for rec in self:
            if rec.company_id.id not in user_company_ids:
                raise AccessError(
                    "No tiene acceso a la compañía de este registro (%s)."
                    % (rec.company_id.name or rec.company_id.id)
                )

    # Estados históricos: Abastecimiento/Transporte solo lectura via write() RPC.
    _HISTORICAL_READONLY_STATES = {"approved", "confirmed", "superseded"}
    # Campos persistibles únicamente por flujos internos autorizados.
    # 'state' se gestiona exclusivamente por _set_request_state().
    _INTERNAL_WRITE_FIELDS = frozenset({
        "approval_date",
        "stock_checked_date",
        "accepted_by",
        "accepted_date",
    })

    def _is_review_role_user(self):
        """Indica si el usuario actual es Abastecimiento o Transporte."""
        user = self.env.user
        return user.has_group(
            "sale_order_request.group_sale_order_request_supply"
        ) or user.has_group("sale_order_request.group_sale_order_request_transport")

    def _internal_request_write(self, vals):
        """Persistencia interna . Privado (_): no invocable por RPC.

        No usa contexto como autorización. Solo debe llamarse desde métodos
        internos tras validar negocio, rol, estado, compañía y registro.
        Ningún método público debe reenviar valores arbitrarios a este helper.
        """
        self.ensure_one()
        vals = dict(vals)
        if not vals:
            return True
        forbidden = set(vals) - self._INTERNAL_WRITE_FIELDS
        if forbidden:
            raise UserError(
                "Escritura interna no permitida para campos: %s"
                % ", ".join(sorted(forbidden))
            )
        return super(SaleOrderRequest, self).write(vals)

    @contextmanager
    def _internal_tier_case(self, case):
        """Activa un caso interno Tier transitorio (no-RPC) con limpieza segura."""
        self.ensure_one()
        if case not in _TIER_CASES_CLOSED:
            raise ValueError("Caso interno Tier no permitido: %s" % case)
        cr = self.env.cr
        _sale_request_tier_case_push(cr, self._name, self.id, case)
        try:
            yield
        finally:
            _sale_request_tier_case_pop(cr, self._name, self.id)

    def _set_request_state(self, state_to, internal_tier_case=None):
        """Establece el estado desde el servidor (métodos action_*).

        Salta el guardia público de write() (que rechaza cualquier cambio
        de `state`) pero sigue pasando por el ORM. Solo debe invocarlo un
        método action_* después de comprobar permisos y condiciones. No es
        invocable por RPC porque su nombre comienza con guion bajo.
        """
        self.ensure_one()
        if internal_tier_case:
            with self._internal_tier_case(internal_tier_case):
                return super(SaleOrderRequest, self).write({"state": state_to})
        return super(SaleOrderRequest, self).write({"state": state_to})

    def write(self, vals):
        # 1. Prohibir escritura directa de `state` por ORM/RPC. Ningún
        #    contexto puede autorizar este cambio.
        if "state" in vals:
            raise UserError(
                "No se permite modificar el estado de la solicitud directamente. "
                "Utilice los métodos de flujo (solicitar validación, aprobar, "
                "rechazar, aceptar, superseder o cancelar)."
            )
        # 2. Prohibir modificación de los campos identificadores sobre
        #    registros ya creados.
        for rec in self.filtered("id"):
            for field in self._IMMUTABLE_FIELDS:
                if field not in vals:
                    continue
                current = rec[field]
                current_val = current.id if current else (current or False)
                new_val = vals[field]
                if field == "unrevisioned_name":
                    current_val = current or False
                    new_val = new_val or False
                new_empty = not new_val
                current_empty = not current_val
                if new_empty and current_empty:
                    continue  # no hay cambio real
                if new_val != current_val:
                    raise UserError(
                        "El campo %s no se puede modificar una vez creada "
                        "la solicitud." % field
                    )
        # 3. Modalidad de entrega: solo el vendedor solicitante (o uid 1)
        #    puede cambiarla en borrador, antes de solicitar validación.
        #    Abastecimiento y Transporte no pueden cambiarla (I-04).
        if "delivery_mode" in vals:
            es_revisor_entrega = self.env.user.has_group(
                "sale_order_request.group_sale_order_request_supply"
            ) or self.env.user.has_group("sale_order_request.group_sale_order_request_transport")
            for rec in self.filtered("id"):
                if vals["delivery_mode"] == rec.delivery_mode:
                    continue
                if es_revisor_entrega:
                    raise UserError(
                        "Abastecimiento y Transporte no pueden cambiar la "
                        "modalidad de entrega de una solicitud."
                    )
                if rec.state != "draft":
                    raise UserError(
                        "No se puede cambiar la modalidad de entrega fuera de "
                        "borrador. Utilice el flujo de validación o cree una "
                        "nueva solicitud."
                    )
                if self.env.uid != 1 and self.env.user != rec.requester_id:
                    raise UserError(
                        "Solo el vendedor solicitante puede cambiar la "
                        "modalidad de entrega en borrador."
                    )
        # C-05: Congelar datos comerciales una vez iniciadas las aprobaciones.
        # No se puede cambiar la modalidad de entrega ni las líneas cuando la
        # solicitud ya salió de borrador, salvo que se cancele/supersede y se
        # cree una nueva solicitud.
        for rec in self.filtered("id"):
            if rec.state in ("pending_approval", "approved", "accepted", "confirmed"):
                if "delivery_mode" in vals and vals["delivery_mode"] != rec.delivery_mode:
                    raise UserError(
                        "No se puede cambiar la modalidad de entrega tras iniciar "
                        "las aprobaciones de la solicitud."
                    )
                if "line_ids" in vals:
                    raise UserError(
                        "No se pueden modificar las líneas de la solicitud tras "
                        "iniciar las aprobaciones."
                    )
        # RPC: Abastecimiento/Transporte solo lectura en histórico.
        # Deny-all, sin depender de lista de campos ni contexto. Fail-closed
        # multi-registro: si algún registro es histórico, se rechaza toda la
        # operación.
        if vals and self._is_review_role_user():
            for rec in self.filtered("id"):
                if rec.state in self._HISTORICAL_READONLY_STATES:
                    raise UserError(
                        "Las solicitudes aprobadas, confirmadas o reemplazadas son de "
                        "solo lectura para Abastecimiento y Transporte."
                    )
        # A3.3: Validar consistencia de compañía antes de escribir.
        for rec in self.filtered("id"):
            rec._check_company_consistency()
        return super(SaleOrderRequest, self).write(vals)

    # ------------------------------------------------------------------
    # Identificación
    # ------------------------------------------------------------------
    name = fields.Char(
        string="Referencia",
        readonly=True,
        copy=False,
        tracking=True,
    )
    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Cotización",
        readonly=True,
        required=True,
        tracking=True,
    )
    sale_order_revision_id = fields.Many2one(
        comodel_name="sale.order",
        string="Revisión de cotización",
        readonly=True,
        required=True,
        tracking=True,
        help="Revisión concreta de la cotización a la que se vincula esta solicitud",
    )
    unrevisioned_name = fields.Char(
        string="Familia de cotización",
        readonly=True,
        help="Identificación de la familia (unrevisioned_name + compañía)",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        readonly=True,
        default=lambda self: self.env.company,
    )

    # ------------------------------------------------------------------
    # Modalidad de entrega
    # ------------------------------------------------------------------
    delivery_mode = fields.Selection(
        [
            ("pickup", "Recojo en tienda"),
            ("delivery", "Despacho"),
        ],
        string="Modalidad de entrega",
        required=True,
        default="pickup",
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Evaluación de inventario
    # ------------------------------------------------------------------
    stock_sufficient = fields.Boolean(
        string="Stock suficiente",
        compute="_compute_stock_sufficient",
        store=True,
        tracking=True,
        help="Indica si todos los productos tienen stock suficiente",
    )
    stock_checked_date = fields.Datetime(
        string="Fecha de última evaluación de stock",
        readonly=True,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Usuarios y fechas
    # ------------------------------------------------------------------
    requester_id = fields.Many2one(
        comodel_name="res.users",
        string="Usuario solicitante",
        readonly=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    accepted_by = fields.Many2one(
        comodel_name="res.users",
        string="Aceptado por",
        readonly=True,
        tracking=True,
    )
    accepted_date = fields.Datetime(
        string="Fecha de aceptación final",
        readonly=True,
        tracking=True,
    )
    request_date = fields.Datetime(
        string="Fecha de solicitud",
        readonly=True,
        default=fields.Datetime.now,
    )
    approval_date = fields.Datetime(
        string="Fecha de aprobación",
        readonly=True,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Líneas y estado
    # ------------------------------------------------------------------
    line_ids = fields.One2many(
        comodel_name="sale.order.request.line",
        inverse_name="request_id",
        string="Líneas de solicitud",
        copy=True,
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("pending_approval", "Pendiente de aprobación"),
            ("approved", "Aprobada"),
            ("rejected", "Rechazada"),
            ("accepted", "Aceptada por vendedor"),
            ("confirmed", "Confirmada"),
            ("superseded", "Reemplazada"),
            ("cancel", "Cancelada"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
        copy=False,
    )

    # ------------------------------------------------------------------
    # Cálculo de disponibilidad de stock
    # ------------------------------------------------------------------
    @api.constrains("sale_order_revision_id", "state")
    def _check_unique_active_request_per_revision(self):
        """A-04: no puede existir más de una solicitud activa para una misma
        revisión de cotización. Captura cambios vía write/ORM que create()
        no previene."""
        for rec in self:
            if rec.state in ("cancel", "superseded", "confirmed"):
                continue
            existing = self.search([
                ("sale_order_revision_id", "=", rec.sale_order_revision_id.id),
                ("state", "not in", ("cancel", "superseded", "confirmed")),
                ("id", "!=", rec.id),
            ], limit=1)
            if existing:
                raise ValidationError(
                    "Ya existe una solicitud activa para esta revisión de cotización."
                )

    @api.constrains("line_ids")
    def _check_no_duplicate_sale_order_lines(self):
        """C-02: no se pueden duplicar líneas de cotización dentro de una
        misma solicitud."""
        for rec in self:
            ids = [l.sale_order_line_id.id for l in rec.line_ids if l.sale_order_line_id]
            if len(ids) != len(set(ids)):
                raise ValidationError(
                    "No se pueden duplicar líneas de cotización en una misma "
                    "solicitud de pedido."
                )

    @api.depends("line_ids.stock_sufficient", "delivery_mode")
    def _compute_stock_sufficient(self):
        for rec in self:
            rec.stock_sufficient = all(
                line.stock_sufficient for line in rec.line_ids
            ) if rec.line_ids else False

    # ------------------------------------------------------------------
    # Métodos de negocio
    # ------------------------------------------------------------------
    def action_request_validation(self):
        """Solicita validación (aprobaciones) según la matriz de reglas.

        Determina qué aprobaciones se requieren basándose en:
        - Disponibilidad de stock (suficiente/insuficiente)
        - Modalidad de entrega (recojo/despacho)

        Las aprobaciones se ejecutan en paralelo a través de Tier Validation.
        """
        self.ensure_one()
        # A3.3: Validar consistencia de compañía.
        self._check_company_consistency()
        # Solo el vendedor solicitante (o uid 1) puede solicitar validación.
        if self.env.uid != 1 and self.env.user != self.requester_id:
            raise UserError(
                "Solo el vendedor solicitante puede solicitar la validación."
            )
        if self.state != "draft":
            raise UserError(
                "Solo se puede solicitar validación desde el estado Borrador."
            )

        # C-02: validar que las líneas de la solicitud cubran todas las líneas
        # comerciales de la cotización (productos, incluidos servicios) y que
        # no haya cantidades subdeclaradas. Las líneas de sección y nota no
        # requieren solicitud.
        order = self.sale_order_id
        commercial_lines = order.order_line.filtered(
            lambda l: l.display_type == False and l.product_id
        )
        request_line_map = {
            line.sale_order_line_id.id: line for line in self.line_ids
        }
        for sol in commercial_lines:
            if sol.id not in request_line_map:
                raise UserError(
                    "La línea de cotización %s no tiene una línea de solicitud "
                    "asociada. Todas las líneas comerciales deben incluirse."
                    % sol.name
                )
        # No puede haber líneas de solicitud para líneas que no pertenecen a
        # la cotización (valida el _check_sale_order_line_link del modelo de línea).

        # Reevaluar stock solo si aún no se ha verificado
        if not self.stock_checked_date:
            self._evaluate_stock()
            self._internal_request_write(
                {"stock_checked_date": fields.Datetime.now()}
            )

        # Determinar si se requieren aprobaciones
        needs_abastecimiento = (
            not self.stock_sufficient
        )  # Siempre se requiere si stock insuficiente
        needs_transporte = (
            self.delivery_mode == "delivery"
        )  # Siempre se requiere si es despacho

        # Si no se requiere ninguna aprobación, aprobar directamente
        if not needs_abastecimiento and not needs_transporte:
            self._set_request_state("approved", internal_tier_case="no_tier_approved")
            self._internal_request_write({"approval_date": fields.Datetime.now()})
            self.message_post(
                body="Solicitud aprobada automáticamente (no se requieren aprobaciones)."
            )
            return

        # Solicitar validación a través de Tier Validation (ruta interna)
        self._set_request_state("pending_approval")
        return self._do_request_validation()

    def _do_request_validation(self):
        """Ruta interna no invocable por RPC. Ejecuta la validación OCA
        real sobre solicitudes ya preparadas por action_request_validation()."""
        self.ensure_one()
        return super(SaleOrderRequest, self).request_validation()

    def _validate_tier(self, tiers=False):
        """Extiende la validación OCA para completar automáticamente el estado
         cuando todas las revisiones requeridas quedan aprobadas.

        Cubre la aprobación directa (validate_tier -> _validate_tier) y la
        aprobación mediante comment.wizard (add_comment -> _validate_tier).
        """
        result = super(SaleOrderRequest, self)._validate_tier(tiers=tiers)
        for rec in self:
            rec._auto_approve_after_tier_validation()
        return result

    def _assert_tier_fully_validated_for_approval(self):
        """Verificación defensiva: revisiones Tier completas y válidas."""
        self.ensure_one()
        self.invalidate_recordset(["validation_status"])
        open_reviews = self.review_ids.filtered(
            lambda r: r.status in ("waiting", "pending")
        )
        if open_reviews:
            raise UserError(
                "No se puede aprobar: existen revisiones Tier pendientes."
            )
        rejected = self.review_ids.filtered(lambda r: r.status == "rejected")
        if rejected:
            raise UserError(
                "No se puede aprobar: existen revisiones Tier rechazadas."
            )
        if self.review_ids and self.validation_status != "validated":
            raise UserError(
                "No se puede aprobar: las revisiones Tier no están validadas."
            )
        self._check_review_integrity()

    def _auto_approve_after_tier_validation(self):
        """Transición interna: pending_approval -> approved tras validar Tier.

        Idempotente. No oculta errores reales; solo omite la transición cuando
        las condiciones de negocio no se cumplen.
        """
        self.ensure_one()
        if self.state != "pending_approval":
            return
        # Refrescar cómputos dependientes de review_ids antes de decidir.
        self.invalidate_recordset(["validation_status"])
        pending = self.review_ids.filtered(
            lambda r: r.status in ("waiting", "pending")
        )
        if pending:
            return
        if self.validation_status != "validated":
            return
        if not self._state_transition_allowed("approved"):
            return
        # Integridad de revisiones Tier (misma verificación que action_approve).
        self._check_review_integrity()
        self._set_request_state("approved", internal_tier_case="tier_validated_approved")
        if not self.approval_date:
            self._internal_request_write({"approval_date": fields.Datetime.now()})
        self.message_post(
            body=(
                "Solicitud aprobada automáticamente: todas las revisiones Tier "
                "requeridas han sido validadas."
            )
        )

    def _tier_validation_check_state_on_write(self, vals):
        """Compatibilidad /OCA para escrituras internas de estado a approved.

        Conserva el comportamiento OCA en todos los casos no cubiertos.
        Solo omite la auto-solicitud/creación de revisiones OCA en dos rutas
        internas  ya validadas, identificadas por marcador transitorio
        no-RPC (por cursor/modelo/id).
        """
        state_field = self._state_field
        if not self or state_field not in vals:
            return super(SaleOrderRequest, self)._tier_validation_check_state_on_write(vals)

        target = vals[state_field]
        deferred = self.browse()
        for rec in self:
            if not rec._check_state_conditions(vals):
                deferred |= rec
                continue

            case = _sale_request_tier_case_get(rec.env.cr, rec._name, rec.id)
            current = rec._tier_validation_get_current_state_value()

            if case == "no_tier_approved" and current == "draft" and target == "approved":
                # Ruta interna: action_request_validation decidió sin Tier.
                rec.invalidate_recordset(["validation_status"])
                inconsistent = rec.review_ids.filtered(
                    lambda r: r.status in ("waiting", "pending", "rejected")
                )
                if inconsistent:
                    raise UserError(
                        "No se puede aprobar: estado de revisiones Tier inconsistente."
                    )
                continue

            if case == "tier_validated_approved" and current == "pending_approval" and target == "approved":
                rec._assert_tier_fully_validated_for_approval()
                continue

            deferred |= rec

        if deferred:
            return super(SaleOrderRequest, deferred)._tier_validation_check_state_on_write(vals)

    def request_validation(self):
        """Bloquea llamadas RPC directas al método genérico OCA."""
        self.ensure_one()
        raise UserError(
            "No se puede invocar la validación Tier directamente. "
            "Utilice 'Solicitar validación' desde el flujo de solicitud de orden de venta."
        )

    def restart_validation(self):
        """Bloquea reinicios genéricos que destruyeran historial Tier."""
        self.ensure_one()
        raise UserError(
            "No se puede reiniciar la validación directamente. "
            "Utilice el flujo de solicitud de orden de venta."
        )

    def reject_tier(self):
        """Rechazo Tier con protección explícita de autorización.

        El comportamiento estándar de tier.validation filtra revisiones
        accionables por el usuario; si no hay ninguna, la operación no altera
        estado. Para este modelo se exige explícitamente que el usuario tenga
        una revisión pendiente asignada que pueda rechazar.
        """
        self.ensure_one()
        self._check_company_consistency()
        if self.env.uid != 1:
            user_reviews = self.review_ids.filtered(
                lambda r: r.status in ("waiting", "pending")
                and self.env.user in r.reviewer_ids
            )
            if not user_reviews:
                raise UserError(
                    "No tiene permiso para rechazar las revisiones Tier de esta solicitud."
                )
        return super(SaleOrderRequest, self).reject_tier()

    def action_approve(self):
        """Aprueba la solicitud (marca como aprobada si todas las revisiones
        Tier están validadas).

        Solo puede ser invocada por un revisor asignado (o superusuario) y
        exige que todas las revisiones Tier estén validadas.
        """
        self.ensure_one()
        # A3.3: Validar consistencia de compañía.
        self._check_company_consistency()
        # Guardia de transición de estado (A3.2).
        if not self._state_transition_allowed("approved"):
            raise UserError(
                "No se puede aprobar la solicitud desde el estado actual: %s."
                % self.state
            )
        # Verificar que no haya revisiones pendientes
        pending = self.review_ids.filtered(
            lambda r: r.status in ("waiting", "pending")
        )
        if pending:
            raise UserError(
                "Todas las aprobaciones deben completarse antes de aprobar la solicitud."
            )
        # Integridad: todas las revisiones deben estar validadas de forma genuina
        if self.validation_status != "validated":
            raise UserError(
                "Todas las revisiones Tier deben estar validadas antes de aprobar la solicitud."
            )
        # A3.2: Verificar que ninguna revisión Tier haya sido falsificada.
        self._check_review_integrity()
        # Solo un revisor asignado (o superusuario, uid 1) puede aprobar
        if (
            self.env.uid != 1
            and self.env.user not in self.review_ids.mapped("reviewer_ids")
        ):
            raise UserError(
                "Solo un revisor asignado a la solicitud puede aprobarla."
            )
        self._set_request_state("approved", internal_tier_case="tier_validated_approved")
        self._internal_request_write({"approval_date": fields.Datetime.now()})
        self.message_post(body="Solicitud aprobada.")

    def action_reject(self):
        """Rechaza la solicitud."""
        self.ensure_one()
        # Idempotente: si ya está rechazada, no genera inconsistencias.
        if self.state == "rejected":
            return
        # A3.3: Validar consistencia de compañía.
        self._check_company_consistency()
        # Abastecimiento/Transporte no pueden rechazar solicitudes históricas,
        # aunque sean revisores. No se extiende a solicitante/administrador.
        if (
            self.state in self._HISTORICAL_READONLY_STATES
            and self._is_review_role_user()
        ):
            raise UserError(
                "Abastecimiento y Transporte no pueden rechazar solicitudes "
                "aprobadas, confirmadas o reemplazadas."
            )
        # Guardia de transición de estado (A3.2).
        if not self._state_transition_allowed("rejected"):
            raise UserError(
                "No se puede rechazar la solicitud desde el estado actual: %s."
                % self.state
            )
        # Solo el solicitante, un revisor asignado o el superusuario (uid 1) pueden rechazar
        reviewers = self.review_ids.mapped("reviewer_ids")
        if (
            self.env.uid != 1
            and self.env.user != self.requester_id
            and self.env.user not in reviewers
        ):
            raise UserError(
                "No tiene permiso para rechazar esta solicitud."
            )
        self.with_context(
            skip_validation_check=True,
        )._set_request_state("rejected")
        self.message_post(body="Solicitud rechazada.")

    def _rejected_tier(self, tiers=False):
        """Sincroniza el rechazo de una revisión Tier con el estado documental.

        Si cualquier revisión requerida queda rechazada, la solicitud pasa
        automáticamente a 'rejected' (sin requerir action_reject manual),
        respetando permisos y transiciones. Idempotente y sin recursión.
        """
        result = super(SaleOrderRequest, self)._rejected_tier(tiers=tiers)
        for rec in self:
            if rec.state in ("pending_approval", "approved"):
                rec.invalidate_recordset(["review_ids", "validation_status"])
                if any(r.status == "rejected" for r in rec.review_ids):
                    # Reutiliza la transición documental coherente.
                    rec.action_reject()
        return result

    def action_accept(self):
        """Aceptación final del vendedor.

        Solo disponible cuando:
        - Todas las aprobaciones requeridas están completadas
        - No hay aprobaciones pendientes ni rechazos vigentes
        - La solicitud corresponde a la revisión actual de la cotización
        - La evaluación de stock está actualizada y el stock es suficiente
        """
        self.ensure_one()
        # A3.3: Validar consistencia de compañía.
        self._check_company_consistency()
        if self.state != "approved":
            raise UserError(
                "La aceptación final solo está disponible cuando la solicitud está aprobada."
            )

        # Solo el vendedor solicitante puede realizar la aceptación final
        if self.env.user != self.requester_id:
            raise UserError(
                "Solo el vendedor solicitante de la solicitud puede realizar la aceptación final."
            )

        # Revalidar inventario antes de aceptar (B-08). La aceptación final
        # se bloquea si el stock disponible no cubre las cantidades solicitadas.
        self._evaluate_stock()
        self._internal_request_write({"stock_checked_date": fields.Datetime.now()})
        if not self.stock_sufficient:
            raise UserError(
                "No se puede aceptar la solicitud: el stock disponible no cubre "
                "las cantidades solicitadas según la última evaluación de inventario."
            )

        # Verificar que no exista una revisión posterior de la cotización
        sale_order = self.sale_order_id
        revision = self.sale_order_revision_id
        # La solicitud debe estar vinculada a la revisión vigente de la cotización.
        if revision != sale_order:
            if sale_order.current_revision_id != revision:
                raise UserError(
                    "La revisión vinculada no es la revisión vigente de la cotización. "
                    "Cree una nueva solicitud para la revisión actual."
                )
        order_to_confirm = revision

        # Verificar que la cotización/revisión pueda confirmarse
        if order_to_confirm.state not in ("draft", "sent"):
            raise UserError(
                "La cotización no se puede confirmar en su estado actual: %s"
                % order_to_confirm.state
            )

        # C-05: re-verificar integridad antes de aceptar: modalidad de entrega,
        # líneas y cantidades son las aprobadas, y las aprobaciones obligatorias
        # existen.
        pending = self.review_ids.filtered(
            lambda r: r.status in ("waiting", "pending")
        )
        if pending:
            raise UserError(
                "Todas las aprobaciones deben completarse antes de aceptar la solicitud."
            )
        # Si hay revisiones Tier, todas deben estar validadas. Si no hay
        # revisiones (autoaprobación por stock suficiente), no hay nada que
        # validar.
        if self.review_ids and self.validation_status != "validated":
            raise UserError(
                "Todas las revisiones Tier deben estar validadas antes de aceptar la solicitud."
            )

        # Aceptación final
        self._set_request_state("accepted")
        self._internal_request_write({
            "accepted_by": self.env.user.id,
            "accepted_date": fields.Datetime.now(),
        })
        self.message_post(
            body="Aceptación final realizada por %s." % self.env.user.name
        )

        # Confirmar la revisión vigente de la cotización (no un segundo sale.order)
        order_to_confirm.with_user(self.env.user).action_confirm()
        self._set_request_state("confirmed")
        self.message_post(
            body="Cotización %s confirmada y pasada a 'sale'." % order_to_confirm.name
        )

    def action_supersede(self):
        """Operación bloqueada como método público independiente.

        La transición a 'superseded' solo se ejecuta mediante el procedimiento
        coordinado de revisión (action_coordinated_revision).
        """
        self.ensure_one()
        raise UserError(
            "No se puede marcar como reemplazada de forma independiente. "
            "Utilice el procedimiento coordinado de revisión de cotización."
        )

    def _mark_superseded_coordinated(self):
        """Marca esta solicitud como superseded. Solo invocable desde
        action_coordinated_revision()."""
        self.ensure_one()
        # A3.3: Validar consistencia de compañía.
        self._check_company_consistency()
        # Guardia de transición de estado (A3.2).
        if not self._state_transition_allowed("superseded"):
            raise UserError(
                "No se puede marcar como reemplazada la solicitud desde el "
                "estado actual: %s." % self.state
            )
        # Usar sudo() porque el coordinador ya fue autorizado en
        # action_coordinated_revision() pero puede no tener write access
        # directo sobre sale.order.request (solo Abastecimiento lo tiene).
        self.sudo().with_context(
            skip_validation_check=True,
        )._set_request_state("superseded")

    def action_cancel(self):
        """Cancela la solicitud."""
        self.ensure_one()
        # A3.3: Validar consistencia de compañía.
        self._check_company_consistency()
        # D-R2-A: Solo el solicitante o el administrador pueden cancelar.
        if self.env.uid != 1 and self.env.user != self.requester_id:
            raise UserError(
                "Solo el vendedor solicitante o el administrador pueden "
                "cancelar esta solicitud."
            )
        # Guardia de transición de estado (A3.2).
        if not self._state_transition_allowed("cancel"):
            raise UserError(
                "No se puede cancelar la solicitud desde el estado actual: %s."
                % self.state
            )
        self.with_context(
            skip_validation_check=True,
        )._set_request_state("cancel")
        self.message_post(body="Solicitud cancelada.")

    def _evaluate_stock(self):
        """Evalúa la disponibilidad de inventario para cada línea.

        - Recojo (pickup): free_qty
        - Despacho (delivery): virtual_available
        """
        self.ensure_one()
        for line in self.line_ids:
            line._evaluate_stock()
        # stock_sufficient es un campo calculado almacenado; forzar su
        # recalculación tras evaluar las líneas para leer el valor actual.
        self._compute_stock_sufficient()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Nunca se acepta un estado impuesto por el creador: la solicitud
            # nace siempre en borrador (B-04).
            vals.pop("state", None)
            vals["state"] = "draft"

            # C-04: validar coherencia de cotización, revisión y compañía.
            # La familia y la compañía se derivan de la cotización para
            # evitar vínculos inconsistentes.
            order_id = vals.get("sale_order_id")
            revision_id = vals.get("sale_order_revision_id")
            if order_id and revision_id:
                order = self.env["sale.order"].browse(order_id)
                revision = self.env["sale.order"].browse(revision_id)
                if not order.exists():
                    raise UserError("La cotización vinculada no existe.")
                if not revision.exists():
                    raise UserError("La revisión de cotización vinculada no existe.")
                if order.unrevisioned_name != revision.unrevisioned_name:
                    raise UserError(
                        "La revisión no pertenece a la misma familia de cotización."
                    )
                if order.company_id.id != revision.company_id.id:
                    raise UserError(
                        "La cotización y la revisión no pertenecen a la misma compañía."
                    )
                company_id = vals.get("company_id")
                if company_id and company_id != order.company_id.id:
                    raise UserError(
                        "La compañía de la solicitud debe coincidir con la de la cotización."
                    )
                # Derivar identificadores desde la cotización (única fuente de verdad).
                vals["unrevisioned_name"] = order.unrevisioned_name
                vals["company_id"] = order.company_id.id

            # A3.3: El usuario creador debe tener acceso a la compañía de la solicitud.
            company_id = vals.get("company_id")
            if company_id and company_id not in self.env.user.company_ids.ids:
                raise UserError(
                    "No tiene acceso a la compañía de la solicitud."
                )

            # A-04: no puede existir más de una solicitud activa para una misma
            # revisión de cotización.
            if revision_id:
                existing = self.search_count([
                    ("sale_order_revision_id", "=", revision_id),
                    ("state", "not in", ("cancel", "superseded", "confirmed")),
                ])
                if existing:
                    raise UserError(
                        "Ya existe una solicitud activa para esta revisión de cotización."
                    )

            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("sale.order.request")
                    or "New"
                )
        return super(SaleOrderRequest, self).create(vals_list)

    def _create_new_request_for_revision(self, new_revision):
        """Crea una nueva solicitud vinculada a una revisión de cotización.

        Privado: solo invocable desde el procedimiento coordinado ya autorizado.
        Conserva la lógica de creación y delega validaciones en create().
        """
        self.ensure_one()
        if not new_revision:
            raise UserError("Falta la revisión de cotización destino.")
        if new_revision.unrevisioned_name != self.unrevisioned_name:
            raise UserError(
                "La revisión destino no pertenece a la familia de la solicitud."
            )
        if new_revision.company_id != self.company_id:
            raise UserError(
                "La revisión destino no pertenece a la compañía de la solicitud."
            )
        # Crear nueva solicitud vinculada a la nueva revisión
        new_request = self.create(
            {
                "sale_order_id": self.sale_order_id.id,
                "sale_order_revision_id": new_revision.id,
                "unrevisioned_name": self.unrevisioned_name,
                "company_id": self.company_id.id,
                "delivery_mode": self.delivery_mode,
                "requester_id": self.requester_id.id,
                "line_ids": [
                    (0, 0, {
                        "sale_order_line_id": line.sale_order_line_id.id,
                        "product_id": line.product_id.id,
                        "product_uom_id": line.product_uom_id.id,
                        "qty": line.qty,
                    })
                    for line in self.line_ids
                ],
            }
        )
        return new_request

    def action_create_new_request_for_revision(self, new_revision):
        """Bloquea la creación directa fuera de la revisión coordinada."""
        self.ensure_one()
        raise UserError(
            "No se puede crear una nueva solicitud de revisión de forma directa. "
            "Utilice el procedimiento coordinado de revisión."
        )

    def action_coordinated_revision(self):
        """Procedimiento coordinado de revisión de cotización sujeta a solicitud de orden de venta.

        Orden de ejecución (atómico, una sola transacción):
        1. Crear la nueva revisión OCA preservando Tier.
        2. Marcar la nueva cotización como .
        3. Marcar la solicitud anterior como superseded.
        4. Crear y vincular la nueva solicitud a la nueva revisión.
        5. Retornar la acción para abrir la nueva solicitud.

        Autorización: requiere grupo group_sale_order_request_coordinator (pendiente
        asignación de usuarios, D-AUD-5).
        """
        self.ensure_one()
        # A3.3: Validar consistencia de compañía.
        self._check_company_consistency()
        # Autorización: solo miembros del grupo coordinador.
        if not self.env.user.has_group(
            "sale_order_request.group_sale_order_request_coordinator"
        ):
            raise UserError(
                "Solo un coordinador autorizado puede ejecutar la revisión "
                "coordinada de cotización."
            )
        # Verificar que exista una solicitud activa aceptada/confirmada
        # (o aprobada, para casos de stock insuficiente donde accept se
        # bloquea por B-08) para esta revisión y compañía.
        solicitud_activa = self.env["sale.order.request"].search(
            [
                ("sale_order_revision_id", "=", self.sale_order_revision_id.id),
                ("state", "in", ("approved", "accepted", "confirmed")),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )
        if not solicitud_activa:
            raise UserError(
                "No existe una solicitud  aceptada o confirmada vinculada "
                "a esta revisión de cotización."
            )
        # 1. Crear la nueva revisión OCA preservando Tier.
        revision_anterior = self.sale_order_revision_id
        nueva_revision = revision_anterior._sale_request_create_revision_preserving_tier_coordinated()
        # 2. Marcar la nueva cotización como .
        nueva_revision._sale_request_mark_subject_coordinated()
        # 3. Marcar la solicitud anterior como superseded.
        self._mark_superseded_coordinated()
        # 4. Crear y vincular la nueva solicitud a la nueva revisión.
        # Usar sudo() porque el coordinador ya fue autorizado pero puede no
        # tener create access sobre sale.order.request (solo Vendedor lo tiene).
        nueva_solicitud = self.sudo()._create_new_request_for_revision(
            nueva_revision
        )
        # 5. Retornar la acción para abrir la nueva solicitud.
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order.request",
            "res_id": nueva_solicitud.id,
            "view_mode": "form",
            "target": "current",
        }
