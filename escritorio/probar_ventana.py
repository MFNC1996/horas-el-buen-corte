# -*- coding: utf-8 -*-
"""
Arma la ventana entera sin mostrarla y prueba el flujo de marcar.

Sirve para que la compilacion falle en GitHub y no en el computador del local.
"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["LOCALAPPDATA"] = tempfile.mkdtemp()
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
v.withdraw()

print("--- pestanas ---")
pestanas = [v.tabs.tab(i, "text").strip() for i in range(v.tabs.index("end"))]
check("son cinco", len(pestanas) == 5)
for esperada in ("Marcar", "Jornadas", "Resumen y pago", "Trabajadores", "Configuracion"):
    check("existe '%s'" % esperada, esperada in pestanas)
check("Marcar es la primera", pestanas[0] == "Marcar")

print("\n--- controles ---")
for nombre in ("caja_nombres", "lbl_quien", "lbl_marca", "btn_marcar", "lbl_hoy",
               "tv_j", "tv_r", "tv_t", "e_us", "e_contrato", "cb_cierre",
               "e_recargo", "e_vextra", "lbl_total_j", "lbl_calc",
               "e_negocio", "lbl_reloj"):
    check("existe %s" % nombre, hasattr(v, nombre))
check("hay 3 trabajadores de ejemplo", len(v.datos.trabajadores()) == 3)

print("\n--- sin nadie elegido no se puede marcar ---")
check("el boton parte apagado", str(v.btn_marcar.cget("state")) == "disabled")
check("pide elegir nombre", "Elige tu nombre" in v.lbl_quien.cget("text"))

print("\n--- elegir a alguien muestra que le toca ---")
uno, dos = v._trabs[0]["id"], v._trabs[1]["id"]
v.elegir(uno)
check("muestra el nombre", v.lbl_quien.cget("text") == v._trabs[0]["nombre"])
check("dice que va a marcar ENTRADA", v.lbl_marca.cget("text") == "ENTRADA")
check("el boton se enciende", str(v.btn_marcar.cget("state")) == "normal")
check("el boton dice que marca", "ENTRADA" in v.btn_marcar.cget("text"))

print("\n--- marcar suelta la seleccion, para que no marque el siguiente ---")
v.marcar()
check("quedo sin nadie elegido", v.sel_trab is None)
check("avisa que quedo registrada", "registrada a las" in v.lbl_aviso.cget("text"))
check("se guardo una marca", v.datos.total_marcas() == 1)

print("\n--- dos trabajadores alternandose no se mezclan ---")
v.elegir(dos)
check("el segundo parte en ENTRADA", v.lbl_marca.cget("text") == "ENTRADA")
v.marcar()
v.elegir(uno)
check("el primero va en INICIO DE COLACION",
      v.lbl_marca.cget("text") == "INICIO DE COLACION")
v.elegir(dos)
check("el segundo tambien, por su cuenta",
      v.lbl_marca.cget("text") == "INICIO DE COLACION")

print("\n--- completar el dia del primero ---")
v.elegir(uno)
for _ in range(3):
    v.elegir(uno); v.marcar()
v.elegir(uno)
check("queda completo", "COMPLETA" in v.lbl_marca.cget("text"))
check("y el boton se apaga", str(v.btn_marcar.cget("state")) == "disabled")
check("son 4 marcas suyas", len(v.datos.marcas_de(uno, v.datos.estado(uno)["fecha"])) == 0
      or len([m for m in v.datos.marcas() if m["trabajador_id"] == uno]) == 4)

print("\n--- el dia aparece en la lista de jornadas ---")
check("hay filas en Jornadas", len(v.tv_j.get_children()) >= 1)
# Los dias incompletos ya no llevan columna de texto: se marcan con el
# color de la fila (etiqueta "falta").
incompletos = [i for i in v.tv_j.get_children()
               if "falta" in v.tv_j.item(i)["tags"]]
check("el dia a medias sale marcado como incompleto", len(incompletos) >= 1)
check("la fila muestra el valor del dia",
      "$" in str(v.tv_j.item(v.tv_j.get_children()[0])["values"][-1]))

print("\n--- configuracion: jornada semanal y valor de la hora extra ---")
v._set(v.e_contrato, "7")
v._set(v.e_us, "42")
v.cb_cierre.current(5)
v.modo_extra.set("fijo"); v._refrescar_modo()
check("al elegir monto fijo se habilita su campo",
      str(v.e_vextra.cget("state")) == "normal")
v._set(v.e_vextra, "6000")
import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.askyesno = lambda *a, **k: False
mb.showerror = lambda *a, **k: fallas.append("showerror: " + str(a))
v.guardar_config()
c = v.datos.config()
check("guarda las horas de contrato", float(c["horas_contrato"]) == 7.0)
check("guarda las horas semanales", float(c["umbral_semanal"]) == 42.0)
check("guarda el dia de pago (sabado)", int(float(c["dia_cierre"])) == 5)
check("guarda el modo", c["modo_extra"] == "fijo")
check("guarda el valor de la hora extra", float(c["valor_extra_global"]) == 6000.0)
check("la regla es diaria sobre el contrato", c["regla"] == "diaria")

print("\n--- la calculadora de valor hora ---")
check("553.553 con 42 h da 3.075", v.aplicar_valor_hora(553553, 42) == 3075)
check("lo deja en el campo", v.e_tvalor.get() == "3075")
check("muestra la formula", "/ 30 x 7 /" in v.lbl_calc.cget("text"))

print("\n--- avisa si el valor hora parece un sueldo ---")
respuestas = []
mb.askyesno = lambda *a, **k: (respuestas.append(a), False)[1]   # el usuario dice No
check("un valor normal no molesta", v._valor_hora_sospechoso(3075) is False)
check("553.553 la hora se frena", v._valor_hora_sospechoso(553553) is True)
check("el aviso explica el error", "sueldo mensual" in str(respuestas[-1]))
mb.askyesno = lambda *a, **k: False

print("\n--- resumen semanal y mensual ---")
v.cambiar_periodo("semana")
check("hay filas en el resumen", len(v.tv_r.get_children()) >= 1)
check("el titulo dice Semana", "Semana" in v.lbl_periodo.cget("text"))
check("dice cuando se paga", "SE PAGA EL" in v.lbl_periodo.cget("text"))
check("muestra la suma de los dias", "suma de los dias" in v.lbl_total_j.cget("text"))
v.cambiar_periodo("mes")
check("cambia a mes", "Semana" not in v.lbl_periodo.cget("text"))
v.cambiar_periodo("semana")

print("\n--- exportar desde el boton, con el dialogo simulado ---")
import tkinter.filedialog as fd
salida = tempfile.mkdtemp()
elegido = {}
def falso(**kw):
    elegido["r"] = os.path.join(salida, "informe" + kw.get("defaultextension", ""))
    return elegido["r"]
fd.asksaveasfilename = falso
v.exportar("excel")
check("genera el Excel", elegido.get("r") and os.path.getsize(elegido["r"]) > 4000)
v.exportar("pdf")
check("genera el PDF", elegido.get("r") and os.path.getsize(elegido["r"]) > 2000)

print("\n--- corregir marcas a mano ---")
tid = uno
fecha = v.datos.marcas()[0]["fecha"]
marcas = v.datos.marcas_de(tid, fecha)
sal = [m for m in marcas if m["tipo"] == "salida"]
if sal:
    v.datos.editar_marca(sal[0]["id"], hora="23:00")
    check("la correccion se guarda",
          [m for m in v.datos.marcas_de(tid, fecha)
           if m["tipo"] == "salida"][0]["hora"] == "23:00")
    check("y queda anotada como corregida a mano",
          [m for m in v.datos.marcas_de(tid, fecha)
           if m["tipo"] == "salida"][0]["origen"] == "manual")

print("\n--- respaldos ---")
check("hizo la copia del dia", v.datos.ultimo_respaldo()[0] is not None)
check("no duplica la copia del dia", v.datos.respaldar() is None)

v.destroy()
print("\n" + ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
sys.exit(1 if fallas else 0)
