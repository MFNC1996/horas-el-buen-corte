# -*- coding: utf-8 -*-
"""
Arma la ventana entera sin mostrarla y prueba el flujo de marcar.

Sirve para que la compilacion falle en GitHub y no en el computador del local.
"""
import os, sys, tempfile
# La consola de Windows usa cp1252 y no sabe escribir simbolos como el del
# check; asi las pruebas no se caen por algo que no tiene que ver con la app.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["LOCALAPPDATA"] = tempfile.mkdtemp()
os.environ["XDG_DATA_HOME"] = os.environ["LOCALAPPDATA"]
os.environ["CH_SIN_CORREO"] = "1"     # el hilo que envia no corre en las pruebas

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

# Durante las pruebas nadie va a presionar OK: cualquier dialogo que se abra
# sin querer tiene que volver al tiro, o la compilacion se queda colgada.
import tkinter.messagebox as mb
for _n in ("showinfo", "showwarning", "showerror"):
    setattr(mb, _n, lambda *a, **k: None)
mb.askyesno = lambda *a, **k: False

v = app.App(presentacion=False)
v.withdraw()

print("--- pantalla de carga ---")
carga = app.Presentacion(v)
textos = [w.cget("text") for w in carga.winfo_children() if isinstance(w, app.tk.Label)]
check("dice 'Carniceria El Buen Corte'", "Carniceria El Buen Corte" in textos)
check("muestra el logo", carga._logo is not None)
check("dice by Macoem", any("by Macoem" in t for t in textos))
carga.paso("Abriendo la base de datos...", 40)
check("avanza la barra", float(carga.barra["value"]) == 40)
check("cambia el mensaje", carga.lbl.cget("text") == "Abriendo la base de datos...")
listo = []
carga.terminar(300, lambda: listo.append(True))
import time
fin = time.time() + 5
while not listo and time.time() < fin:
    v.update(); time.sleep(0.02)
check("al terminar abre la aplicacion", listo == [True])
check("la barra llega al final", float(carga.barra["value"]) == 100)
carga.destroy()
print()

print("--- pestanas ---")
pestanas = [v.tabs.tab(i, "text").strip() for i in range(v.tabs.index("end"))]
check("son cinco", len(pestanas) == 5)
for esperada in ("Marcar", "Dias trabajados", "Pagos por persona", "Trabajadores",
                 "Configuracion"):
    check("existe '%s'" % esperada, esperada in pestanas)
check("Marcar es la primera", pestanas[0] == "Marcar")

print("\n--- controles ---")
for nombre in ("caja_nombres", "lbl_quien", "lbl_marca", "btn_marcar", "lbl_hoy",
               "tv_j", "tv_r", "tv_d", "tv_t", "e_contrato", "btn_pagar_todo",
               "e_recargo", "e_vextra", "lbl_calc",
               "e_negocio", "lbl_reloj"):
    check("existe %s" % nombre, hasattr(v, nombre))
check("hay 3 trabajadores de ejemplo", len(v.datos.trabajadores()) == 3)
check("'by Macoem' en la cabecera", v.lbl_autor.cget("text") == "by Macoem")
check("'by Macoem' en la barra de titulo", "by Macoem" in v.title())

print("\n--- una sola ventana a la vez ---")
import instancia
check("la primera toma el candado", instancia.tomar(tempfile.mkdtemp()) is True)
check("una segunda ya no puede", instancia.tomar(tempfile.mkdtemp()) is False)

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

print("\n--- el dia aparece en Dias trabajados ---")
check("hay filas", len(v.tv_j.get_children()) >= 1)
# Los dias incompletos ya no llevan columna de texto: se marcan con el
# color de la fila (etiqueta "falta").
incompletos = [i for i in v.tv_j.get_children()
               if "falta" in v.tv_j.item(i)["tags"]]
check("el dia a medias sale marcado como incompleto", len(incompletos) >= 1)
check("las filas completas muestran lo que hay que pagar",
      any("$" in str(v.tv_j.item(i)["values"][-1]) for i in v.tv_j.get_children()))

