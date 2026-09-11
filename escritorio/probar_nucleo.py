# -*- coding: utf-8 -*-
"""Pruebas del nucleo. Ejecutar:  python probar_nucleo.py"""
import os, sys, tempfile
# La consola de Windows usa cp1252 y no sabe escribir simbolos como el del
# check; asi las pruebas no se caen por algo que no tiene que ver con la app.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as N

fallas = []

def check(nombre, obtenido, esperado):
    ok = (round(obtenido, 2) == round(esperado, 2)) if isinstance(esperado, float) \
         else (obtenido == esperado)
    print(("  ok   " if ok else "FALLA ") + nombre + "  ->  " + str(obtenido) +
          ("" if ok else "   (esperado " + str(esperado) + ")"))
    if not ok:
        fallas.append(nombre)

print("--- horas trabajadas ---")
check("09:00-18:00 col 60", N.horas_trabajadas("09:00", "18:00", 60), 8.0)
check("08:00-19:30 col 45", N.horas_trabajadas("08:00", "19:30", 45), 10.75)
check("22:00-06:00 nocturno", N.horas_trabajadas("22:00", "06:00", 0), 8.0)
check("23:30-07:15 col 30", N.horas_trabajadas("23:30", "07:15", 30), 7.25)
check("hora invalida", N.horas_trabajadas("25:00", "09:00", 0), 0.0)

print("\n--- semana y fechas ---")
check("domingo -> lunes", N.lunes_de("2026-09-13"), "2026-09-07")
check("cruce de anio", N.lunes_de("2027-01-01"), "2026-12-28")
check("ultimo dia feb bisiesto", N.ultimo_dia(2028, 2), 29)
check("ultimo dia diciembre", N.ultimo_dia(2026, 12), 31)
check("formato pesos", N.pesos(1234567), "$1.234.567")
check("horas texto", N.horas_txt(10.5), "10,50")
check("hh:mm", N.hhmm_txt(10.5), "10:30")

print("\n--- valor de la hora extra ---")
t = {"valor_hora": 3000.0, "valor_hora_extra": 0.0}
check("recargo 50%", N.valor_hora_extra({"modo_extra": "recargo", "recargo_extra": "50"}, t), 4500.0)
check("recargo 0%", N.valor_hora_extra({"modo_extra": "recargo", "recargo_extra": "0"}, t), 3000.0)
check("fijo general", N.valor_hora_extra({"modo_extra": "fijo", "valor_extra_global": "5000"}, t), 5000.0)
t2 = {"valor_hora": 3000.0, "valor_hora_extra": 6000.0}
check("fijo propio manda", N.valor_hora_extra({"modo_extra": "fijo", "valor_extra_global": "5000"}, t2), 6000.0)

def jornada(d, tid, fecha, ent, sal, col_min):
    """Arma un dia con sus cuatro marcas, con la colacion al medio del turno."""
    bruto = N.minutos_turno(ent, sal)
    e = N.a_minutos(ent)
    d.agregar_marca(tid, fecha, "entrada", ent)
    if col_min:
        medio = e + (bruto - col_min) // 2
        d.agregar_marca(tid, fecha, "colacion_inicio", N.a_hhmm(medio))
        d.agregar_marca(tid, fecha, "colacion_fin", N.a_hhmm(medio + col_min))
    d.agregar_marca(tid, fecha, "salida", sal)


print("\n--- mes completo con plata ---")
ruta = os.path.join(tempfile.mkdtemp(), "p.sqlite3")
d = N.Datos(ruta)
juan = d.agregar_trabajador("Juan", 3000)
ana  = d.agregar_trabajador("Ana", 4000)
# Juan: lunes a sabado, 6 dias de 09:00 a 19:00 con 60 min = 9 h/dia = 54 h
for dia in range(7, 13):
    jornada(d, juan, "2026-09-%02d" % dia, "09:00", "19:00", 60)
# Ana: 2 turnos de 8 h justas, sin extra
jornada(d, ana, "2026-09-08", "10:00", "18:30", 30)
jornada(d, ana, "2026-09-09", "22:00", "06:00", 0)

r = N.resumen_mensual(d, 2026, 9)
juanr = [f for f in r["filas"] if f["nombre"] == "Juan"][0]
anar  = [f for f in r["filas"] if f["nombre"] == "Ana"][0]

check("Juan turnos", juanr["turnos"], 6)
check("Juan horas", juanr["horas"], 54.0)
# Contrato de 7 h al dia: cada dia de 9 h deja 2 extra.
check("Juan extra (2 por dia x 6)", juanr["extra"], 12.0)
check("Juan ordinarias 7 x 6", juanr["ordinarias"], 42.0)
check("Juan ordinarias+extra = horas", juanr["ordinarias"] + juanr["extra"], juanr["horas"])
# 42 normales x 3000 + 12 extra x 4500 = 126.000 + 54.000
check("Juan total", juanr["total"], 180000)
check("sin pagar, se le debe todo", juanr["por_pagar"], 180000)
check("Ana horas", anar["horas"], 16.0)
check("Ana extra (1 por dia x 2)", anar["extra"], 2.0)
check("Ana total 14*4000 + 2*6000", anar["total"], 68000)
check("total general", r["totales"]["total"], 248000)

print("\n--- el total es la suma de sus dias ---")
check("detalle de 6 dias", len(juanr["dias"]), 6)
check("el total es la suma de los dias",
      juanr["total"], sum(x["total"] for x in juanr["dias"]))

print("\n--- semana a caballo entre dos meses ---")
ruta2 = os.path.join(tempfile.mkdtemp(), "q.sqlite3")
d2 = N.Datos(ruta2)
d2.guardar_config({"horas_contrato": "7"})
p = d2.agregar_trabajador("Pedro", 1000)
# Semana del 28 sept al 4 oct: 3 dias en septiembre y 3 en octubre, 10 h c/u = 60 h
for f in ["2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02", "2026-10-03"]:
    jornada(d2, p, f, "08:00", "19:00", 60)
sep = [f for f in N.resumen_mensual(d2, 2026, 9)["filas"]][0]
oct_ = [f for f in N.resumen_mensual(d2, 2026, 10)["filas"]][0]
check("septiembre 3 turnos", sep["turnos"], 3)
check("octubre 3 turnos", oct_["turnos"], 3)
# Cada dia son 10 h con contrato de 7: 3 extra por dia, 9 en cada mes.
check("septiembre 9 extra", sep["extra"], 9.0)
check("octubre 9 extra", oct_["extra"], 9.0)
check("septiembre cuadra", sep["ordinarias"] + sep["extra"], sep["horas"])
check("octubre cuadra", oct_["ordinarias"] + oct_["extra"], oct_["horas"])
check("cada mes es la suma de sus dias",
      sep["total"], sum(x["total"] for x in sep["dias"]))

print("\n--- validaciones ---")
for nombre, args in [("hora imposible", (juan, "2026-09-22", "entrada", "99:99")),
                     ("tipo desconocido", (juan, "2026-09-23", "almuerzo", "12:00")),
                     ("marca repetida el mismo dia", (juan, "2026-09-07", "entrada", "10:00"))]:
    try:
        d.agregar_marca(*args)
        print("FALLA  " + nombre + " -> deberia haber sido rechazada")
        fallas.append(nombre)
    except ValueError as e:
        print("  ok   " + nombre + " -> rechazada: " + str(e)[:52])

print("\n" + ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
sys.exit(1 if fallas else 0)
