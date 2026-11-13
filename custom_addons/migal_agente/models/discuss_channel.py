import logging

from odoo import models

_logger = logging.getLogger(__name__)


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    def _message_post_after_hook(self, message, msg_vals):
        res = super()._message_post_after_hook(message, msg_vals)
        self._migal_agente_responder(msg_vals)
        return res

    def _migal_agente_responder(self, msg_vals):
        """Responde cuando un usuario escribe al Agente MIGAL en un chat directo."""
        if self.channel_type != "chat" or msg_vals.get("message_type") != "comment":
            return
        agente = self.env.ref("migal_agente.partner_agente_migal", raise_if_not_found=False)
        if not agente or msg_vals.get("author_id") == agente.id:
            return
        if agente not in self.channel_member_ids.partner_id:
            return
        if not self.env.user._is_internal():
            return
        body = msg_vals.get("body") or ""
        texto = self.env["migal.agente"]._html_a_texto(body)
        if not texto:
            return
        html, _log = self.env["migal.agente"].procesar_mensaje(texto, canal="chat", session_id="chat-%s" % self.id)
        self.sudo().message_post(
            author_id=agente.id, body=html, message_type="comment",
            subtype_xmlid="mail.mt_comment", silent=True,
        )
