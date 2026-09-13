# -*- coding: utf-8 -*-
"""
Avisarle a Windows que falta algo antes de apagar el computador.

Cuando alguien apaga Windows, el sistema le pregunta a cada programa si puede
cerrar (WM_QUERYENDSESSION). Si contestamos que no, Windows muestra la pantalla
de "esta aplicacion impide que se cierre la sesion" con el motivo que dejamos
registrado, y el programa alcanza a avisar en pantalla.

IMPORTANTE, y hay que decirlo claro: esto NO detiene un apagado forzado. Ni el
boton "Apagar de todas formas" de esa misma pantalla, ni `shutdown /f`, ni
mantener apretado el boton del computador. Ningun programa puede impedir eso.
Por si acaso, lo que quedo en la cola se manda igual la proxima vez que se abra
el programa.

Se avisa UNA sola vez: al segundo intento se deja apagar, para no dejar a nadie
peleando con su computador.
"""

import ctypes
import sys

WM_QUERYENDSESSION = 0x0011
GWLP_WNDPROC = -4

SEGUIR, BLOQUEAR = "seguir", "bloquear"


def decidir(mensaje, hay_pendiente, ya_aviso):
    """
    Que hacer con un mensaje de Windows. Aparte para poder probarlo sin Windows.

    Solo se bloquea el primer intento de apagado, y solo si de verdad quedo
    algo sin mandar.
    """
    if mensaje != WM_QUERYENDSESSION:
        return SEGUIR
    if not hay_pendiente or ya_aviso:
        return SEGUIR
    return BLOQUEAR


class Guardia(object):
    """Se mete en medio de los mensajes de la ventana para atajar el apagado."""

    def __init__(self, ventana, hay_pendiente, avisar, motivo):
        self.ventana = ventana
        self.hay_pendiente = hay_pendiente    # funcion: queda algo por mandar?
        self.avisar = avisar                  # funcion: mostrar el aviso
        self.motivo = motivo
        self.ya_aviso = False
        self._hwnd = None
        self._anterior = None
        self._callback = None

    # -- armado ---------------------------------------------------------
    def instalar(self):
        if not sys.platform.startswith("win"):
            return False
        try:
            u = ctypes.windll.user32
            hwnd = self.ventana.winfo_id()
            padre = u.GetParent(hwnd)          # la ventana con barra de titulo
            self._hwnd = padre or hwnd
            tipo = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_void_p,
                                      ctypes.c_uint, ctypes.c_size_t,
                                      ctypes.c_ssize_t)
            self._callback = tipo(self._mensaje)
            poner = getattr(u, "SetWindowLongPtrW", None) or u.SetWindowLongW
            poner.restype = ctypes.c_void_p
            poner.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
            self._anterior = poner(self._hwnd, GWLP_WNDPROC,
                                   ctypes.cast(self._callback, ctypes.c_void_p))
            return bool(self._anterior)
        except Exception:
            self._anterior = None
            return False

    def soltar(self):
        """Devuelve la ventana a como estaba y saca el motivo del apagado."""
        try:
            u = ctypes.windll.user32
            if self._anterior:
                poner = getattr(u, "SetWindowLongPtrW", None) or u.SetWindowLongW
                poner(self._hwnd, GWLP_WNDPROC, self._anterior)
                self._anterior = None
            if self._hwnd:
                u.ShutdownBlockReasonDestroy(self._hwnd)
        except Exception:
            pass

    # -- lo que pasa cuando Windows pregunta ----------------------------
    def _mensaje(self, hwnd, mensaje, wparam, lparam):
        try:
            if decidir(mensaje, bool(self.hay_pendiente()), self.ya_aviso) == BLOQUEAR:
                self.ya_aviso = True
                try:
                    ctypes.windll.user32.ShutdownBlockReasonCreate(
                        ctypes.c_void_p(self._hwnd), ctypes.c_wchar_p(self.motivo))
                except Exception:
                    pass
                # El aviso se muestra despues, no dentro del mensaje de Windows.
                self.ventana.after(50, self.avisar)
                return 0                        # 0 = todavia no, por favor
            if mensaje == WM_QUERYENDSESSION:
                try:
                    ctypes.windll.user32.ShutdownBlockReasonDestroy(
                        ctypes.c_void_p(self._hwnd))
                except Exception:
                    pass
        except Exception:
            pass                                # ante la duda, dejar apagar
        return ctypes.windll.user32.CallWindowProcW(
            ctypes.c_void_p(self._anterior), ctypes.c_void_p(hwnd),
            ctypes.c_uint(mensaje), ctypes.c_size_t(wparam),
            ctypes.c_ssize_t(lparam))


def cuidar(ventana, hay_pendiente, avisar, motivo):
    """Deja el guardia puesto. Devuelve None si no se pudo (o no es Windows)."""
    g = Guardia(ventana, hay_pendiente, avisar, motivo)
    return g if g.instalar() else None
