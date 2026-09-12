# -*- coding: utf-8 -*-
"""
Llena la base con marcas de ejemplo para fotografiar la aplicacion durante la
compilacion. No forma parte del programa que se instala.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from datetime import date, timedelta

import nucleo as N

HOY = date.today()


def f(dias_atras):
    """Fecha relativa: asi el ejemplo sirve cualquier dia que se compile."""
    return (HOY - timedelta(days=dias_atras)).isoformat()

d = N.Datos()
if d.total_marcas():
    print("ya tenia marcas"); sys.exit(0)

for t in d.trabajadores():
    d.desactivar_trabajador(t["id"])

# Valor hora sacado del contrato: 553.553 / 30 x 7 / 42 = 3.075
juan = d.agregar_trabajador("Juan Perez", 3075)
ana = d.agregar_trabajador("Ana Soto", 3075)
carlos = d.agregar_trabajador("Carlos Mena", 3075)

def dia(tid, fecha, ent, ci, cf, sal):
    for tipo, hora in (("entrada", ent), ("colacion_inicio", ci),
                       ("colacion_fin", cf), ("salida", sal)):
        if hora:
            d.agregar_marca(tid, fecha, tipo, hora)

# Turnos del contrato: 08:30-12:00 y 13:00-16:30, o 11:00-14:30 y 15:30-19:00.
# Todo termina AYER, para que hoy quede libre y se vea la pantalla de marcar.
for n, sal in zip(range(6, 0, -1), ["19:30", "16:30", "16:30", "18:30", "16:30", "20:00"]):
    ci, cf = ("13:30", "14:30") if sal > "17:00" else ("12:00", "13:00")
    dia(juan, f(n), "08:30", ci, cf, sal)                    # varios dias con extra
for n in (3, 2, 1):
    dia(ana, f(n), "11:00", "14:30", "15:30", "19:00")       # justo el contrato
dia(carlos, f(3), "08:30", "12:00", "13:00", "16:30")
dia(carlos, f(2), "08:30", "12:00", None, None)              # dia incompleto
dia(carlos, f(1), "08:30", "13:30", "14:30", "20:30")

d.guardar_config({"horas_contrato": "7", "modo_extra": "fijo",
                  "valor_extra_global": "3900"})
# Algunos dias ya pagados, para que se vea el check.
for n in (6, 5, 4):
    d.marcar_pagado(juan, f(n))                    # dias pagados enteros
d.marcar_pagado(ana, f(3))

d.guardar_config({"negocio": "Carniceria El Buen Corte", "ciudad": "Loncoche",
                  "horas_contrato": "7", "umbral_semanal": "42",
                  "modo_extra": "fijo", "valor_extra_global": "3900"})
print("sembradas %d marcas en %d dias" % (d.total_marcas(), d.total_jornadas()))