print("\n--- configuracion: jornada semanal y valor de la hora extra ---")
v._set(v.e_contrato, "7")
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

v.cb_mes_r.set("Todo"); v.recargar_resumen()

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

print("\n--- dias trabajados: horas como reloj y los montos separados ---")
v.datos.editar_trabajador(uno, v._trabs[0]["nombre"], 3075)
for tipo, h in (("entrada", "08:30"), ("colacion_inicio", "13:30"),
                ("colacion_fin", "13:48"), ("salida", "19:30")):
    v.datos.agregar_marca(uno, "2026-09-07", tipo, h)
v.cb_mes_j.set("Todos"); v.solo_pendientes.set(False); v.recargar_todo()
fila = "2026-09-07|%d" % uno
check("el dia aparece en la lista", v.tv_j.exists(fila))
vals = [str(x) for x in v.tv_j.item(fila)["values"]]
# columnas: pagado, fecha, trabajador, horas, normales, $normales, extra, $extra, total
check("10,7 h se ven como 10:42, no con decimales", vals[3] == "10:42")
check("7:00 normales", vals[4] == "7:00")
check("muestra cuanto es en normales", vals[5] == "$21.525")   # 7 x 3.075
check("3:42 de extra", vals[6] == "3:42")
check("muestra cuanto es en extra", vals[7] == "$22.200")       # 3,7 x 6.000
check("y el total del dia", vals[8] == "$43.725")
pesos = lambda s: int(s.replace("$", "").replace(".", ""))
check("las dos partes suman el total, tal como se ven",
      pesos(vals[5]) + pesos(vals[7]) == pesos(vals[8]))
check("parte sin pagar", "Pagar" in vals[0])

v.cambiar_pagado(fila)
check("el clic paga el dia completo",
      v.datos.pago_de(uno, "2026-09-07", "normal") is not None
      and v.datos.pago_de(uno, "2026-09-07", "extra") is not None)
check("y dice Pagado", "Pagado" in str(v.tv_j.item(fila)["values"][0]))

avisos = []
mb.showinfo = lambda *a, **k: avisos.append(a)
v.tv_j.selection_set(fila); v.abrir_editor()
check("un dia pagado no se deja corregir", bool(avisos) and "ya se pago" in str(avisos[-1]))
mb.showinfo = lambda *a, **k: None

v.solo_pendientes.set(True); v.recargar_jornadas()
check("'solo lo que falta pagar' lo esconde", not v.tv_j.exists(fila))
v.solo_pendientes.set(False); v.recargar_jornadas()

mb.askyesno = lambda *a, **k: True
v.cambiar_pagado(fila)
check("se puede quitar el check",
      v.datos.pago_de(uno, "2026-09-07", "normal") is None)
mb.askyesno = lambda *a, **k: False

avisos = []
mb.showwarning = lambda *a, **k: avisos.append(a)
incompleto = [i for i in v.tv_j.get_children() if "falta" in v.tv_j.item(i)["tags"]]
if incompleto:
    v.cambiar_pagado(incompleto[0])
check("un dia incompleto no se deja pagar", bool(avisos) and "faltan marcas" in str(avisos[-1]))

print("\n--- eliminar un dia desde Dias trabajados ---")
dos_id = v._trabs[1]["id"]
for tipo, h in (("entrada", "08:30"), ("colacion_inicio", "12:00"),
                ("colacion_fin", "13:00"), ("salida", "16:30")):
    v.datos.agregar_marca(dos_id, "2026-09-08", tipo, h)
v.recargar_todo()
fila_b = "2026-09-08|%d" % dos_id
check("el dia esta en la lista", v.tv_j.exists(fila_b))
mb.askyesno = lambda *a, **k: False
v.tv_j.selection_set(fila_b); v.eliminar_dia()
check("si dice que no, no se borra", v.tv_j.exists(fila_b))
preguntas = []
mb.askyesno = lambda *a, **k: (preguntas.append(a), True)[1]
v.tv_j.selection_set(fila_b); v.eliminar_dia()
check("pregunta mostrando de quien y cuanto",
      bool(preguntas) and "7:00" in str(preguntas[-1]) and "$" in str(preguntas[-1]))
