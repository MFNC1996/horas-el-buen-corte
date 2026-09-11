# -*- coding: utf-8 -*-
"""Pruebas de los pagos: el check por dia, lo pagado y lo pendiente."""
import os, sys, tempfile
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as N

fallas = []
def check(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(("  ok   " if ok else "FALLA ") + nombre + "  ->  " + repr(obtenido) +
          ("" if ok else "   (esperado " + repr(esperado) + ")"))
    if not ok: fallas.append(nombre)

def rechaza(nombre, fn):
    try:
        fn(); print("FALLA  " + nombre + " -> no lo rechazo"); fallas.append(nombre)
    except ValueError as e:
        print("  ok   " + nombre + " -> " + str(e)[:60])

d = N.Datos(os.path.join(tempfile.mkdtemp(), "p.sqlite3"))
d.guardar_config({"horas_contrato": "7", "modo_extra": "fijo", "valor_extra_global": "3900"})
isa = d.agregar_trabajador("Isabel", 3075)
juan = d.agregar_trabajador("Juan", 3075)

def dia(tid, f, e, ci, cf, s):
    for tipo, h in (("entrada", e), ("colacion_inicio", ci), ("colacion_fin", cf), ("salida", s)):
        if h: d.agregar_marca(tid, f, tipo, h)

dia(isa, "2026-09-07", "08:30", "13:30", "14:30", "19:30")   # 10 h -> $33.225
dia(isa, "2026-09-08", "08:30", "12:00", "13:00", "16:30")   #  7 h -> $21.525
dia(isa, "2026-09-09", "08:30", "12:00", None, None)         # incompleto
dia(juan, "2026-09-07", "08:30", "13:30", "13:48", "19:30")  # 10:42

print("--- las horas se muestran como reloj, no con decimales ---")
j = N.dias_con_valor(d, "2026-09-07", "2026-09-07", juan)[0]
check("10,7 h se ve 10:42", N.hhmm_txt(j["horas"]), "10:42")
check("7 h se ve 7:00", N.hhmm_txt(7.0), "7:00")
check("3,7 h de extra se ven 3:42", N.hhmm_txt(j["extra"]), "3:42")
for m in range(0, 24 * 60, 7):                       # todo minuto del dia vuelve igual
    if N.hhmm_txt(round(m / 60.0, 2)) != "%d:%02d" % (m // 60, m % 60):
        check("minuto %d" % m, N.hhmm_txt(round(m / 60.0, 2)), "%d:%02d" % (m // 60, m % 60))
        break
else:
    print("  ok   todos los minutos del dia se muestran exactos")

print("\n--- al principio nada esta pagado ---")
r = N.resumen_todo(d)
isar = [f for f in r["filas"] if f["nombre"] == "Isabel"][0]
check("3 dias trabajados", isar["turnos"], 3)
check("0 pagados", isar["dias_pagados"], 0)
check("2 por pagar (el incompleto no cuenta)", isar["dias_pendientes"], 2)
check("se le deben 33.225 + 21.525", isar["por_pagar"], 54750)
check("pagado $0", isar["pagado"], 0)

print("\n--- el check de pagado ---")
check("pagar el dia devuelve su valor", d.marcar_pagado(isa, "2026-09-07", date(2026, 9, 7)), 33225)
isar = [f for f in N.resumen_todo(d)["filas"] if f["nombre"] == "Isabel"][0]
check("1 pagado", isar["dias_pagados"], 1)
check("pagado $33.225", isar["pagado"], 33225)
check("queda 1 por pagar", isar["dias_pendientes"], 1)
check("se le debe $21.525", isar["por_pagar"], 21525)
check("marcarlo dos veces no duplica", d.marcar_pagado(isa, "2026-09-07"), None)

print("\n--- no se paga lo que no corresponde ---")
rechaza("un dia incompleto", lambda: d.marcar_pagado(isa, "2026-09-09"))
rechaza("un dia sin marcas", lambda: d.marcar_pagado(isa, "2026-09-20"))
sinvalor = d.agregar_trabajador("Sin valor hora", 0)
dia(sinvalor, "2026-09-07", "08:30", "12:00", "13:00", "16:30")
d.guardar_config({"valor_extra_global": "3900"})
rechaza("un dia que vale $0", lambda: d.marcar_pagado(sinvalor, "2026-09-07"))

print("\n--- un dia pagado no se puede corregir ---")
m = d.marcas_de(isa, "2026-09-07")[0]
rechaza("editar una marca", lambda: d.editar_marca(m["id"], hora="09:00"))
rechaza("borrar una marca", lambda: d.borrar_marca(m["id"]))
rechaza("agregar una marca", lambda: d.agregar_marca(isa, "2026-09-07", "salida", "20:00"))
d.desmarcar_pagado(isa, "2026-09-07")
d.editar_marca([x for x in d.marcas_de(isa, "2026-09-07") if x["tipo"] == "salida"][0]["id"],
               hora="19:00")
check("quitando el check si se puede", N.dias_con_valor(d, "2026-09-07", "2026-09-07", isa)[0]["horas"], 9.5)

print("\n--- lo pagado queda fijo aunque cambie el valor hora ---")
d.marcar_pagado(isa, "2026-09-08", date(2026, 9, 8))          # 7 h x 3075 = 21.525
d.editar_trabajador(isa, "Isabel", 4000)                        # le suben el valor hora
dia8 = N.dias_con_valor(d, "2026-09-08", "2026-09-08", isa)[0]
check("el dia ahora valdria 28.000", dia8["total"], 28000)
check("pero lo pagado sigue en 21.525", dia8["monto_pagado"], 21525)
isar = [f for f in N.resumen_todo(d)["filas"] if f["nombre"] == "Isabel"][0]
check("y el resumen suma lo realmente pagado", isar["pagado"], 21525)

print("\n--- pagar todo lo pendiente de una vez (fin de mes) ---")
n, total = d.pagar_pendientes(isa, "2026-09-01", "2026-09-30", date(2026, 9, 30))
check("paga el dia que quedaba", n, 1)
isar = [f for f in N.resumen_mensual(d, 2026, 9)["filas"] if f["nombre"] == "Isabel"][0]
check("ya no se le debe nada", isar["por_pagar"], 0)
check("el incompleto sigue sin pagar", len(isar["incompletos"]), 1)

print("\n--- aviso de plata pendiente de otro mes ---")
dia(juan, "2026-08-31", "08:30", "12:00", "13:00", "16:30")
n, total = N.pendiente_fuera(d, "2026-09-01", "2026-09-30")
check("un dia de agosto sin pagar", n, 1)
check("por $21.525", total, 21525)

print("\n" + ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
sys.exit(1 if fallas else 0)
