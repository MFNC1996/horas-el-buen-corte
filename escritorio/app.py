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

        self.title("Control de Horas  -  El Buen Corte")
        ancho = min(1120, self.winfo_screenwidth() - 60)
        alto = min(720, self.winfo_screenheight() - 110)
        self.geometry("%dx%d+%d+%d" % (
            ancho, alto, max(0, (self.winfo_screenwidth() - ancho) // 2),
            max(0, (self.winfo_screenheight() - alto) // 3)))
        self.minsize(min(900, ancho), min(560, alto))
        self.configure(bg=PAPEL)

        self.sel_trab = None          # trabajador elegido en la pantalla de marcar
        self.periodo = "semana"
        self.ancla = date.today().isoformat()

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
        cont = tk.Frame(barra, bg=BLANCO)
        cont.pack(side="left", padx=18, pady=10)
        tk.Label(cont, text="El Buen Corte", bg=BLANCO, fg=ROJO,
                 font=(FUENTE, 19, "bold italic")).pack(anchor="w")
        tk.Label(cont, text="LONCOCHE  ·  CONTROL DE HORAS", bg=BLANCO, fg=SUAVE,
                 font=(FUENTE, 8, "bold")).pack(anchor="w", pady=(2, 0))
        self.lbl_reloj = tk.Label(barra, text="", bg=BLANCO, fg=TINTA,
                                  font=(MONO, 22, "bold"))
        self.lbl_reloj.pack(side="right", padx=22)
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
        self.lbl_quien.pack(pady=(22, 2))
        self.lbl_toca = tk.Label(self.panel, text="", bg=BLANCO, fg=SUAVE,
                                 font=(FUENTE, 11))
        self.lbl_toca.pack()
        self.lbl_marca = tk.Label(self.panel, text="", bg=BLANCO, fg=ROJO,
                                  font=(FUENTE, 30, "bold"))
        self.lbl_marca.pack(pady=(2, 14))

        self.btn_marcar = tk.Button(
            self.panel, text="MARCAR", command=self.marcar,
            bg=TINTA, fg=PAPEL, activebackground=ROJO, activeforeground=BLANCO,
            font=(FUENTE, 17, "bold"), relief="flat", cursor="hand2",
            padx=52, pady=17, state="disabled")
        self.btn_marcar.pack()

        self.lbl_hoy = tk.Label(self.panel, text="", bg=BLANCO, fg=SUAVE,
                                font=(MONO, 11), justify="center")
        self.lbl_hoy.pack(pady=(18, 6))
        self.lbl_aviso = tk.Label(self.panel, text="", bg=BLANCO,
                                  font=(FUENTE, 12, "bold"))
        self.lbl_aviso.pack(pady=(0, 20))

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
            resumen += "\n\nLlevas %s h trabajadas" % N.horas_txt(est["horas"])
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

    # ====================================================== pestana JORNADAS
    def _tab_jornadas(self):
        p = ttk.Frame(self, padding=14)
        self.tabs.add(p, text="  Jornadas  ")

        f = ttk.Frame(p)
        f.pack(fill="x")
        ttk.Label(f, text="Mes", style="Rotulo.TLabel").pack(side="left", padx=(0, 6))
        self.cb_mes_j = ttk.Combobox(f, state="readonly", width=18, font=(FUENTE, 10))
        self.cb_mes_j.pack(side="left", padx=(0, 14))
        self.cb_mes_j.bind("<<ComboboxSelected>>", lambda e: self.recargar_jornadas())
        ttk.Label(f, text="Trabajador", style="Rotulo.TLabel").pack(side="left", padx=(0, 6))
        self.cb_filtro_trab = ttk.Combobox(f, state="readonly", width=20, font=(FUENTE, 10))
        self.cb_filtro_trab.pack(side="left")
        self.cb_filtro_trab.bind("<<ComboboxSelected>>", lambda e: self.recargar_jornadas())
        ttk.Button(f, text="Corregir marcas del dia", style="Principal.TButton",
                   command=self.abrir_editor).pack(side="right")

        tk.Label(p, bg=PAPEL, fg=SUAVE, font=(FUENTE, 9), anchor="w",
                 text="Doble clic sobre un dia para corregir sus marcas. Los dias "
                      "a los que les falta alguna marca salen en ambar."
                 ).pack(fill="x", pady=(8, 4))
        self.lbl_total_j = tk.Label(p, text="", bg=PAPEL, fg=TINTA,
                                    font=(FUENTE, 12, "bold"), anchor="e")
        self.lbl_total_j.pack(side="bottom", fill="x", pady=(8, 0))

        cols = ("fecha", "dia", "trab", "e", "ci", "cf", "s",
                "horas", "norm", "extra", "pnorm", "pextra", "total")
        titulos = ["Fecha", "Dia", "Trabajador", "Entrada", "Col. ini",
                   "Col. fin", "Salida", "Horas", "Normal", "Extra",
                   "$ normal", "$ extra", "VALOR DEL DIA"]
        anchos = [78, 44, 116, 56, 56, 56, 56, 52, 54, 48, 76, 72, 104]
        marco = ttk.Frame(p)
        marco.pack(fill="both", expand=True)
        self.tv_j = ttk.Treeview(marco, columns=cols, show="headings", selectmode="browse")
        for c, t, a in zip(cols, titulos, anchos):
            self.tv_j.heading(c, text=t)
            self.tv_j.column(c, width=a, minwidth=a, stretch=(c == "trab"),
                             anchor="w" if c == "trab" else
                             ("e" if c in ("pnorm", "pextra", "total") else "center"))
        self.tv_j.tag_configure("falta", background=AMBAR_CLARO, foreground=AMBAR)
        self.tv_j.tag_configure("conextra", foreground=ROJO)
        sb = ttk.Scrollbar(marco, orient="vertical", command=self.tv_j.yview)
        sbh = ttk.Scrollbar(marco, orient="horizontal", command=self.tv_j.xview)
        self.tv_j.configure(yscrollcommand=sb.set, xscrollcommand=sbh.set)
        sb.pack(side="right", fill="y")
        sbh.pack(side="bottom", fill="x")
        self.tv_j.pack(side="left", fill="both", expand=True)
        self.tv_j.bind("<Double-1>", lambda e: self.abrir_editor())

    def abrir_editor(self):
        sel = self.tv_j.selection()
        if not sel:
            return messagebox.showinfo("Elige un dia",
                                       "Selecciona una fila de la lista.")
        fecha, tid = sel[0].split("|")
        EditorMarcas(self, int(tid), fecha)

    # ======================================================= pestana RESUMEN
    def _tab_resumen(self):
        p = ttk.Frame(self, padding=14)
        self.tabs.add(p, text="  Resumen y pago  ")

        barra = ttk.Frame(p)
        barra.pack(fill="x")
        self.btn_sem = ttk.Button(barra, text="Semana", style="Principal.TButton",
                                  command=lambda: self.cambiar_periodo("semana"))
        self.btn_sem.pack(side="left")
        self.btn_mes = ttk.Button(barra, text="Mes",
                                  command=lambda: self.cambiar_periodo("mes"))
        self.btn_mes.pack(side="left", padx=(6, 14))
        ttk.Button(barra, text="◀", width=3, command=lambda: self.mover(-1)).pack(side="left")
        ttk.Button(barra, text="▶", width=3, command=lambda: self.mover(1)).pack(side="left", padx=(4, 10))
        ttk.Button(barra, text="Hoy", command=self.ir_hoy).pack(side="left")
        ttk.Button(barra, text="Exportar a Excel", style="Principal.TButton",
                   command=lambda: self.exportar("excel")).pack(side="right", padx=(8, 0))
        ttk.Button(barra, text="Exportar a PDF",
                   command=lambda: self.exportar("pdf")).pack(side="right")

        self.lbl_periodo = tk.Label(p, text="", bg=PAPEL, fg=TINTA,
                                    font=(FUENTE, 14, "bold"), anchor="w")
        self.lbl_periodo.pack(fill="x", pady=(12, 8))

        self.lbl_regla = tk.Label(p, text="", bg=PAPEL, fg=SUAVE, font=(FUENTE, 9),
                                  anchor="w", justify="left", wraplength=1040)
        self.lbl_regla.pack(side="bottom", fill="x", pady=(10, 0))

        cols = ("trab", "dias", "horas", "ord", "extra", "vh", "vhe",
                "pord", "pext", "total")
        titulos = ["Trabajador", "Dias", "Horas", "H. normales", "H. EXTRA",
                   "Valor hora", "Valor h. extra", "$ normales", "$ extra",
                   "TOTAL A PAGAR"]
        anchos = [132, 46, 62, 78, 66, 78, 90, 88, 84, 110]
        marco = ttk.Frame(p)
        marco.pack(fill="both", expand=True)
        self.tv_r = ttk.Treeview(marco, columns=cols, show="headings", selectmode="none")
        for c, t, a in zip(cols, titulos, anchos):
            self.tv_r.heading(c, text=t)
            self.tv_r.column(c, width=a, minwidth=a, stretch=(c == "trab"),
                             anchor="e" if c != "trab" else "w")
        self.tv_r.tag_configure("total", font=(FUENTE, 10, "bold"), background="#E6E1DC")
        self.tv_r.tag_configure("extra", foreground=ROJO)
        sbr = ttk.Scrollbar(marco, orient="horizontal", command=self.tv_r.xview)
        self.tv_r.configure(xscrollcommand=sbr.set)
        sbr.pack(side="bottom", fill="x")
        self.tv_r.pack(fill="both", expand=True)

    def cambiar_periodo(self, cual):
        self.periodo = cual
        self.btn_sem.config(style="Principal.TButton" if cual == "semana" else "TButton")
        self.btn_mes.config(style="Principal.TButton" if cual == "mes" else "TButton")
        self.recargar_resumen()

    def mover(self, n):
        d = datetime.strptime(self.ancla, "%Y-%m-%d").date()
        if self.periodo == "semana":
            self.ancla = (d + timedelta(days=7 * n)).isoformat()
        else:
            self.ancla = date(d.year + (d.month + n - 1) // 12,
                              (d.month + n - 1) % 12 + 1, 1).isoformat()
        self.recargar_resumen()

    def ir_hoy(self):
        self.ancla = date.today().isoformat()
        self.recargar_resumen()

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
        self.e_tvalor = ttk.Entry(f, width=13, font=(MONO, 10), justify="right")
        self.e_tvalor.grid(row=1, column=1, padx=(0, 16), sticky="w")
        ttk.Label(f, text="Valor hora extra ($)", style="Rotulo.TLabel").grid(row=0, column=2, sticky="w")
        self.e_tvalorx = ttk.Entry(f, width=13, font=(MONO, 10), justify="right")
        self.e_tvalorx.grid(row=1, column=2, padx=(0, 16), sticky="w")
        ttk.Label(f, text="Horas contrato/dia", style="Rotulo.TLabel").grid(
            row=0, column=3, sticky="w")
        self.e_tcontrato = ttk.Entry(f, width=8, font=(MONO, 10), justify="right")
        self.e_tcontrato.grid(row=1, column=3, padx=(0, 16), sticky="w")
        ttk.Label(f, text="en blanco usa la general", style="Rotulo.TLabel").grid(
            row=1, column=4, sticky="w")

        calc = ttk.LabelFrame(p, text=" SACAR EL VALOR HORA DESDE EL SUELDO ", padding=12)
        calc.pack(fill="x", pady=(12, 0))
        ttk.Label(calc, text="Sueldo mensual del contrato ($)",
                  style="Rotulo.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.e_sueldo = ttk.Entry(calc, width=13, font=(MONO, 10), justify="right")
        self.e_sueldo.grid(row=1, column=0, padx=(0, 12), sticky="w")
        ttk.Label(calc, text="Horas semanales pactadas",
                  style="Rotulo.TLabel").grid(row=0, column=1, sticky="w", padx=(0, 12))
        self.e_hsem = ttk.Entry(calc, width=8, font=(MONO, 10), justify="right")
        self.e_hsem.grid(row=1, column=1, padx=(0, 12), sticky="w")
        ttk.Button(calc, text="Calcular y poner arriba",
                   command=self.calcular_valor_hora).grid(row=1, column=2, padx=(0, 12))
        self.lbl_calc = tk.Label(calc, text="", bg=PAPEL, fg=SUAVE,
                                 font=(FUENTE, 9), justify="left", anchor="w")
        self.lbl_calc.grid(row=1, column=3, sticky="w")
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

        a = ttk.LabelFrame(p, text=" JORNADA Y DIA DE PAGO ", padding=14)
        a.pack(fill="x")
        ttk.Label(a, text="Horas de contrato al dia", style="Rotulo.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 14), pady=(0, 2))
        self.e_contrato = ttk.Entry(a, width=8, font=(MONO, 10), justify="right")
        self.e_contrato.grid(row=1, column=0, padx=(0, 14), sticky="nw")
        ttk.Label(a, text="Se paga el dia", style="Rotulo.TLabel").grid(
            row=0, column=1, sticky="w", padx=(0, 14), pady=(0, 2))
        self.cb_cierre = ttk.Combobox(a, state="readonly", width=11, font=(FUENTE, 10),
                                      values=[d.capitalize() for d in N.DIAS])
        self.cb_cierre.grid(row=1, column=1, padx=(0, 14), sticky="nw")
        ttk.Label(a, text="Horas semanales (informativo)", style="Rotulo.TLabel").grid(
            row=0, column=2, sticky="w", padx=(0, 14), pady=(0, 2))
        self.e_us = ttk.Entry(a, width=8, font=(MONO, 10), justify="right")
        self.e_us.grid(row=1, column=2, padx=(0, 14), sticky="nw")
        tk.Label(a, bg=PAPEL, fg=SUAVE, font=(FUENTE, 9), justify="left", anchor="w",
                 text="Todo lo que se pase de las horas de contrato EN EL DIA es hora extra.\n"
                      "La semana se acumula sola y cierra el dia de pago que elijas, para que\n"
                      "el total que muestra sea justo lo que hay que pagar ese dia."
                 ).grid(row=1, column=3, sticky="nw")

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
    def agregar_trabajador(self):
        try:
            self.datos.agregar_trabajador(self.e_tnombre.get(),
                                          self._numero(self.e_tvalor.get()),
                                          self._numero(self.e_tvalorx.get()),
                                          self._numero(self.e_tcontrato.get()))
        except ValueError as e:
            return messagebox.showerror("No se pudo agregar", str(e))
        for c in (self.e_tnombre, self.e_tvalor, self.e_tvalorx, self.e_tcontrato):
            self._set(c, "")
        self.recargar_todo()

    def calcular_valor_hora(self):
        """sueldo / 30 x 7 / horas semanales = valor de la hora ordinaria."""
        try:
            sueldo = self._numero(self.e_sueldo.get())
            horas = self._numero(self.e_hsem.get())
        except ValueError as e:
            return messagebox.showerror("Dato invalido", str(e))
        v = N.valor_hora_desde_sueldo(sueldo, horas)
        if not v:
            return messagebox.showinfo(
                "Faltan datos",
                "Escribe el sueldo mensual y las horas semanales del contrato.")
        self._set(self.e_tvalor, "%d" % v)
        self.lbl_calc.config(
            text="%s / 30 x 7 / %s h  =  %s la hora\n"
                 "Puesto arriba en 'Valor hora normal'. Confirmalo con tu contador."
                 % (N.pesos(sueldo), N._limpio(horas), N.pesos(v)))

    def guardar_trabajador(self):
        sel = self.tv_t.selection()
        if not sel:
            return messagebox.showinfo("Elige un trabajador",
                                       "Selecciona uno de la lista de abajo.")
        try:
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
                "umbral_semanal": self._numero(self.e_us.get()) or 45,
                "dia_cierre": max(0, self.cb_cierre.current()),
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
        if self.periodo == "semana":
            lunes = N.lunes_de(self.ancla)
            r = N.resumen_semanal(self.datos, lunes)
            nombre_base = "horas-semana-%s" % lunes
        else:
            d = datetime.strptime(self.ancla, "%Y-%m-%d").date()
            r = N.resumen_mensual(self.datos, d.year, d.month)
            nombre_base = "horas-%04d-%02d" % (d.year, d.month)
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
        dias.sort(key=lambda x: (x["fecha"], x["nombre"]), reverse=True)
        total = 0
        for j in dias:
            tags = () if j["completa"] else ("falta",)
            if j["extra"] > 0 and j["completa"]:
                tags = ("conextra",)
            total += j["total"]
            self.tv_j.insert("", "end", iid=j["id"], tags=tags, values=(
                j["fecha"], N.nombre_dia(j["fecha"])[:3], j["nombre"],
                j["entrada"] or "--:--", j["colacion_inicio"] or "--:--",
                j["colacion_fin"] or "--:--", j["salida"] or "--:--",
                N.horas_txt(j["horas"]), N.horas_txt(j["normales"]),
                N.horas_txt(j["extra"]) if j["extra"] else "-",
                N.pesos(j["pago_normal"]),
                N.pesos(j["pago_extra"]) if j["pago_extra"] else "-",
                N.pesos(j["total"])))
        self.lbl_total_j.config(
            text="%d dias   ·   suma de los dias mostrados:  %s"
                 % (len(dias), N.pesos(total)))

    def recargar_resumen(self):
        for f in self.tv_r.get_children():
            self.tv_r.delete(f)
        if self.periodo == "semana":
            r = N.resumen_semanal(self.datos, self.ancla)
            titulo = "%s        %s" % (r["titulo"], r["subtitulo"].upper())
        else:
            d = datetime.strptime(self.ancla, "%Y-%m-%d").date()
            r = N.resumen_mensual(self.datos, d.year, d.month)
            titulo = r["titulo"]
        nota = ("Jornada del contrato: %s h al dia. Todo lo que se pasa de ahi en el "
                "dia son horas extra, y la hora extra se paga con %s.\n"
                "El total de arriba ya viene sumado: es lo que hay que pagar."
                % (r["contrato"], r["regla_extra"]))
        self.lbl_periodo.config(text=titulo)
        self.lbl_regla.config(text=nota)

        for f in r["filas"]:
            self.tv_r.insert("", "end", tags=("extra",) if f["extra"] > 0 else (), values=(
                f["nombre"], f["turnos"], N.horas_txt(f["horas"]),
                N.horas_txt(f["ordinarias"]), N.horas_txt(f["extra"]),
                N.pesos(f["valor_hora"]), N.pesos(f["valor_extra"]),
                N.pesos(f["pago_ordinario"]), N.pesos(f["pago_extra"]),
                N.pesos(f["total"])))
        t = r["totales"]
        self.tv_r.insert("", "end", tags=("total",), values=(
            "TOTAL", t["turnos"], N.horas_txt(t["horas"]),
            N.horas_txt(t["ordinarias"]), N.horas_txt(t["extra"]), "", "",
            N.pesos(t["pago_ordinario"]), N.pesos(t["pago_extra"]),
            N.pesos(t["total"])))

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
        self._set(self.e_us, N._limpio(c.get("umbral_semanal", "45")))
        self.cb_cierre.current(N.dia_cierre_de(c))
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
                 text="Escribe la hora como 14:30 y presiona Guardar. Deja el campo\n"
                      "vacio y guarda para borrar esa marca."
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
            self.campos[tipo] = e
            origen = por_tipo.get(tipo, {}).get("origen", "")
            tk.Label(self.caja, bg=PAPEL, fg=SUAVE, font=(FUENTE, 9),
                     text={"app": "marcada en la app", "manual": "corregida a mano",
                           "migrado": "viene del formato anterior",
                           "biometrico": "reloj biometrico"}.get(origen, "falta")
                     ).grid(row=i, column=2, sticky="w")
        self.lbl_total.config(text="Horas del dia: %s"
                                   % N.horas_txt(N.horas_de_marcas(marcas)))

    def guardar(self):
        marcas = self.datos.marcas_de(self.tid, self.fecha)
        por_tipo = dict((m["tipo"], m) for m in marcas)
        try:
            for tipo, campo in self.campos.items():
                texto = campo.get().strip()
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