check("si dice que si, desaparece", not v.tv_j.exists(fila_b))
mb.askyesno = lambda *a, **k: False
v.datos.marcar_pagado(uno, "2026-09-07"); v.recargar_todo()
avisos = []
mb.showwarning = lambda *a, **k: avisos.append(a)
v.tv_j.selection_set("2026-09-07|%d" % uno); v.eliminar_dia()
check("un dia con un pago no se deja eliminar",
      v.tv_j.exists("2026-09-07|%d" % uno) and "check" in str(avisos[-1]))
v.datos.desmarcar_pagado(uno, "2026-09-07"); v.recargar_todo()

print("\n--- pagos por persona ---")
v.cb_mes_r.set("Todo"); v.recargar_resumen()
check("una fila por persona, sin fila de total",
      "total" not in v.tv_r.get_children() and len(v.tv_r.get_children()) >= 1)
check("muestra de entrada los dias de la primera persona", len(v.tv_d.get_children()) >= 1)
v.tv_r.selection_set(str(uno)); v.recargar_detalle()
check("muestra los dias de esa persona", len(v.tv_d.get_children()) >= 1)
check("ofrece pagar lo pendiente", "Pagar lo pendiente" in v.btn_pagar_todo.cget("text"))
fila_d = "2026-09-07|%d" % uno
vd = [str(x) for x in v.tv_d.item(fila_d)["values"]]
check("el detalle trae el check", "Pagar" in vd[0])
check("y muestra los montos separados", vd[4] == "$21.525" and vd[6] == "$22.200")
v.cambiar_pagado(fila_d)
check("se paga el dia desde el detalle",
      v.datos.pago_de(uno, "2026-09-07", "normal") is not None)
check("y el detalle lo muestra", "Pagado" in str(v.tv_d.item(fila_d)["values"][0]))
mb.askyesno = lambda *a, **k: True
v.cambiar_pagado(fila_d)

print("\n--- pagar lo pendiente de una persona ---")
v.tv_r.selection_set(str(uno)); v.recargar_detalle()
v.pagar_todo()
mb.askyesno = lambda *a, **k: False
fila_r = [f for f in v._resumen["filas"] if f["id"] == uno][0]
check("no se le debe nada", fila_r["por_pagar"] == 0)
check("el resumen igual muestra lo pagado en cada parte",
      fila_r["pagado_normal"] > 0 and fila_r["pagado_extra"] > 0)
check("el boton lo dice", v.btn_pagar_todo.cget("text") == "Todo pagado")

print("\n--- el correo del trabajador ---")
v.tabs.select(3)
v.tv_t.selection_set(str(uno)); v.cargar_trabajador_sel()
check("la ficha tiene campo de correo", v.e_tcorreo.get() == "")
v._set(v.e_tcorreo, "ana@gmail.com")
v.guardar_trabajador()
check("se guarda con el trabajador",
      v.datos.trabajador(uno)["correo"] == "ana@gmail.com")
check("y sale en la lista",
      "ana@gmail.com" in [str(x) for x in v.tv_t.item(str(uno))["values"]])
v.tv_t.selection_set(str(uno)); v.cargar_trabajador_sel()
check("al elegirlo de nuevo aparece", v.e_tcorreo.get() == "ana@gmail.com")
errores = []
mb.showerror = lambda *a, **k: errores.append(a)
v._set(v.e_tcorreo, "ana-arroba-gmail")
v.guardar_trabajador()
check("un correo mal escrito no se guarda",
      v.datos.trabajador(uno)["correo"] == "ana@gmail.com" and errores)
check("y dice como tiene que ser", "nombre@gmail.com" in str(errores[-1]))
v._set(v.e_tcorreo, "ana@gmail.com"); v.guardar_trabajador()
mb.showerror = lambda *a, **k: fallas.append("showerror: " + str(a))

