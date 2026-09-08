# -*- coding: utf-8 -*-
"""
Llena la base con datos de ejemplo para sacarle capturas a la aplicacion
durante la compilacion. No forma parte del programa que se instala.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import nucleo as N

d = N.Datos()
if d.total_jornadas():
    print("ya tenia datos"); sys.exit(0)

for t in d.trabajadores():
    d.desactivar_trabajador(t["id"])

juan = d.agregar_trabajador("Juan Perez", 3000)
ana = d.agregar_trabajador("Ana Soto", 4000)
carlos = d.agregar_trabajador("Carlos Mena", 3500)

for dia in range(7, 13):
    d.guardar_jornada(None, juan, "2026-09-%02d" % dia, "09:00", "19:00", 60)
d.guardar_jornada(None, ana, "2026-09-08", "10:00", "18:30", 30)
d.guardar_jornada(None, ana, "2026-09-09", "22:00", "06:00", 0, "turno de noche")
d.guardar_jornada(None, ana, "2026-09-10", "10:00", "18:30", 30)
d.guardar_jornada(None, carlos, "2026-09-07", "08:00", "17:00", 45)
d.guardar_jornada(None, carlos, "2026-09-08", "08:00", "20:30", 60)
d.guardar_jornada(None, carlos, "2026-09-09", "08:00", "17:00", 45)
d.guardar_config({"negocio": "Carniceria El Buen Corte", "ciudad": "Loncoche"})
print("sembradas %d jornadas" % d.total_jornadas())
