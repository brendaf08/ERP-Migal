import base64
import hashlib
import json
import logging
import re

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..lib import lectura, matcher
from ..lib.normalizador import EMPAQUES, _sin_tildes, singular

_logger = logging.getLogger(__name__)

NIVEL_ALTA, NIVEL_MEDIA = 0.80, 0.60
# Por debajo de este puntaje no se muestra sugerencia: evita proponer productos sin relación.
UMBRAL_SUGERENCIA = 0.50
TIPOS_ARCHIVO = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif", "application/pdf"}


class MigalOcrDocumento(models.Model):
    _name = "migal.ocr.documento"
    _description = "Lista de productos escaneada"
    _inherit = ["mail.thread"]
    _order = "id desc"

    name = fields.Char("Referencia", required=True, readonly=True, copy=False,
                       default=lambda s: _("Nueva lista"))
    partner_id = fields.Many2one("res.partner", "Cliente", tracking=True)
    order_id = fields.Many2one("sale.order", "Cotización", tracking=True,
                               domain="[('state', 'in', ('draft', 'sent'))]")
    archivo = fields.Binary("Foto o PDF de la lista", attachment=True)
    archivo_nombre = fields.Char()
    texto_lista = fields.Text("O pegue la lista",
                              help="Una línea por producto, por ejemplo: «10 bls cemento sol», «fierro 1/2 x 20».")
    estado = fields.Selection([("borrador", "Por leer"), ("leido", "Por revisar"), ("aplicado", "Agregada"),
                               ("error", "No se pudo leer")], default="borrador", required=True, tracking=True)
    origen = fields.Selection([("ia", "Foto/PDF con IA"), ("texto", "Texto")], readonly=True)
    modelo_ia = fields.Char("Modelo usado", readonly=True)
    mensaje = fields.Text(readonly=True)
    hash_archivo = fields.Char(readonly=True, index=True, copy=False)
    linea_ids = fields.One2many("migal.ocr.linea", "documento_id", "Líneas")
    total_lineas = fields.Integer(compute="_compute_resumen")
    lineas_alta = fields.Integer(compute="_compute_resumen")
    lineas_revisar = fields.Integer(compute="_compute_resumen")
    coincidencia_promedio = fields.Float(compute="_compute_resumen", string="Coincidencia promedio (%)")
    company_id = fields.Many2one("res.company", default=lambda s: s.env.company, required=True)

    @api.depends("linea_ids.confianza", "linea_ids.product_id")
    def _compute_resumen(self):
        for doc in self:
            lineas = doc.linea_ids
            doc.total_lineas = len(lineas)
            doc.lineas_alta = len(lineas.filtered(lambda l: l.nivel in ("alta", "manual")))
            doc.lineas_revisar = len(lineas.filtered(lambda l: l.nivel in ("media", "baja", "ninguna")))
            doc.coincidencia_promedio = (sum(lineas.mapped("confianza")) / len(lineas) * 100) if lineas else 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("Nueva lista")) == _("Nueva lista"):
                vals["name"] = self.env["ir.sequence"].next_by_code("migal.ocr.documento") or _("Lista")
            if vals.get("order_id") and not vals.get("partner_id"):
                vals["partner_id"] = self.env["sale.order"].browse(vals["order_id"]).partner_id.id
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Configuración de IA OCR (independiente del agente, R-05)
    # ------------------------------------------------------------------
    OCR_PROVEEDORES_PERMITIDOS = {"gemini"}

    def _param_bool(self, key):
        return self.env["ir.config_parameter"].sudo().get_param(key) in ("True", "1", True)

    def _ocr_modelos_permitidos(self, modelos):
        permitidos = []
        for modelo in [m.strip() for m in (modelos or "").split(",") if m.strip()]:
            if re.fullmatch(r"[a-zA-Z0-9._-]+", modelo) and modelo.startswith("gemini-"):
                permitidos.append(modelo)
        return permitidos

    def _config_ia(self):
        icp = self.env["ir.config_parameter"].sudo()
        enabled = self._param_bool("migal_ocr.llm_enabled")
        ack = self._param_bool("migal_ocr.llm_data_ack")
        proveedor = "gemini"  # OCR actualmente soporta solo Gemini
        clave = (icp.get_param("migal_ocr.llm_api_key") or "").strip()
        if not clave:
            # Compatibilidad controlada: reutiliza clave del agente solo si proveedor agente es Gemini.
            if (icp.get_param("migal_agente.llm_proveedor") or "gemini") == "gemini":
                clave = (icp.get_param("migal_agente.llm_api_key") or "").strip()
        modelos_raw = (icp.get_param("migal_ocr.gemini_modelos") or lectura.MODELOS_POR_DEFECTO).strip()
        modelos = self._ocr_modelos_permitidos(modelos_raw)
        return {
            "enabled": enabled,
            "api_key": clave,
            "proveedor": proveedor,
            "modelos": ",".join(modelos),
            "modelos_validos": bool(modelos),
            "consentimiento": ack,
        }

    def _jerga(self):
        return {s.termino: s.equivale for s in self.env["migal.ocr.sinonimo"].sudo().search([("active", "=", True)])}

    def _catalogo(self, jerga):
        productos = self.env["product.product"].search([("sale_ok", "=", True)])
        datos = []
        for p in productos:
            partes = [p.name] + p.product_template_attribute_value_ids.mapped("name")
            datos.append((p.id, " ".join(partes)))
        return matcher.preparar_catalogo(datos, jerga)

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def action_leer(self):
        self.ensure_one()
        if not self.archivo and not (self.texto_lista or "").strip():
            raise UserError(_("Suba la foto o el PDF de la lista, o pegue el texto."))
        try:
            if self.archivo:
                contenido = base64.b64decode(self.archivo)
                tipo = self._tipo_mime(contenido)
                cfg = self._config_ia()
                if not cfg["enabled"]:
                    raise lectura.LecturaError(
                        _("El OCR con IA está deshabilitado. Habilítelo en Ajustes › Agente MIGAL › OCR, "
                          "o pegue la lista como texto."))
                if cfg["proveedor"] not in self.OCR_PROVEEDORES_PERMITIDOS:
                    raise lectura.LecturaError(_("El proveedor de IA configurado para OCR no está permitido."))
                if not cfg["consentimiento"]:
                    raise lectura.LecturaError(
                        _("Falta autorizar el envío de documentos OCR al proveedor de IA (Ajustes › Agente MIGAL)."))
                if not cfg["api_key"]:
                    raise lectura.LecturaError(
                        _("Falta la clave de API para OCR con IA. Configúrela en Ajustes › Agente MIGAL. "
                          "Mientras tanto puede pegar la lista como texto."))
                if not cfg["modelos_validos"]:
                    raise lectura.LecturaError(_("La configuración de modelos OCR no es válida."))
                modelo, filas = lectura.leer_con_gemini(contenido, tipo, cfg["api_key"], cfg["modelos"])
                self.write({"origen": "ia", "modelo_ia": modelo,
                            "hash_archivo": hashlib.sha256(contenido).hexdigest()})
            else:
                filas = lectura.leer_texto(self.texto_lista)
                self.write({"origen": "texto", "modelo_ia": False})
        except lectura.LecturaError as exc:
            self.write({"estado": "error", "mensaje": str(exc)})
            raise UserError(str(exc)) from exc
        if not filas:
            self.write({"estado": "error", "mensaje": _("No se encontraron líneas de productos legibles.")})
            raise UserError(_("No se encontraron líneas de productos legibles."))
        self._emparejar(filas)
        return True

    def _emparejar(self, filas):
        jerga = self._jerga()
        catalogo = self._catalogo(jerga)
        palabras = matcher.vocabulario(catalogo)
        lineas = []
        for secuencia, (texto, cantidad) in enumerate(filas, 1):
            texto, cantidad, entrada = self._preparar_entrada(texto, cantidad)
            normalizado, coincidencias, corregida = matcher.coincidencias(
                entrada, catalogo, umbral_baja=UMBRAL_SUGERENCIA, jerga_extra=jerga, palabras=palabras)
            coincidencias = self._desempatar_presentacion(texto, coincidencias)
            mejor = coincidencias[0] if coincidencias else None
            # Relacionados: las coincidencias y los demás productos del mismo tipo, sin repetir.
            relacionados = [c.producto_id for c in coincidencias]
            for pid in matcher.relacionados(entrada, catalogo, jerga_extra=jerga, palabras=palabras):
                if pid not in relacionados:
                    relacionados.append(pid)
            lineas.append((0, 0, {
                "secuencia": secuencia,
                "texto_crudo": texto,
                "texto_normalizado": normalizado,
                "cantidad": cantidad if cantidad is not None else 1.0,
                "cantidad_leida": cantidad is not None,
                "product_id": mejor.producto_id if mejor and mejor.confianza >= NIVEL_MEDIA else False,
                "producto_sugerido_id": mejor.producto_id if mejor else False,
                "confianza": mejor.confianza if mejor else 0.0,
                "corregida": corregida,
                "alternativas_json": json.dumps([[c.producto_id, c.confianza] for c in coincidencias]),
                "alternativa_ids": [(6, 0, [c.producto_id for c in coincidencias[1:]])],
                "relacionado_ids": [(6, 0, relacionados[:8])],
            }))
        self.linea_ids.unlink()
        self.write({"linea_ids": lineas, "estado": "leido", "mensaje": False})
        self.message_post(body=Markup(_("Lista leída: <b>%s</b> líneas (%s). Coincidencia promedio %s%%.")) % (
            self.total_lineas, dict(self._fields["origen"].selection).get(self.origen),
            round(self.coincidencia_promedio)))

    def _desempatar_presentacion(self, texto, coincidencias):
        """Empate entre granel y bolsa («PIEDRA CHANCADA» y «PIEDRA CHANCADA - BOLSA»): «bls/bol/bolsa» en la
        línea elige la bolsa; «m3/mt/mtrs» o nada, el granel."""
        if len(coincidencias) < 2 or coincidencias[0].confianza - coincidencias[1].confianza > 0.02:
            return coincidencias
        pide_bolsa = bool(re.search(r"\b(bls?|bol|bols|bolsas?)\b", _sin_tildes(texto.lower())))
        empatadas = [c for c in coincidencias if coincidencias[0].confianza - c.confianza <= 0.02]
        nombres = {p.id: (p.name or "").upper() for p in self.env["product.product"].browse(
            [c.producto_id for c in empatadas])}
        preferida = next((c for c in empatadas if ("BOLSA" in nombres.get(c.producto_id, "")) == pide_bolsa), None)
        if not preferida or preferida is coincidencias[0]:
            return coincidencias
        return [preferida] + [c for c in coincidencias if c is not preferida]

    @staticmethod
    def _preparar_entrada(texto, cantidad):
        """(texto, cantidad, entrada para el emparejador).

        - Si el texto empieza con la cantidad («30 cemento sol» con cantidad 30), se quita: repetida resta
          similitud. Sin cantidad leída, el número inicial se toma como cantidad.
        - Solo cuando la primera palabra es un envase («3 rollos temflex») se antepone la cantidad, para que
          el normalizador mueva el envase al final y compare por el producto.
        """
        texto = (texto or "").strip()
        m = re.match(r"^(\d+(?:[.,]\d+)?)\s+(\S.*)$", texto)
        if m:
            numero = float(m.group(1).replace(",", "."))
            if cantidad is None or abs(numero - cantidad) < 1e-6:
                cantidad, texto = numero, m.group(2)
        primera = singular(_sin_tildes(texto.split()[0].lower().strip(".,"))) if texto.split() else ""
        entrada = ("%g %s" % (cantidad, texto)) if cantidad is not None and primera in EMPAQUES else texto
        return texto, cantidad, entrada

    @staticmethod
    def _tipo_mime(contenido):
        if contenido[:4] == b"%PDF":
            return "application/pdf"
        if contenido[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if contenido[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
            return "image/webp"
        if contenido[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1", b"ftyphevc"):
            return "image/heic"
        raise lectura.LecturaError(_("Formato no admitido: suba una foto (JPG, PNG, WEBP, HEIC) o un PDF."))

    def action_agregar_a_cotizacion(self):
        self.ensure_one()
        lineas = self.linea_ids.filtered(lambda l: l.product_id and l.cantidad > 0)
        if not lineas:
            raise UserError(_("No hay líneas con producto asignado. Elija el producto de cada línea."))
        order = self.order_id
        if order and order.state not in ("draft", "sent"):
            raise UserError(_("La cotización %s ya no está abierta; deje el campo vacío para crear una nueva.")
                            % order.name)
        if not order:
            if not self.partner_id:
                raise UserError(_("Indique el cliente para crear la cotización."))
            order = self.env["sale.order"].create({"partner_id": self.partner_id.id})
        # Un producto que aparece en varias filas de la lista se suma en una sola línea de la cotización.
        cantidades = {}
        for l in lineas:
            cantidades[l.product_id] = cantidades.get(l.product_id, 0.0) + l.cantidad
        comandos = []
        sumados_existentes = 0
        for producto, cantidad in cantidades.items():
            existente = order.order_line.filtered(
                lambda ol: ol.product_id == producto and not ol.display_type
                and ol.product_uom_id == producto.uom_id)[:1]
            if existente:
                # Ya estaba en la cotización: se suma a esa línea en vez de duplicarla.
                comandos.append((1, existente.id, {"product_uom_qty": existente.product_uom_qty + cantidad}))
                sumados_existentes += 1
            else:
                comandos.append((0, 0, {"product_id": producto.id, "product_uom_qty": cantidad}))
        order.write({"order_line": comandos})
        sin_producto = len(self.linea_ids) - len(lineas)
        self.write({"order_id": order.id, "estado": "aplicado"})
        repetidas = len(lineas) - len(cantidades)
        detalle = []
        if repetidas:
            detalle.append(_("%s filas repetidas se sumaron") % repetidas)
        if sumados_existentes:
            detalle.append(_("%s productos ya estaban y se sumó la cantidad") % sumados_existentes)
        order.message_post(body=Markup(_("Se agregaron <b>%s</b> productos desde la lista escaneada %s%s.")) % (
            len(cantidades), self._get_html_link(), (" (%s)" % ", ".join(detalle)) if detalle else ""))
        if sin_producto:
            self.message_post(body=_("%s líneas sin producto no se agregaron.") % sin_producto)
        if self.env.context.get("migal_ocr_dialogo"):
            # Abierto en ventana sobre la cotización: se cierra y la cotización de fondo se recarga.
            return {"type": "ir.actions.act_window_close"}
        return {"type": "ir.actions.act_window", "res_model": "sale.order", "res_id": order.id,
                "view_mode": "form", "views": [(False, "form")], "target": "current"}

    def action_volver_a_leer(self):
        self.ensure_one()
        self.write({"estado": "borrador"})
        return self.action_leer()


class MigalOcrLinea(models.Model):
    _name = "migal.ocr.linea"
    _description = "Línea de una lista escaneada"
    _order = "documento_id, secuencia, id"

    documento_id = fields.Many2one("migal.ocr.documento", required=True, ondelete="cascade", index=True)
    secuencia = fields.Integer(default=10)
    texto_crudo = fields.Char("Texto leído", required=True)
    texto_normalizado = fields.Char("Interpretado como")
    cantidad = fields.Float(default=1.0, digits="Product Unit")
    cantidad_leida = fields.Boolean(default=True)
    product_id = fields.Many2one("product.product", "Producto", domain="[('sale_ok', '=', True)]")
    producto_sugerido_id = fields.Many2one("product.product", "Sugerido", readonly=True)
    uom_id = fields.Many2one(related="product_id.uom_id", string="Unidad")
    confianza = fields.Float(readonly=True)
    coincidencia = fields.Float("Coincidencia", compute="_compute_nivel",
                                help="Porcentaje de coincidencia entre el texto leído y el producto sugerido.")
    corregida = fields.Boolean(readonly=True, help="Se corrigió un error de escritura antes de comparar.")
    alternativas_json = fields.Text(readonly=True)
    alternativa_ids = fields.Many2many("product.product", string="Otras opciones", readonly=True)
    relacionado_ids = fields.Many2many(
        "product.product", "migal_ocr_linea_relacionado_rel", "linea_id", "product_id",
        string="Sugerencias", readonly=True,
        help="Productos del catálogo relacionados con lo leído. El selector de producto solo muestra estos.")
    sugerencias_otras_ids = fields.Many2many(
        "product.product", "migal_ocr_linea_sugerencia_rel", "linea_id", "product_id",
        string="Sugerencias", compute="_compute_sugerencias_otras",
        help="Otras opciones relacionadas (sin el producto elegido).")

    @api.depends("relacionado_ids", "product_id")
    def _compute_sugerencias_otras(self):
        for l in self:
            l.sugerencias_otras_ids = l.relacionado_ids - l.product_id
    nivel = fields.Selection([("alta", "Alta"), ("media", "Revisar"), ("baja", "Baja"), ("ninguna", "Sin coincidencia"),
                              ("manual", "Elegido a mano")], compute="_compute_nivel")

    @api.depends("confianza", "product_id", "producto_sugerido_id")
    def _compute_nivel(self):
        for l in self:
            if not l.product_id or l.product_id == l.producto_sugerido_id:
                # Sin producto elegido se muestra el puntaje de la sugerencia, para que se vea por qué no se eligió.
                l.coincidencia = round(l.confianza * 100, 1)
            else:
                l.coincidencia = round(dict(json.loads(l.alternativas_json or "[]")).get(l.product_id.id, 0) * 100, 1)
            if l.product_id and l.product_id != l.producto_sugerido_id and not l.coincidencia:
                l.nivel = "manual"
            elif not l.producto_sugerido_id:
                l.nivel = "ninguna"
            else:
                c = l.coincidencia / 100
                l.nivel = "alta" if c >= NIVEL_ALTA else "media" if c >= NIVEL_MEDIA else "baja"