print("\n--- encender el aviso por correo ---")
v.tabs.select(4)
v.update_idletasks()
alto_contenido = v._lienzo_config.bbox("all")[3]
check("la configuracion se puede bajar cuando no cabe",
      alto_contenido > 0 and v._lienzo_config.cget("yscrollcommand") != "")
v._lienzo_config.yview_moveto(0)
v._rueda(type("E", (), {"delta": -120})())
una = v._lienzo_config.canvasy(0)
check("una muesca de la rueda la baja", una > 0)
v._lienzo_config.yview_moveto(0)
v._rueda(type("E", (), {"delta": -600})())
check("y girar rapido la baja mas, no lo mismo",
      v._lienzo_config.canvasy(0) > una)
v._lienzo_config.yview_moveto(0)
v._rueda(type("E", (), {"delta": 120})())
check("hacia arriba no se pasa del principio", v._lienzo_config.canvasy(0) == 0)
check("viene apagado", not v.correo_activo.get())
# La casilla decide si se manda, no si se puede escribir: si no, para llenar
# la cuenta habria que marcar primero la casilla que necesita esa cuenta.
check("pero los campos se pueden llenar igual",
      str(v.e_cservidor.cget("state")) == "normal"
      and str(v.e_cclave.cget("state")) == "normal")
check("el boton de prueba tampoco espera a la casilla",
      str(v.btn_probar_correo.cget("state")) == "normal")
v.correo_activo.set(True); v._refrescar_correo()
check("y siguen habilitados al encenderla", str(v.e_cclave.cget("state")) == "normal")
check("la contrasena no se ve al escribirla", v.e_cclave.cget("show") != "")
check("Gmail viene puesto de fabrica", v.e_cservidor.get() == "smtp.gmail.com")
check("con su puerto", v.e_cpuerto.get() == "587")
check("y la casilla del negocio ya viene escrita",
      v.e_cusuario.get() == "marcacion.elbuencorte@gmail.com")
check("el campo es lo bastante ancho para verla entera",
      int(v.e_cusuario.cget("width")) >= len("marcacion.elbuencorte@gmail.com"))
check("la contrasena no viene de ninguna parte", v.e_cclave.get() == "")

avisos = []
mb.showwarning = lambda *a, **k: avisos.append(a)
v.guardar_config()
check("no deja encenderlo sin la contrasena", bool(avisos))
check("y la configuracion no queda encendida a medias",
      v.datos.config()["correo_activo"] == "0")
mb.showwarning = lambda *a, **k: None

v._set(v.e_cusuario, "carniceria@gmail.com")
v._set(v.e_cclave, "clave-de-aplicacion")
infos = []
mb.showinfo = lambda *a, **k: infos.append(a)
v.guardar_config()
c = v.datos.config()
check("ahora si lo guarda", c["correo_activo"] == "1")
check("guarda la cuenta", c["correo_usuario"] == "carniceria@gmail.com")
check("y la contrasena", c["correo_clave"] == "clave-de-aplicacion")
check("avisa de los que quedaron sin correo",
      any("todavia no tienen correo" in str(a) for a in infos))
mb.showinfo = lambda *a, **k: None

print("\n--- marcar avisa por correo ---")
# Gente nueva, para no chocar con los dias ya pagados de la prueba anterior.
con = v.datos.agregar_trabajador("Con Correo", 3000, correo="con@gmail.com")
sin = v.datos.agregar_trabajador("Sin Correo", 3000)
v.recargar_todo()
v.tabs.select(0)
v.elegir(con); v.marcar()
check("la pantalla dice a donde se le aviso",
      "con@gmail.com" in v.lbl_aviso.cget("text"))
check("y el correo quedo en la cola", len(v.datos.correos_por_enviar()) == 1)
v._mirar_correos(seguir=False)
check("el estado en pantalla cuenta lo que espera",
      "1 esperando conexion" in v.lbl_correo.cget("text"))
v.datos.correo_enviado(v.datos.correos_por_enviar()[0]["id"])
v._mirar_correos(seguir=False)
check("y lo que ya salio", "1 avisos enviados" in v.lbl_correo.cget("text"))
check("el que no tiene correo marca igual",
      v.datos.marcar(sin)["correo"] is None
      and len(v.datos.correos_por_enviar()) == 0)

