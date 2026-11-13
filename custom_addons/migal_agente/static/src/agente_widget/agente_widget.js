/** @odoo-module **/
/**
 * Asistente flotante del Agente MIGAL.
 *
 * Avatar en la esquina inferior derecha. Al abrirlo detecta la pantalla actual
 * (cotización o cliente) y ofrece las acciones del agente. Los pasos que se
 * muestran animados son los controles reales que devolvieron las herramientas
 * del servidor (contrato, permisos, guardarraíles y bitácora incluidos).
 */
import { Component, markup, onPatched, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";

const esperar = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export class AgenteMigalWidget extends Component {
    static template = "migal_agente.AgenteWidget";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.cuerpo = useRef("cuerpo");
        this.state = useState({
            abierto: false,
            ctx: null,
            pasos: [],
            visibles: 0,
            corriendo: false,
            pensando: false,
            resultado: null,
            mensajeWa: "",
            texto: "",
            respuestas: [],
            ocupado: false,
            qrGrande: false,
            periodo: "mes",
            fechaCob: "cotizacion",
            fechaOtra: "",
            sugerencia: "",
            copiado: false,
            pestana: "enviar",
            incluirDisp: false,
            sinGuardar: false,
        });
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => {
            if (this.state.abierto && !this.state.ocupado) {
                this.reiniciar();
                this.cargarContexto();
            }
        });
        onPatched(() => {
            const el = this.cuerpo.el;
            if (el) {
                el.scrollTop = el.scrollHeight;
            }
        });
    }

    // ------------------------------------------------------------------
    get registroActual() {
        const ctrl = this.actionService.currentController;
        if (!ctrl || !ctrl.props) {
            return { model: false, resId: false };
        }
        let resId = false;
        try {
            resId = (ctrl.getLocalState && ctrl.getLocalState().resId) || ctrl.props.resId || false;
        } catch {
            resId = ctrl.props.resId || false;
        }
        return { model: ctrl.props.resModel || false, resId };
    }

    get enlaceWhatsapp() {
        const wa = this.state.resultado && this.state.resultado.whatsapp;
        if (!wa) {
            return "#";
        }
        return `https://wa.me/${wa.telefono.replace("+", "")}?text=${encodeURIComponent(this.state.mensajeWa || "")}`;
    }

    get estadoAvatar() {
        if (this.state.pensando) {
            return "pensando";
        }
        if (this.state.resultado) {
            return this.state.resultado.ok ? "feliz" : "atento";
        }
        return "normal";
    }

    // ------------------------------------------------------------------
    async alternar() {
        this.state.abierto = !this.state.abierto;
        if (this.state.abierto && !this.state.ocupado) {
            this.reiniciar();
            await this.cargarContexto();
        }
    }

    reiniciar() {
        Object.assign(this.state, {
            pasos: [], visibles: 0, corriendo: false, pensando: false, resultado: null, mensajeWa: "", respuestas: [],
            qrGrande: false,
        });
    }

    async volver() {
        this.reiniciar();
        await this.cargarContexto();
    }

    async cargarContexto() {
        this.state.sinGuardar = this.formularioSinGuardar();
        const { model, resId } = this.registroActual;
        this.state.ctx = await this.orm.call("migal.agente", "widget_contexto", [model, resId]);
    }

    async animarPasos(pasos) {
        const pausa = pasos.length > 10 ? 380 : 620;
        for (let i = 0; i < pasos.length; i++) {
            this.state.pasos.push(pasos[i]);
            this.state.visibles = this.state.pasos.length;
            this.state.corriendo = true;
            await esperar(pausa + Math.random() * 250);
            this.state.corriendo = false;
            await esperar(120);
        }
    }

    get fechasPeriodo() {
        const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
        const hoy = new Date();
        let desde = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
        if (this.state.periodo === "trimestre") {
            desde = new Date(hoy.getFullYear(), hoy.getMonth() - 2, 1);
        } else if (this.state.periodo === "anio") {
            desde = new Date(hoy.getFullYear(), 0, 1);
        }
        return { fecha_desde: iso(desde), fecha_hasta: iso(hoy) };
    }

    get accionesVisibles() {
        const ctx = this.state.ctx;
        if (!ctx) {
            return [];
        }
        if (ctx.pestanas) {
            const p = ctx.pestanas.find((t) => t.id === this.state.pestana) || ctx.pestanas[0];
            return p.acciones;
        }
        return ctx.acciones;
    }

    get tieneFecha() {
        return this.accionesVisibles.some((a) => a.fecha);
    }

    cambiarPestana(id) {
        this.state.pestana = id;
        this.reiniciar();
    }

    formularioSinGuardar() {
        const { model, resId } = this.registroActual;
        if (model !== "sale.order") {
            return false;
        }
        return !resId || Boolean(document.querySelector(".o_form_view .o_form_status_indicator_buttons:not(.invisible)"));
    }

    async guardarYRevisar() {
        const boton = document.querySelector(".o_form_view .o_form_button_save");
        if (boton) {
            boton.click();
            for (let i = 0; i < 40 && this.formularioSinGuardar(); i++) {
                await esperar(150);
            }
        }
        await this.volver();
    }

    get fechaCobertura() {
        const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
        const dias = { hoy: 0, "3": 3, "7": 7 }[this.state.fechaCob];
        if (dias !== undefined) {
            const d = new Date();
            d.setDate(d.getDate() + dias);
            return iso(d);
        }
        return this.state.fechaCob === "otra" ? this.state.fechaOtra : "";
    }

    get enlaceSugerencia() {
        const sg = this.state.resultado && this.state.resultado.sugerencia;
        if (!sg || !sg.telefono) {
            return "#";
        }
        return `https://wa.me/${sg.telefono.replace("+", "")}?text=${encodeURIComponent(this.state.sugerencia || "")}`;
    }

    async copiarSugerencia() {
        try {
            await navigator.clipboard.writeText(this.state.sugerencia || "");
            this.state.copiado = true;
            setTimeout(() => (this.state.copiado = false), 2000);
        } catch {
            this.state.copiado = false;
        }
    }

    get tienePeriodo() {
        return this.accionesVisibles.some((a) => a.periodo);
    }

    ejecutarAccion(acc) {
        if (this.formularioSinGuardar()) {
            this.state.sinGuardar = true;
            return;
        }
        if (acc.fecha) {
            const fecha = this.fechaCobertura;
            return this.ejecutar(acc.id, fecha ? { fecha } : {});
        }
        if (acc.id === "procesar_cotizacion") {
            return this.ejecutar(acc.id, { incluir_disponibilidad: this.state.incluirDisp });
        }
        return this.ejecutar(acc.id, acc.periodo ? this.fechasPeriodo : {});
    }

    async ejecutar(accion, params = {}) {
        if (this.state.ocupado) {
            return;
        }
        const { model, resId } = this.registroActual;
        this.reiniciar();
        this.state.ocupado = true;
        this.state.pensando = true;
        try {
            const [res] = await Promise.all([
                this.orm.call("migal.agente", "widget_ejecutar", [accion, model, resId, params]),
                esperar(500),
            ]);
            await this.animarPasos(res.pasos || []);
            this.state.resultado = res;
            this.state.mensajeWa = (res.whatsapp && res.whatsapp.mensaje) || "";
            this.state.sugerencia = (res.sugerencia && res.sugerencia.mensaje) || "";
        } finally {
            this.state.pensando = false;
            this.state.ocupado = false;
        }
    }

    async registrarEnvio() {
        const { model, resId } = this.registroActual;
        this.state.ocupado = true;
        this.state.pensando = true;
        try {
            const accion = (this.state.resultado.whatsapp && this.state.resultado.whatsapp.accion_registro) || "registrar_envio";
            const res = await this.orm.call("migal.agente", "widget_ejecutar", [
                accion, model, resId, { mensaje: this.state.mensajeWa },
            ]);
            await this.animarPasos(res.pasos || []);
            this.state.resultado = Object.assign({}, this.state.resultado, {
                registrado: res.registrado,
                final: res.final,
                ok: res.ok,
            });
        } finally {
            this.state.pensando = false;
            this.state.ocupado = false;
        }
    }

    async enviarTexto() {
        const texto = (this.state.texto || "").trim();
        if (!texto || this.state.ocupado) {
            return;
        }
        const { model, resId } = this.registroActual;
        this.state.respuestas.push({ autor: "yo", html: texto });
        this.state.texto = "";
        this.state.ocupado = true;
        this.state.pensando = true;
        try {
            const [res] = await Promise.all([
                this.orm.call("migal.agente", "widget_mensaje", [texto, model, resId]),
                esperar(700),
            ]);
            this.state.respuestas.push({ autor: "agente", html: markup(res.html) });
        } finally {
            this.state.pensando = false;
            this.state.ocupado = false;
        }
    }

    onTecla(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.enviarTexto();
        }
    }

    iconoPaso(paso, indice) {
        if (this.state.corriendo && indice === this.state.visibles - 1) {
            return "fa fa-circle-o-notch fa-spin text-primary";
        }
        return {
            ok: "fa fa-check-circle text-success",
            error: "fa fa-times-circle text-danger",
            aviso: "fa fa-exclamation-circle text-warning",
            info: "fa fa-info-circle text-info",
        }[paso.tipo] || "fa fa-circle-o";
    }
}

registry.category("main_components").add("migal_agente.AgenteWidget", { Component: AgenteMigalWidget });
