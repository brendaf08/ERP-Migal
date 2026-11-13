import base64
import json
import re
from urllib.parse import quote
from urllib.request import urlopen

from odoo import fields, models
from odoo.exceptions import AccessError
from odoo.tools import format_amount, format_date

E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")


def normalizar_telefono(raw):
    """Quita espacios, guiones, puntos y paréntesis; convierte 00 inicial en +."""
    if not raw:
        return ""
    tel = re.sub(r"[\s\-\.\(\)]", "", raw)
    if tel.startswith("00"):
        tel = "+" + tel[2:]
    return tel


class MigalAgenteToolWhatsapp(models.AbstractModel):
    """Herramientas preparar_whatsapp_cotizacion y registrar_envio_whatsapp."""

    _name = "migal.agente.tool.whatsapp"
    _inherit = "migal.agente.tool.base"
    _description = "Herramienta WhatsApp del Agente MIGAL"

    # ------------------------------------------------------------------
    def _evaluar_envio(self, ref, requiere_telefono=True):
        """Controles comunes. Devuelve (order, controles, bloqueos, telefono)."""
        order, vigente, error = self._buscar_cotizacion(ref)
        if error:
            return order, [self._control("Cotización localizada", False, error)], [error], ""
        controles, bloqueos = [], []

        def add(nombre, ok, detalle):
            controles.append(self._control(nombre, ok, detalle))
            if not ok:
                bloqueos.append(detalle)

        add("Cotización localizada", True, order.name)
        add("Revisión vigente", order == vigente,
            "Es la revisión vigente." if order == vigente else
            "%s fue reemplazada; la revisión vigente es %s. Envíe esa versión." % (order.name, vigente.name))
        add("Estado de la cotización", order.state in ("draft", "sent"),
            "Cotización en estado %s." % dict(order._fields["state"]._description_selection(self.env)).get(order.state)
            if order.state in ("draft", "sent") else
            "La cotización está en estado «%s»; solo se envían cotizaciones en borrador o enviadas."
            % dict(order._fields["state"]._description_selection(self.env)).get(order.state))
        status = order.validation_status if "validation_status" in order._fields else "no"
        add("Autorizaciones", status not in ("waiting", "pending", "rejected"),
            "Sin aprobaciones pendientes." if status not in ("waiting", "pending", "rejected") else
            ("Tiene una autorización pendiente: no envíe al cliente el precio o la condición en revisión."
             if status in ("waiting", "pending") else "Una autorización fue rechazada: ajuste la propuesta antes de enviarla."))
        hoy = self._hoy()
        vencida = bool(order.validity_date and order.validity_date < hoy)
        add("Vigencia", not vencida,
            "Válida hasta %s." % format_date(self.env, order.validity_date) if order.validity_date and not vencida else
            ("Sin fecha de vencimiento registrada." if not order.validity_date else
             "La cotización venció el %s; genere una nueva revisión." % format_date(self.env, order.validity_date)))
        partner = order.partner_id
        telefono = normalizar_telefono(partner.phone)
        if not requiere_telefono:
            return order, controles, bloqueos, telefono
        add("Teléfono internacional", bool(E164_RE.match(telefono)),
            "Número %s de %s." % (telefono, partner.display_name) if E164_RE.match(telefono) else
            "El contacto %s no tiene un número válido en formato internacional (ej. +51 987 654 321). "
            "Corrija el teléfono del contacto." % partner.display_name)
        return order, controles, bloqueos, telefono

    def _tunel_activo(self):
        """URL pública del publicador temporal (herramientas/publicar_cotizaciones.py), si está corriendo.

        Se consulta su estado en 127.0.0.1 (solo local, timeout corto). Si no responde, no hay túnel.
        """
        puerto = self.env["ir.config_parameter"].sudo().get_param("migal_agente.puerto_publicador", "8090")
        try:
            with urlopen("http://127.0.0.1:%s/estado" % int(puerto), timeout=1.5) as resp:
                url = (json.loads(resp.read(4096) or b"{}").get("url_publica") or "")
        except (OSError, ValueError):
            return ""
        return url.rstrip("/") if re.match(r"^https://[a-z0-9-]+\.trycloudflare\.com$", url) else ""

    def _base_publica(self, order):
        """Dirección con la que el cliente llega a la cotización: túnel activo > URL pública > web.base.url."""
        return (self._tunel_activo() or self.env["ir.config_parameter"].sudo().get_param("migal_agente.url_publica")
                or order.get_base_url()).rstrip("/")

    @staticmethod
    def es_local(url):
        return bool(re.search(r"//(localhost|127\.|\[::1\])", url or ""))

    def _url_digital(self, order, asegurar_token=False):
        """Versión digital de solo lectura: el PDF de la cotización en el portal (sin botones de aceptar,
        firmar ni pagar, para no saltarse el flujo de Solicitud de Orden de Venta - RN-006)."""
        token = order.access_token
        if not token and asegurar_token:
            token = order.sudo()._portal_ensure_token()
        if not token:
            return ""
        return "%s%s?access_token=%s&report_type=pdf" % (self._base_publica(order), order.access_url, token)

    def _url_portal(self, order):
        # En el mensaje de WhatsApp solo se incluye si el cliente puede abrirlo (no localhost).
        # Tampoco la dirección temporal del túnel: el mensaje queda en el chat y el enlace dejaría de abrir.
        url = self._url_digital(order)
        return "" if self.es_local(url) or ".trycloudflare.com" in url else url

    def _mensaje(self, order):
        partner = order.partner_id
        partes = [
            "Hola %s, le saluda %s de Ferre & Inversiones MIGAL." % (partner.name, self.env.user.name),
            "Le envío la cotización %s por un total de %s." % (
                order.name, format_amount(self.env, order.amount_total, order.currency_id)),
        ]
        if order.validity_date:
            partes.append("La cotización es válida hasta el %s." % format_date(self.env, order.validity_date))
        partes.append("Le adjunto el PDF con el detalle.")
        url = self._url_portal(order)
        if url:
            partes.append("También puede revisarla aquí: %s" % url)
        partes.append("Quedo atento a su conformidad o a cualquier consulta.")
        return " ".join(partes)

    @staticmethod
    def enlace_wa(telefono, mensaje):
        return "https://wa.me/%s?text=%s" % (telefono.lstrip("+"), quote(mensaje or ""))

    # ------------------------------------------------------------------
    def preparar(self, cotizacion):
        order, controles, bloqueos, telefono = self._evaluar_envio(cotizacion)
        if bloqueos:
            return self._resultado(
                False, "bloqueado", "WhatsApp: envío no habilitado",
                "No se puede preparar el envío de %s: %s" % (order.name or cotizacion, " ".join(bloqueos)),
                controles=controles, reglas=["CT-002"], res=order or None,
                datos={"cotizacion": order.name or cotizacion})
        mensaje = self._mensaje(order)
        enlace = self.enlace_wa(telefono, mensaje)
        avisos = []
        if not order.amount_total:
            avisos.append("La cotización tiene total 0,00: revise precios antes de enviarla.")
        if not self._url_portal(order):
            avisos.append("El mensaje no incluye enlace al portal (Odoo no tiene un dominio público): el cliente recibe el PDF adjunto.")
        return self._resultado(
            True, "listo", "WhatsApp listo para %s" % order.name,
            "Enlace preparado para %s (%s). Revise el mensaje, adjunte el PDF y confirme el envío desde "
            "WhatsApp. Después pídame «registrar envío %s»." % (order.partner_id.display_name, telefono, order.name),
            controles=controles, avisos=avisos, res=order,
            datos={
                "cotizacion": order.name, "revision": order.revision_number, "cliente": order.partner_id.display_name,
                "telefono": telefono, "total": order.amount_total, "moneda": order.currency_id.name,
                "mensaje": mensaje, "enlace_whatsapp": enlace,
            })

    def registrar(self, cotizacion, mensaje=None):
        order, controles, bloqueos, telefono = self._evaluar_envio(cotizacion)
        if bloqueos:
            return self._resultado(
                False, "bloqueado", "WhatsApp: no se registró el envío",
                "No registré el envío de %s: %s" % (order.name or cotizacion, " ".join(bloqueos)),
                controles=controles, reglas=["CT-002"], res=order or None,
                datos={"cotizacion": order.name or cotizacion})
        envio = self.env["migal.agente.whatsapp.envio"].create({
            "order_id": order.id,
            "cotizacion": order.name,
            "revision_number": order.revision_number,
            "partner_id": order.partner_id.id,
            "telefono": telefono,
            "amount_total": order.amount_total,
            "currency_id": order.currency_id.id,
            "mensaje": mensaje or self._mensaje(order),
        })
        nota = "Agente MIGAL: %s registró el envío por WhatsApp de %s (revisión %s) a %s (%s)." % (
            self.env.user.name, order.name, order.revision_number, order.partner_id.display_name, telefono)
        try:
            order.message_post(body=nota, message_type="comment", subtype_xmlid="mail.mt_note")
        except AccessError:
            order.sudo().message_post(body=nota, author_id=self.env.user.partner_id.id,
                                      message_type="comment", subtype_xmlid="mail.mt_note")
        return self._resultado(
            True, "registrado", "Envío registrado",
            "Registré el envío de %s a %s (%s) el %s." % (
                order.name, order.partner_id.display_name, telefono,
                fields.Datetime.context_timestamp(self, envio.fecha).strftime("%d/%m/%Y %H:%M")),
            controles=controles, res=order,
            datos={"envio_id": envio.id, "cotizacion": order.name, "revision": order.revision_number,
                   "destinatario": order.partner_id.display_name, "telefono": telefono})

    def _alcance(self, url):
        """Controles y avisos según desde dónde podrá abrir el cliente el enlace. Devuelve (controles, avisos, local)."""
        controles, avisos = [], []
        local = self.es_local(url)
        if ".trycloudflare.com" in url:
            controles.append(self._control(
                "Publicación temporal activa", True,
                "Se abre desde cualquier red (datos móviles incluidos) mientras el publicador esté abierto."))
        elif local:
            avisos.append("No hay publicación activa y Odoo está en una dirección local: el celular del cliente no "
                          "podrá abrir el QR. Inicie herramientas\\publicar_cotizaciones.py.")
        elif re.search(r"//(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)", url):
            avisos.append("El QR usa una dirección de la red local: solo abre en celulares conectados al mismo Wi-Fi. "
                          "Para cualquier red, inicie herramientas\\publicar_cotizaciones.py.")
        return controles, avisos, local

    # ------------------------------------------------------------------
    def qr(self, cotizacion):
        """Atención presencial: QR con la versión digital (PDF de solo lectura) de la cotización."""
        order, controles, bloqueos, _tel = self._evaluar_envio(cotizacion, requiere_telefono=False)
        if bloqueos:
            return self._resultado(
                False, "bloqueado", "QR no disponible",
                "No puedo mostrar %s al cliente: %s" % (order.name or cotizacion, " ".join(bloqueos)),
                controles=controles, reglas=["CT-002"], res=order or None,
                datos={"cotizacion": order.name or cotizacion})
        url = self._url_digital(order, asegurar_token=True)
        png = self.env["ir.actions.report"].barcode("QR", url, width=320, height=320, quiet=1)
        extra, avisos, local = self._alcance(url)
        controles += extra
        controles.append(self._control("Enlace seguro de solo lectura", True,
                                       "Abre el PDF de la cotización con un token de acceso; no permite aceptar ni pagar."))
        return self._resultado(
            True, "listo", "QR listo para %s" % order.name,
            "Pida al cliente que escanee el código con la cámara de su celular: se abrirá la cotización %s."
            % order.name,
            controles=controles, avisos=avisos, res=order,
            datos={"cotizacion": order.name, "cliente": order.partner_id.display_name,
                   "total": order.amount_total, "url": url, "accesible": not local,
                   "qr_png_base64": base64.b64encode(png).decode()})
