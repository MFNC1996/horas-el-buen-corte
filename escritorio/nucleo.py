# -*- coding: utf-8 -*-
"""
Nucleo del control de horas: datos y calculos.

No depende de la interfaz, asi que se puede probar solo. La ventana
(app.py) solo llama a estas funciones.
"""

import os
import sqlite3
import sys
from datetime import date, datetime, timedelta

NEGOCIO_DEF = "Carniceria El Buen Corte"
CIUDAD_DEF = "Loncoche"

CONFIG_DEF = {
    "umbral_diario": "8",
    "umbral_semanal": "45",
    "regla": "diaria",          # diaria | semanal | mayor
    "modo_extra": "recargo",    # recargo (% sobre la hora normal) | fijo (monto en pesos)
    "recargo_extra": "50",      # % sobre el valor hora, si modo_extra=recargo
    "valor_extra_global": "0",  # $ por hora extra, si modo_extra=fijo
    "negocio": NEGOCIO_DEF,
    "ciudad": CIUDAD_DEF,
}

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


# ----------------------------------------------------------------- ubicacion
def carpeta_datos():
    """Los datos viven fuera del .exe, para que actualizarlo no los borre."""
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    ruta = os.path.join(base, "ControlDeHoras")
    os.makedirs(ruta, exist_ok=True)
    return ruta


# ------------------------------------------------------------------ calculos
def a_minutos(hhmm):
    """'08:30' -> 510. Devuelve None si no se entiende."""
    try:
        h, m = str(hhmm).strip().split(":")
        h, m = int(h), int(m)
    except (ValueError, AttributeError):
        return None
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return h * 60 + m


