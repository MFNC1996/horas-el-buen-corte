# -*- coding: utf-8 -*-
"""
Control de horas - Carniceria El Buen Corte
Aplicacion de escritorio. No necesita internet ni servidor.

    python app.py
"""

import os
import subprocess
import sys
import traceback
from datetime import date, datetime, timedelta

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as N

# Paleta del logo del local
ROJO = "#B4141F"
ROJO_CLARO = "#F8E4E5"
VERDE = "#16793B"
VERDE_CLARO = "#DFF0E4"
AMBAR = "#8A5A00"
AMBAR_CLARO = "#FBF0DC"
TINTA = "#15100F"
PAPEL = "#F1EFEC"
BLANCO = "#FFFFFF"
LINEA = "#DFD8D1"
SUAVE = "#6C625C"

VERSION = "1.4.1"
AUTOR = "Macoem"

FUENTE = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"
MONO = "Consolas" if sys.platform.startswith("win") else "Menlo"


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.datos = N.Datos()
        primera = self.datos.sembrar_si_vacia()
        try:
            self.datos.respaldar()
        except Exception:
            pass

        self.title("Control de Horas  -  El Buen Corte   |   by %s" % AUTOR)
        ancho = min(1120, self.winfo_screenwidth() - 60)
        alto = min(720, self.winfo_screenheight() - 110)
        self.geometry("%dx%d+%d+%d" % (
            ancho, alto, max(0, (self.winfo_screenwidth() - ancho) // 2),
            max(0, (self.winfo_screenheight() - alto) // 3)))
        self.minsize(min(900, ancho), min(560, alto))
        self.configure(bg=PAPEL)

        self.sel_trab = None          # trabajador elegido en la pantalla de marcar

        self._estilos()
        self._cabecera()
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.tabs.enable_traversal()
        self._tab_marcar()
        self._tab_jornadas()
        self._tab_resumen()
        self._tab_trabajadores()
        self._tab_config()

        self.recargar_todo()
        self._latido()
        if primera:
            self.after(400, lambda: messagebox.showinfo(
                "Primer uso",
                "Cree tres trabajadores de ejemplo.\n\nAnda a la pestana "
                "Trabajadores para ponerles el nombre real y el valor de la hora."))

    # ------------------------------------------------------------ apariencia
    def _estilos(self):
        e = ttk.Style(self)
        try:
            e.theme_use("clam")
        except tk.TclError:
            pass
        e.configure(".", background=PAPEL, foreground=TINTA,
                    font=(FUENTE, 10), fieldbackground=BLANCO)
        e.configure("TNotebook", background=PAPEL, borderwidth=0)
        e.configure("TNotebook.Tab", padding=(18, 10), font=(FUENTE, 10, "bold"),
                    background=PAPEL, foreground=SUAVE)
        e.map("TNotebook.Tab", background=[("selected", TINTA)],
              foreground=[("selected", PAPEL)])
        e.configure("TFrame", background=PAPEL)
        e.configure("TLabelframe", background=PAPEL, borderwidth=1,
                    relief="solid", bordercolor=LINEA)
        e.configure("TLabelframe.Label", background=PAPEL, foreground=SUAVE,
                    font=(FUENTE, 9, "bold"))
        e.configure("TLabel", background=PAPEL)
        e.configure("Rotulo.TLabel", foreground=SUAVE, font=(FUENTE, 9, "bold"))
        e.configure("TButton", padding=(12, 7), font=(FUENTE, 10))
        e.configure("Principal.TButton", padding=(16, 9),
                    font=(FUENTE, 10, "bold"), background=TINTA, foreground=PAPEL)
        e.map("Principal.TButton", background=[("active", ROJO)])
        e.configure("Chip.TButton", padding=(9, 5), font=(MONO, 10))
        e.configure("Treeview", rowheight=27, fieldbackground=BLANCO,
                    background=BLANCO, font=(FUENTE, 10))
        e.configure("Treeview.Heading", font=(FUENTE, 9, "bold"),
                    background=TINTA, foreground=PAPEL, padding=(6, 8))
        e.map("Treeview", background=[("selected", ROJO)],
              foreground=[("selected", BLANCO)])

    def _cabecera(self):
        barra = tk.Frame(self, bg=BLANCO, height=76)
        barra.pack(fill="x", side="top")
        barra.pack_propagate(False)

        # Las chairas cruzadas del logo del local.
        self.img_marca = None
        try:
            import imagen_marca
            self.img_marca = tk.PhotoImage(data=imagen_marca.CABECERA)
            tk.Label(barra, image=self.img_marca, bg=BLANCO).pack(
                side="left", padx=(16, 0), pady=8)
        except Exception:
            pass                      # sin la imagen la ventana igual sirve

        cont = tk.Frame(barra, bg=BLANCO)
        cont.pack(side="left", padx=14, pady=10)
        tk.Label(cont, text="El Buen Corte", bg=BLANCO, fg=ROJO,
                 font=(FUENTE, 19, "bold italic")).pack(anchor="w")
        tk.Label(cont, text="LONCOCHE  ·  CONTROL DE HORAS", bg=BLANCO, fg=SUAVE,
                 font=(FUENTE, 8, "bold")).pack(anchor="w", pady=(2, 0))
        derecha = tk.Frame(barra, bg=BLANCO)
        derecha.pack(side="right", padx=22)
        self.lbl_reloj = tk.Label(derecha, text="", bg=BLANCO, fg=TINTA,
                                  font=(MONO, 22, "bold"))
        self.lbl_reloj.pack(anchor="e")
        self.lbl_autor = tk.Label(derecha, text="by %s" % AUTOR, bg=BLANCO, fg=ROJO,
                                  font=(FUENTE, 9, "bold italic"))
        self.lbl_autor.pack(anchor="e")
        tk.Frame(self, bg=VERDE, height=3).pack(fill="x")

    def _latido(self):
        """Reloj de la cabecera: la hora que se va a registrar al marcar."""
        self.lbl_reloj.config(text=datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._latido)

    # ======================================================== pestana MARCAR
    def _tab_marcar(self):
        p = ttk.Frame(self, padding=16)
        self.tabs.add(p, text="  Marcar  ")

        tk.Label(p, text="1.  Toca tu nombre", bg=PAPEL, fg=SUAVE,
                 font=(FUENTE, 10, "bold")).pack(anchor="w")
        self.caja_nombres = tk.Frame(p, bg=PAPEL)
        self.caja_nombres.pack(fill="x", pady=(8, 16))

        self.panel = tk.Frame(p, bg=BLANCO, highlightbackground=LINEA,
                              highlightthickness=1)
        self.panel.pack(fill="both", expand=True)

        self.lbl_quien = tk.Label(self.panel, text="", bg=BLANCO, fg=TINTA,
                                  font=(FUENTE, 20, "bold"))
        self.lbl_quien.pack(pady=(14, 1))
        self.lbl_toca = tk.Label(self.panel, text="", bg=BLANCO, fg=SUAVE,
                                 font=(FUENTE, 11))
        self.lbl_toca.pack()
        self.lbl_marca = tk.Label(self.panel, text="", bg=BLANCO, fg=ROJO,
                                  font=(FUENTE, 26, "bold"))
        self.lbl_marca.pack(pady=(1, 10))

        self.btn_marcar = tk.Button(
            self.panel, text="MARCAR", command=self.marcar,
            bg=TINTA, fg=PAPEL, activebackground=ROJO, activeforeground=BLANCO,
            font=(FUENTE, 16, "bold"), relief="flat", cursor="hand2",
            padx=46, pady=13, state="disabled")
        self.btn_marcar.pack()

        self.lbl_hoy = tk.Label(self.panel, text="", bg=BLANCO, fg=SUAVE,
                                font=(MONO, 11), justify="center")
        self.lbl_hoy.pack(pady=(12, 4))
        self.lbl_aviso = tk.Label(self.panel, text="", bg=BLANCO,
                                  font=(FUENTE, 12, "bold"))
        self.lbl_aviso.pack(pady=(0, 12))

    def _pintar_nombres(self):
        for w in self.caja_nombres.winfo_children():
            w.destroy()
        if not self._trabs:
            tk.Label(self.caja_nombres, bg=PAPEL, fg=SUAVE, font=(FUENTE, 10),
                     text="No hay trabajadores. Agregalos en la pestana "
                          "Trabajadores.").pack(anchor="w")
            return
        for t in self._trabs:
            elegido = self.sel_trab == t["id"]
            b = tk.Button(
                self.caja_nombres, text=t["nombre"],
                command=lambda i=t["id"]: self.elegir(i),
                bg=ROJO if elegido else BLANCO, fg=BLANCO if elegido else TINTA,
                activebackground=ROJO if elegido else PAPEL,
                font=(FUENTE, 13, "bold" if elegido else "normal"),
                relief="flat", cursor="hand2", padx=22, pady=13,
                highlightbackground=LINEA, highlightthickness=1)
            b.pack(side="left", padx=(0, 8))

    def elegir(self, tid):
        self.sel_trab = tid
        self.lbl_aviso.config(text="")
        self._pintar_nombres()
        self._pintar_panel()

    def _pintar_panel(self):
        if self.sel_trab is None:
            self.lbl_quien.config(text="Elige tu nombre arriba")
            self.lbl_toca.config(text="")
            self.lbl_marca.config(text="")
            self.lbl_hoy.config(text="")
            self.btn_marcar.config(state="disabled", text="MARCAR")
            return
        t = [x for x in self._trabs if x["id"] == self.sel_trab]
        if not t:
            self.sel_trab = None
            return self._pintar_panel()
        est = self.datos.estado(self.sel_trab)
        self.lbl_quien.config(text=t[0]["nombre"])

        if est["completa"]:
            self.lbl_toca.config(text="Ya marcaste las cuatro veces de hoy")
            self.lbl_marca.config(text="JORNADA COMPLETA", fg=VERDE)
            self.btn_marcar.config(state="disabled", text="NADA QUE MARCAR")
        else:
            self.lbl_toca.config(text="Vas a marcar:")
            self.lbl_marca.config(text=est["etiqueta"].upper(), fg=ROJO)
            self.btn_marcar.config(state="normal",
                                   text="MARCAR  " + est["etiqueta"].upper())

        hechas = dict((m["tipo"], m["hora"]) for m in est["marcas"])
        partes = []
        for tipo in N.TIPOS:
            partes.append("%-18s %s" % (N.ETIQUETAS[tipo],
                                        hechas.get(tipo, "--:--")))
        resumen = "\n".join(partes)
        if est["horas"]:
            resumen += "\n\nLlevas %s horas trabajadas" % N.hhmm_txt(est["horas"])
        self.lbl_hoy.config(text=resumen)

    def marcar(self):
        if self.sel_trab is None:
            return
        try:
            r = self.datos.marcar(self.sel_trab)
        except ValueError as e:
            return messagebox.showwarning("No se pudo marcar", str(e))
        nombre = [x["nombre"] for x in self._trabs if x["id"] == self.sel_trab][0]
        # Se suelta la seleccion al tiro: asi el siguiente que llegue no puede
        # marcar por error a nombre del anterior.
        self.sel_trab = None
        self.recargar_todo()
        self.lbl_aviso.config(
            text="Listo, %s:  %s registrada a las %s" % (nombre, r["etiqueta"], r["hora"]),
            fg=VERDE, bg=BLANCO)
        self.after(9000, lambda: self.lbl_aviso.config(text=""))

    # ================================================= pestana DIAS TRABAJADOS
    def _tab_jornadas(self):
        """Cada dia de cada trabajador: horas, lo que vale, y si ya se pago."""
        p = ttk.Frame(self, padding=14)
        self.tabs.add(p, text="  Dias trabajados  ")

        f = ttk.Frame(p)
        f.pack(fill="x")
        ttk.Label(f, text="Mes", style="Rotulo.TLabel").pack(side="left", padx=(0, 6))
        self.cb_mes_j = ttk.Combobox(f, state="readonly", width=18, font=(FUENTE, 10))
        self.cb_mes_j.pack(side="left", padx=(0, 14))
        self.cb_mes_j.bind("<<ComboboxSelected>>", lambda e: self.recargar_jornadas())
        ttk.Label(f, text="Trabajador", style="Rotulo.TLabel").pack(side="left", padx=(0, 6))
        self.cb_filtro_trab = ttk.Combobox(f, state="readonly", width=18, font=(FUENTE, 10))
        self.cb_filtro_trab.pack(side="left", padx=(0, 14))
        self.cb_filtro_trab.bind("<<ComboboxSelected>>", lambda e: self.recargar_jornadas())
        self.solo_pendientes = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Solo lo que falta pagar", variable=self.solo_pendientes,
                        command=self.recargar_jornadas).pack(side="left")

        tk.Label(p, bg=PAPEL, fg=SUAVE, font=(FUENTE, 9), anchor="w",
                 text="Para marcar un dia como pagado, haz clic en  ☐ Pagar.   "
                      "Para corregir las horas, doble clic en la fila."
                 ).pack(fill="x", pady=(8, 4))

        cols = ("pagado", "fecha", "trab", "horas", "norm", "extra", "total")
        titulos = ["Pagado", "Fecha", "Trabajador", "Horas trabajadas",
                   "Horas normales", "Horas extra", "A PAGAR"]
        anchos = [104, 118, 180, 118, 118, 100, 124]
        marco = ttk.Frame(p)
        marco.pack(fill="both", expand=True)
        self.tv_j = ttk.Treeview(marco, columns=cols, show="headings", selectmode="browse")
        for c, t, a in zip(cols, titulos, anchos):
            self.tv_j.heading(c, text=t)
            self.tv_j.column(c, width=a, minwidth=60, stretch=(c == "trab"),
                             anchor="w" if c in ("trab", "pagado") else
                             ("e" if c == "total" else "center"))
        self.tv_j.tag_configure("falta", background=AMBAR_CLARO, foreground=AMBAR)
        self.tv_j.tag_configure("pagado", foreground=VERDE)
        sb = ttk.Scrollbar(marco, orient="vertical", command=self.tv_j.yview)
        self.tv_j.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tv_j.pack(side="left", fill="both", expand=True)
        self.tv_j.bind("<Button-1>", self._clic_en_dia)
        self.tv_j.bind("<Double-1>", self._doble_clic_en_dia)

    def _doble_clic_en_dia(self, evento):
        # El doble clic sobre el cuadrado de pagado no abre el corrector.
        if self.tv_j.identify_column(evento.x) == "#1":
            return "break"
        self.abrir_editor()

    def _clic_en_dia(self, evento):
        """Un clic en la columna Pagado cambia el check de ese dia."""
        if self.tv_j.identify_region(evento.x, evento.y) != "cell":
            return
        if self.tv_j.identify_column(evento.x) != "#1":
            return
        fila = self.tv_j.identify_row(evento.y)
        if fila:
            self.cambiar_pagado(fila)
            return "break"

    def cambiar_pagado(self, fila):
        fecha, tid = fila.split("|")
        tid = int(tid)
        pago = self.datos.pago_de(tid, fecha)
        nombre = next((t["nombre"] for t in self.datos.trabajadores(False)
                       if t["id"] == tid), "?")
        if pago:
            if not messagebox.askyesno(
                    "Quitar el pago",
                    "El %s de %s figura pagado (%s, el %s).\n\n"
                    "¿Quitar el check? El dia vuelve a quedar por pagar."
                    % (fecha, nombre, N.pesos(pago["monto"]), pago["pagado_en"])):
                return
            self.datos.desmarcar_pagado(tid, fecha)
        else:
            try:
                self.datos.marcar_pagado(tid, fecha)
            except ValueError as e:
                return messagebox.showwarning("No se puede marcar como pagado", str(e))
        self.recargar_todo()

    def abrir_editor(self):
        sel = self.tv_j.selection()
        if not sel:
            return messagebox.showinfo("Elige un dia",
                                       "Selecciona una fila de la lista.")
        fecha, tid = sel[0].split("|")
        pago = self.datos.pago_de(int(tid), fecha)
        if pago:
            return messagebox.showinfo(
                "Dia ya pagado",
                "Ese dia ya se pago (%s, el %s), asi que no se puede corregir.\n\n"
                "Si hay que arreglarlo, primero quitale el check de pagado."
                % (N.pesos(pago["monto"]), pago["pagado_en"]))
        EditorMarcas(self, int(tid), fecha)

    # =============================================== pestana PAGOS POR PERSONA
    def _tab_resumen(self):
        """Por trabajador: dias, cuanto se le pago y cuanto se le debe."""
        p = ttk.Frame(self, padding=14)
        self.tabs.add(p, text="  Pagos por persona  ")

        barra = ttk.Frame(p)
        barra.pack(fill="x")
        ttk.Label(barra, text="Periodo", style="Rotulo.TLabel").pack(side="left", padx=(0, 6))
        self.cb_mes_r = ttk.Combobox(barra, state="readonly", width=20, font=(FUENTE, 10))
        self.cb_mes_r.pack(side="left")
        self.cb_mes_r.bind("<<ComboboxSelected>>", lambda e: self.recargar_resumen())
        ttk.Button(barra, text="Exportar a Excel", style="Principal.TButton",
                   command=lambda: self.exportar("excel")).pack(side="right", padx=(8, 0))
        ttk.Button(barra, text="Exportar a PDF",
                   command=lambda: self.exportar("pdf")).pack(side="right")

        tk.Label(p, bg=PAPEL, fg=SUAVE, font=(FUENTE, 9), anchor="w",
                 text="Toca a una persona y abajo aparecen sus dias. Ahi mismo marcas "
                      "cada dia con  ☐ Pagar, o todos juntos con el boton."
                 ).pack(fill="x", pady=(8, 0))
        self.lbl_aviso_r = tk.Label(p, text="", bg=AMBAR_CLARO, fg=AMBAR,
                                    font=(FUENTE, 10, "bold"), anchor="w", padx=12, pady=6)

        cols = ("trab", "dias", "pagados", "pagado", "pend", "debe")
        titulos = ["Trabajador", "Dias trabajados", "Dias pagados", "Se le ha pagado",
                   "Dias por pagar", "SE LE DEBE"]
        anchos = [190, 120, 110, 140, 110, 140]
        marco = ttk.Frame(p)
        marco.pack(fill="x", pady=(12, 0))
        self.tv_r = ttk.Treeview(marco, columns=cols, show="headings",
                                 selectmode="browse", height=5)
        for c, t, a in zip(cols, titulos, anchos):
            self.tv_r.heading(c, text=t)
            self.tv_r.column(c, width=a, minwidth=60, stretch=(c == "trab"),
                             anchor="w" if c == "trab" else "e")
        self.tv_r.pack(fill="x")
        self.tv_r.bind("<<TreeviewSelect>>", lambda e: self.recargar_detalle())

        cab = ttk.Frame(p)
        cab.pack(fill="x", pady=(16, 4))
        self.lbl_det = tk.Label(cab, text="", bg=PAPEL, fg=TINTA,
                                font=(FUENTE, 12, "bold"), anchor="w")
        self.lbl_det.pack(side="left")
        self.btn_pagar_todo = ttk.Button(cab, text="Pagar todo lo pendiente",
                                         style="Principal.TButton",
                                         command=self.pagar_todo, state="disabled")
        self.btn_pagar_todo.pack(side="right")

        cols = ("pagado", "fecha", "horas", "norm", "extra", "valor", "estado")
        titulos = ["Pagado", "Fecha", "Horas", "Normales", "Extra", "Valor del dia",
                   "Estado"]
        anchos = [104, 118, 80, 86, 76, 116, 200]
        marco2 = ttk.Frame(p)
        marco2.pack(fill="both", expand=True)
        self.tv_d = ttk.Treeview(marco2, columns=cols, show="headings", selectmode="none")
        for c, t, a in zip(cols, titulos, anchos):
            self.tv_d.heading(c, text=t)
            self.tv_d.column(c, width=a, minwidth=60, stretch=(c == "estado"),
                             anchor="w" if c in ("estado", "pagado") else
                             ("e" if c == "valor" else "center"))
        self.tv_d.tag_configure("pagado", foreground=VERDE)
        self.tv_d.tag_configure("falta", background=AMBAR_CLARO, foreground=AMBAR)
        sb2 = ttk.Scrollbar(marco2, orient="vertical", command=self.tv_d.yview)
        self.tv_d.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self.tv_d.pack(side="left", fill="both", expand=True)
        self.tv_d.bind("<Button-1>", self._clic_en_detalle)

    def _clic_en_detalle(self, evento):
        """Mismo check de pagado que en Dias trabajados, en los dias de la persona."""
        if self.tv_d.identify_region(evento.x, evento.y) != "cell":
            return
        if self.tv_d.identify_column(evento.x) != "#1":
            return
        fila = self.tv_d.identify_row(evento.y)
        if fila:
            self.cambiar_pagado(fila)
            return "break"

    def _periodo_r(self):
        """(desde, hasta, titulo) del periodo elegido en Pagos por persona."""
        t = self.cb_mes_r.get()
        if t == "Todo" or not t:
            return None, None, "Todo lo registrado"
        for ym in self._meses_lista:
            if self._mes_texto(ym) == t:
                a, m = int(ym[:4]), int(ym[5:7])
                return "%s-01" % ym, "%s-%02d" % (ym, N.ultimo_dia(a, m)), t
        return None, None, "Todo lo registrado"

    def pagar_todo(self):
        sel = self.tv_r.selection()
        if not sel:
            return
        tid = int(sel[0])
        desde, hasta, titulo = self._periodo_r()
        fila = [f for f in self._resumen["filas"] if f["id"] == tid][0]
        if not fila["dias_pendientes"]:
            return
        if not messagebox.askyesno(
                "Pagar lo pendiente",
                "%s tiene %d dias por pagar en %s.\n\n"
                "Total: %s\n\n¿Marcarlos todos como pagados hoy?"
                % (fila["nombre"], fila["dias_pendientes"], titulo.lower(),
                   N.pesos(fila["por_pagar"]))):
            return
        self.datos.pagar_pendientes(tid, desde, hasta)
        self.recargar_todo()
        self.tv_r.selection_set(str(tid))

    # ================================================== pestana TRABAJADORES
    def _tab_trabajadores(self):
        p = ttk.Frame(self, padding=14)
        self.tabs.add(p, text="  Trabajadores  ")

        f = ttk.LabelFrame(p, text=" DATOS DEL TRABAJADOR ", padding=12)
        f.pack(fill="x")
        ttk.Label(f, text="Nombre", style="Rotulo.TLabel").grid(row=0, column=0, sticky="w")
        self.e_tnombre = ttk.Entry(f, width=26, font=(FUENTE, 11))
        self.e_tnombre.grid(row=1, column=0, padx=(0, 16), sticky="w")
        ttk.Label(f, text="Valor hora normal ($)", style="Rotulo.TLabel").grid(row=0, column=1, sticky="w")
        caja_vh = ttk.Frame(f)
        caja_vh.grid(row=1, column=1, padx=(0, 16), sticky="w")
        self.e_tvalor = ttk.Entry(caja_vh, width=11, font=(MONO, 10), justify="right")
        self.e_tvalor.pack(side="left")
        ttk.Button(caja_vh, text="¿No lo sabes?", style="Chip.TButton",
                   command=self.abrir_calculadora).pack(side="left", padx=(5, 0))
        ttk.Label(f, text="Valor hora extra ($)", style="Rotulo.TLabel").grid(row=0, column=2, sticky="w")
        self.e_tvalorx = ttk.Entry(f, width=13, font=(MONO, 10), justify="right")
        self.e_tvalorx.grid(row=1, column=2, padx=(0, 16), sticky="w")
        ttk.Label(f, text="Horas contrato/dia", style="Rotulo.TLabel").grid(
            row=0, column=3, sticky="w")
        self.e_tcontrato = ttk.Entry(f, width=8, font=(MONO, 10), justify="right")
        self.e_tcontrato.grid(row=1, column=3, padx=(0, 16), sticky="w")
        ttk.Label(f, text="en blanco usa la general", style="Rotulo.TLabel").grid(
            row=1, column=4, sticky="w")

        self.lbl_calc = tk.Label(p, text="", bg=PAPEL, fg=VERDE, font=(FUENTE, 9),
                                 justify="left", anchor="w")
        self.lbl_calc.pack(fill="x", pady=(8, 0))
        b = ttk.Frame(f)
        b.grid(row=2, column=0, columnspan=4, sticky="w", pady=(12, 0))
        ttk.Button(b, text="Agregar nuevo", style="Principal.TButton",
                   command=self.agregar_trabajador).pack(side="left")
        ttk.Button(b, text="Guardar cambios del seleccionado",
                   command=self.guardar_trabajador).pack(side="left", padx=6)
        ttk.Button(b, text="Quitar de la lista",
                   command=self.quitar_trabajador).pack(side="left")

        marco = ttk.LabelFrame(p, text=" TRABAJADORES ", padding=10)
        marco.pack(fill="both", expand=True, pady=(14, 0))
        cols = ("nombre", "vh", "vhe", "contrato", "dias")
        self.tv_t = ttk.Treeview(marco, columns=cols, show="headings", selectmode="browse")
        for c, t, a, al in zip(cols, ["Nombre", "Valor hora", "Valor hora extra",
                                      "Contrato (h/dia)", "Dias trabajados"],
                               [200, 120, 140, 130, 120],
                               ["w", "e", "e", "e", "e"]):
            self.tv_t.heading(c, text=t)
            self.tv_t.column(c, width=a, anchor=al)
        self.tv_t.pack(fill="both", expand=True)
        self.tv_t.bind("<<TreeviewSelect>>", lambda e: self.cargar_trabajador_sel())

    # =================================================== pestana CONFIGURACION
    def _tab_config(self):
        p = ttk.Frame(self, padding=14)
        self.tabs.add(p, text="  Configuracion  ")

        a = ttk.LabelFrame(p, text=" JORNADA DEL CONTRATO ", padding=14)
        a.pack(fill="x")
        ttk.Label(a, text="Horas de contrato al dia", style="Rotulo.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 14), pady=(0, 2))
        self.e_contrato = ttk.Entry(a, width=8, font=(MONO, 10), justify="right")
        self.e_contrato.grid(row=1, column=0, padx=(0, 14), sticky="nw")
        tk.Label(a, bg=PAPEL, fg=SUAVE, font=(FUENTE, 9), justify="left", anchor="w",
                 text="Todo lo que se trabaje por sobre estas horas, en el dia, es hora extra."
                 ).grid(row=1, column=1, sticky="w")

        b = ttk.LabelFrame(p, text=" CUANTO VALE UNA HORA EXTRA ", padding=14)
        b.pack(fill="x", pady=(14, 0))
        self.modo_extra = tk.StringVar(value="recargo")
        ttk.Radiobutton(b, text="Recargo sobre la hora normal", value="recargo",
                        variable=self.modo_extra, command=self._refrescar_modo
                        ).grid(row=0, column=0, sticky="w", pady=3)
        self.e_recargo = ttk.Entry(b, width=8, font=(MONO, 10), justify="right")
        self.e_recargo.grid(row=0, column=1, padx=8)
        ttk.Label(b, text="%   (50 % es lo que fija la ley en Chile)",
                  style="Rotulo.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Radiobutton(b, text="Monto fijo por hora extra", value="fijo",
                        variable=self.modo_extra, command=self._refrescar_modo
                        ).grid(row=1, column=0, sticky="w", pady=3)
        self.e_vextra = ttk.Entry(b, width=10, font=(MONO, 10), justify="right")
        self.e_vextra.grid(row=1, column=1, padx=8)
        ttk.Label(b, text="$ por hora   (cada trabajador puede tener el suyo)",
                  style="Rotulo.TLabel").grid(row=1, column=2, sticky="w")
        self.lbl_ejemplo = tk.Label(b, text="", bg=ROJO_CLARO, fg=ROJO, anchor="w",
                                    font=(FUENTE, 10, "bold"), padx=12, pady=8)
        self.lbl_ejemplo.grid(row=2, column=0, columnspan=3, sticky="we", pady=(12, 0))

        c = ttk.LabelFrame(p, text=" DATOS DEL NEGOCIO (salen en el informe) ", padding=14)
        c.pack(fill="x", pady=(14, 0))
        ttk.Label(c, text="Nombre", style="Rotulo.TLabel").grid(row=0, column=0, sticky="w")
        self.e_negocio = ttk.Entry(c, width=32, font=(FUENTE, 11))
        self.e_negocio.grid(row=1, column=0, padx=(0, 20), sticky="w")
        ttk.Label(c, text="Ciudad", style="Rotulo.TLabel").grid(row=0, column=1, sticky="w")
        self.e_ciudad = ttk.Entry(c, width=20, font=(FUENTE, 11))
        self.e_ciudad.grid(row=1, column=1, padx=(0, 20), sticky="w")


        pie = ttk.Frame(p)
        pie.pack(fill="x", pady=(16, 0))
        ttk.Button(pie, text="Guardar configuracion", style="Principal.TButton",
                   command=self.guardar_config).pack(side="left")
        ttk.Button(pie, text="Abrir carpeta de datos",
                   command=self.abrir_carpeta_datos).pack(side="left", padx=8)
        ttk.Button(pie, text="Guardar copia en un pendrive...",
                   command=self.copia_manual).pack(side="left")
        self.lbl_ruta = tk.Label(p, text="", bg=PAPEL, fg=SUAVE, font=(FUENTE, 8),
                                 anchor="w", justify="left")
        self.lbl_ruta.pack(fill="x", pady=(12, 0))
        tk.Label(p, text="Control de Horas  v%s   ·   desarrollado por Macoem"
                         % VERSION, bg=PAPEL, fg=SUAVE,
                 font=(FUENTE, 9, "bold"), anchor="w").pack(fill="x", pady=(10, 0))

    # ============================================================= utilidades
    @staticmethod
    def _set(campo, valor):
        campo.delete(0, "end")
        campo.insert(0, valor)

    @staticmethod
    def _numero(txt):
        txt = (txt or "").replace(".", "").replace(",", ".").replace("$", "").strip()
        try:
            return float(txt or 0)
        except ValueError:
            raise ValueError("'%s' no es un monto valido." % txt)

    def _refrescar_modo(self):
        fijo = self.modo_extra.get() == "fijo"
        self.e_recargo.config(state="disabled" if fijo else "normal")
        self.e_vextra.config(state="normal" if fijo else "disabled")
        try:
            if fijo:
                self.lbl_ejemplo.config(text="Cada hora extra se paga %s"
                                             % N.pesos(float(self.e_vextra.get() or 0)))
            else:
                r = float(self.e_recargo.get() or 0)
                self.lbl_ejemplo.config(
                    text="Ejemplo: si la hora normal son $3.000, la extra sale %s"
                         % N.pesos(3000 * (1 + r / 100.0)))
        except ValueError:
            self.lbl_ejemplo.config(text="Escribe un numero valido")

    def _meses(self):
        meses = sorted({j["fecha"][:7] for j in self.datos.jornadas()}, reverse=True)
        hoy = date.today().strftime("%Y-%m")
        if hoy not in meses:
            meses.insert(0, hoy)
        return meses

    @staticmethod
    def _mes_texto(ym):
        a, m = ym.split("-")
        return "%s de %s" % (N.nombre_mes(int(m)).capitalize(), a)

    # ============================================================== acciones
    def _valor_hora_sospechoso(self, v):
        """
        Un valor hora de mas de $50.000 casi seguro es el sueldo mensual mal
        puesto. Si pasa inadvertido, cada dia se paga cientos de veces de mas.
        """
        if v <= 50000:
            return False
        return not messagebox.askyesno(
            "Revisa ese valor",
            "Pusiste %s como valor de UNA HORA.\n\n"
            "Eso parece un sueldo mensual, no un valor por hora. Con ese numero, "
            "un dia de 7 horas se pagaria %s.\n\n"
            "Si escribiste el sueldo por equivocacion, dale que No y usa el boton "
            "'¿No lo sabes?' que esta al lado del campo.\n\n"
            "¿Seguro que %s es lo que vale una hora?" % (N.pesos(v), N.pesos(v * 7),
                                                          N.pesos(v)))

    def agregar_trabajador(self):
        try:
            if self._valor_hora_sospechoso(self._numero(self.e_tvalor.get())):
                return
            self.datos.agregar_trabajador(self.e_tnombre.get(),
                                          self._numero(self.e_tvalor.get()),
                                          self._numero(self.e_tvalorx.get()),
                                          self._numero(self.e_tcontrato.get()))
        except ValueError as e:
            return messagebox.showerror("No se pudo agregar", str(e))
        for c in (self.e_tnombre, self.e_tvalor, self.e_tvalorx, self.e_tcontrato):
            self._set(c, "")
        self.lbl_calc.config(text="")
        self.recargar_todo()

    def abrir_calculadora(self):
        Calculadora(self)

    def aplicar_valor_hora(self, sueldo, horas):
        """sueldo / 30 x 7 / horas semanales = valor de la hora ordinaria."""
        v = N.valor_hora_desde_sueldo(sueldo, horas)
        if not v:
            return 0
        self._set(self.e_tvalor, "%d" % v)
        self.lbl_calc.config(
            text="Valor hora puesto arriba:  %s / 30 x 7 / %s h  =  %s la hora."
                 % (N.pesos(sueldo), N._limpio(horas), N.pesos(v)))
        return v

    def guardar_trabajador(self):
        sel = self.tv_t.selection()
        if not sel:
            return messagebox.showinfo("Elige un trabajador",
                                       "Selecciona uno de la lista de abajo.")
        try:
            if self._valor_hora_sospechoso(self._numero(self.e_tvalor.get())):
                return
            self.datos.editar_trabajador(int(sel[0]), self.e_tnombre.get(),
                                         self._numero(self.e_tvalor.get()),
                                         self._numero(self.e_tvalorx.get()),
                                         self._numero(self.e_tcontrato.get()))
        except ValueError as e:
            return messagebox.showerror("No se pudo guardar", str(e))
        self.recargar_todo()

    def quitar_trabajador(self):
        sel = self.tv_t.selection()
        if not sel:
            return messagebox.showinfo("Elige un trabajador",
                                       "Selecciona uno de la lista de abajo.")
        tid = int(sel[0])
        n = self.datos.jornadas_de(tid)
        if messagebox.askyesno("Quitar de la lista",
                               "Sale de la lista pero sus %d dias registrados se "
                               "conservan, para que los informes anteriores sigan "
                               "cuadrando.\n\nContinuar?" % n):
            self.datos.desactivar_trabajador(tid)
            if self.sel_trab == tid:
                self.sel_trab = None
            self.recargar_todo()

    def guardar_config(self):
        try:
            cambios = {
                "horas_contrato": self._numero(self.e_contrato.get()) or 7,
                "umbral_diario": self._numero(self.e_contrato.get()) or 7,
                "regla": "diaria",
                "modo_extra": self.modo_extra.get(),
                "recargo_extra": self._numero(self.e_recargo.get()),
                "valor_extra_global": self._numero(self.e_vextra.get()),
                "negocio": self.e_negocio.get().strip() or N.NEGOCIO_DEF,
                "ciudad": self.e_ciudad.get().strip() or N.CIUDAD_DEF,
            }
        except ValueError as e:
            return messagebox.showerror("Dato invalido", str(e))
        self.datos.guardar_config(cambios)
        self.recargar_todo()
        messagebox.showinfo("Listo", "Configuracion guardada.")

    def exportar(self, formato):
        desde, hasta, titulo = self._periodo_r()
        if desde:
            a, m = int(desde[:4]), int(desde[5:7])
            r = N.resumen_mensual(self.datos, a, m)
            nombre_base = "pagos-%04d-%02d" % (a, m)
        else:
            r = N.resumen_todo(self.datos)
            nombre_base = "pagos-todo-%s" % date.today().isoformat()
        if not r["filas"]:
            return messagebox.showinfo("Sin datos",
                                       "No hay marcas registradas en ese periodo.")
        ext = "xlsx" if formato == "excel" else "pdf"
        ruta = filedialog.asksaveasfilename(
            title="Guardar informe", defaultextension="." + ext,
            initialfile="%s.%s" % (nombre_base, ext),
            filetypes=[("Excel", "*.xlsx")] if formato == "excel" else [("PDF", "*.pdf")])
        if not ruta:
            return
        try:
            import informes
            if formato == "excel":
                informes.a_excel(r, ruta)
            else:
                informes.a_pdf(r, ruta)
        except Exception as e:
            return messagebox.showerror("No se pudo crear el informe",
                                        "%s\n\n%s" % (e, traceback.format_exc(limit=2)))
        if messagebox.askyesno("Informe listo",
                               "Se guardo en:\n%s\n\nQueres abrirlo ahora?" % ruta):
            self._abrir(ruta)

    @staticmethod
    def _abrir(ruta):
        try:
            if sys.platform.startswith("win"):
                os.startfile(ruta)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", ruta])
            else:
                subprocess.Popen(["xdg-open", ruta])
        except Exception:
            pass

    def abrir_carpeta_datos(self):
        self._abrir(N.carpeta_datos())

    def copia_manual(self):
        ruta = filedialog.asksaveasfilename(
            title="Guardar copia de seguridad", defaultextension=".sqlite3",
            initialfile="horas-%s.sqlite3" % date.today().isoformat(),
            filetypes=[("Base de datos", "*.sqlite3")])
        if not ruta:
            return
        try:
            self.datos.respaldar(ruta)
        except Exception as e:
            return messagebox.showerror("No se pudo copiar", str(e))
        messagebox.showinfo("Copia guardada", "Se guardo una copia en:\n%s" % ruta)

    # ============================================================== recargas
    def recargar_todo(self):
        self._trabs = self.datos.trabajadores()
        self._pintar_nombres()
        self._pintar_panel()

        meses = self._meses()
        textos = [self._mes_texto(m) for m in meses]
        self._meses_lista = meses
        actual = self.cb_mes_j.get()
        self.cb_mes_j["values"] = ["Todos"] + textos
        self.cb_mes_j.set(actual if actual in self.cb_mes_j["values"] else "Todos")
        actual = self.cb_filtro_trab.get()
        self.cb_filtro_trab["values"] = ["Todos"] + [t["nombre"] for t in self._trabs]
        self.cb_filtro_trab.set(actual if actual in self.cb_filtro_trab["values"] else "Todos")
        actual = self.cb_mes_r.get()
        self.cb_mes_r["values"] = textos + ["Todo"]
        self.cb_mes_r.set(actual if actual in self.cb_mes_r["values"] else textos[0])

        self.recargar_jornadas()
        self.recargar_resumen()
        self.recargar_trabajadores()
        self.recargar_config()

    def recargar_jornadas(self):
        for f in self.tv_j.get_children():
            self.tv_j.delete(f)
        t = self.cb_mes_j.get()
        desde = hasta = None
        if t != "Todos":
            for ym in self._meses_lista:
                if self._mes_texto(ym) == t:
                    a, m = int(ym[:4]), int(ym[5:7])
                    desde, hasta = "%s-01" % ym, "%s-%02d" % (ym, N.ultimo_dia(a, m))
        tid = None
        for x in self._trabs:
            if x["nombre"] == self.cb_filtro_trab.get():
                tid = x["id"]
        dias = N.dias_con_valor(self.datos, desde, hasta, tid)
        if self.solo_pendientes.get():
            dias = [d for d in dias if not d["pagado"]]
        dias.sort(key=lambda x: (x["fecha"], x["nombre"]), reverse=True)

        for j in dias:
            if not j["completa"]:
                tags, marca = ("falta",), "  -"
                a_pagar = "falta marcar"
            elif j["pagado"]:
                tags, marca = ("pagado",), "  ☑  Pagado"
                a_pagar = N.pesos(j["monto_pagado"])
            else:
                tags, marca = (), "  ☐  Pagar"
                a_pagar = N.pesos(j["total"])
            self.tv_j.insert("", "end", iid=j["id"], tags=tags, values=(
                marca,
                "%s %s" % (N.nombre_dia(j["fecha"])[:3], j["fecha"][8:10] + "-" +
                           j["fecha"][5:7]),
                j["nombre"],
                N.hhmm_txt(j["horas"]) if j["completa"] else "-",
                N.hhmm_txt(j["normales"]) if j["completa"] else "-",
                N.hhmm_txt(j["extra"]) if j["extra"] else "-",
                a_pagar))


    def recargar_resumen(self):
        elegido = self.tv_r.selection()
        for f in self.tv_r.get_children():
            self.tv_r.delete(f)
        desde, hasta, titulo = self._periodo_r()
        r = N.resumen_mensual(self.datos, int(desde[:4]), int(desde[5:7])) \
            if desde else N.resumen_todo(self.datos)
        self._resumen = r

        for f in r["filas"]:
            self.tv_r.insert("", "end", iid=str(f["id"]), values=(
                f["nombre"], f["turnos"], f["dias_pagados"], N.pesos(f["pagado"]),
                f["dias_pendientes"], N.pesos(f["por_pagar"])))

        n, plata = N.pendiente_fuera(self.datos, desde, hasta)
        if n:
            self.lbl_aviso_r.config(
                text="Ojo: fuera de %s hay %d dias sin pagar, por %s."
                     % (titulo.lower(), n, N.pesos(plata)))
            self.lbl_aviso_r.pack(fill="x", pady=(10, 0), after=self.cb_mes_r.master)
        else:
            self.lbl_aviso_r.pack_forget()

        if elegido and self.tv_r.exists(elegido[0]):
            self.tv_r.selection_set(elegido[0])
        elif r["filas"]:
            self.tv_r.selection_set(str(r["filas"][0]["id"]))
        self.recargar_detalle()

    def recargar_detalle(self):
        """Los dias de la persona elegida: lo que vale cada uno y si se pago."""
        for f in self.tv_d.get_children():
            self.tv_d.delete(f)
        sel = self.tv_r.selection()
        if not sel:
            self.lbl_det.config(text="Elige a una persona para ver sus dias")
            self.btn_pagar_todo.config(state="disabled", text="Pagar todo lo pendiente")
            return
        fila = [f for f in self._resumen["filas"] if f["id"] == int(sel[0])]
        if not fila:
            return
        fila = fila[0]
        self.lbl_det.config(text="Dias de %s" % fila["nombre"])
        for d in sorted(fila["dias"], key=lambda x: x["fecha"]):
            if not d["completa"]:
                tags, estado, marca = ("falta",), "falta marcar: " + ", ".join(
                    x.lower() for x in d["faltan"]), "  -"
                valor = "-"
            elif d["pagado"]:
                tags, estado, marca = ("pagado",), "pagado el %s-%s" % (
                    d["pagado_en"][8:10], d["pagado_en"][5:7]), "  ☑  Pagado"
                valor = N.pesos(d["monto_pagado"])
            else:
                tags, estado, valor, marca = (), "por pagar", N.pesos(d["total"]), \
                    "  ☐  Pagar"
            self.tv_d.insert("", "end", iid=d["id"], tags=tags, values=(
                marca,
                "%s %s" % (N.nombre_dia(d["fecha"])[:3], d["fecha"][8:10] + "-" +
                           d["fecha"][5:7]),
                N.hhmm_txt(d["horas"]) if d["completa"] else "-",
                N.hhmm_txt(d["normales"]) if d["completa"] else "-",
                N.hhmm_txt(d["extra"]) if d["extra"] else "-",
                valor, estado))
        if fila["dias_pendientes"]:
            self.btn_pagar_todo.config(
                state="normal",
                text="Pagar lo pendiente:  %s" % N.pesos(fila["por_pagar"]))
        else:
            self.btn_pagar_todo.config(state="disabled", text="Todo pagado")

    def recargar_trabajadores(self):
        for f in self.tv_t.get_children():
            self.tv_t.delete(f)
        for t in self._trabs:
            self.tv_t.insert("", "end", iid=str(t["id"]), values=(
                t["nombre"], N.pesos(t["valor_hora"]),
                N.pesos(t["valor_hora_extra"]) if t["valor_hora_extra"] else "-",
                N._limpio(t["horas_contrato"]) if t["horas_contrato"] else "general",
                self.datos.jornadas_de(t["id"])))

    def cargar_trabajador_sel(self):
        sel = self.tv_t.selection()
        if not sel:
            return
        for t in self._trabs:
            if t["id"] == int(sel[0]):
                self._set(self.e_tnombre, t["nombre"])
                self._set(self.e_tvalor, "%d" % round(t["valor_hora"] or 0))
                self._set(self.e_tvalorx,
                          "%d" % round(t["valor_hora_extra"]) if t["valor_hora_extra"] else "")
                self._set(self.e_tcontrato,
                          N._limpio(t["horas_contrato"]) if t["horas_contrato"] else "")

    def recargar_config(self):
        c = self.datos.config()
        self._set(self.e_contrato, N._limpio(c.get("horas_contrato", "7")))
        self.modo_extra.set(c.get("modo_extra", "recargo"))
        self.e_recargo.config(state="normal")
        self.e_vextra.config(state="normal")
        self._set(self.e_recargo, N._limpio(c.get("recargo_extra", "50")))
        self._set(self.e_vextra, N._limpio(c.get("valor_extra_global", "0")))
        self._set(self.e_negocio, c.get("negocio", N.NEGOCIO_DEF))
        self._set(self.e_ciudad, c.get("ciudad", N.CIUDAD_DEF))
        self._refrescar_modo()
        fecha, cuantos = self.datos.ultimo_respaldo()
        self.lbl_ruta.config(
            text="Los datos se guardan en:  %s\n%d marcas en %d dias registrados.\n%s"
                 % (self.datos.ruta, self.datos.total_marcas(),
                    self.datos.total_jornadas(),
                    ("Respaldo automatico: ultima copia del %s, %d guardadas."
                     % (fecha, cuantos)) if fecha else "Todavia no hay respaldos."))


# ------------------------------------ sacar el valor hora desde el sueldo
class Calculadora(tk.Toplevel):
    """
    Convierte el sueldo del contrato en valor por hora.

        sueldo / 30 = sueldo diario
        diario x 7  = sueldo semanal
        semanal / horas semanales pactadas = valor hora
    """

    def __init__(self, padre):
        tk.Toplevel.__init__(self, padre)
        self.padre = padre
        self.title("Sacar el valor hora desde el sueldo")
        self.configure(bg=PAPEL)
        self.resizable(False, False)
        self.transient(padre)
        self.grab_set()

        tk.Label(self, text="¿Cuanto vale una hora?", bg=PAPEL, fg=TINTA,
                 font=(FUENTE, 15, "bold")).pack(anchor="w", padx=20, pady=(18, 2))
        tk.Label(self, bg=PAPEL, fg=SUAVE, font=(FUENTE, 10), justify="left",
                 text="Escribe lo que dice el contrato y te lo calculo."
                 ).pack(anchor="w", padx=20)

        caja = tk.Frame(self, bg=PAPEL)
        caja.pack(padx=20, pady=(16, 6), anchor="w")
        tk.Label(caja, text="Sueldo mensual ($)", bg=PAPEL, fg=SUAVE,
                 font=(FUENTE, 9, "bold")).grid(row=0, column=0, sticky="w")
        self.e_sueldo = ttk.Entry(caja, width=14, font=(MONO, 13), justify="right")
        self.e_sueldo.grid(row=1, column=0, padx=(0, 14))
        tk.Label(caja, text="Horas semanales", bg=PAPEL, fg=SUAVE,
                 font=(FUENTE, 9, "bold")).grid(row=0, column=1, sticky="w")
        self.e_horas = ttk.Entry(caja, width=8, font=(MONO, 13), justify="right")
        self.e_horas.grid(row=1, column=1)
        self.e_horas.insert(0, N._limpio(padre.datos.config().get("umbral_semanal", "42")))

        self.lbl = tk.Label(self, text="", bg=PAPEL, fg=SUAVE, font=(MONO, 11),
                            justify="left", anchor="w")
        self.lbl.pack(fill="x", padx=20, pady=(10, 4))

        for e in (self.e_sueldo, self.e_horas):
            e.bind("<KeyRelease>", lambda ev: self._recalcular())

        pie = tk.Frame(self, bg=PAPEL)
        pie.pack(fill="x", padx=20, pady=(8, 18))
        self.btn = ttk.Button(pie, text="Usar este valor", style="Principal.TButton",
                              command=self.usar, state="disabled")
        self.btn.pack(side="left")
        ttk.Button(pie, text="Cancelar", command=self.destroy).pack(side="left", padx=6)

        self._recalcular()
        self.e_sueldo.focus_set()
        self.update_idletasks()
        self.geometry("+%d+%d" % (
            max(0, padre.winfo_rootx() + (padre.winfo_width() - self.winfo_width()) // 2),
            max(0, padre.winfo_rooty() + 120)))

    def _valores(self):
        try:
            return (self.padre._numero(self.e_sueldo.get()),
                    self.padre._numero(self.e_horas.get()))
        except ValueError:
            return 0, 0

    def _recalcular(self):
        sueldo, horas = self._valores()
        v = N.valor_hora_desde_sueldo(sueldo, horas)
        if not v:
            self.lbl.config(text="", fg=SUAVE)
            self.btn.config(state="disabled")
            return
        self.lbl.config(
            text="%s / 30      = %s al dia\n"
                 "%s x 7       = %s a la semana\n"
                 "%s / %s h    = %s la hora"
                 % (N.pesos(sueldo), N.pesos(sueldo / 30.0),
                    N.pesos(sueldo / 30.0), N.pesos(sueldo / 30.0 * 7),
                    N.pesos(sueldo / 30.0 * 7), N._limpio(horas), N.pesos(v)),
            fg=VERDE)
        self.btn.config(state="normal")

    def usar(self):
        sueldo, horas = self._valores()
        if self.padre.aplicar_valor_hora(sueldo, horas):
            self.destroy()


# ------------------------------------------------- corregir marcas de un dia
class EditorMarcas(tk.Toplevel):
    """Ventanita para que el administrador arregle las marcas de un dia."""

    def __init__(self, padre, tid, fecha):
        tk.Toplevel.__init__(self, padre)
        self.padre = padre
        self.datos = padre.datos
        self.tid = tid
        self.fecha = fecha
        nombre = next((t["nombre"] for t in self.datos.trabajadores(solo_activos=False)
                       if t["id"] == tid), "?")
        self.title("Corregir marcas  -  %s  -  %s" % (nombre, fecha))
        self.configure(bg=PAPEL)
        self.resizable(False, False)
        self.transient(padre)
        self.grab_set()

        tk.Label(self, text=nombre, bg=PAPEL, fg=TINTA,
                 font=(FUENTE, 15, "bold")).pack(anchor="w", padx=18, pady=(16, 0))
        tk.Label(self, text="%s, %s" % (N.nombre_dia(fecha), fecha), bg=PAPEL,
                 fg=SUAVE, font=(FUENTE, 10)).pack(anchor="w", padx=18)

        self.caja = tk.Frame(self, bg=PAPEL)
        self.caja.pack(padx=18, pady=14)
        self.lbl_total = tk.Label(self, text="", bg=PAPEL, fg=VERDE,
                                  font=(FUENTE, 12, "bold"))
        self.lbl_total.pack(pady=(0, 6))
        tk.Label(self, bg=PAPEL, fg=SUAVE, font=(FUENTE, 9), justify="left",
                 text="Puedes escribir la hora corta: 830 queda como 08:30, y 1930\n"
                      "como 19:30. Deja el campo vacio y guarda para borrar esa marca."
                 ).pack(padx=18, pady=(0, 10))

        pie = tk.Frame(self, bg=PAPEL)
        pie.pack(fill="x", padx=18, pady=(0, 16))
        ttk.Button(pie, text="Guardar", style="Principal.TButton",
                   command=self.guardar).pack(side="left")
        ttk.Button(pie, text="Cerrar", command=self.destroy).pack(side="left", padx=6)
        ttk.Button(pie, text="Borrar el dia completo",
                   command=self.borrar_dia).pack(side="right")

        self.campos = {}
        self._pintar()
        self.update_idletasks()
        x = padre.winfo_rootx() + (padre.winfo_width() - self.winfo_width()) // 2
        y = padre.winfo_rooty() + 90
        self.geometry("+%d+%d" % (max(0, x), max(0, y)))

    def _pintar(self):
        for w in self.caja.winfo_children():
            w.destroy()
        self.campos = {}
        marcas = self.datos.marcas_de(self.tid, self.fecha)
        por_tipo = dict((m["tipo"], m) for m in marcas)
        for i, tipo in enumerate(N.TIPOS):
            tk.Label(self.caja, text=N.ETIQUETAS[tipo], bg=PAPEL, fg=TINTA,
                     font=(FUENTE, 11), anchor="w", width=18).grid(
                row=i, column=0, sticky="w", pady=4)
            e = ttk.Entry(self.caja, width=9, font=(MONO, 14), justify="center")
            e.grid(row=i, column=1, padx=8)
            if tipo in por_tipo:
                e.insert(0, por_tipo[tipo]["hora"])
            # Escribes 830 y al cambiarte de campo queda 08:30.
            e.bind("<FocusOut>", self._acomodar)
            e.bind("<Return>", self._acomodar)
            self.campos[tipo] = e
            origen = por_tipo.get(tipo, {}).get("origen", "")
            tk.Label(self.caja, bg=PAPEL, fg=SUAVE, font=(FUENTE, 9),
                     text={"app": "marcada en la app", "manual": "corregida a mano",
                           "migrado": "viene del formato anterior",
                           "biometrico": "reloj biometrico"}.get(origen, "falta")
                     ).grid(row=i, column=2, sticky="w")
        self.lbl_total.config(text="Horas del dia: %s"
                                   % N.hhmm_txt(N.horas_de_marcas(marcas)))

    @staticmethod
    def _acomodar(evento):
        campo = evento.widget
        texto = campo.get().strip()
        if not texto:
            return
        limpia = N.normalizar_hora(texto)
        if limpia and limpia != texto:
            campo.delete(0, "end")
            campo.insert(0, limpia)

    def guardar(self):
        marcas = self.datos.marcas_de(self.tid, self.fecha)
        por_tipo = dict((m["tipo"], m) for m in marcas)
        try:
            for tipo, campo in self.campos.items():
                texto = N.normalizar_hora(campo.get()) or campo.get().strip()
                if not texto:
                    if tipo in por_tipo:
                        self.datos.borrar_marca(por_tipo[tipo]["id"])
                    continue
                if tipo in por_tipo:
                    if texto != por_tipo[tipo]["hora"]:
                        self.datos.editar_marca(por_tipo[tipo]["id"], hora=texto)
                else:
                    self.datos.agregar_marca(self.tid, self.fecha, tipo, texto)
        except ValueError as e:
            return messagebox.showerror("No se pudo guardar", str(e), parent=self)
        self._pintar()
        self.padre.recargar_todo()

    def borrar_dia(self):
        if not messagebox.askyesno("Borrar el dia",
                                   "Se borran las marcas de ese dia. Seguro?",
                                   parent=self):
            return
        for m in self.datos.marcas_de(self.tid, self.fecha):
            self.datos.borrar_marca(m["id"])
        self.padre.recargar_todo()
        self.destroy()


def main():
    try:
        App().mainloop()
    except Exception:
        try:
            import tkinter.messagebox as mb
            mb.showerror("Error", traceback.format_exc())
        except Exception:
            traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
