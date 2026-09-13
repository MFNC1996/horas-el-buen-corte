# -*- coding: utf-8 -*-
"""
Pruebas del aviso por correo. No manda nada de verdad: reemplaza al
servidor por uno de mentira que anota lo que se le pide enviar.

    python probar_correo.py
"""

import os
import smtplib
import socket
import sys
import tempfile
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as N
import correo as C

fallas = []


def check(que, ok):
    print(("  ok   " if ok else "FALLA ") + que)
    if not ok:
        fallas.append(que)


# ------------------------------------------------ servidor de correo falso
class SesionFalsa(object):
    """Se hace pasar por la sesion SMTP y guarda lo que se le manda."""

    def __init__(self, rechaza=None):
        self.enviados = []
        self.rechaza = rechaza       # direccion que va a rebotar
        self.cerrada = False

    def send_message(self, m):
        if self.rechaza and m["To"] == self.rechaza:
            raise smtplib.SMTPRecipientsRefused({m["To"]: (550, b"no such user")})
        self.enviados.append(m)

    def quit(self):
        self.cerrada = True


def con_servidor(sesion_o_error):
    """Devuelve un reemplazo de C.conectar que entrega esta sesion, o falla."""
    def conectar(cfg):
        if isinstance(sesion_o_error, Exception):
            raise sesion_o_error
        return sesion_o_error
    return conectar


def base(activo="1", correo="ana@gmail.com"):
    d = N.Datos(os.path.join(tempfile.mkdtemp(), "h.sqlite3"))
    d.guardar_config({"correo_activo": activo,
                      "correo_servidor": "smtp.gmail.com",
                      "correo_puerto": "587",
                      "correo_usuario": "carniceria@gmail.com",
                      "correo_clave": "clave-de-aplicacion"})
    tid = d.agregar_trabajador("Ana Soto", 3075, correo=correo)
    return d, tid


print("--- la direccion del trabajador ---")
check("acepta una direccion normal",
      N.limpiar_correo(" Ana@Gmail.com ") == "Ana@Gmail.com")
check("deja vacio lo vacio", N.limpiar_correo("") == "" and N.limpiar_correo(None) == "")
for malo in ("ana", "ana@", "@gmail.com", "ana@gmail", "ana gomez@gmail.com",
             "ana@@gmail.com", "ana@gmail."):
    try:
        N.limpiar_correo(malo)
        check("rechaza '%s'" % malo, False)
    except ValueError:
        check("rechaza '%s'" % malo, True)

d, tid = base()
check("se guarda con el trabajador", d.trabajador(tid)["correo"] == "ana@gmail.com")
d.editar_trabajador(tid, "Ana Soto", 3075, correo="otra@gmail.com")
check("se puede cambiar", d.trabajador(tid)["correo"] == "otra@gmail.com")
d.editar_trabajador(tid, "Ana Soto", 3075, correo="")
check("y se puede dejar sin correo", d.trabajador(tid)["correo"] == "")

print("\n--- la cuenta que envia viene puesta ---")
limpia = N.Datos(os.path.join(tempfile.mkdtemp(), "limpia.sqlite3"))
check("una base nueva ya trae la casilla del negocio",
      limpia.config()["correo_usuario"] == "marcacion.elbuencorte@gmail.com")
check("pero no trae contrasena", limpia.config()["correo_clave"] == "")
check("ni viene encendido", limpia.config()["correo_activo"] == "0")
limpia.guardar_config({"correo_usuario": "otra@gmail.com"})
ruta_l = limpia.ruta
limpia.cerrar()
check("si el jefe la cambia, no se la pisamos",
      N.Datos(ruta_l).config()["correo_usuario"] == "otra@gmail.com")

print("\n--- al marcar se encola el aviso ---")
d, tid = base()
r = d.marcar(tid, datetime(2026, 9, 14, 8, 30))
check("la marca dice a quien se le avisa", r["correo"] == "ana@gmail.com")
cola = d.correos_por_enviar()
check("quedo uno en la cola", len(cola) == 1)
check("va a la direccion del trabajador", cola[0]["para"] == "ana@gmail.com")
check("el asunto dice que marco y a que hora",
      "Entrada" in cola[0]["asunto"] and "08:30" in cola[0]["asunto"])
check("el asunto lleva el nombre del negocio",
      N.NEGOCIO_DEF in cola[0]["asunto"])
cuerpo = cola[0]["cuerpo"]
check("el cuerpo lo saluda por su nombre", "Ana Soto" in cuerpo)
check("dice la fecha con todas sus letras", "lunes 14 de septiembre" in cuerpo)
check("muestra las cuatro marcas del dia",
      all(e in cuerpo for e in N.ETIQUETAS.values()))
check("las que faltan salen vacias", cuerpo.count("--:--") == 3)
check("avisa que no hay que responderlo", "No respondas" in cuerpo)