def a_hhmm(minutos):
    minutos = int(minutos) % 1440
    return "%02d:%02d" % (minutos // 60, minutos % 60)


def minutos_turno(entrada, salida):
    """Minutos entre entrada y salida. Si cruza medianoche, suma 24 h."""
    e, s = a_minutos(entrada), a_minutos(salida)
    if e is None or s is None:
        return 0
    d = s - e
    if d < 0:
        d += 1440
    return d


def horas_trabajadas(entrada, salida, colacion_min):
    """Horas efectivas, con la colacion ya descontada. Nunca negativas."""
    d = minutos_turno(entrada, salida) - int(colacion_min or 0)
    return round(max(0, d) / 60.0, 2)


def extra_del_dia(horas, umbral_diario):
    return round(max(0.0, horas - float(umbral_diario)), 2)


def lunes_de(iso):
    d = datetime.strptime(iso, "%Y-%m-%d").date()
    return (d - timedelta(days=d.weekday())).isoformat()


def nombre_dia(iso):
    return DIAS[datetime.strptime(iso, "%Y-%m-%d").date().weekday()]


def nombre_mes(mes):
    return MESES[mes - 1]


def ultimo_dia(anio, mes):
    if mes == 12:
        return date(anio, 12, 31).day
    return (date(anio, mes + 1, 1) - timedelta(days=1)).day


def pesos(monto):
    """1234567 -> '$1.234.567'"""
    return "$" + "{:,.0f}".format(round(monto or 0)).replace(",", ".")


def horas_txt(h):
    """10.5 -> '10,50'"""
    return "{:.2f}".format(h or 0).replace(".", ",")


def hhmm_txt(h):
    """10.5 -> '10:30'"""
    total = int(round((h or 0) * 60))
    return "%d:%02d" % (total // 60, total % 60)


# --------------------------------------------------------------------- datos
class Datos(object):
    def __init__(self, ruta=None):
        self.ruta = ruta or os.path.join(carpeta_datos(), "horas.sqlite3")
        self.cx = sqlite3.connect(self.ruta)
        self.cx.row_factory = sqlite3.Row
        self.cx.execute("PRAGMA journal_mode=WAL")
        self.cx.execute("PRAGMA foreign_keys=ON")
        self._preparar()

    def _preparar(self):
        c = self.cx
        c.execute("""CREATE TABLE IF NOT EXISTS trabajadores (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       nombre     TEXT    NOT NULL,
                       valor_hora REAL    NOT NULL DEFAULT 0,
                       valor_hora_extra REAL NOT NULL DEFAULT 0,
                       activo     INTEGER NOT NULL DEFAULT 1,
                       orden      INTEGER NOT NULL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS jornadas (
                       id            INTEGER PRIMARY KEY AUTOINCREMENT,
                       trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
                       fecha         TEXT    NOT NULL,
                       entrada       TEXT    NOT NULL,
                       salida        TEXT    NOT NULL,
                       colacion      INTEGER NOT NULL DEFAULT 0,
                       nota          TEXT    NOT NULL DEFAULT '')""")
        c.execute("CREATE INDEX IF NOT EXISTS ix_jornadas_fecha ON jornadas(fecha)")
        # Migracion para bases creadas antes de que existiera el valor fijo.
        columnas = [f[1] for f in c.execute("PRAGMA table_info(trabajadores)")]
        if "valor_hora_extra" not in columnas:
            c.execute("ALTER TABLE trabajadores ADD COLUMN "
                      "valor_hora_extra REAL NOT NULL DEFAULT 0")
        c.execute("""CREATE TABLE IF NOT EXISTS config (
                       clave TEXT PRIMARY KEY,
                       valor TEXT NOT NULL)""")
        for k, v in CONFIG_DEF.items():
            c.execute("INSERT OR IGNORE INTO config VALUES (?,?)", (k, v))
        c.commit()

    def cerrar(self):
        self.cx.close()

    # -- configuracion --------------------------------------------------
    def config(self):
        cfg = dict(CONFIG_DEF)
        for f in self.cx.execute("SELECT clave, valor FROM config"):
            cfg[f["clave"]] = f["valor"]
        return cfg

    def guardar_config(self, cambios):
        for k, v in cambios.items():
            self.cx.execute("INSERT INTO config VALUES (?,?) "
                            "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
                            (k, str(v)))
        self.cx.commit()

    def num(self, clave):
        try:
            return float(self.config().get(clave, CONFIG_DEF.get(clave, 0)))
        except (TypeError, ValueError):
            return float(CONFIG_DEF.get(clave, 0))

    # -- trabajadores ---------------------------------------------------
    def trabajadores(self, solo_activos=True):
        sql = "SELECT * FROM trabajadores"
        if solo_activos:
            sql += " WHERE activo=1"
        sql += " ORDER BY orden, id"
        return [dict(f) for f in self.cx.execute(sql)]

    def agregar_trabajador(self, nombre, valor_hora=0, valor_hora_extra=0):
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValueError("El nombre no puede estar vacio.")
        orden = self.cx.execute(
            "SELECT COALESCE(MAX(orden),0)+1 FROM trabajadores").fetchone()[0]
        cur = self.cx.execute(
            "INSERT INTO trabajadores (nombre, valor_hora, valor_hora_extra, orden) "
            "VALUES (?,?,?,?)",
            (nombre, float(valor_hora or 0), float(valor_hora_extra or 0), orden))
        self.cx.commit()
        return cur.lastrowid

    def editar_trabajador(self, tid, nombre, valor_hora, valor_hora_extra=0):
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValueError("El nombre no puede estar vacio.")
        self.cx.execute("UPDATE trabajadores SET nombre=?, valor_hora=?, "
                        "valor_hora_extra=? WHERE id=?",
                        (nombre, float(valor_hora or 0), float(valor_hora_extra or 0), tid))
        self.cx.commit()

    def desactivar_trabajador(self, tid):
        """No se borra: sus jornadas historicas tienen que seguir cuadrando."""
        self.cx.execute("UPDATE trabajadores SET activo=0 WHERE id=?", (tid,))
        self.cx.commit()

    def jornadas_de(self, tid):
        return self.cx.execute(
            "SELECT COUNT(*) FROM jornadas WHERE trabajador_id=?", (tid,)).fetchone()[0]

    # -- jornadas -------------------------------------------------------
    def guardar_jornada(self, jid, tid, fecha, entrada, salida, colacion, nota=""):
        datetime.strptime(fecha, "%Y-%m-%d")          # valida el formato
        if a_minutos(entrada) is None or a_minutos(salida) is None:
            raise ValueError("La hora de entrada o de salida no es valida.")
        if entrada == salida:
            raise ValueError("La entrada y la salida son la misma hora.")
        colacion = max(0, int(colacion or 0))
        if colacion >= minutos_turno(entrada, salida):
            raise ValueError("La colacion no puede durar mas que el turno.")
        if jid:
            self.cx.execute("""UPDATE jornadas SET trabajador_id=?, fecha=?, entrada=?,
                               salida=?, colacion=?, nota=? WHERE id=?""",
                            (tid, fecha, entrada, salida, colacion, nota or "", jid))
        else:
            self.cx.execute("""INSERT INTO jornadas
                               (trabajador_id, fecha, entrada, salida, colacion, nota)
                               VALUES (?,?,?,?,?,?)""",
                            (tid, fecha, entrada, salida, colacion, nota or ""))
        self.cx.commit()

    def borrar_jornada(self, jid):
        self.cx.execute("DELETE FROM jornadas WHERE id=?", (jid,))
        self.cx.commit()

    def jornadas(self, desde=None, hasta=None, tid=None):
        sql = ("SELECT j.*, t.nombre, t.valor_hora, t.valor_hora_extra FROM jornadas j "
               "JOIN trabajadores t ON t.id = j.trabajador_id WHERE 1=1")
        p = []
        if desde:
            sql += " AND j.fecha >= ?"; p.append(desde)
        if hasta:
            sql += " AND j.fecha <= ?"; p.append(hasta)
        if tid:
            sql += " AND j.trabajador_id = ?"; p.append(tid)
        sql += " ORDER BY j.fecha DESC, t.orden, j.id DESC"
        return [dict(f) for f in self.cx.execute(sql, p)]

    def total_jornadas(self):
        return self.cx.execute("SELECT COUNT(*) FROM jornadas").fetchone()[0]

    # -- respaldos ------------------------------------------------------
    def carpeta_respaldos(self):
        c = os.path.join(os.path.dirname(self.ruta), "respaldos")
        os.makedirs(c, exist_ok=True)
        return c

    def respaldar(self, destino=None, conservar=30):
        """
        Copia la base de datos. Sin destino hace la copia del dia dentro de
        respaldos/ y borra las mas viejas; con destino la guarda donde se le
        diga (un pendrive, por ejemplo).

        Usa la copia propia de SQLite y no copiar el archivo a mano, porque
        con WAL el archivo suelto puede quedar a medias.
        """
        automatico = destino is None
        if automatico:
            destino = os.path.join(self.carpeta_respaldos(),
                                   "horas-%s.sqlite3" % date.today().isoformat())
            if os.path.exists(destino):
                return None                      # ya hay copia de hoy
        otro = sqlite3.connect(destino)
        try:
            with otro:
                self.cx.backup(otro)
        finally:
            otro.close()
        if automatico:
            self._podar_respaldos(conservar)
        return destino

    def _podar_respaldos(self, conservar):
        c = self.carpeta_respaldos()
        copias = sorted(f for f in os.listdir(c)
                        if f.startswith("horas-") and f.endswith(".sqlite3"))
        for viejo in copias[:-conservar] if conservar > 0 else []:
            try:
                os.remove(os.path.join(c, viejo))
            except OSError:
                pass

    def ultimo_respaldo(self):
        """(fecha, cuantas copias hay). (None, 0) si todavia no hay ninguna."""
        try:
            copias = sorted(f for f in os.listdir(self.carpeta_respaldos())
                            if f.startswith("horas-") and f.endswith(".sqlite3"))
        except OSError:
            return None, 0
        if not copias:
            return None, 0
        return copias[-1][len("horas-"):-len(".sqlite3")], len(copias)

    def sembrar_si_vacia(self):
        if self.cx.execute("SELECT COUNT(*) FROM trabajadores").fetchone()[0]:
            return False
        for i in (1, 2, 3):
            self.agregar_trabajador("Trabajador %d" % i, 0)
        return True


# ------------------------------------------------------- valor de la hora extra
def valor_hora_extra(cfg, trabajador):
    """
    Cuanto vale una hora extra para este trabajador.

    Dos modos, elegidos en Configuracion:
      - 'recargo': la hora normal mas un porcentaje (50 % es lo legal en Chile).
      - 'fijo':    un monto en pesos escrito a mano. Si el trabajador tiene el
                   suyo, manda ese; si no, se usa el valor general.
    """
    normal = float(trabajador.get("valor_hora") or 0)
    if str(cfg.get("modo_extra", "recargo")) == "fijo":
        propio = float(trabajador.get("valor_hora_extra") or 0)
        if propio > 0:
            return propio
        try:
            return float(cfg.get("valor_extra_global") or 0)
        except (TypeError, ValueError):
            return 0.0
    try:
        recargo = float(cfg.get("recargo_extra") or 0)
    except (TypeError, ValueError):
        recargo = 0.0
    return normal * (1.0 + recargo / 100.0)


def texto_regla_extra(cfg):
    if str(cfg.get("modo_extra", "recargo")) == "fijo":
        return "monto fijo por hora extra"
    return "hora normal + %s%% de recargo" % _limpio(cfg.get("recargo_extra", "50"))


def _limpio(n):
    t = str(n)
    return t[:-2] if t.endswith(".0") else t


# --------------------------------------------------------- resumen del mes
def _extras_por_semana(jornadas, cfg):
    """
    Horas extra de cada semana completa (lunes a domingo), por trabajador,
    segun la regla configurada.

    Devuelve {(lunes, trabajador_id): {'horas':h, 'extra':e, 'por_mes':{...}}}
    """
    umbral_d = float(cfg.get("umbral_diario", 8) or 8)
    umbral_s = float(cfg.get("umbral_semanal", 45) or 45)
    regla = str(cfg.get("regla", "diaria"))

    semanas = {}
    for j in jornadas:
        clave = (lunes_de(j["fecha"]), j["trabajador_id"])
        s = semanas.setdefault(clave, {"horas": 0.0, "extra_diaria": 0.0,
                                       "por_mes": {}})
        h = horas_trabajadas(j["entrada"], j["salida"], j["colacion"])
        s["horas"] += h
        s["extra_diaria"] += extra_del_dia(h, umbral_d)
        s["por_mes"][j["fecha"][:7]] = s["por_mes"].get(j["fecha"][:7], 0.0) + h

    for s in semanas.values():
        s["horas"] = round(s["horas"], 2)
        s["extra_diaria"] = round(s["extra_diaria"], 2)
        s["extra_semanal"] = round(max(0.0, s["horas"] - umbral_s), 2)
        if regla == "semanal":
            s["extra"] = s["extra_semanal"]
        elif regla == "mayor":
            s["extra"] = max(s["extra_diaria"], s["extra_semanal"])
        else:
            s["extra"] = s["extra_diaria"]
    return semanas


def resumen_mensual(datos, anio, mes):
    """
    Todo lo que necesita el informe de un mes: por trabajador, sus turnos,
    horas, colacion, horas extra y cuanto se le paga.

    Las horas extra de las reglas semanales se reparten entre los meses que
    toca cada semana, en proporcion a las horas de cada mes. Asi las horas
    ordinarias mas las extra siempre suman las horas del mes, que es lo que
    tiene que cuadrar en una liquidacion.
    """
    cfg = datos.config()
    ym = "%04d-%02d" % (anio, mes)
    desde = "%s-01" % ym
    hasta = "%s-%02d" % (ym, ultimo_dia(anio, mes))

    del_mes = datos.jornadas(desde, hasta)

    # Para las reglas semanales hacen falta las semanas completas, que pueden
    # empezar el mes anterior o terminar el siguiente.
    borde_ini = (datetime.strptime(desde, "%Y-%m-%d").date() - timedelta(days=7)).isoformat()
    borde_fin = (datetime.strptime(hasta, "%Y-%m-%d").date() + timedelta(days=7)).isoformat()
    semanas = _extras_por_semana(datos.jornadas(borde_ini, borde_fin), cfg)

    extra_mes = {}
    for (_lunes, tid), s in semanas.items():
        horas_semana = sum(s["por_mes"].values())
        if horas_semana <= 0 or s["extra"] <= 0:
            continue
        proporcion = s["por_mes"].get(ym, 0.0) / horas_semana
        extra_mes[tid] = extra_mes.get(tid, 0.0) + s["extra"] * proporcion

    por_trabajador = {}
    for t in datos.trabajadores(solo_activos=False):
        por_trabajador[t["id"]] = {
            "id": t["id"], "nombre": t["nombre"],
            "valor_hora": float(t["valor_hora"] or 0),
            "valor_extra": valor_hora_extra(cfg, dict(t)),
            "turnos": 0, "horas": 0.0, "colacion": 0.0,
            "detalle": [],
        }

    for j in del_mes:
        r = por_trabajador.get(j["trabajador_id"])
        if r is None:
            continue
        h = horas_trabajadas(j["entrada"], j["salida"], j["colacion"])
        r["turnos"] += 1
        r["horas"] += h
        r["colacion"] += int(j["colacion"] or 0) / 60.0
        r["detalle"].append({
            "id": j["id"], "fecha": j["fecha"], "dia": nombre_dia(j["fecha"]),
            "entrada": j["entrada"], "salida": j["salida"],
            "colacion": int(j["colacion"] or 0), "horas": h,
            "extra_dia": extra_del_dia(h, float(cfg.get("umbral_diario", 8) or 8)),
            "nota": j.get("nota", ""),
        })

    filas = []
    for r in por_trabajador.values():
        if not r["turnos"]:
            continue
        r["horas"] = round(r["horas"], 2)
        r["colacion"] = round(r["colacion"], 2)
        r["extra"] = round(min(extra_mes.get(r["id"], 0.0), r["horas"]), 2)
        r["ordinarias"] = round(r["horas"] - r["extra"], 2)
        r["pago_ordinario"] = round(r["ordinarias"] * r["valor_hora"])
        r["pago_extra"] = round(r["extra"] * r["valor_extra"])
        r["total"] = r["pago_ordinario"] + r["pago_extra"]
        r["detalle"].sort(key=lambda d: (d["fecha"], d["entrada"]))
        filas.append(r)

    filas.sort(key=lambda r: r["nombre"].lower())
    totales = {
        "turnos": sum(r["turnos"] for r in filas),
        "horas": round(sum(r["horas"] for r in filas), 2),
        "colacion": round(sum(r["colacion"] for r in filas), 2),
        "ordinarias": round(sum(r["ordinarias"] for r in filas), 2),
        "extra": round(sum(r["extra"] for r in filas), 2),
        "pago_ordinario": sum(r["pago_ordinario"] for r in filas),
        "pago_extra": sum(r["pago_extra"] for r in filas),
        "total": sum(r["total"] for r in filas),
    }
    return {
        "anio": anio, "mes": mes,
        "titulo": "%s de %d" % (nombre_mes(mes).capitalize(), anio),
        "negocio": cfg.get("negocio", NEGOCIO_DEF),
        "ciudad": cfg.get("ciudad", CIUDAD_DEF),
        "cfg": cfg, "filas": filas, "totales": totales,
        "regla_extra": texto_regla_extra(cfg),
        "umbral_diario": _limpio(cfg.get("umbral_diario", "8")),
        "umbral_semanal": _limpio(cfg.get("umbral_semanal", "45")),
        "regla": str(cfg.get("regla", "diaria")),
    }
