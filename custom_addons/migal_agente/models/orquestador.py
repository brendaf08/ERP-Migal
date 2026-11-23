"""Orquestador multiagente: registro de agentes, consultas entre agentes, eventos y simulador.

- Registro: cualquier modelo que herede de `migal.agente.especialista` con `_agente_codigo` queda
  registrado al instalar su módulo. No hay listas que editar a mano.
- consultar(desde, herramienta, args): un agente pregunta a otro. Solo lo permitido por el catálogo
  (agent/catalogo.py). Si el agente dueño aún no la implementa, responde el SIMULADOR con la salida de
  ejemplo del contrato, marcada como simulada.
- emitir(evento, datos, desde): un agente avisa un evento EV del que es dueño; se entrega a los agentes
  que lo escuchan. Un oyente que falla no afecta a los demás ni a la operación de Odoo.
Todo queda en la bitácora (migal.agente.log) con el agente que actuó.
"""
import copy
import json
import logging
import uuid

from odoo import api, models

from ..agent import catalogo, contracts

_logger = logging.getLogger(__name__)


class MigalAgenteOrquestador(models.AbstractModel):
    _inherit = "migal.agente"

    # ------------------------------------------------------------------
    # Registro
    # ------------------------------------------------------------------
    @api.model
    def _agentes(self):
        """{codigo: modelo} de los agentes especialistas instalados."""
        agentes = {}
        for nombre in self.env.registry.models:
            clase = self.env.registry[nombre]
            codigo = getattr(clase, "_agente_codigo", False)
            if codigo and nombre != "migal.agente.especialista" and not getattr(clase, "_abstract_base", False):
                agentes[codigo] = self.env[nombre]
        return agentes

    @api.model
    def _herramientas_registradas(self):
        """{nombre: contrato} con las herramientas del núcleo y las de cada agente instalado."""
        registro = {}
        for nombre, spec in contracts.TOOLS.items():
            registro[nombre] = dict(spec, agente=catalogo.DUENO_HERRAMIENTAS_NUCLEO.get(nombre, "orquestador"),
                                    nucleo=True)
        for codigo, agente in self._agentes().items():
            for nombre, spec in (agente._herramientas() or {}).items():
                if nombre in registro:
                    _logger.error("Agente MIGAL: la herramienta %s de %s ya existe en %s; se ignora.",
                                  nombre, codigo, registro[nombre]["agente"])
                    continue
                spec = dict(spec, agente=codigo, modelo=agente._name, nucleo=False)
                spec.setdefault("description", spec.get("descripcion", ""))
                registro[nombre] = spec
        return registro

    @api.model
    def _spec(self, nombre):
        return self._herramientas_registradas().get(nombre)

    @api.model
    def _herramientas_para_usuario(self):
        """Contratos que el usuario actual puede usar (lo único que se le muestra a la IA)."""
        from ..agent import guardrails
        roles = set(guardrails.user_roles(self.env.user, contracts.ROLE_GROUPS))
        return [{"name": n, "description": s["description"], "input_schema": s["input_schema"]}
                for n, s in self._herramientas_registradas().items() if roles & set(s.get("roles", ()))]

    @api.model
    def _ejecutar_registrada(self, nombre, spec, limpio):
        modelo = self.env[spec["modelo"]]
        return getattr(modelo, spec["metodo"])(**limpio)

    # ------------------------------------------------------------------
    # Consultas entre agentes
    # ------------------------------------------------------------------
    @api.model
    def consultar(self, desde, herramienta, args, *, traza=None):
        traza = traza if traza is not None else []
        base = self.env["migal.agente.tool.base"]
        contrato = catalogo.CONSULTAS.get(herramienta)
        if not contrato:
            res = base._resultado(False, "contrato", "Consulta no acordada",
                                  "«%s» no figura en el catálogo de contratos entre agentes." % herramienta)
        elif desde not in contrato["consumidores"]:
            res = base._resultado(False, "contrato", "Consulta no permitida",
                                  "El agente «%s» no está autorizado a consultar «%s» (catálogo de contratos)." % (
                                      desde, herramienta))
        else:
            spec = self._spec(herramienta)
            if spec and spec["agente"] == contrato["proveedor"]:
                res = self.ejecutar_herramienta(herramienta, args, traza=traza)
            else:
                res = copy.deepcopy(contrato["ejemplo_salida"])
                res.setdefault("controles", [])
                res.setdefault("reglas", [])
                res.setdefault("escalar_a", [])
                res["avisos"] = list(res.get("avisos") or []) + [
                    "Respuesta SIMULADA: el agente «%s» aún no está instalado o no implementa «%s»." % (
                        catalogo.AGENTES[contrato["proveedor"]]["nombre"], herramienta)]
                res["simulado"] = True
                traza.append({"tool": herramienta, "arguments": args, "simulado": True})
            campos = (contrato.get("campos_por_consumidor") or {}).get(desde)
            if campos and isinstance(res.get("datos"), dict):
                res["datos"] = {k: v for k, v in res["datos"].items() if k in campos}
        self._registrar_interno("consulta", "[consulta] %s → %s %s" % (desde, herramienta, json.dumps(
            args, ensure_ascii=False, default=str)), traza, res, agente=desde)
        return res

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    @api.model
    def emitir(self, evento, datos, desde=None):
        """Entrega el evento a los agentes que lo escuchan. Devuelve la lista de agentes que lo recibieron."""
        definicion = catalogo.EVENTOS.get(evento)
        if not definicion:
            _logger.warning("Agente MIGAL: evento %s no figura en el catálogo.", evento)
            return []
        if desde and desde != definicion["emisor"]:
            _logger.warning("Agente MIGAL: %s intentó emitir %s, cuyo dueño es %s.", desde, evento, definicion["emisor"])
            return []
        entregados, fallidos = [], []
        for codigo, agente in self._agentes().items():
            metodo = (agente._eventos_escuchados() or {}).get(evento)
            if not metodo:
                continue
            try:
                with self.env.cr.savepoint():
                    getattr(agente, metodo)(dict(datos))
                entregados.append(codigo)
            except Exception:  # noqa: BLE001 - un oyente no debe romper la operación
                _logger.exception("Agente MIGAL: el agente %s falló al procesar %s", codigo, evento)
                fallidos.append(codigo)
        res = self.env["migal.agente.tool.base"]._resultado(
            not fallidos, "ok" if not fallidos else "error", "%s %s" % (evento, definicion["nombre"]),
            "Entregado a: %s%s" % (", ".join(entregados) or "ningún agente instalado",
                                   (". Falló en: %s" % ", ".join(fallidos)) if fallidos else ""))
        self._registrar_interno("evento", "[evento] %s %s" % (evento, json.dumps(datos, ensure_ascii=False, default=str)),
                                [], res, agente=definicion["emisor"])
        return entregados

    # ------------------------------------------------------------------
    # Bitácora de consultas y eventos
    # ------------------------------------------------------------------
    def _registrar_interno(self, canal, texto, traza, res, agente=None):
        try:
            self.sudo()._registrar(texto, canal, "reglas", traza, self.render_resultado(res),
                                   resultado="ok" if res.get("ok") else "error",
                                   session_id="%s-%s" % (canal, uuid.uuid4().hex[:8]), agente=agente)
        except Exception:  # noqa: BLE001 - la bitácora nunca interrumpe
            _logger.exception("Agente MIGAL: no se pudo registrar %s", canal)

    # ------------------------------------------------------------------
    # Asistente flotante: botones de los agentes
    # ------------------------------------------------------------------
    @api.model
    def widget_contexto(self, res_model=False, res_id=False):
        ctx = super().widget_contexto(res_model, res_id)
        if not (res_model and res_id) or res_model not in self.env:
            return ctx
        record = self.env[res_model].browse(res_id).exists()
        if not record:
            return ctx
        pestanas_agentes = []
        for codigo, agente in self._agentes().items():
            acciones = []
            for accion in agente._acciones_widget(record) or []:
                accion = dict(accion, id="%s.%s" % (codigo, accion["id"]))
                acciones.append(accion)
            if acciones:
                pestanas_agentes.append({"id": "agente-%s" % codigo, "label": agente._agente_nombre,
                                         "icon": acciones[0].get("icon", "fa-bolt"), "acciones": acciones})
        if not pestanas_agentes:
            return ctx
        if ctx.get("pestanas"):
            ctx["pestanas"] += pestanas_agentes
            ctx["acciones"] = ctx.get("acciones", []) + [a for p in pestanas_agentes for a in p["acciones"]]
        else:
            ctx["acciones"] = ctx.get("acciones", []) + [a for p in pestanas_agentes for a in p["acciones"]]
            if res_model not in ("sale.order", "res.partner"):
                ctx["titulo"] = record.display_name
                ctx["subtitulo"] = "Esto es lo que puedo hacer aquí."
                ctx["registro"] = record.display_name
        return ctx

    @api.model
    def widget_ejecutar(self, accion, res_model=False, res_id=False, params=None):
        if accion and "." in accion:
            codigo, propia = accion.split(".", 1)
            agente = self._agentes().get(codigo)
            record = self.env[res_model].browse(res_id).exists() if res_model in self.env and res_id else None
            if agente and record:
                res = agente._widget_ejecutar(propia, record, params or {})
                if res is not None:
                    return res
        return super().widget_ejecutar(accion, res_model, res_id, params)