d.marcar(tid, datetime(2026, 9, 14, 13, 30))
d.marcar(tid, datetime(2026, 9, 14, 14, 0))
r = d.marcar(tid, datetime(2026, 9, 14, 18, 0))
ultimo = d.correos_por_enviar()[-1]
check("un aviso por cada marca", len(d.correos_por_enviar()) == 4)
check("el ultimo avisa que la jornada quedo completa",
      "Jornada completa" in ultimo["cuerpo"])
check("y con cuantas horas", "9:00" in ultimo["cuerpo"])

print("\n--- cuando no corresponde avisar ---")
d, tid = base(activo="0")
d.marcar(tid, datetime(2026, 9, 14, 8, 30))
check("apagado, no encola nada", d.correos_por_enviar() == [])
d, tid = base(correo="")
r = d.marcar(tid, datetime(2026, 9, 14, 8, 30))
check("sin correo del trabajador, tampoco",
      d.correos_por_enviar() == [] and r["correo"] is None)
check("pero la marca quedo igual", len(d.marcas_de(tid, "2026-09-14")) == 1)

print("\n--- enviar la cola ---")
d, tid = base()
d.marcar(tid, datetime(2026, 9, 14, 8, 30))
d.marcar(tid, datetime(2026, 9, 14, 13, 30))
sesion = SesionFalsa()
C.conectar, original = con_servidor(sesion), C.conectar
enviados, fallidos = C.vaciar_cola(d)
check("manda los dos", (enviados, fallidos) == (2, 0) and len(sesion.enviados) == 2)
check("cierra la sesion", sesion.cerrada)
check("la cola queda vacia", d.correos_por_enviar() == [])
check("y quedan anotados como enviados", d.cuenta_correos()["enviados"] == 2)
m = sesion.enviados[0]
check("el remitente es la casilla configurada", "carniceria@gmail.com" in m["From"])
check("y se muestra con el nombre del negocio", N.NEGOCIO_DEF in m["From"])
check("el destinatario es el trabajador", m["To"] == "ana@gmail.com")
check("el texto viaja completo",
      "Ana Soto" in m.get_content() and "08:30" in m.get_content())
check("no manda dos veces lo mismo", C.vaciar_cola(d) == (0, 0))

print("\n--- sin internet, la marca no se pierde ---")
d, tid = base()
d.marcar(tid, datetime(2026, 9, 14, 8, 30))
C.conectar = con_servidor(socket.gaierror("sin dns"))
check("no se pudo enviar", C.vaciar_cola(d) == (0, 1))
check("sigue esperando en la cola", len(d.correos_por_enviar()) == 1)
check("con el error explicado", "internet" in d.ultimo_error_correo())
check("y lleva un intento", d.correos_por_enviar()[0]["intentos"] == 1)
sesion = SesionFalsa()
C.conectar = con_servidor(sesion)
check("cuando vuelve el internet, sale", C.vaciar_cola(d) == (1, 0))

print("\n--- despues de mucho fallar, se deja de insistir ---")
d, tid = base()
d.marcar(tid, datetime(2026, 9, 14, 8, 30))
C.conectar = con_servidor(socket.gaierror("sin dns"))
for _ in range(N.INTENTOS_CORREO + 3):
    C.vaciar_cola(d)
check("no insiste para siempre",
      d.correos_por_enviar() == [] and d.cuenta_correos()["perdidos"] == 1)
check("pero queda a la vista que no salio", d.cuenta_correos()["esperando"] == 0)
check("y se puede volver a intentar a mano", d.reintentar_correos() == 1)
check("vuelve a la cola", len(d.correos_por_enviar()) == 1)

print("\n--- la clave equivocada ---")
d, tid = base()
d.marcar(tid, datetime(2026, 9, 14, 8, 30))
C.conectar = con_servidor(
    smtplib.SMTPAuthenticationError(535, b"Username and Password not accepted"))
C.vaciar_cola(d)
check("dice que tiene que ser contrasena de aplicacion",
      "APLICACION" in d.ultimo_error_correo())

print("\n--- una direccion que rebota no frena a las demas ---")
d, _ = base()
uno = d.agregar_trabajador("Juan", 3000, correo="juan@gmail.com")
dos = d.agregar_trabajador("Pedro", 3000, correo="noexiste@gmail.com")
d.marcar(dos, datetime(2026, 9, 14, 8, 30))
d.marcar(uno, datetime(2026, 9, 14, 8, 31))
sesion = SesionFalsa(rechaza="noexiste@gmail.com")
C.conectar = con_servidor(sesion)
check("el bueno sale igual", C.vaciar_cola(d) == (1, 1))
check("y del malo queda dicho por que no",
      "rechazo la direccion" in d.ultimo_error_correo())

