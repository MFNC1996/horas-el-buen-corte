# -*- coding: utf-8 -*-
"""
El cartero: saca de la cola los avisos y los manda por correo.

Va aparte del nucleo a proposito. Marcar guarda la marca y deja el aviso
encolado; esto lo envia despues, en otro hilo. Asi, si no hay internet o
el correo esta mal configurado, la gente igual puede marcar.
"""

import os
import smtplib
import socket
import ssl
import threading
from email.message import EmailMessage
from email.utils import formataddr

import nucleo as N

# Cada cuanto se revisa la cola, en segundos.
ESPERA = 60
# Cuanto se aguanta a un servidor que no responde.
PACIENCIA = 20


def _texto_error(e):
    """Traduce la falla a algo que el jefe pueda leer y arreglar."""
    if isinstance(e, smtplib.SMTPAuthenticationError):
        return ("La cuenta o la contrasena no fueron aceptadas. Si es Gmail, "
                "tiene que ser una CONTRASENA DE APLICACION, no la de la cuenta.")
    if isinstance(e, smtplib.SMTPRecipientsRefused):
        return "El servidor rechazo la direccion del trabajador."
    if isinstance(e, smtplib.SMTPSenderRefused):
        return "El servidor rechazo la casilla que envia."
    if isinstance(e, (socket.gaierror, socket.timeout, TimeoutError)):
        return "No se pudo llegar al servidor de correo: revisa el internet."
    if isinstance(e, ConnectionError):
        return "Se corto la conexion con el servidor de correo."
    if isinstance(e, ssl.SSLError):
        return "Falla de seguridad al conectar: revisa el puerto (587 o 465)."
    return str(e) or e.__class__.__name__


def configurado(cfg):
    """Hay cuenta y clave como para intentar enviar algo."""
    return bool((cfg.get("correo_usuario") or "").strip()
                and (cfg.get("correo_clave") or "").strip()
                and (cfg.get("correo_servidor") or "").strip())


def conectar(cfg):
    """Abre la sesion con el servidor. El que llama se encarga de cerrarla."""
    servidor = (cfg.get("correo_servidor") or "").strip()
    try:
        puerto = int(float(cfg.get("correo_puerto") or 587))
    except (TypeError, ValueError):
        puerto = 587
    usuario = (cfg.get("correo_usuario") or "").strip()
    clave = cfg.get("correo_clave") or ""
    if puerto == 465:
        s = smtplib.SMTP_SSL(servidor, puerto, timeout=PACIENCIA,
                             context=ssl.create_default_context())
    else:
        s = smtplib.SMTP(servidor, puerto, timeout=PACIENCIA)
        s.ehlo()
        s.starttls(context=ssl.create_default_context())
        s.ehlo()
    s.login(usuario, clave)
    return s


def armar(cfg, para, asunto, cuerpo):
    m = EmailMessage()
    de = (cfg.get("correo_usuario") or "").strip()
    m["From"] = formataddr((cfg.get("negocio") or N.NEGOCIO_DEF, de))
    m["To"] = para
    m["Subject"] = asunto
    m.set_content(cuerpo)
    return m


def enviar_uno(sesion, cfg, para, asunto, cuerpo):
    sesion.send_message(armar(cfg, para, asunto, cuerpo))


def vaciar_cola(datos, limite=20):
    """
    Manda lo que este esperando. Devuelve (enviados, fallidos).

    Si no se puede ni conectar, se le anota el error a los que estaban en
    la cola y se vuelve a intentar en la proxima vuelta.
    """
    cfg = datos.config()
    if cfg.get("correo_activo", "0") != "1" or not configurado(cfg):
        return 0, 0
    cola = datos.correos_por_enviar(limite)
    if not cola:
        return 0, 0
    try:
        sesion = conectar(cfg)
    except Exception as e:                      # servidor caido, sin internet...
        for c in cola:
            datos.correo_fallo(c["id"], _texto_error(e))
        return 0, len(cola)
    enviados = fallidos = 0
    try:
        for c in cola:
            try:
                enviar_uno(sesion, cfg, c["para"], c["asunto"], c["cuerpo"])
                datos.correo_enviado(c["id"])
                enviados += 1
            except Exception as e:
                datos.correo_fallo(c["id"], _texto_error(e))
                fallidos += 1
    finally:
        try:
            sesion.quit()
        except Exception:
            pass
    return enviados, fallidos


def probar(cfg, destino=None):
    """
    Manda un correo de prueba a la misma casilla que envia.

    Devuelve el texto que se muestra en pantalla; si algo falla, levanta
    ValueError ya traducido.
    """
    if not configurado(cfg):
        raise ValueError("Falta llenar el servidor, la cuenta o la contrasena.")
    destino = destino or (cfg.get("correo_usuario") or "").strip()
    negocio = cfg.get("negocio") or N.NEGOCIO_DEF
    try:
        sesion = conectar(cfg)
    except Exception as e:
        raise ValueError(_texto_error(e))
    try:
        enviar_uno(sesion, cfg, destino,
                   "Prueba del Control de Horas - %s" % negocio,
                   "Este es un correo de prueba.\n\n"
                   "Si te llego, los avisos de marcacion van a salir bien.\n\n"
                   "--\nControl de Horas de %s." % negocio)
    except Exception as e:
        raise ValueError(_texto_error(e))
    finally:
        try:
            sesion.quit()
        except Exception:
            pass
    return "Correo de prueba enviado a %s. Revisa esa casilla." % destino


class Cartero(threading.Thread):
    """
    Revisa la cola cada tanto, en su propio hilo y con su propia conexion
    a la base (sqlite no deja compartirla entre hilos).
    """

    def __init__(self, ruta, espera=ESPERA):
        threading.Thread.__init__(self, name="cartero", daemon=True)
        self.ruta = ruta
        self.espera = espera
        self._parar = threading.Event()
        self._despierta = threading.Event()
        self.ultimo = (0, 0)

    def apurar(self):
        """Para no esperar la vuelta completa despues de una marcacion."""
        self._despierta.set()

    def detener(self):
        self._parar.set()
        self._despierta.set()

    def run(self):
        datos = None
        try:
            while not self._parar.is_set():
                try:
                    if datos is None:
                        datos = N.Datos(self.ruta)
                    self.ultimo = vaciar_cola(datos)
                except Exception:
                    # Ni siquiera una base bloqueada puede voltear el hilo.
                    try:
                        if datos is not None:
                            datos.cerrar()
                    except Exception:
                        pass
                    datos = None
                self._despierta.wait(self.espera)
                self._despierta.clear()
        finally:
            if datos is not None:
                try:
                    datos.cerrar()
                except Exception:
                    pass


def arrancar(ruta, espera=ESPERA):
    """Deja el cartero andando. Devuelve None si se pidio no arrancarlo."""
    if os.environ.get("CH_SIN_CORREO"):          # para las pruebas
        return None
    c = Cartero(ruta, espera)
    c.start()
    return c
