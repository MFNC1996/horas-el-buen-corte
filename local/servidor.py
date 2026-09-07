#!/usr/bin/env python3
"""
Servidor local del control de horas de Carniceria El Buen Corte.

Solo usa la libreria estandar de Python 3: no hay que instalar nada.
Guarda todo en datos.sqlite3, al lado de este archivo.

    python3 servidor.py

Despues abre la direccion que imprime en pantalla. Los celulares que esten
en la misma red WiFi pueden entrar a esa misma direccion.
"""

import http.server
import json
import os
import shutil
import socket
import sqlite3
import sys
import threading
import time
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(AQUI, "datos.sqlite3")
PAGINA = os.path.join(AQUI, "index.html")
RESPALDOS = os.path.join(AQUI, "respaldos")
PUERTO_PREFERIDO = 8080
RESPALDOS_A_GUARDAR = 30

_candado = threading.Lock()


# --------------------------------------------------------------- base de datos
def conectar():
    cx = sqlite3.connect(BASE, timeout=10)
    cx.execute("PRAGMA journal_mode=WAL")
    return cx


def preparar_base():
    with conectar() as cx:
        cx.execute("""CREATE TABLE IF NOT EXISTS documentos (
                        ruta  TEXT PRIMARY KEY,
                        datos TEXT NOT NULL
                      )""")
        cx.execute("""CREATE TABLE IF NOT EXISTS meta (
                        clave TEXT PRIMARY KEY,
                        valor TEXT NOT NULL
                      )""")
        cx.execute("INSERT OR IGNORE INTO meta VALUES ('version', '1')")


def version_actual():
    with _candado, conectar() as cx:
        return int(cx.execute("SELECT valor FROM meta WHERE clave='version'").fetchone()[0])


def leer_todo():
    with _candado, conectar() as cx:
        version = cx.execute("SELECT valor FROM meta WHERE clave='version'").fetchone()[0]
        filas = cx.execute("SELECT ruta, datos FROM documentos").fetchall()
    return {"version": int(version),
            "docs": {ruta: json.loads(datos) for ruta, datos in filas}}


def subir_version(cx):
    cx.execute("UPDATE meta SET valor = CAST(CAST(valor AS INTEGER) + 1 AS TEXT) "
               "WHERE clave='version'")


def escribir(ruta, datos):
    with _candado, conectar() as cx:
        cx.execute("INSERT INTO documentos (ruta, datos) VALUES (?, ?) "
                   "ON CONFLICT(ruta) DO UPDATE SET datos=excluded.datos",
                   (ruta, json.dumps(datos, ensure_ascii=False)))
        subir_version(cx)


def borrar(ruta):
    with _candado, conectar() as cx:
        cx.execute("DELETE FROM documentos WHERE ruta = ?", (ruta,))
        subir_version(cx)


def sembrar_si_esta_vacia():
    """Primera vez: deja la configuracion por defecto y tres trabajadores."""
    with _candado, conectar() as cx:
        if cx.execute("SELECT COUNT(*) FROM documentos").fetchone()[0]:
            return False
        inicial = {
            "config/general":   {"umbralDiario": 8, "umbralSemanal": 45, "regla": "diaria"},
            "trabajadores/t1":  {"nombre": "Trabajador 1", "orden": 1},
            "trabajadores/t2":  {"nombre": "Trabajador 2", "orden": 2},
            "trabajadores/t3":  {"nombre": "Trabajador 3", "orden": 3},
        }
        for ruta, datos in inicial.items():
            cx.execute("INSERT INTO documentos (ruta, datos) VALUES (?, ?)",
                       (ruta, json.dumps(datos, ensure_ascii=False)))
        subir_version(cx)
    return True


def respaldar():
    """Copia la base una vez al dia y conserva los ultimos 30 dias."""
    if not os.path.exists(BASE):
        return
    os.makedirs(RESPALDOS, exist_ok=True)
    destino = os.path.join(RESPALDOS, "datos-%s.sqlite3" % date.today().isoformat())
    if not os.path.exists(destino):
        try:
            with conectar() as cx:
                otro = sqlite3.connect(destino)
                cx.backup(otro)
                otro.close()
        except Exception as e:
            print("  aviso: no se pudo respaldar (%s)" % e)
            return
    viejos = sorted(f for f in os.listdir(RESPALDOS) if f.startswith("datos-"))
    for f in viejos[:-RESPALDOS_A_GUARDAR]:
        try:
            os.remove(os.path.join(RESPALDOS, f))
        except OSError:
            pass


