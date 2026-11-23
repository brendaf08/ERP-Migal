"""Clase base de los agentes especialistas de MIGAL.

Cada agente es un módulo `migal_agente_<codigo>` con un modelo abstracto:

    class AgenteSuministro(models.AbstractModel):
        _name = "migal.agente.suministro"
        _inherit = "migal.agente.especialista"
        _description = "Agente de cadena de suministro"
        _agente_codigo = "suministro"
        _agente_nombre = "Cadena de suministro"

Al instalarse, el orquestador lo registra solo: sus herramientas quedan disponibles en el chat, en la IA
(solo para los roles autorizados), en el asistente flotante y para las consultas de otros agentes.
Ver AGENTS.md y producto/agentes/README.md.
"""
from odoo import models


class MigalAgenteEspecialista(models.AbstractModel):
    _name = "migal.agente.especialista"
    _inherit = "migal.agente.tool.base"
    _description = "Base de los agentes especialistas del Agente MIGAL"

    _agente_codigo = False   # código del catálogo (agent/catalogo.py), p. ej. "suministro"
    _agente_nombre = False

    # ------------------------------------------------------------------
    # Lo que cada agente declara (sobrescribir)
    # ------------------------------------------------------------------
    def _herramientas(self):
        """{nombre: contrato}. Contrato:
            descripcion   qué hace (lo lee la IA)
            input_schema  JSON Schema de la entrada (type object, properties, required)
            roles         roles autorizados, p. ej. ["CMP", "GER"]
            escritura     "Ninguna (solo bitácora)." o qué borrador crea
            reglas        reglas RN que aplica, p. ej. ["RN-012"]
            metodo        nombre del método de este modelo que la ejecuta (recibe los argumentos validados)
        Las herramientas que figuran en CONSULTAS del catálogo quedan disponibles para otros agentes.
        """
        return {}

    def _eventos_escuchados(self):
        """{"EV-018": "nombre_del_metodo"}: el método recibe un dict con los datos del evento."""
        return {}

    def _reconocer(self, texto):
        """Frases del chat que atiende este agente sin IA. Recibe el texto normalizado (minúsculas, sin
        tildes) y devuelve (nombre_herramienta, argumentos) o None. Se consulta cuando el núcleo no
        reconoce la frase."""
        return None

    def _acciones_widget(self, record):
        """Botones del asistente flotante para el registro abierto. Lista de dicts con id, label, icon y
        descripcion; el núcleo antepone el código del agente al id."""
        return []

    def _widget_ejecutar(self, accion, record, params):
        """Ejecuta un botón propio del asistente. Por defecto, el id del botón es el nombre de la herramienta
        y sus argumentos salen de _argumentos_widget."""
        args = self._argumentos_widget(accion, record, params)
        if args is None:
            return None
        res = self.env["migal.agente"].ejecutar_desde_boton(accion, args, descripcion="[asistente] %s %s" % (
            self._agente_codigo, accion))
        return self._widget_desde_resultado(res)

    def _argumentos_widget(self, accion, record, params):
        """Argumentos de la herramienta `accion` a partir del registro abierto (sobrescribir)."""
        return None

    # ------------------------------------------------------------------
    # Utilidades para los agentes
    # ------------------------------------------------------------------
    def _consultar(self, herramienta, args):
        """Pregunta a otro agente según el catálogo (respuesta real o simulada)."""
        return self.env["migal.agente"].consultar(self._agente_codigo, herramienta, args)

    def _emitir(self, evento, datos):
        """Avisa un evento del que este agente es dueño. Nunca interrumpe la operación de Odoo."""
        return self.env["migal.agente"].emitir(evento, datos, desde=self._agente_codigo)

    def _widget_desde_resultado(self, res):
        """Convierte el resultado estándar de una herramienta en pasos del asistente flotante."""
        pasos = [{"titulo": c["control"], "detalle": c["detalle"], "tipo": "ok" if c["ok"] else "error"}
                 for c in res.get("controles") or []]
        if res.get("ok"):
            pasos.append({"titulo": res.get("titulo", ""), "detalle": res.get("mensaje", ""), "tipo": "ok"})
        return {"ok": bool(res.get("ok")), "pasos": pasos, "final": res.get("mensaje"),
                "avisos": res.get("avisos") or [], "html": str(self.env["migal.agente"].render_resultado(res))}