print("\n--- el informe del dia para el dueno ---")
v.tabs.select(4)
check("viene apagado", not v.informe_activo.get())
check("el correo del dueno se puede escribir de entrada",
      str(v.e_cjefe.cget("state")) == "normal")
v.informe_activo.set(True); v._refrescar_correo()
avisos = []
mb.showwarning = lambda *a, **k: avisos.append(a)
v.guardar_config()
check("no deja encenderlo sin el correo del dueno", bool(avisos))
check("y no queda encendido a medias", v.datos.config()["informe_activo"] == "0")
mb.showwarning = lambda *a, **k: None
v._set(v.e_cjefe, "jefe@gmail.com")
v.guardar_config()
check("con el correo puesto, lo guarda", v.datos.config()["informe_activo"] == "1")
check("y guarda a quien va", v.datos.config()["correo_jefe"] == "jefe@gmail.com")
check("la pantalla dice que no se ha mandado ninguno",
      "Todavia no" in v.lbl_informe.cget("text"))

hoy = app.date.today().isoformat()
check("hoy esta por informar", hoy in v.informes_pendientes())
check("pero al abrir no se ofrece el de hoy",
      hoy not in v.informes_pendientes(incluir_hoy=False))

print("\n--- cerrar el dia: solo manda si se dice que si ---")
dias = v.informes_pendientes()
for f in dias:
    v.datos.encolar_informe(f)
check("el informe queda en la cola",
      any(c["trabajador_id"] is None for c in v.datos.correos_por_enviar()))
check("y el dia queda dado por informado",
      v.datos.config()["ultimo_informe"] == dias[-1])
check("ya no vuelve a pedirlo al cerrar", v.informes_pendientes() == [])
v.recargar_config()
check("la pantalla ahora dice cual fue el ultimo",
      "Ultimo informe" in v.lbl_informe.cget("text"))
mb.askyesno = lambda *a, **k: False

print("\n--- respaldos ---")
check("hizo la copia del dia", v.datos.ultimo_respaldo()[0] is not None)
check("no duplica la copia del dia", v.datos.respaldar() is None)

print("\n--- al cerrar se pregunta, y si se dice que no, no manda nada ---")
v.datos.guardar_config({"ultimo_informe": ""})     # como si no se hubiera mandado
check("hay algo que informar", bool(v.informes_pendientes()))
antes = len(v.datos.correos_por_enviar())
preguntas = []
mb.askyesno = lambda *a, **k: preguntas.append(a) or False
v.cerrar()
check("pregunta antes de cerrar", bool(preguntas))
check("la pregunta dice a que correo va", "jefe@gmail.com" in str(preguntas[-1]))
check("si se dice que no, no encola nada",
      len(v.datos.correos_por_enviar()) == antes)
try:                      # la ventana principal es la raiz: al cerrarla se
    vive = bool(v.winfo_exists())   # lleva el interprete de Tk entero
except app.tk.TclError:
    vive = False
check("y cierra igual", not vive)
print("\n--- y si se dice que si, arma el informe y se despide ---")
v = app.App(presentacion=False)      # la anterior quedo cerrada
v.withdraw()
v.datos.guardar_config({"ultimo_informe": ""})
dias = v.informes_pendientes()
antes = len(v.datos.correos_por_enviar())
# El hilo que envia no corre en las pruebas, asi que no hay nada que esperar.
v._esperar_envio = lambda paso, segundos=25: 0
mb.askyesno = lambda *a, **k: True
v.cerrar()
ahora = v.datos.correos_por_enviar()
check("encola el informe", len(ahora) > antes)
check("al correo del dueno", ahora[-1]["para"] == "jefe@gmail.com")
check("con el Excel y el PDF pegados",
      len(v.datos.adjuntos_de(ahora[-1]["id"])) == 2)
check("y da el dia por informado",
      v.datos.config()["ultimo_informe"] == dias[-1])
v.apagar_todo()

print("\n" + ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
sys.exit(1 if fallas else 0)
