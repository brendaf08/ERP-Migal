# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""
Extensión de sale.order para la protección de confirmación del flujo de solicitud de orden de venta.

Impide confirmar una cotización sujeta al proceso de solicitud de orden de venta cuando no exista una
Solicitud de Pedido válida y aceptada vinculada a la revisión que se confirma,
y evita que el estado pase directamente a 'sale' sin pasar por
action_confirm() (creación o escritura directa de estado).

La protección se aplica en servidor y no depende de botones ni vistas.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # ------------------------------------------------------------------
    # Identificación de cotizaciones sujetas al flujo de solicitud de orden de venta (Fase A3.1 - C-01)
    # ------------------------------------------------------------------
    sale_request_subject = fields.Boolean(
        string="Sujeto a flujo de solicitud de orden de venta",
        default=False,
        readonly=True,
        copy=False,
        tracking=True,
        help="Indica si la cotización pertenece al flujo de Solicitud de Pedido "
             ". La pertenencia se asigna automáticamente cuando "
             "sale_request_applicable=True, o mediante action_mark_sale_request_subject(). "
             "No puede desasignarse, para evitar la evasión de la protección "
             "de confirmación.",
    )
    sale_request_applicable = fields.Boolean(
        string="Aplicable a flujo de solicitud de orden de venta",
        default=False,
        copy=False,
        tracking=True,
        help="Indica si la cotización debe ser gestionada mediante el flujo "
             ". Cuando se establece a True, el sistema marca automáticamente "
             "sale_request_subject=True y activa la protección de confirmación. Este "
             "campo no puede modificarse una vez la cotización está sujeta a .",
    )

    # ------------------------------------------------------------------
    # Protección de confirmación directa (Fase A - A1)
    # ------------------------------------------------------------------
    def _is_sale_request_subject(self):
        """Indica si la orden pertenece al flujo de solicitud de orden de venta según indicador
        explícito y protegido, no según la existencia de una solicitud."""
        self.ensure_one()
        return bool(self.sale_request_subject)

    def action_mark_sale_request_subject(self):
        """Marca la cotización como sujeta al flujo de solicitud de orden de venta.

        Solo puede asignarse una vez. No puede desasignarse para evitar
        la evasión de la protección de confirmación. Es el único punto de
        entrada controlado para establecer este indicador.

        Solo usuarios del grupo vendedor de solicitudes de orden de venta pueden ejecutar esta acción.
        """
        self.ensure_one()
        if not self.env.user.has_group(
            "sale_order_request.group_sale_order_request_salesperson"
        ):
            raise UserError(
                "Solo un vendedor de solicitudes de orden de venta puede marcar una cotización como sujeta "
                "al flujo de solicitud de orden de venta."
            )
        if self.sale_request_subject:
            raise UserError(
                "La cotización ya está sujeta al flujo de solicitud de orden de venta."
            )
        # Escritura vía ORM (super().write()) para respetar la caché y
        # recomputaciones de Odoo. Este super() salta el override de write()
        # de esta clase y va directamente al padre (sale.order), por lo que
        # el bloqueo de sale_request_applicable/sale_request_subject no se aplica aquí.
        # La autorización ya se verificó arriba mediante la comprobación de
        # grupo de vendedor de solicitudes.
        super(SaleOrder, self).write({"sale_request_subject": True, "sale_request_applicable": True})

    def action_create_sale_order_request_from_quotation(self):
        """Crea una Solicitud de Pedido vinculada a esta cotización.

        La solicitud queda en borrador y vinculada a la revisión vigente de la
        cotización. No crea una segunda sale.order ni modifica el estado
        comercial de la cotización.

        Solo usuarios del grupo vendedor de solicitudes de orden de venta pueden ejecutar esta acción.
        """
        self.ensure_one()
        # Verificar que la cotización esté sujeta al flujo de solicitud de orden de venta.
        if not self.sale_request_subject or not self.sale_request_applicable:
            raise UserError(
                "La cotización no está marcada como sujeta al flujo de solicitud de orden de venta."
            )
        # Solo vendedor de solicitudes de orden de venta puede crear solicitudes.
        if not self.env.user.has_group("sale_order_request.group_sale_order_request_salesperson"):
            raise UserError(
                "Solo un vendedor de solicitudes de orden de venta puede crear solicitudes de pedido."
            )
        # Verificar permiso de lectura sobre la cotización concreta (API vigente Odoo 19).
        self.check_access('read')
        # Solo desde cotización en Borrador o Enviado.
        if self.state not in ("draft", "sent"):
            raise UserError(
                "Solo se puede crear una solicitud desde cotización en Borrador "
                "o Enviado."
            )
        # Determinar la revisión vigente: si existe current_revision_id, esa es
        # la revisión vigente; si no, la cotización misma es la revisión vigente.
        revision = self.current_revision_id or self
        # Verificar que no exista ya una solicitud activa para esta revisión.
        existing = self.env["sale.order.request"].search_count([
            ("sale_order_revision_id", "=", revision.id),
            ("state", "not in", ("cancel", "superseded", "confirmed")),
        ])
        if existing:
            raise UserError(
                "Ya existe una solicitud activa para esta revisión de cotización."
            )
        # Construir líneas de solicitud desde las líneas de cotización.
        line_vals = []
        for line in self.order_line:
            if line.display_type or not line.product_id:
                continue
            line_vals.append((0, 0, {
                "sale_order_line_id": line.id,
                "product_id": line.product_id.id,
                "product_uom_id": line.product_uom_id.id,
                "qty": line.product_uom_qty,
            }))
        # Crear la solicitud mediante el modelo sale.order.request, que aplica
        # todas sus validaciones (familia, compañía, A-04, ACL, etc.).
        request = self.env["sale.order.request"].create({
            "sale_order_id": self.id,
            "sale_order_revision_id": revision.id,
            "unrevisioned_name": self.unrevisioned_name,
            "company_id": self.company_id.id,
            "delivery_mode": "pickup",
            "requester_id": self.env.user.id,
            "line_ids": line_vals,
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order.request",
            "res_id": request.id,
            "view_mode": "form",
            "target": "current",
        }

    def _sale_request_accepted_for_revision(self):
        """Solicitud  aceptada/confirmada vinculada a esta revisión.

        Se filtra también por compañía para impedir que una solicitud de otra
        compañía valide la confirmación de esta orden.
        """
        self.ensure_one()
        return self.env["sale.order.request"].search(
            [
                ("sale_order_revision_id", "=", self.id),
                ("state", "in", ("accepted", "confirmed")),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )

    def _check_sale_request_confirmation(self):
        """Impide la confirmación si la orden es  y no hay una
        solicitud aceptada para la revisión que se confirma."""
        self.ensure_one()
        # Una orden que ya tiene una revisión posterior está obsoleta:
        # no debe poder confirmarse (incluso si existe una solicitud
        # aceptada vinculada a ella desde un ciclo anterior).
        if self.current_revision_id:
            raise UserError(
                "No se puede confirmar esta revisión de cotización: existe una "
                "revisión posterior vigente."
            )
        if self._is_sale_request_subject() and not self._sale_request_accepted_for_revision():
            raise UserError(
                "No se puede confirmar la cotización sin una Solicitud de orden de venta "
                "válida y aceptada vinculada a esta revisión."
            )

    @api.model_create_multi
    def create(self, vals_list):
        # No se permite crear una orden ya confirmada (state='sale'). La
        # confirmación solo debe alcanzarse mediante action_confirm() tras
        # completar el flujo de solicitud de orden de venta cuando la orden es sujeta al mismo.
        # No se permite crear una orden ya marcada como sujeta a : el
        # indicador solo se asigna mediante action_mark_sale_request_subject().
        # La asignación directa de sale_request_applicable/sale_request_subject en create()
        # queda bloqueada para impedir el marcaje  fuera de rutas
        # autorizadas.
        for vals in vals_list:
            if vals.get("state") == "sale":
                raise UserError(
                    "No se puede crear una orden de venta directamente en "
                    "estado confirmado."
                )
            # Bloquear asignación directa de indicadores  en creación.
            vals.pop("sale_request_applicable", None)
            vals.pop("sale_request_subject", None)
        # Crear todas las órdenes de una vez.
        orders = super().create(vals_list)
        return orders

    def action_confirm(self):
        for order in self:
            order._check_sale_request_confirmation()
        return super().action_confirm()

    def write(self, vals):
        # Bloquear escritura directa de sale_request_applicable y sale_request_subject por
        # RPC. Los métodos privados autorizados (
        # action_mark_sale_request_subject y el procedimiento coordinado) establecen
        # estos campos llamando a super().write() directamente, lo que salta
        # este override y va al padre (sale.order de OCA/Odoo core).
        if "sale_request_applicable" in vals:
            raise UserError(
                "No se puede modificar el campo sale_request_applicable directamente. "
                "Utilice los métodos de flujo autorizados."
            )
        if "sale_request_subject" in vals:
            raise UserError(
                "No se puede modificar el campo sale_request_subject directamente. "
                "Utilice los métodos de flujo autorizados."
            )
        # Bloquear escritura directa de state='sale' por ORM/RPC cuando la
        # orden es  y no cuenta con solicitud aceptada.
        if "state" in vals and vals["state"] == "sale":
            for order in self:
                if order._is_sale_request_subject() and not order._sale_request_accepted_for_revision():
                    raise UserError(
                        "No se puede pasar la cotización a 'sale' directamente: "
                        "requiere una Solicitud de orden de venta aceptada."
                    )
        # No se permite cambiar la familia (unrevisioned_name) de una orden
        # que ya participa en el flujo de solicitud de orden de venta, pues ello permitiría evadir la
        # protección apuntando a una familia sin solicitud aceptada.
        if "unrevisioned_name" in vals:
            for order in self:
                if order.id and order._is_sale_request_subject():
                    current = order.unrevisioned_name or False
                    new_val = vals["unrevisioned_name"] or False
                    if new_val != current:
                        raise UserError(
                            "No se puede cambiar la familia de una cotización "
                            "que ya tiene una Solicitud de orden de venta."
                        )
        return super().write(vals)

    # ------------------------------------------------------------------
    # Protección de duplicación (copy) y marcado  coordinado
    # ------------------------------------------------------------------
    def copy(self, default=None):
        """Impide que una copia de cotización sujeta a solicitud de orden de venta herede o introduzca
        los indicadores sale_request_applicable/sale_request_subject fuera de una ruta
        autorizada."""
        default = default or {}
        default.pop("sale_request_applicable", None)
        default.pop("sale_request_subject", None)
        return super(SaleOrder, self).copy(default=default)

    def _sale_request_mark_subject_coordinated(self):
        """Establece sale_request_subject=True y sale_request_applicable=True en la nueva
        cotización durante el procedimiento coordinado de revisión.

        Método privado (nombre con guion bajo): no invocable por RPC.
        La autorización se verifica en action_coordinated_revision() antes
        de invocarlo. Establece ambos campos de forma coherente vía SQL
        directa para evitar la restricción de write() que protege estos
        campos.
        """
        self.ensure_one()
        # Escritura vía ORM (super().write()) para respetar la caché y
        # recomputaciones de Odoo. Este super() salta el override de write()
        # de esta clase y va directamente al padre (sale.order), por lo que
        # el bloqueo de sale_request_applicable/sale_request_subject no se aplica aquí.
        # La autorización se verifica en el llamante público
        # (action_coordinated_revision) antes de invocar este método.
        super(SaleOrder, self).write({"sale_request_subject": True, "sale_request_applicable": True})

    # ------------------------------------------------------------------
    # Protección R-1 en sale.order: bloquear Request/Restart genéricos
    # para cotizaciones sujetas a solicitud de orden de venta
    # ------------------------------------------------------------------
    def request_validation(self):
        """Bloquea la validación Tier genérica en cotizaciones sujetas a solicitud de orden de venta."""
        self.ensure_one()
        if self.sale_request_subject:
            raise UserError(
                "Validación Tier genérica no permitida en cotización sujeta a solicitud de orden de venta. "
                "Utilice el flujo de Solicitud de Pedido."
            )
        return super(SaleOrder, self).request_validation()

    def restart_validation(self):
        """Bloquea el reinicio genérico de validación Tier en cotizaciones
        ."""
        self.ensure_one()
        if self.sale_request_subject:
            raise UserError(
                "Reinicio de validación Tier genérico no permitido en "
                "cotización sujeta a solicitud de orden de venta."
            )
        return super(SaleOrder, self).restart_validation()

    # ------------------------------------------------------------------
    # Protección D-AUD-4b: bloquear creación genérica de revisiones en
    # cotizaciones sujetas a solicitud de orden de venta
    # ------------------------------------------------------------------
    def create_revision(self):
        """Bloquea la creación directa de revisiones sobre cotizaciones sujetas a solicitud de orden de venta.
        Las revisiones  solo se crean mediante el procedimiento
        coordinado (_sale_request_create_revision_preserving_tier_coordinated)."""
        self.ensure_one()
        if self.sale_request_subject:
            raise UserError(
                "No se puede crear una revisión directamente sobre una "
                "cotización sujeta a solicitud de orden de venta. Utilice el procedimiento de revisión "
                "coordinada."
            )
        return super(SaleOrder, self).create_revision()

    def create_revision_preserving_tier(self):
        """Bloquea la creación directa de revisiones preservando Tier sobre
        cotizaciones sujetas a solicitud de orden de venta."""
        self.ensure_one()
        if self.sale_request_subject:
            raise UserError(
                "No se puede crear una revisión preservando Tier directamente "
                "sobre una cotización sujeta a solicitud de orden de venta. Utilice el procedimiento de "
                "revisión coordinada."
            )
        return super(SaleOrder, self).create_revision_preserving_tier()

    def _sale_request_create_revision_preserving_tier_coordinated(self):
        """Ruta interna del procedimiento coordinado: crea la revisión OCA
        preservando Tier saltando el bloqueo público de create_revision().

        Llama directamente a copy_revision_with_context() de base.revision
        (método subyacente que create_revision() usa internamente), pasando
        el contexto preserve_tier_reviews_on_revision para evitar la eliminación
        de revisiones Tier durante el archivado de la orden anterior.

        Usa sudo() porque el coordinador ya ha sido autorizado en
        action_coordinated_revision() pero puede no tener lectura directa
        sobre el registro sale.origin. No es invocable por RPC (nombre con
        guion bajo).
        """
        self.ensure_one()
        new_revision = self.sudo().with_context(
            skip_validation_check=True,
            preserve_tier_reviews_on_revision=True,
        ).copy_revision_with_context()
        return new_revision
