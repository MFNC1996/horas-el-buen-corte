# -*- coding: utf-8 -*-
"""
Comprueba que la ventana se arma entera sin abrirla en pantalla.

Sirve para que la compilacion falle en GitHub y no en el computador del
local: construye la aplicacion completa, revisa que esten las cuatro
pestanas y los controles que importan, y la cierra.
"""
import os, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["LOCALAPPDATA"] = tempfile.mkdtemp()   # base de pruebas, no la real
os.environ["XDG_DATA_HOME"] = os.environ["LOCALAPPDATA"]

import nucleo as N

try:
    import app
except ImportError as e:
    print("FALLA: no se pudo importar la ventana: %s" % e)
    sys.exit(1)

fallas = []

def check(nombre, cond):
    print(("  ok   " if cond else "FALLA ") + nombre)
    if not cond:
        fallas.append(nombre)

v = app.App()
v.withdraw()                       # se arma pero no se muestra

pestanas = [v.tabs.tab(i, "text").strip() for i in range(v.tabs.index("end"))]
print("--- pestanas ---")
check("son cuatro", len(pestanas) == 4)
for esperada in ("Jornadas", "Resumen del mes", "Trabajadores", "Configuracion"):
    check("existe '%s'" % esperada, esperada in pestanas)

print("\n--- controles ---")
for nombre in ("cb_trab", "e_fecha", "e_ent", "e_sal", "cb_col", "tv_j",
               "tv_r", "tv_t", "e_ud", "e_us", "cb_regla", "e_recargo",
               "e_vextra", "e_negocio", "lbl_previa"):
    check("existe %s" % nombre, hasattr(v, nombre))

print("\n--- se sembraron los trabajadores de ejemplo ---")
check("hay 3 trabajadores", len(v.datos.trabajadores()) == 3)

print("\n--- los atajos de hora funcionan ---")
v._set(v.e_ent, "09:00"); v._set(v.e_sal, "19:00")
v.cb_col.current(3); v._vista_previa()
check("vista previa calcula 9 h", "9,00" in v.lbl_previa.cget("text"))
check("marca la hora extra", "extra" in v.lbl_previa.cget("text"))
v._paso(v.e_ent, 15)
check("+15 sobre 09:00 da 09:15", v.e_ent.get() == "09:15")
v._paso(v.e_ent, -30)
check("-30 da 08:45", v.e_ent.get() == "08:45")

print("\n--- guardar una jornada de punta a punta ---")
v._set(v.e_ent, "08:00"); v._set(v.e_sal, "19:30")
v._set(v.e_fecha, "2026-09-07"); v.cb_trab.current(0)
v.guardar_jornada()
check("quedo guardada", v.datos.total_jornadas() == 1)
check("aparece en la lista", len(v.tv_j.get_children()) == 1)
check("aparece en el resumen", len(v.tv_r.get_children()) >= 2)

print("\n--- los informes se generan ---")
import informes
r = N.resumen_mensual(v.datos, 2026, 9)
d = tempfile.mkdtemp()
x = informes.a_excel(r, os.path.join(d, "i.xlsx"))
p = informes.a_pdf(r, os.path.join(d, "i.pdf"))
check("Excel con contenido", os.path.getsize(x) > 4000)
check("PDF con contenido", os.path.getsize(p) > 2000)

v.destroy()
print("\n" + ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
sys.exit(1 if fallas else 0)
