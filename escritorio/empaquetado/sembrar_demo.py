# -*- coding: utf-8 -*-
"""
Llena la base con marcas de ejemplo para fotografiar la aplicacion durante la
compilacion. No forma parte del programa que se instala.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import nucleo as N

d = N.Datos()
if d.total_marcas():
    print("ya tenia marcas"); sys.exit(0)

for t in d.trabajadores():
    d.desactivar_trabajador(t["id"])

juan = d.agregar_trabajador("Juan Perez", 3000)
ana = d.agregar_trabajador("Ana Soto", 4000)
carlos = d.agregar_trabajador("Carlos Mena", 3500)

def dia(tid, fecha, ent, ci, cf, sal):
    for tipo, hora in (("entrada", ent), ("colacion_inicio", ci),
                       ("colacion_fin", cf), ("salida", sal)):
        if hora:
            d.agregar_marca(tid, fecha, tipo, hora)

for n in range(7, 13):                                  # Juan: 54 h -> 9 extra
    dia(juan, "2026-09-%02d" % n, "09:00", "13:00", "14:00", "19:00")
dia(ana, "2026-09-08", "10:00", "13:30", "14:00", "18:30")
dia(ana, "2026-09-09", "22:00", "01:00", "01:30", "06:00")   # turno de noche
dia(ana, "2026-09-10", "10:00", "13:30", "14:00", "18:30")
dia(carlos, "2026-09-08", "08:00", "13:00", "13:45", "17:00")
dia(carlos, "2026-09-09", "08:00", "13:00", None, None)      # dia incompleto
dia(carlos, "2026-09-10", "08:00", "13:00", "14:00", "20:30")

d.guardar_config({"negocio": "Carniceria El Buen Corte", "ciudad": "Loncoche",
                  "umbral_semanal": "45", "modo_extra": "fijo",
                  "valor_extra_global": "5200"})
print("sembradas %d marcas en %d dias" % (d.total_marcas(), d.total_jornadas()))
