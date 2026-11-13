"""Publicador temporal de cotizaciones para el QR del Agente MIGAL.

Uso (desde C:\\Users\\luisn\\Downloads\\odoo19, con Odoo ya arrancado):

    python herramientas\\publicar_cotizaciones.py

Qué hace:
1. Levanta un «portero» HTTP local (127.0.0.1:8090) que SOLO deja pasar
   GET /my/orders/<id>?access_token=<uuid>&report_type=pdf (cotización) y
   GET /migal/estado-cuenta/<uuid> (estado de cuenta compartido, caduca a las 24 h) hacia Odoo.
   Cualquier otra ruta (inicio de sesión, /web, /odoo, /xmlrpc, /json...) responde 404.
2. Abre un túnel rápido de Cloudflare (sin cuenta) hacia el portero y obtiene una
   dirección pública temporal https://<aleatorio>.trycloudflare.com.
3. El Agente MIGAL consulta el portero en http://127.0.0.1:8090/estado y usa esa
   dirección en el QR. Al cerrar este programa (Ctrl+C), el túnel y la dirección dejan
   de existir y los QR anteriores dejan de abrir.

Buenas prácticas aplicadas:
- Odoo no se expone: solo el PDF de solo lectura de una cotización con su token (UUID).
- Sin cookies ni sesión: el portero no reenvía cabeceras del visitante a Odoo.
- Cabeceras de seguridad: no-store, noindex, nosniff, no-referrer.
- Límite de peticiones por visitante y registro en consola sin tokens.
- El estado con la URL pública solo se entrega a peticiones locales (no vía túnel).
"""
import argparse
import json
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

BASE = Path(__file__).resolve().parent
RUTA_PERMITIDA = re.compile(r"^/my/orders/(\d{1,9})$")
RUTA_ESTADO = re.compile(r"^/migal/estado-cuenta/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$")
TOKEN_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
URL_TUNEL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
LIMITE_POR_MINUTO = 30
CABECERAS_SEGURIDAD = {
    "Cache-Control": "no-store, private",
    "X-Robots-Tag": "noindex, nofollow, noarchive",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}

ESTADO = {"url_publica": None, "desde": None, "odoo": None}
_visitas = defaultdict(deque)
_lock = threading.Lock()


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def permitido_por_limite(ip):
    ahora = time.monotonic()
    with _lock:
        cola = _visitas[ip]
        while cola and ahora - cola[0] > 60:
            cola.popleft()
        if len(cola) >= LIMITE_POR_MINUTO:
            return False
        cola.append(ahora)
        return True


