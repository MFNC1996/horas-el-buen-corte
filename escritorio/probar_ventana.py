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

print("\n--- exportar desde el boton, con el dialogo simulado ---")
import tkinter.filedialog as fd, tkinter.messagebox as mb
salida = tempfile.mkdtemp()
elegido = {"ruta": None}
def falso_guardar(**kw):
    elegido["ruta"] = os.path.join(salida, "informe" + kw.get("defaultextension", ""))
    return elegido["ruta"]
fd.asksaveasfilename = falso_guardar
mb.askyesno = lambda *a, **k: False          # no abrir el archivo despues
mb.showinfo = lambda *a, **k: None
mb.showerror = lambda *a, **k: fallas.append("showerror: " + str(a))

v.cb_mes_r.set(v._mes_texto("2026-09"))
v.exportar("excel")
check("el boton genera el Excel", elegido["ruta"] and os.path.getsize(elegido["ruta"]) > 4000)
v.exportar("pdf")
check("el boton genera el PDF", elegido["ruta"] and os.path.getsize(elegido["ruta"]) > 2000)

print("\n--- agregar y editar trabajadores ---")
antes = len(v.datos.trabajadores())
v._set(v.e_tnombre, "Prueba Uno"); v._set(v.e_tvalor, "5.000"); v._set(v.e_tvalorx, "7500")
v.agregar_trabajador()
check("se agrego", len(v.datos.trabajadores()) == antes + 1)
nuevo = [t for t in v.datos.trabajadores() if t["nombre"] == "Prueba Uno"][0]
check("acepta el monto con punto de miles", nuevo["valor_hora"] == 5000.0)
check("guarda el valor de hora extra propio", nuevo["valor_hora_extra"] == 7500.0)

v.tv_t.selection_set(str(nuevo["id"])); v.cargar_trabajador_sel()
check("carga el seleccionado en el formulario", v.e_tnombre.get() == "Prueba Uno")
v._set(v.e_tnombre, "Prueba Editada"); v._set(v.e_tvalor, "6000")
v.guardar_trabajador()
check("guarda el cambio de nombre",
      any(t["nombre"] == "Prueba Editada" for t in v.datos.trabajadores()))

print("\n--- guardar configuracion ---")
v._set(v.e_ud, "9"); v._set(v.e_us, "44")
v.cb_regla.current(1)
# Igual que al pulsar el boton de radio: cambiar la variable y refrescar, que
# es lo que habilita el campo. Tk ignora escribir en un campo deshabilitado.
v.modo_extra.set("fijo"); v._refrescar_modo()
v._set(v.e_vextra, "7000")
check("al elegir monto fijo se habilita su campo",
      str(v.e_vextra.cget("state")) == "normal")
check("y se deshabilita el del recargo",
      str(v.e_recargo.cget("state")) == "disabled")
v.guardar_config()
c = v.datos.config()
check("umbral diario guardado", float(c["umbral_diario"]) == 9.0)
check("umbral semanal guardado", float(c["umbral_semanal"]) == 44.0)
check("regla guardada", c["regla"] == "semanal")
check("modo de hora extra guardado", c["modo_extra"] == "fijo")
check("valor fijo guardado", float(c["valor_extra_global"]) == 7000.0)

print("\n--- editar y borrar una jornada ---")
jid = v.tv_j.get_children()[0]
v.tv_j.selection_set(jid); v.editar_sel()
check("carga la jornada en el formulario", v.editando == int(jid))
v._set(v.e_sal, "20:00"); v.guardar_jornada()
check("guarda el cambio sin duplicar", v.datos.total_jornadas() == 1)
check("la salida quedo cambiada", v.datos.jornadas()[0]["salida"] == "20:00")

mb.askyesno = lambda *a, **k: True
v.tv_j.selection_set(v.tv_j.get_children()[0]); v.borrar_sel()
check("borra la jornada", v.datos.total_jornadas() == 0)

print("\n--- quitar un trabajador conserva su historial ---")
tid = [t for t in v.datos.trabajadores() if t["nombre"] == "Prueba Editada"][0]["id"]
v.guardar_jornada.__self__.datos.guardar_jornada(None, tid, "2026-09-15", "09:00", "18:00", 60)
v.tv_t.selection_set(str(tid)); v.quitar_trabajador()
check("sale de la lista", not any(t["id"] == tid for t in v.datos.trabajadores()))
check("su jornada sigue guardada", v.datos.jornadas_de(tid) == 1)

print("\n--- respaldos ---")
check("hizo la copia del dia", v.datos.ultimo_respaldo()[0] is not None)
check("no duplica la copia del dia", v.datos.respaldar() is None)
manual = os.path.join(tempfile.mkdtemp(), "copia.sqlite3")
v.datos.respaldar(manual)
check("la copia manual queda utilizable", os.path.getsize(manual) > 0)

v.destroy()
print("\n" + ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
sys.exit(1 if fallas else 0)