# ------------------------------------------------------------------- servidor
class Manejador(http.server.BaseHTTPRequestHandler):
    server_version = "HorasElBuenCorte"

    def log_message(self, formato, *args):
        pass  # sin ruido en la consola

    # -- utilidades ---------------------------------------------------------
    def responder(self, codigo, cuerpo, tipo="application/json; charset=utf-8"):
        if isinstance(cuerpo, str):
            cuerpo = cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(cuerpo)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def cuerpo_json(self):
        largo = int(self.headers.get("Content-Length") or 0)
        if largo <= 0 or largo > 1_000_000:
            return None
        try:
            return json.loads(self.rfile.read(largo).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    @staticmethod
    def ruta_valida(ruta):
        if not isinstance(ruta, str) or not ruta or len(ruta) > 400:
            return False
        partes = ruta.split("/")
        if len(partes) % 2 or len(partes) > 8:
            return False
        permitido = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")
        return all(p and p not in (".", "..") and set(p) <= permitido for p in partes)

    # -- rutas --------------------------------------------------------------
    def do_GET(self):
        camino = self.path.split("?")[0]
        if camino in ("/", "/index.html"):
            try:
                with open(PAGINA, "rb") as f:
                    return self.responder(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                return self.responder(500, "Falta index.html al lado de servidor.py",
                                      "text/plain; charset=utf-8")
        if camino == "/api/docs":
            # El cliente manda ?version=N; si nada cambio devolvemos una
            # respuesta minima en vez de toda la base.
            pedida = None
            if "?" in self.path:
                for par in self.path.split("?", 1)[1].split("&"):
                    if par.startswith("version="):
                        try:
                            pedida = int(par[8:])
                        except ValueError:
                            pedida = None
            actual = version_actual()
            if pedida is not None and pedida == actual:
                return self.responder(200, '{"version":%d,"sinCambios":true}' % actual)
            return self.responder(200, json.dumps(leer_todo(), ensure_ascii=False))
        self.responder(404, '{"error":"no existe"}')

    def do_POST(self):
        camino = self.path.split("?")[0]
        cuerpo = self.cuerpo_json()
        if cuerpo is None:
            return self.responder(400, '{"error":"cuerpo invalido"}')
        ruta = cuerpo.get("ruta")
        if not self.ruta_valida(ruta):
            return self.responder(400, '{"error":"ruta invalida"}')

        if camino == "/api/set":
            datos = cuerpo.get("datos")
            if not isinstance(datos, dict):
                return self.responder(400, '{"error":"datos invalidos"}')
            escribir(ruta, datos)
            return self.responder(200, '{"ok":true}')

        if camino == "/api/borrar":
            borrar(ruta)
            return self.responder(200, '{"ok":true}')

        self.responder(404, '{"error":"no existe"}')


class Servidor(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


# ----------------------------------------------------------------------- main
def ip_de_la_red():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.168.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def nombre_mdns():
    """Nombre .local del equipo, o None si no hay uno usable.

    gethostname() a veces devuelve la IP en vez de un nombre; en ese caso
    anunciar "http://192.local" seria peor que no decir nada.
    """
    try:
        crudo = socket.gethostname()
    except OSError:
        return None
    nombre = crudo.split(".")[0].strip().lower()
    if not nombre or not any(c.isalpha() for c in nombre):
        return None
    if not all(c.isalnum() or c == "-" for c in nombre):
        return None
    return nombre


def elegir_puerto():
    for puerto in range(PUERTO_PREFERIDO, PUERTO_PREFERIDO + 20):
        try:
            s = socket.socket()
            s.bind(("", puerto))
            s.close()
            return puerto
        except OSError:
            continue
    return None


def main():
    # Sin esto, al redirigir la salida a un archivo (como hacen los
    # instaladores) el banner con la direccion queda atrapado en el bufer
    # y el usuario no lo ve.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    if not os.path.exists(PAGINA):
        print("ERROR: falta index.html en la misma carpeta que servidor.py.")
        return 1

    preparar_base()
    primera = sembrar_si_esta_vacia()
    respaldar()

    puerto = elegir_puerto()
    if puerto is None:
        print("ERROR: no hay puertos libres entre %d y %d."
              % (PUERTO_PREFERIDO, PUERTO_PREFERIDO + 19))
        return 1

    ip = ip_de_la_red()
    linea = "=" * 58
    print("\n" + linea)
    print("  CONTROL DE HORAS  --  El Buen Corte, Loncoche")
    print(linea)
    if primera:
        print("  Base de datos creada con 3 trabajadores de ejemplo.")
        print("  Cambiales el nombre en la pestana Ajustes.\n")
    print("  En este computador:      http://localhost:%d" % puerto)
    if ip:
        print("  Desde los celulares:     http://%s:%d" % (ip, puerto))
        nombre = nombre_mdns()
        if nombre:
            print("  Direccion estable:       http://%s.local:%d" % (nombre, puerto))
            print("  (esta no cambia aunque el router le cambie la IP al equipo)")
        print("  Los celulares tienen que estar en la misma red WiFi.")
    else:
        print("  Sin red detectada: solo funciona en este computador.")
    print("\n  Datos:     %s" % BASE)
    print("  Respaldos: %s" % RESPALDOS)
    print("\n  Para apagarlo: Control + C, o cierra esta ventana.")
    print(linea + "\n")

    servidor = Servidor(("0.0.0.0", puerto), Manejador)
    hilo = threading.Thread(target=respaldo_diario, daemon=True)
    hilo.start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido. Los datos quedaron guardados.\n")
    finally:
        servidor.server_close()
    return 0


def respaldo_diario():
    while True:
        time.sleep(6 * 60 * 60)
        try:
            respaldar()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