class Portero(BaseHTTPRequestHandler):
    server_version = "MIGAL-Publicador"
    sys_version = ""

    def log_message(self, *args):  # silenciar el log por defecto (incluiría el token)
        pass

    def _responder(self, codigo, cuerpo=b"", tipo="text/plain; charset=utf-8", extra=None):
        self.send_response(codigo)
        for k, v in {**CABECERAS_SEGURIDAD, **(extra or {})}.items():
            self.send_header(k, v)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(cuerpo)

    def _via_tunel(self):
        return bool(self.headers.get("Cf-Connecting-Ip") or self.headers.get("Cf-Ray"))

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        visitante = self.headers.get("Cf-Connecting-Ip") or self.client_address[0]
        partes = urlsplit(self.path)

        if partes.path == "/estado":
            if self._via_tunel():
                return self._responder(404, b"No encontrado")
            return self._responder(200, json.dumps(ESTADO).encode(), "application/json")

        if not permitido_por_limite(visitante):
            log("429 demasiadas peticiones desde %s" % visitante)
            return self._responder(429, b"Demasiadas solicitudes. Intente en un minuto.")

        e = RUTA_ESTADO.match(partes.path)
        if e and not partes.query:
            return self._reenviar("%s/migal/estado-cuenta/%s" % (ESTADO["odoo"], e.group(1)), "estado de cuenta", visitante)

        m = RUTA_PERMITIDA.match(partes.path)
        qs = parse_qs(partes.query)
        token = (qs.get("access_token") or [""])[0]
        if not (m and TOKEN_RE.match(token) and qs.get("report_type") == ["pdf"] and set(qs) <= {"access_token", "report_type"}):
            log("404 ruta no permitida: %s" % partes.path[:60])
            return self._responder(404, b"No encontrado")

        destino = "%s/my/orders/%s?access_token=%s&report_type=pdf" % (ESTADO["odoo"], m.group(1), token)
        return self._reenviar(destino, "cotización id %s" % m.group(1), visitante)

    def _reenviar(self, destino, que, visitante):
        req = urllib.request.Request(destino, headers={"User-Agent": "MIGAL-Publicador"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                tipo = resp.headers.get("Content-Type", "")
                cuerpo = resp.read(25 * 1024 * 1024)
                final = resp.geturl()
        except (urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
                log("404 %s no disponible o caducado" % que)
                return self._responder(404, b"No encontrado o caducado")
            log("502 Odoo no respondió para %s (%s)" % (que, exc.__class__.__name__))
            return self._responder(502, b"Servicio no disponible temporalmente.")
        # Si Odoo redirige (token inválido -> /my o login) no es un PDF: 404 genérico, sin revelar nada.
        if not tipo.startswith("application/pdf") or "/web/login" in final:
            log("404 token inválido o %s no disponible" % que)
            return self._responder(404, b"No encontrado")
        log("200 PDF de %s entregado a %s" % (que, visitante))
        nombre = "Estado-de-cuenta-MIGAL.pdf" if "estado" in que else "Cotizacion-MIGAL.pdf"
        return self._responder(200, cuerpo, "application/pdf",
                               {"Content-Disposition": 'inline; filename="%s"' % nombre})


def iniciar_tunel(cloudflared, puerto):
    cmd = [str(cloudflared), "tunnel", "--no-autoupdate", "--url", "http://127.0.0.1:%s" % puerto]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace",
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    def leer():
        for linea in proc.stdout:
            m = URL_TUNEL_RE.search(linea)
            if m and not ESTADO["url_publica"]:
                ESTADO["url_publica"] = m.group(0)
                ESTADO["desde"] = time.strftime("%Y-%m-%d %H:%M:%S")
                log("Túnel activo: %s" % ESTADO["url_publica"])
            elif " ERR " in linea:
                log("cloudflared: %s" % linea.strip()[:200])
        ESTADO["url_publica"] = None
        log("El túnel se cerró.")

    threading.Thread(target=leer, daemon=True).start()
    return proc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--odoo", default="http://127.0.0.1:8069", help="Dirección local de Odoo")
    ap.add_argument("--puerto", type=int, default=8090, help="Puerto local del portero")
    ap.add_argument("--cloudflared", default=str(BASE / "cloudflared" / "cloudflared.exe"))
    args = ap.parse_args()

    cloudflared = Path(args.cloudflared)
    if not cloudflared.exists() and not shutil.which("cloudflared"):
        sys.exit("No encuentro cloudflared en %s" % cloudflared)
    try:
        urllib.request.urlopen(args.odoo + "/web/login", timeout=10)
    except Exception:
        sys.exit("Odoo no responde en %s. Arranque Odoo primero." % args.odoo)

    ESTADO["odoo"] = args.odoo.rstrip("/")
    servidor = ThreadingHTTPServer(("127.0.0.1", args.puerto), Portero)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    log("Portero escuchando en http://127.0.0.1:%s (solo PDFs de cotizaciones con token)" % args.puerto)

    proc = iniciar_tunel(cloudflared, args.puerto)
    detener = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: detener.set())
    log("Abriendo el túnel... (Ctrl+C para cerrar y despublicar)")
    try:
        while not detener.is_set() and proc.poll() is None:
            time.sleep(0.5)
    finally:
        ESTADO["url_publica"] = None
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
        servidor.shutdown()
        log("Publicación cerrada: los QR emitidos ya no abren.")


if __name__ == "__main__":
    main()