print("\n--- el boton de probar ---")
cfg = d.config()
sesion = SesionFalsa()
C.conectar = con_servidor(sesion)
texto = C.probar(cfg)
check("manda la prueba a la casilla que envia",
      sesion.enviados[0]["To"] == "carniceria@gmail.com")
check("y lo dice en pantalla", "carniceria@gmail.com" in texto)
C.conectar = con_servidor(smtplib.SMTPAuthenticationError(535, b"nope"))
try:
    C.probar(cfg)
    check("avisa si la clave esta mala", False)
except ValueError as e:
    check("avisa si la clave esta mala", "APLICACION" in str(e))
try:
    C.probar({"correo_usuario": "", "correo_clave": "", "correo_servidor": ""})
    check("avisa si falta llenar datos", False)
except ValueError as e:
    check("avisa si falta llenar datos", "Falta llenar" in str(e))
C.conectar = original

print("\n--- informe del dia para el dueno ---")
import apagado


def con_jefe(**extra):
    d = N.Datos(os.path.join(tempfile.mkdtemp(), "j.sqlite3"))
    cfg = {"informe_activo": "1", "correo_jefe": "jefe@gmail.com",
           "correo_usuario": "carniceria@gmail.com", "correo_clave": "clave",
           "modo_extra": "fijo", "valor_extra_global": "3900"}
    cfg.update(extra)
    d.guardar_config(cfg)
    return d


def jornada(d, tid, fecha, entrada="08:30", sale="19:30"):
    for tipo, h in (("entrada", entrada), ("colacion_inicio", "13:30"),
                    ("colacion_fin", "14:30"), ("salida", sale)):
        d.agregar_marca(tid, fecha, tipo, h)


d = con_jefe()
ana = d.agregar_trabajador("Ana Soto", 3075)
juan = d.agregar_trabajador("Juan Perez", 3075)
jornada(d, ana, "2026-09-10", sale="16:30")     # 7:00, sin extra
jornada(d, juan, "2026-09-10")                  # 10:00 = 7 + 3 extra
d.agregar_marca(ana, "2026-09-11", "entrada", "08:30")   # dia a medias
check("esta configurado", d.informe_configurado())
check("los dos dias estan por informar",
      d.dias_por_informar(N.date(2026, 9, 11)) == ["2026-09-10", "2026-09-11"])

asunto, cuerpo = d.texto_informe("2026-09-10")
check("el asunto dice de que dia es", "jueves 10 de septiembre" in asunto)
check("y de que negocio", N.NEGOCIO_DEF in asunto)
check("lista a los que trabajaron", "Ana Soto" in cuerpo and "Juan Perez" in cuerpo)
check("con sus horas como reloj", "10:00 h" in cuerpo)
check("separando normales y extra", "7:00 normales + 3:00 extra" in cuerpo)
check("dice cuanto vale el dia", "$33.225" in cuerpo)
check("y el total del dia", "Total del dia:" in cuerpo and "$54.750" in cuerpo)
check("marca lo que esta por pagar", "POR PAGAR" in cuerpo)
check("resume lo que se debe hasta hoy", "LO QUE SE DEBE HASTA HOY" in cuerpo)
check("con el total a pagar", "TOTAL POR PAGAR" in cuerpo)
check("avisa que van los archivos pegados", "Van pegados el Excel y el PDF" in cuerpo)

cuerpo_11 = d.texto_informe("2026-09-11")[1]
check("el dia a medias avisa que falta marcar",
      "falta marcar" in cuerpo_11 and "Salida" in cuerpo_11)

d.marcar_pagado(juan, "2026-09-10")
cuerpo2 = d.texto_informe("2026-09-10")[1]
check("lo pagado sale como pagado", "pagado" in cuerpo2)
check("y ya no se cuenta en lo que se debe",
      "Juan Perez" not in cuerpo2.split("LO QUE SE DEBE HASTA HOY")[1])

print("\n--- se manda una sola vez al dia ---")
d = con_jefe()
ana = d.agregar_trabajador("Ana Soto", 3075)
jornada(d, ana, "2026-09-10", sale="16:30")
check("hay uno por informar", d.dias_por_informar(N.date(2026, 9, 10)) == ["2026-09-10"])
check("se encola al jefe",
      d.encolar_informe("2026-09-10") == "jefe@gmail.com")
check("queda anotado como informado", d.config()["ultimo_informe"] == "2026-09-10")
check("y ya no pide mandarlo de nuevo",
      d.dias_por_informar(N.date(2026, 9, 10)) == [])
jornada(d, ana, "2026-09-11", sale="16:30")
check("al dia siguiente si", d.dias_por_informar(N.date(2026, 9, 11)) == ["2026-09-11"])
check("el informe no es de ningun trabajador",
      d.correos_por_enviar()[0]["trabajador_id"] is None)
