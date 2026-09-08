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
TINTA = "#15100F"
PAPEL = "#F1EFEC"
BLANCO = "#FFFFFF"
LINEA = "#DFD8D1"
SUAVE = "#6C625C"

COLACIONES = [0, 30, 45, 60]
FUENTE = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"


def mono():
    return ("Consolas" if sys.platform.startswith("win") else "Menlo", 11)


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.datos = N.Datos()
        primera = self.datos.sembrar_si_vacia()

        self.title("Control de Horas  -  El Buen Corte")
        self.geometry("1120x730")
        self.minsize(940, 620)
        self.configure(bg=PAPEL)

        self.editando = None          # id de la jornada en edicion
        hoy = date.today()
        self.mes_sel = tk.StringVar(value="%04d-%02d" % (hoy.year, hoy.month))

        self._estilos()
        self._cabecera()

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.tabs.enable_traversal()
        self._tab_jornadas()
        self._tab_resumen()
        self._tab_trabajadores()
        self._tab_config()

        self.recargar_todo()
        if primera:
            self.after(400, lambda: messagebox.showinfo(
                "Primer uso",
                "Cree tres trabajadores de ejemplo.\n\n"
                "Anda a la pestana Trabajadores para ponerles el nombre real "
                "y el valor de la hora."))

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
        e.configure("TNotebook.Tab", padding=(20, 10), font=(FUENTE, 10, "bold"),
                    background=PAPEL, foreground=SUAVE)
        e.map("TNotebook.Tab", background=[("selected", TINTA)],
              foreground=[("selected", PAPEL)])
        e.configure("TFrame", background=PAPEL)
        e.configure("Tarjeta.TFrame", background=BLANCO, relief="flat")
        e.configure("TLabelframe", background=PAPEL, borderwidth=1,
                    relief="solid", bordercolor=LINEA)
        e.configure("TLabelframe.Label", background=PAPEL, foreground=SUAVE,
                    font=(FUENTE, 9, "bold"))
        e.configure("TLabel", background=PAPEL)
        e.configure("Rotulo.TLabel", foreground=SUAVE, font=(FUENTE, 9, "bold"))
        e.configure("Titulo.TLabel", font=(FUENTE, 15, "bold"), foreground=TINTA)
        e.configure("Dato.TLabel", font=mono())
        e.configure("TButton", padding=(12, 7), font=(FUENTE, 10))
        e.configure("Principal.TButton", padding=(16, 9),
                    font=(FUENTE, 10, "bold"), background=TINTA, foreground=PAPEL)
        e.map("Principal.TButton", background=[("active", ROJO)])
        e.configure("Chip.TButton", padding=(9, 5), font=mono())
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
        tk.Frame(self, bg=VERDE, height=3).pack(fill="x")

    # ------------------------------------------------------ pestana Jornadas
    def _tab_jornadas(self):
        p = ttk.Frame(self, padding=14)
        self.tabs.add(p, text="  Jornadas  ")

        f = ttk.LabelFrame(p, text=" REGISTRAR UNA JORNADA ", padding=12)
        f.pack(fill="x")

        fila1 = ttk.Frame(f); fila1.pack(fill="x", pady=(0, 10))
        ttk.Label(fila1, text="Trabajador", style="Rotulo.TLabel").grid(row=0, column=0, sticky="w")
        self.cb_trab = ttk.Combobox(fila1, state="readonly", width=26, font=(FUENTE, 11))
        self.cb_trab.grid(row=1, column=0, sticky="w", padx=(0, 18))

        ttk.Label(fila1, text="Fecha", style="Rotulo.TLabel").grid(row=0, column=1, sticky="w")
        self.e_fecha = ttk.Entry(fila1, width=13, font=mono(), justify="center")
        self.e_fecha.grid(row=1, column=1, sticky="w", padx=(0, 4))
        self.e_fecha.insert(0, date.today().isoformat())
        bf = ttk.Frame(fila1); bf.grid(row=1, column=2, sticky="w", padx=(0, 18))
        ttk.Button(bf, text="Hoy", style="Chip.TButton", width=5,
                   command=lambda: self._set(self.e_fecha, date.today().isoformat())).pack(side="left", padx=1)
        ttk.Button(bf, text="◀", style="Chip.TButton", width=3,
                   command=lambda: self._mover_fecha(-1)).pack(side="left", padx=1)
        ttk.Button(bf, text="▶", style="Chip.TButton", width=3,
                   command=lambda: self._mover_fecha(1)).pack(side="left", padx=1)

        ttk.Label(fila1, text="Colacion", style="Rotulo.TLabel").grid(row=0, column=3, sticky="w")
        self.cb_col = ttk.Combobox(fila1, state="readonly", width=12, font=(FUENTE, 11),
                                   values=["Sin colacion", "30 min", "45 min", "60 min"])
        self.cb_col.current(3)
        self.cb_col.grid(row=1, column=3, sticky="w")
        self.cb_col.bind("<<ComboboxSelected>>", lambda e: self._vista_previa())

        fila2 = ttk.Frame(f); fila2.pack(fill="x")
        self.e_ent = self._campo_hora(fila2, "Hora de entrada", 0, ["08:00", "08:30", "09:00", "10:00"])
        self.e_sal = self._campo_hora(fila2, "Hora de salida", 1, ["14:00", "18:00", "19:00", "20:00"])

        fila3 = ttk.Frame(f); fila3.pack(fill="x", pady=(12, 0))
        ttk.Label(fila3, text="Nota (opcional)", style="Rotulo.TLabel").pack(anchor="w")
        self.e_nota = ttk.Entry(fila3, font=(FUENTE, 10))
        self.e_nota.pack(fill="x", pady=(2, 0))

        fila4 = tk.Frame(f, bg=PAPEL); fila4.pack(fill="x", pady=(12, 0))
        self.lbl_previa = tk.Label(fila4, text="", bg=VERDE_CLARO, fg=VERDE,
                                   font=(FUENTE, 12, "bold"), anchor="w", padx=14, pady=9)
        self.lbl_previa.pack(side="left", fill="x", expand=True)
        self.btn_guardar = ttk.Button(fila4, text="Guardar jornada",
                                      style="Principal.TButton", command=self.guardar_jornada)
        self.btn_guardar.pack(side="left", padx=(10, 0))
        self.btn_cancelar = ttk.Button(fila4, text="Cancelar", command=self.limpiar_form)

        lista = ttk.LabelFrame(p, text=" JORNADAS REGISTRADAS ", padding=10)
        lista.pack(fill="both", expand=True, pady=(14, 0))
        filtros = ttk.Frame(lista); filtros.pack(fill="x", pady=(0, 8))
        ttk.Label(filtros, text="Mes", style="Rotulo.TLabel").pack(side="left", padx=(0, 6))
        self.cb_mes_j = ttk.Combobox(filtros, state="readonly", width=18, font=(FUENTE, 10))
        self.cb_mes_j.pack(side="left", padx=(0, 14))
        self.cb_mes_j.bind("<<ComboboxSelected>>", lambda e: self.recargar_jornadas())
        ttk.Label(filtros, text="Trabajador", style="Rotulo.TLabel").pack(side="left", padx=(0, 6))
        self.cb_filtro_trab = ttk.Combobox(filtros, state="readonly", width=22, font=(FUENTE, 10))
        self.cb_filtro_trab.pack(side="left")
        self.cb_filtro_trab.bind("<<ComboboxSelected>>", lambda e: self.recargar_jornadas())
        ttk.Button(filtros, text="Editar", command=self.editar_sel).pack(side="right", padx=3)
        ttk.Button(filtros, text="Borrar", command=self.borrar_sel).pack(side="right", padx=3)

        cols = ("fecha", "dia", "trab", "ent", "sal", "col", "horas", "extra", "nota")
        titulos = ["Fecha", "Dia", "Trabajador", "Entrada", "Salida",
                   "Colacion", "Horas", "Extra", "Nota"]
        anchos = [92, 88, 170, 76, 76, 78, 72, 68, 200]
        self.tv_j = ttk.Treeview(lista, columns=cols, show="headings", selectmode="browse")
        for c, t, a in zip(cols, titulos, anchos):
            self.tv_j.heading(c, text=t)
            self.tv_j.column(c, width=a, anchor="center" if c not in ("trab", "nota") else "w")
        self.tv_j.tag_configure("extra", foreground=ROJO)
        self.tv_j.tag_configure("par", background="#FAF8F6")
        sb = ttk.Scrollbar(lista, orient="vertical", command=self.tv_j.yview)
        self.tv_j.configure(yscrollcommand=sb.set)
        self.tv_j.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tv_j.bind("<Double-1>", lambda e: self.editar_sel())

    def _campo_hora(self, padre, rotulo, col, sugeridas):
        caja = ttk.Frame(padre)
        caja.grid(row=0, column=col, sticky="w", padx=(0, 26))
        ttk.Label(caja, text=rotulo, style="Rotulo.TLabel").pack(anchor="w")
        arriba = ttk.Frame(caja); arriba.pack(anchor="w", pady=(2, 4))
        campo = ttk.Entry(arriba, width=8, font=(mono()[0], 15), justify="center")
        campo.pack(side="left")
        campo.bind("<KeyRelease>", lambda e: self._vista_previa())
        ttk.Button(arriba, text="Ahora", style="Chip.TButton", width=6,
                   command=lambda: self._ahora(campo)).pack(side="left", padx=(5, 0))
        ttk.Button(arriba, text="−15", style="Chip.TButton", width=4,
                   command=lambda: self._paso(campo, -15)).pack(side="left", padx=(5, 0))
        ttk.Button(arriba, text="+15", style="Chip.TButton", width=4,
                   command=lambda: self._paso(campo, 15)).pack(side="left", padx=2)
        abajo = ttk.Frame(caja); abajo.pack(anchor="w")
        for h in sugeridas:
            ttk.Button(abajo, text=h, style="Chip.TButton", width=6,
                       command=lambda v=h, c=campo: self._set(c, v)).pack(side="left", padx=2)
        return campo

    # ------------------------------------------------------- pestana Resumen
    def _tab_resumen(self):
        p = ttk.Frame(self, padding=14)
        self.tabs.add(p, text="  Resumen del mes  ")

        barra = ttk.Frame(p); barra.pack(fill="x")
        ttk.Label(barra, text="Mes", style="Rotulo.TLabel").pack(side="left", padx=(0, 8))
        self.cb_mes_r = ttk.Combobox(barra, state="readonly", width=20, font=(FUENTE, 11))
        self.cb_mes_r.pack(side="left")
        self.cb_mes_r.bind("<<ComboboxSelected>>", lambda e: self.recargar_resumen())
        ttk.Button(barra, text="Exportar a Excel", style="Principal.TButton",
                   command=lambda: self.exportar("excel")).pack(side="right", padx=(8, 0))
        ttk.Button(barra, text="Exportar a PDF",
                   command=lambda: self.exportar("pdf")).pack(side="right")

        cols = ("trab", "turnos", "horas", "col", "ord", "extra",
                "vh", "vhe", "pord", "pext", "total")
        titulos = ["Trabajador", "Turnos", "Horas", "Colacion", "H. ordinarias",
                   "H. extra", "Valor hora", "Valor h. extra", "Pago ordinario",
                   "Pago extra", "TOTAL"]
        anchos = [148, 58, 68, 74, 88, 66, 82, 92, 98, 86, 104]
        self.lbl_regla = tk.Label(p, text="", bg=PAPEL, fg=SUAVE, font=(FUENTE, 9),
                                  anchor="w", justify="left", wraplength=1040)
        self.lbl_regla.pack(side="bottom", fill="x", pady=(10, 0))
        marco = ttk.Frame(p); marco.pack(fill="both", expand=True, pady=(12, 0))
        self.tv_r = ttk.Treeview(marco, columns=cols, show="headings", selectmode="none")
        for c, t, a in zip(cols, titulos, anchos):
            self.tv_r.heading(c, text=t)
            self.tv_r.column(c, width=a, minwidth=a, stretch=(c == "trab"),
                             anchor="e" if c != "trab" else "w")
        self.tv_r.tag_configure("total", font=(FUENTE, 10, "bold"), background="#E6E1DC")
        self.tv_r.tag_configure("extra", foreground=ROJO)
        self.tv_r.pack(fill="both", expand=True)


    # -------------------------------------------------- pestana Trabajadores
    def _tab_trabajadores(self):
        p = ttk.Frame(self, padding=14)
        self.tabs.add(p, text="  Trabajadores  ")

        f = ttk.LabelFrame(p, text=" DATOS DEL TRABAJADOR ", padding=12)
        f.pack(fill="x")
        ttk.Label(f, text="Nombre", style="Rotulo.TLabel").grid(row=0, column=0, sticky="w")
        self.e_tnombre = ttk.Entry(f, width=28, font=(FUENTE, 11))
        self.e_tnombre.grid(row=1, column=0, padx=(0, 16), sticky="w")
        ttk.Label(f, text="Valor hora normal ($)", style="Rotulo.TLabel").grid(row=0, column=1, sticky="w")
        self.e_tvalor = ttk.Entry(f, width=14, font=mono(), justify="right")
        self.e_tvalor.grid(row=1, column=1, padx=(0, 16), sticky="w")
        ttk.Label(f, text="Valor hora extra ($)", style="Rotulo.TLabel").grid(row=0, column=2, sticky="w")
        self.e_tvalorx = ttk.Entry(f, width=14, font=mono(), justify="right")
        self.e_tvalorx.grid(row=1, column=2, padx=(0, 16), sticky="w")
        ttk.Label(f, text="solo si en Configuracion elegiste monto fijo;\n"
                          "en blanco usa el valor general",
                  style="Rotulo.TLabel", foreground=SUAVE).grid(row=1, column=3, sticky="w")
        botones = ttk.Frame(f); botones.grid(row=2, column=0, columnspan=4, sticky="w", pady=(12, 0))
        ttk.Button(botones, text="Agregar nuevo", style="Principal.TButton",
                   command=self.agregar_trabajador).pack(side="left")
        ttk.Button(botones, text="Guardar cambios del seleccionado",
                   command=self.guardar_trabajador).pack(side="left", padx=6)
        ttk.Button(botones, text="Quitar de la lista",
                   command=self.quitar_trabajador).pack(side="left")

        marco = ttk.LabelFrame(p, text=" TRABAJADORES ", padding=10)
        marco.pack(fill="both", expand=True, pady=(14, 0))
        cols = ("nombre", "vh", "vhe", "jornadas")
        self.tv_t = ttk.Treeview(marco, columns=cols, show="headings", selectmode="browse")
        for c, t, a, al in zip(cols,
                               ["Nombre", "Valor hora", "Valor hora extra", "Jornadas"],
                               [240, 130, 150, 110], ["w", "e", "e", "e"]):
            self.tv_t.heading(c, text=t)
            self.tv_t.column(c, width=a, anchor=al)
        self.tv_t.pack(fill="both", expand=True)
        self.tv_t.bind("<<TreeviewSelect>>", lambda e: self.cargar_trabajador_sel())

    # -------------------------------------------------- pestana Configuracion
    def _tab_config(self):
        p = ttk.Frame(self, padding=14)
        self.tabs.add(p, text="  Configuracion  ")

        a = ttk.LabelFrame(p, text=" CUANDO UNA HORA ES EXTRA ", padding=14)
        a.pack(fill="x")
        ttk.Label(a, text="Umbral diario (horas)", style="Rotulo.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 20), pady=(0, 2))
        self.e_ud = ttk.Entry(a, width=10, font=mono(), justify="right")
        self.e_ud.grid(row=1, column=0, padx=(0, 20), sticky="w")
        ttk.Label(a, text="Umbral semanal (horas)", style="Rotulo.TLabel").grid(
            row=0, column=1, sticky="w", padx=(0, 20), pady=(0, 2))
        self.e_us = ttk.Entry(a, width=10, font=mono(), justify="right")
        self.e_us.grid(row=1, column=1, padx=(0, 20), sticky="w")
        ttk.Label(a, text="Regla que se aplica", style="Rotulo.TLabel").grid(
            row=0, column=2, sticky="w", pady=(0, 2))
        self.cb_regla = ttk.Combobox(a, state="readonly", width=46, font=(FUENTE, 10), values=[
            "Diaria  -  lo que pasa del umbral de cada dia",
            "Semanal  -  lo que pasa del umbral de la semana",
            "La mayor de las dos"])
        self.cb_regla.grid(row=1, column=2, sticky="w")

        b = ttk.LabelFrame(p, text=" CUANTO VALE UNA HORA EXTRA ", padding=14)
        b.pack(fill="x", pady=(14, 0))
        self.modo_extra = tk.StringVar(value="recargo")
        ttk.Radiobutton(b, text="Recargo sobre la hora normal", value="recargo",
                        variable=self.modo_extra, command=self._refrescar_modo
                        ).grid(row=0, column=0, sticky="w", pady=3)
        self.e_recargo = ttk.Entry(b, width=8, font=mono(), justify="right")
        self.e_recargo.grid(row=0, column=1, padx=8)
        ttk.Label(b, text="%   (50 % es lo que fija la ley en Chile)",
                  style="Rotulo.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Radiobutton(b, text="Monto fijo por hora extra", value="fijo",
                        variable=self.modo_extra, command=self._refrescar_modo
                        ).grid(row=1, column=0, sticky="w", pady=3)
        self.e_vextra = ttk.Entry(b, width=10, font=mono(), justify="right")
        self.e_vextra.grid(row=1, column=1, padx=8)
        ttk.Label(b, text="$ por hora   (cada trabajador puede tener el suyo)",
                  style="Rotulo.TLabel").grid(row=1, column=2, sticky="w")
        self.lbl_ejemplo = tk.Label(b, text="", bg=ROJO_CLARO, fg=ROJO, anchor="w",
                                    font=(FUENTE, 10, "bold"), padx=12, pady=8)
        self.lbl_ejemplo.grid(row=2, column=0, columnspan=3, sticky="we", pady=(12, 0))

        c = ttk.LabelFrame(p, text=" DATOS DEL NEGOCIO (salen en el informe) ", padding=14)
        c.pack(fill="x", pady=(14, 0))
        ttk.Label(c, text="Nombre", style="Rotulo.TLabel").grid(row=0, column=0, sticky="w")
        self.e_negocio = ttk.Entry(c, width=34, font=(FUENTE, 11))
        self.e_negocio.grid(row=1, column=0, padx=(0, 20), sticky="w")
        ttk.Label(c, text="Ciudad", style="Rotulo.TLabel").grid(row=0, column=1, sticky="w")
        self.e_ciudad = ttk.Entry(c, width=22, font=(FUENTE, 11))
        self.e_ciudad.grid(row=1, column=1, sticky="w")

        pie = ttk.Frame(p); pie.pack(fill="x", pady=(16, 0))
        ttk.Button(pie, text="Guardar configuracion", style="Principal.TButton",
                   command=self.guardar_config).pack(side="left")
        ttk.Button(pie, text="Abrir carpeta de datos",
                   command=self.abrir_carpeta_datos).pack(side="left", padx=8)
        self.lbl_ruta = tk.Label(p, text="", bg=PAPEL, fg=SUAVE, font=(FUENTE, 8),
                                 anchor="w", justify="left")
        self.lbl_ruta.pack(fill="x", pady=(12, 0))

    # =========================================================== utilidades
    @staticmethod
    def _set(campo, valor):
        campo.delete(0, "end")
        campo.insert(0, valor)

    def _ahora(self, campo):
        ahora = datetime.now()
        m = int(round((ahora.hour * 60 + ahora.minute) / 5.0)) * 5
        self._set(campo, N.a_hhmm(m))
        self._vista_previa()

    def _paso(self, campo, delta):
        base = N.a_minutos(campo.get())
        if base is None:
            ahora = datetime.now()
            base = int(round((ahora.hour * 60 + ahora.minute) / 15.0)) * 15
        else:
            base += delta
        self._set(campo, N.a_hhmm(base))
        self._vista_previa()

    def _mover_fecha(self, delta):
        try:
            d = datetime.strptime(self.e_fecha.get(), "%Y-%m-%d").date()
        except ValueError:
            d = date.today()
        self._set(self.e_fecha, (d + timedelta(days=delta)).isoformat())

    def _colacion(self):
        return COLACIONES[self.cb_col.current() if self.cb_col.current() >= 0 else 3]

    def _vista_previa(self, *_):
        e, s = self.e_ent.get(), self.e_sal.get()
        if N.a_minutos(e) is None or N.a_minutos(s) is None:
            self.lbl_previa.config(text="Falta la hora de entrada o de salida",
                                   bg=VERDE_CLARO, fg=SUAVE)
            return
        h = N.horas_trabajadas(e, s, self._colacion())
        x = N.extra_del_dia(h, self.datos.num("umbral_diario"))
        if x > 0:
            self.lbl_previa.config(
                text="%s h trabajadas   ·   %s h extra" % (N.horas_txt(h), N.horas_txt(x)),
                bg=ROJO_CLARO, fg=ROJO)
        else:
            self.lbl_previa.config(
                text="%s h trabajadas   ·   dentro del umbral" % N.horas_txt(h),
                bg=VERDE_CLARO, fg=VERDE)

    def _refrescar_modo(self):
        fijo = self.modo_extra.get() == "fijo"
        self.e_recargo.config(state="disabled" if fijo else "normal")
        self.e_vextra.config(state="normal" if fijo else "disabled")
        try:
            if fijo:
                v = float(self.e_vextra.get() or 0)
                self.lbl_ejemplo.config(
                    text="Cada hora extra se paga %s" % N.pesos(v))
            else:
                r = float(self.e_recargo.get() or 0)
                self.lbl_ejemplo.config(
                    text="Ejemplo: si la hora normal son $3.000, la extra sale %s"
                         % N.pesos(3000 * (1 + r / 100.0)))
        except ValueError:
            self.lbl_ejemplo.config(text="Escribe un numero valido")

    def _meses_disponibles(self):
        js = self.datos.jornadas()
        meses = sorted({j["fecha"][:7] for j in js}, reverse=True)
        hoy = date.today().strftime("%Y-%m")
        if hoy not in meses:
            meses.insert(0, hoy)
        return meses

    @staticmethod
    def _mes_texto(ym):
        a, m = ym.split("-")
        return "%s de %s" % (N.nombre_mes(int(m)).capitalize(), a)

    # ============================================================== acciones
    def guardar_jornada(self):
        i = self.cb_trab.current()
        if i < 0:
            return messagebox.showwarning("Falta el trabajador",
                                          "Elige a quien corresponde la jornada.")
        try:
            self.datos.guardar_jornada(
                self.editando, self._trabs[i]["id"], self.e_fecha.get().strip(),
                self.e_ent.get().strip(), self.e_sal.get().strip(),
                self._colacion(), self.e_nota.get().strip())
        except ValueError as err:
            return messagebox.showerror("No se pudo guardar", str(err))
        self.limpiar_form()
        self.recargar_todo()

    def limpiar_form(self):
        self.editando = None
        self._set(self.e_ent, ""); self._set(self.e_sal, "")
        self._set(self.e_nota, "")
        self.cb_col.current(3)
        self.btn_guardar.config(text="Guardar jornada")
        self.btn_cancelar.pack_forget()
        self._vista_previa()

    def editar_sel(self):
        sel = self.tv_j.selection()
        if not sel:
            return messagebox.showinfo("Elige una jornada",
                                       "Selecciona una fila de la lista.")
        jid = int(sel[0])
        j = [x for x in self.datos.jornadas() if x["id"] == jid]
        if not j:
            return
        j = j[0]
        self.editando = jid
        for k, t in enumerate(self._trabs):
            if t["id"] == j["trabajador_id"]:
                self.cb_trab.current(k)
        self._set(self.e_fecha, j["fecha"])
        self._set(self.e_ent, j["entrada"]); self._set(self.e_sal, j["salida"])
        self._set(self.e_nota, j.get("nota", ""))
        col = int(j["colacion"] or 0)
        self.cb_col.current(COLACIONES.index(col) if col in COLACIONES else 3)
        self.btn_guardar.config(text="Guardar cambios")
        self.btn_cancelar.pack(side="left", padx=(6, 0))
        self._vista_previa()
        self.tabs.select(0)

    def borrar_sel(self):
        sel = self.tv_j.selection()
        if not sel:
            return messagebox.showinfo("Elige una jornada",
                                       "Selecciona una fila de la lista.")
        v = self.tv_j.item(sel[0])["values"]
        if messagebox.askyesno("Borrar jornada",
                               "Borrar la jornada de %s del %s?" % (v[2], v[0])):
            self.datos.borrar_jornada(int(sel[0]))
            self.recargar_todo()

    def agregar_trabajador(self):
        try:
            self.datos.agregar_trabajador(self.e_tnombre.get(),
                                          self._numero(self.e_tvalor.get()),
                                          self._numero(self.e_tvalorx.get()))
        except ValueError as e:
            return messagebox.showerror("No se pudo agregar", str(e))
        self._set(self.e_tnombre, ""); self._set(self.e_tvalor, "")
        self._set(self.e_tvalorx, "")
        self.recargar_todo()

    def guardar_trabajador(self):
        sel = self.tv_t.selection()
        if not sel:
            return messagebox.showinfo("Elige un trabajador",
                                       "Selecciona uno de la lista de abajo.")
        try:
            self.datos.editar_trabajador(int(sel[0]), self.e_tnombre.get(),
                                         self._numero(self.e_tvalor.get()),
                                         self._numero(self.e_tvalorx.get()))
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
        if messagebox.askyesno(
                "Quitar de la lista",
                "Se saca de la lista pero sus %d jornadas se conservan,\n"
                "para que los informes de meses anteriores sigan cuadrando.\n\n"
                "Continuar?" % n):
            self.datos.desactivar_trabajador(tid)
            self.recargar_todo()

    @staticmethod
    def _numero(txt):
        txt = (txt or "").replace(".", "").replace(",", ".").replace("$", "").strip()
        try:
            return float(txt or 0)
        except ValueError:
            raise ValueError("'%s' no es un monto valido." % txt)

    def guardar_config(self):
        try:
            cambios = {
                "umbral_diario": self._numero(self.e_ud.get()) or 8,
                "umbral_semanal": self._numero(self.e_us.get()) or 45,
                "regla": ["diaria", "semanal", "mayor"][max(0, self.cb_regla.current())],
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
        ym = self._ym_resumen()
        anio, mes = int(ym[:4]), int(ym[5:7])
        r = N.resumen_mensual(self.datos, anio, mes)
        if not r["filas"]:
            return messagebox.showinfo("Mes sin datos",
                                       "No hay jornadas registradas en ese mes.")
        ext = "xlsx" if formato == "excel" else "pdf"
        sugerido = "horas-%s-%04d-%02d.%s" % (
            r["negocio"].lower().replace(" ", "-"), anio, mes, ext)
        ruta = filedialog.asksaveasfilename(
            title="Guardar informe", defaultextension="." + ext,
            initialfile=sugerido,
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
            return messagebox.showerror(
                "No se pudo crear el informe",
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

    # ============================================================== recargas
    def _ym_resumen(self):
        t = self.cb_mes_r.get()
        for ym in self._meses:
            if self._mes_texto(ym) == t:
                return ym
        return date.today().strftime("%Y-%m")

    def recargar_todo(self):
        self._trabs = self.datos.trabajadores()
        self.cb_trab["values"] = [t["nombre"] for t in self._trabs]
        if self._trabs and self.cb_trab.current() < 0:
            self.cb_trab.current(0)

        self._meses = self._meses_disponibles()
        textos = [self._mes_texto(m) for m in self._meses]
        for cb in (self.cb_mes_j, self.cb_mes_r):
            actual = cb.get()
            cb["values"] = ["Todos"] + textos if cb is self.cb_mes_j else textos
            if actual in cb["values"]:
                cb.set(actual)
            else:
                cb.current(0)
        actual = self.cb_filtro_trab.get()
        self.cb_filtro_trab["values"] = ["Todos"] + [t["nombre"] for t in self._trabs]
        self.cb_filtro_trab.set(actual if actual in self.cb_filtro_trab["values"] else "Todos")

        self.recargar_jornadas()
        self.recargar_resumen()
        self.recargar_trabajadores()
        self.recargar_config()
        self._vista_previa()

    def recargar_jornadas(self):
        for f in self.tv_j.get_children():
            self.tv_j.delete(f)
        t = self.cb_mes_j.get()
        desde = hasta = None
        if t != "Todos":
            for ym in self._meses:
                if self._mes_texto(ym) == t:
                    a, m = int(ym[:4]), int(ym[5:7])
                    desde, hasta = "%s-01" % ym, "%s-%02d" % (ym, N.ultimo_dia(a, m))
        tid = None
        nom = self.cb_filtro_trab.get()
        for x in self._trabs:
            if x["nombre"] == nom:
                tid = x["id"]
        umbral = self.datos.num("umbral_diario")
        for i, j in enumerate(self.datos.jornadas(desde, hasta, tid)):
            h = N.horas_trabajadas(j["entrada"], j["salida"], j["colacion"])
            x = N.extra_del_dia(h, umbral)
            tags = []
            if x > 0:
                tags.append("extra")
            elif i % 2:
                tags.append("par")
            self.tv_j.insert("", "end", iid=str(j["id"]), tags=tags, values=(
                j["fecha"], N.nombre_dia(j["fecha"]), j["nombre"], j["entrada"],
                j["salida"], "%d min" % int(j["colacion"] or 0),
                N.horas_txt(h), N.horas_txt(x) if x else "-", j.get("nota", "")))

    def recargar_resumen(self):
        for f in self.tv_r.get_children():
            self.tv_r.delete(f)
        ym = self._ym_resumen()
        r = N.resumen_mensual(self.datos, int(ym[:4]), int(ym[5:7]))
        for f in r["filas"]:
            self.tv_r.insert("", "end", tags=("extra",) if f["extra"] > 0 else (), values=(
                f["nombre"], f["turnos"], N.horas_txt(f["horas"]),
                N.horas_txt(f["colacion"]), N.horas_txt(f["ordinarias"]),
                N.horas_txt(f["extra"]), N.pesos(f["valor_hora"]),
                N.pesos(f["valor_extra"]), N.pesos(f["pago_ordinario"]),
                N.pesos(f["pago_extra"]), N.pesos(f["total"])))
        t = r["totales"]
        self.tv_r.insert("", "end", tags=("total",), values=(
            "TOTAL", t["turnos"], N.horas_txt(t["horas"]), N.horas_txt(t["colacion"]),
            N.horas_txt(t["ordinarias"]), N.horas_txt(t["extra"]), "", "",
            N.pesos(t["pago_ordinario"]), N.pesos(t["pago_extra"]), N.pesos(t["total"])))
        reglas = {"diaria": "lo que pasa del umbral diario",
                  "semanal": "lo que pasa del umbral semanal",
                  "mayor": "la mayor entre el criterio diario y el semanal"}
        self.lbl_regla.config(
            text="Horas extra: %s  (umbral %s h al dia, %s h a la semana).   "
                 "Valor de la hora extra: %s."
                 % (reglas.get(r["regla"], ""), r["umbral_diario"],
                    r["umbral_semanal"], r["regla_extra"]))

    def recargar_trabajadores(self):
        for f in self.tv_t.get_children():
            self.tv_t.delete(f)
        for t in self._trabs:
            self.tv_t.insert("", "end", iid=str(t["id"]), values=(
                t["nombre"], N.pesos(t["valor_hora"]),
                N.pesos(t["valor_hora_extra"]) if t["valor_hora_extra"] else "-",
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

    def recargar_config(self):
        c = self.datos.config()
        self._set(self.e_ud, N._limpio(c.get("umbral_diario", "8")))
        self._set(self.e_us, N._limpio(c.get("umbral_semanal", "45")))
        self.cb_regla.current({"diaria": 0, "semanal": 1, "mayor": 2}.get(
            c.get("regla", "diaria"), 0))
        self.modo_extra.set(c.get("modo_extra", "recargo"))
        self.e_recargo.config(state="normal"); self.e_vextra.config(state="normal")
        self._set(self.e_recargo, N._limpio(c.get("recargo_extra", "50")))
        self._set(self.e_vextra, N._limpio(c.get("valor_extra_global", "0")))
        self._set(self.e_negocio, c.get("negocio", N.NEGOCIO_DEF))
        self._set(self.e_ciudad, c.get("ciudad", N.CIUDAD_DEF))
        self._refrescar_modo()
        self.lbl_ruta.config(text="Los datos se guardan en:  %s\n"
                                  "Hay %d jornadas registradas."
                                  % (self.datos.ruta, self.datos.total_jornadas()))


def main():
    try:
        app = App()
        app.mainloop()
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
