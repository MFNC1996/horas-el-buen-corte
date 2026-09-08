# -*- coding: utf-8 -*-
"""Pruebas de las marcas: orden, independencia entre trabajadores y calculos."""
import os, sys, tempfile
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as N

fallas = []
def check(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(("  ok   " if ok else "FALLA ") + nombre + "  ->  " + repr(obtenido) +
          ("" if ok else "   (esperado " + repr(esperado) + ")"))
    if not ok: fallas.append(nombre)

def H(dia, hh, mm=0):
    return datetime(2026, 9, dia, hh, mm)

d = N.Datos(os.path.join(tempfile.mkdtemp(), "m.sqlite3"))
pepito = d.agregar_trabajador("Pepito", 3000)
juanito = d.agregar_trabajador("Juanito", 4000)

print("--- la primera marca del dia es siempre entrada ---")
check("proxima de Pepito", d.estado(pepito, H(7, 8)) ["etiqueta"], "Entrada")
check("proxima de Juanito", d.estado(juanito, H(7, 8))["etiqueta"], "Entrada")

print("\n--- alternancia entre dos trabajadores: no se deben mezclar ---")
d.marcar(pepito,  H(7, 8, 0))     # Pepito entra
check("Pepito ahora va en colacion", d.estado(pepito,  H(7, 9))["etiqueta"], "Inicio de colacion")
check("Juanito sigue en entrada",    d.estado(juanito, H(7, 9))["etiqueta"], "Entrada")

d.marcar(juanito, H(7, 8, 30))    # Juanito entra
check("Juanito pasa a colacion",     d.estado(juanito, H(7, 9))["etiqueta"], "Inicio de colacion")
check("Pepito no se movio",          d.estado(pepito,  H(7, 9))["etiqueta"], "Inicio de colacion")

d.marcar(pepito,  H(7, 13, 0))    # Pepito inicia colacion
check("Pepito va en fin de colacion", d.estado(pepito,  H(7, 14))["etiqueta"], "Fin de colacion")
check("Juanito sigue en inicio",      d.estado(juanito, H(7, 14))["etiqueta"], "Inicio de colacion")

d.marcar(juanito, H(7, 13, 30))
d.marcar(pepito,  H(7, 14, 0))    # Pepito termina colacion
check("Pepito ya solo debe la salida", d.estado(pepito,  H(7, 15))["etiqueta"], "Salida")
check("Juanito aun debe fin colacion", d.estado(juanito, H(7, 15))["etiqueta"], "Fin de colacion")

d.marcar(juanito, H(7, 14, 30))
d.marcar(pepito,  H(7, 18, 0))    # Pepito sale
check("el dia de Pepito quedo completo", d.estado(pepito, H(7, 19))["completa"], True)
check("Juanito todavia no",              d.estado(juanito, H(7, 19))["completa"], False)
d.marcar(juanito, H(7, 19, 0))

print("\n--- horas del dia calculadas desde las 4 marcas ---")
# Pepito 08:00-18:00 con colacion 13:00-14:00 = 9 h
check("Pepito 9 h",  d.estado(pepito,  H(7, 20))["horas"], 9.0)
# Juanito 08:30-19:00 con colacion 13:30-14:30 = 9.5 h
check("Juanito 9,5 h", d.estado(juanito, H(7, 20))["horas"], 9.5)

print("\n--- no se puede marcar una quinta vez ---")
try:
    d.marcar(pepito, H(7, 20))
    check("rechaza la quinta marca", "no rechazo", "ValueError")
except ValueError as e:
    print("  ok   rechaza la quinta marca -> " + str(e)[:52])

print("\n--- al dia siguiente vuelve a empezar por entrada ---")
check("nuevo dia", d.estado(pepito, H(8, 8))["etiqueta"], "Entrada")
check("y es otro dia laboral", d.estado(pepito, H(8, 8))["fecha"], "2026-09-08")

print("\n--- turno de noche: la jornada no se parte a medianoche ---")
noche = d.agregar_trabajador("Nocturno", 3000)
d.marcar(noche, H(10, 22, 0))                 # entra el 10 a las 22:00
check("sigue en el dia 10", d.estado(noche, datetime(2026, 9, 11, 2, 0))["fecha"], "2026-09-10")
d.marcar(noche, datetime(2026, 9, 11, 1, 0))  # colacion pasada la medianoche
d.marcar(noche, datetime(2026, 9, 11, 1, 30))
d.marcar(noche, datetime(2026, 9, 11, 6, 0))  # sale a las 06:00
# Ya completo la jornada, asi que estado() apunta al dia siguiente: las horas
# del turno cerrado se leen de sus propias marcas.
check("8 h y media descontando colacion",
      N.horas_de_marcas(d.marcas_de(noche, "2026-09-10")), 7.5)
check("todo quedo en el dia 10", len(d.marcas_de(noche, "2026-09-10")), 4)

print("\n--- jornada abandonada: a las 20 h se corta sola ---")
olvido = d.agregar_trabajador("Olvidadizo", 3000)
d.marcar(olvido, H(12, 9, 0))                 # entra y nunca marca salida
check("al otro dia empieza de nuevo",
      d.estado(olvido, H(13, 9, 0))["etiqueta"], "Entrada")
check("y en el dia nuevo", d.estado(olvido, H(13, 9, 0))["fecha"], "2026-09-13")

print("\n--- correcciones del administrador ---")
marcas = d.marcas_de(pepito, "2026-09-07")
salida = [m for m in marcas if m["tipo"] == "salida"][0]
d.editar_marca(salida["id"], hora="19:00")
check("editar la hora recalcula", d.estado(pepito, H(7, 23))["horas"], 10.0)
try:
    entrada = [m for m in marcas if m["tipo"] == "entrada"][0]
    d.editar_marca(entrada["id"], tipo="salida")
    check("rechaza tipo duplicado", "no rechazo", "ValueError")
except ValueError as e:
    print("  ok   rechaza tipo duplicado -> " + str(e)[:46])

d.borrar_marca(salida["id"])
check("sin salida no hay horas", d.estado(pepito, H(7, 23))["horas"], 0.0)
check("y vuelve a pedir la salida", d.estado(pepito, H(7, 23))["etiqueta"], "Salida")
d.agregar_marca(pepito, "2026-09-07", "salida", "18:00")
check("agregar a mano la repone", d.estado(pepito, H(7, 23))["horas"], 9.0)

print("\n--- si falta una marca del medio, la pide esa ---")
ci = [m for m in d.marcas_de(pepito, "2026-09-07") if m["tipo"] == "colacion_inicio"][0]
d.borrar_marca(ci["id"])
check("pide justo la que falta", d.estado(pepito, H(7, 23))["etiqueta"], "Inicio de colacion")
d.agregar_marca(pepito, "2026-09-07", "colacion_inicio", "13:00")

print("\n--- el ejemplo exacto del contrato ---")
# Contrato de 7 h. Entra 08:30, colacion 13:30-14:30, sale 19:30.
# Son 10 h trabajadas: 7 normales + 3 extra.
d.guardar_config({"horas_contrato": "7", "modo_extra": "fijo",
                  "valor_extra_global": "3900", "dia_cierre": "5"})
isa = d.agregar_trabajador("Isabel", 3075)
d.agregar_marca(isa, "2026-09-07", "entrada", "08:30")
d.agregar_marca(isa, "2026-09-07", "colacion_inicio", "13:30")
d.agregar_marca(isa, "2026-09-07", "colacion_fin", "14:30")
d.agregar_marca(isa, "2026-09-07", "salida", "19:30")
dias = N.dias_con_valor(d, "2026-09-07", "2026-09-07", isa)
uno = dias[0]
check("10 h trabajadas", uno["horas"], 10.0)
check("7 normales", uno["normales"], 7.0)
check("3 extra", uno["extra"], 3.0)
check("pago normal 7 x 3075", uno["pago_normal"], 21525)
check("pago extra 3 x 3900", uno["pago_extra"], 11700)
check("valor del dia", uno["total"], 33225)

print("\n--- la jornada justa no genera extra ---")
d.agregar_marca(isa, "2026-09-08", "entrada", "08:30")
d.agregar_marca(isa, "2026-09-08", "colacion_inicio", "12:00")
d.agregar_marca(isa, "2026-09-08", "colacion_fin", "13:00")
d.agregar_marca(isa, "2026-09-08", "salida", "16:30")
justo = N.dias_con_valor(d, "2026-09-08", "2026-09-08", isa)[0]
check("turno del contrato son 7 h", justo["horas"], 7.0)
check("sin extra", justo["extra"], 0.0)
check("el dia vale 7 x 3075", justo["total"], 21525)

print("\n--- valor hora desde el sueldo del contrato ---")
check("553.553 con 42 h semanales", N.valor_hora_desde_sueldo(553553, 42), 3075)
check("sin sueldo da 0", N.valor_hora_desde_sueldo(0, 42), 0.0)

print("\n--- la semana se acumula sola y cierra el sabado ---")
check("semana del 7 (lunes)", N.semana_de("2026-09-07", 5), ("2026-09-06", "2026-09-12"))
check("semana del 12 (sabado)", N.semana_de("2026-09-12", 5), ("2026-09-06", "2026-09-12"))
check("el domingo 13 ya es otra", N.semana_de("2026-09-13", 5), ("2026-09-13", "2026-09-19"))
sem = N.resumen_semanal(d, "2026-09-07")
isar = [f for f in sem["filas"] if f["nombre"] == "Isabel"][0]
check("suma los dos dias", isar["turnos"], 2)
check("horas de la semana", isar["horas"], 17.0)
check("extra de la semana", isar["extra"], 3.0)
check("total = suma de los dias", isar["total"], 33225 + 21525)
check("se paga el sabado", sem["pago_el"], "2026-09-12")
check("dice cuando se paga", "sabado" in sem["subtitulo"], True)

print("\n--- jornada propia por trabajador ---")
medio = d.agregar_trabajador("Media jornada", 4000, 5000, 4)   # contrato de 4 h
d.agregar_marca(medio, "2026-09-09", "entrada", "09:00")
d.agregar_marca(medio, "2026-09-09", "colacion_inicio", "11:00")
d.agregar_marca(medio, "2026-09-09", "colacion_fin", "11:30")
d.agregar_marca(medio, "2026-09-09", "salida", "14:30")
md = N.dias_con_valor(d, "2026-09-09", "2026-09-09", medio)[0]
check("5 h trabajadas", md["horas"], 5.0)
check("su contrato es de 4 h", md["contrato"], 4.0)
check("1 h extra, no 0", md["extra"], 1.0)
check("usa su propio valor extra", md["pago_extra"], 5000)

print("\n--- dias incompletos quedan marcados ---")
suelto = d.agregar_trabajador("Incompleto", 1000)
d.agregar_marca(suelto, "2026-09-08", "entrada", "09:00")
sem = N.resumen_semanal(d, "2026-09-07")
inc = [f for f in sem["filas"] if f["nombre"] == "Incompleto"][0]
check("se detecta el dia incompleto", len(inc["incompletos"]), 1)
check("dice que faltan 3 marcas", len(inc["dias"][0]["faltan"]), 3)
check("sin salida no suma horas", inc["horas"], 0.0)

print("\n" + ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
sys.exit(1 if fallas else 0)