check("si no hay correo del dueno, no se encola nada",
      con_jefe(correo_jefe="").encolar_informe("2026-09-10") is None)
check("apagado, no esta configurado",
      not con_jefe(informe_activo="0").informe_configurado())

print("\n--- si el computador estuvo apagado varios dias ---")
d = con_jefe()
ana = d.agregar_trabajador("Ana Soto", 3075)
for n in range(1, 13):
    jornada(d, ana, "2026-09-%02d" % n, sale="16:30")
pendientes = d.dias_por_informar(N.date(2026, 9, 12))
check("no manda doce correos de golpe", len(pendientes) == 7)
check("manda los ultimos siete", pendientes[-1] == "2026-09-12")

print("\n--- el informe viaja con el Excel y el PDF ---")
import informes
d = con_jefe()
ana = d.agregar_trabajador("Ana Soto", 3075)
jornada(d, ana, "2026-09-10")
adj = informes.bytes_del_mes(d, 2026, 9)
check("se arma el Excel y el PDF", len(adj) == 2)
check("el Excel tiene contenido", adj[0][0].endswith(".xlsx") and len(adj[0][1]) > 4000)
check("el PDF tambien", adj[1][0].endswith(".pdf") and len(adj[1][1]) > 2000)
check("un mes sin nada no arma archivos", informes.bytes_del_mes(d, 2025, 1) == [])
d.encolar_informe("2026-09-10", adj)
cid = d.correos_por_enviar()[0]["id"]
check("los adjuntos quedan guardados con el correo",
      [n for n, _ in d.adjuntos_de(cid)] == [a[0] for a in adj])
sesion = SesionFalsa()
C.conectar = con_servidor(sesion)
C.vaciar_cola(d)
m = sesion.enviados[0]
pegados = [(p.get_filename(), p.get_content_type()) for p in m.iter_attachments()]
check("y llegan pegados al correo", len(pegados) == 2)
check("el Excel como Excel", "spreadsheetml" in pegados[0][1])
check("el PDF como PDF", pegados[1][1] == "application/pdf")
check("va al correo del dueno", m["To"] == "jefe@gmail.com")
check("sale aunque el aviso al trabajador este apagado",
      d.config()["correo_activo"] == "0")
C.conectar = original

print("\n--- avisar antes de que Windows apague ---")
check("con algo pendiente, el primer intento se bloquea",
      apagado.decidir(apagado.WM_QUERYENDSESSION, True, False) == apagado.BLOQUEAR)
check("el segundo intento deja apagar",
      apagado.decidir(apagado.WM_QUERYENDSESSION, True, True) == apagado.SEGUIR)
check("sin nada pendiente no molesta",
      apagado.decidir(apagado.WM_QUERYENDSESSION, False, False) == apagado.SEGUIR)
check("los demas mensajes pasan de largo",
      apagado.decidir(0x0005, True, False) == apagado.SEGUIR)

print("\n--- limpieza de los viejos ---")
d, tid = base()
d.marcar(tid, datetime(2026, 9, 14, 8, 30))
cid = d.correos_por_enviar()[0]["id"]
d.correo_enviado(cid, datetime(2025, 1, 1, 10, 0))
check("borra los enviados hace mucho",
      d.purgar_correos(90, N.date(2026, 9, 14)) == 1)
d.marcar(tid, datetime(2026, 9, 14, 13, 30))
d.correo_enviado(d.correos_por_enviar()[0]["id"], datetime(2026, 9, 13, 10, 0))
check("y deja los de ahora", d.purgar_correos(90, N.date(2026, 9, 14)) == 0)

print("\n--- bases viejas ---")
ruta = os.path.join(tempfile.mkdtemp(), "vieja.sqlite3")
import sqlite3
cx = sqlite3.connect(ruta)
cx.execute("CREATE TABLE trabajadores (id INTEGER PRIMARY KEY AUTOINCREMENT, "
           "nombre TEXT NOT NULL, valor_hora REAL NOT NULL DEFAULT 0, "
           "activo INTEGER NOT NULL DEFAULT 1, orden INTEGER NOT NULL DEFAULT 0)")
cx.execute("INSERT INTO trabajadores (nombre, valor_hora) VALUES ('Vieja', 3000)")
cx.commit()
cx.close()
d = N.Datos(ruta)
check("le agrega la columna del correo sin romper nada",
      d.trabajador(1)["correo"] == "" and d.trabajador(1)["nombre"] == "Vieja")
d.editar_trabajador(1, "Vieja", 3000, correo="vieja@gmail.com")
check("y se le puede poner uno", d.trabajador(1)["correo"] == "vieja@gmail.com")

print("")
if fallas:
    print("%d FALLAS: %s" % (len(fallas), fallas))
    sys.exit(1)
print("TODO OK")
