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
    "umbral_diario": "8",          # solo para destacar dias largos; no define el pago
    "umbral_semanal": "45",        # jornada semanal legal: de aqui salen las horas extra
    "regla": "semanal",         # el pago sale del excedente SEMANAL
    "modo_extra": "recargo",    # recargo (% sobre la hora normal) | fijo (monto en pesos)
    "recargo_extra": "50",      # % sobre el valor hora, si modo_extra=recargo
    "valor_extra_global": "0",  # $ por hora extra, si modo_extra=fijo
    "negocio": NEGOCIO_DEF,
    "ciudad": CIUDAD_DEF,
}

# Las cuatro marcas del dia, SIEMPRE en este orden.
TIPOS = ["entrada", "colacion_inicio", "colacion_fin", "salida"]
ETIQUETAS = {
    "entrada":         "Entrada",
    "colacion_inicio": "Inicio de colacion",
    "colacion_fin":    "Fin de colacion",
    "salida":          "Salida",
}
# Si alguien marco entrada y se fue sin marcar salida, a las tantas horas
# dejamos de considerar esa jornada abierta y la siguiente marca empieza una nueva.
HORAS_JORNADA_ABIERTA = 20

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


def horas_de_marcas(marcas):
    """
    Horas efectivas de un dia a partir de sus marcas.

    Necesita entrada y salida. Si estan las dos de colacion, se descuenta ese
    rato. Cada tramo se mide con el resto de 24 h, asi que un turno que cruza
    la medianoche (22:00 a 06:00) sale bien.
    """
    por_tipo = {}
    for m in marcas:
        por_tipo[m["tipo"]] = m["hora"]
    if "entrada" not in por_tipo or "salida" not in por_tipo:
        return 0.0
    bruto = minutos_turno(por_tipo["entrada"], por_tipo["salida"])
    colacion = 0
    if "colacion_inicio" in por_tipo and "colacion_fin" in por_tipo:
        colacion = minutos_turno(por_tipo["colacion_inicio"], por_tipo["colacion_fin"])
    return round(max(0, bruto - colacion) / 60.0, 2)


def minutos_colacion(marcas):
    """Minutos de colacion de un dia, 0 si no estan las dos marcas."""
    por_tipo = dict((m["tipo"], m["hora"]) for m in marcas)
    if "colacion_inicio" in por_tipo and "colacion_fin" in por_tipo:
        return minutos_turno(por_tipo["colacion_inicio"], por_tipo["colacion_fin"])
    return 0


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
        # Una fila por marca. Es el formato que tambien podria alimentar un
        # reloj biometrico mas adelante: basta con insertar aqui.
        c.execute("""CREATE TABLE IF NOT EXISTS marcas (
                       id            INTEGER PRIMARY KEY AUTOINCREMENT,
                       trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
                       fecha         TEXT    NOT NULL,   -- dia laboral (el de la entrada)
                       tipo          TEXT    NOT NULL,   -- entrada|colacion_inicio|colacion_fin|salida
                       hora          TEXT    NOT NULL,   -- HH:MM, editable por el administrador
                       origen        TEXT    NOT NULL DEFAULT 'app',
                       registrado_en TEXT    NOT NULL DEFAULT '',
                       nota          TEXT    NOT NULL DEFAULT '')""")
        c.execute("CREATE INDEX IF NOT EXISTS ix_marcas ON marcas(trabajador_id, fecha)")
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
        self.migrar_jornadas_a_marcas()

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
            "SELECT COUNT(DISTINCT fecha) FROM marcas WHERE trabajador_id=?",
            (tid,)).fetchone()[0]

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

    # ================================================================
    #  MARCAS
    #  Que le toca marcar a alguien se calcula SIEMPRE desde el historial
    #  del trabajador que se pasa por parametro. No hay estado global ni
    #  compartido, asi que dos personas marcando alternadamente no se
    #  pueden mezclar. Esto importa: de aqui sale el pago.
    # ================================================================

    def marcas_de(self, tid, fecha):
        """Las marcas de ese trabajador en ese dia laboral, en orden."""
        return [dict(f) for f in self.cx.execute(
            "SELECT * FROM marcas WHERE trabajador_id=? AND fecha=? "
            "ORDER BY id", (tid, fecha))]

    def _dia_laboral(self, tid, ahora):
        """
        A que dia laboral pertenece la proxima marca de ESTE trabajador.

        Si tiene una jornada empezada y sin cerrar, la marca sigue en ese dia
        aunque el calendario ya haya cambiado: asi un turno de noche (entra
        22:00, sale 06:00) queda entero en un solo dia laboral.
        """
        fila = self.cx.execute(
            "SELECT fecha FROM marcas WHERE trabajador_id=? "
            "ORDER BY fecha DESC, id DESC LIMIT 1", (tid,)).fetchone()
        hoy = ahora.date().isoformat()
        if not fila:
            return hoy
        fecha = fila["fecha"]
        marcas = self.marcas_de(tid, fecha)
        if self.proxima_de(set(m["tipo"] for m in marcas)) is None:
            return hoy                                   # jornada completa
        entrada = [m for m in marcas if m["tipo"] == "entrada"]
        if entrada:
            ini = datetime.strptime(fecha + " " + entrada[0]["hora"], "%Y-%m-%d %H:%M")
            if (ahora - ini).total_seconds() > HORAS_JORNADA_ABIERTA * 3600:
                return hoy                               # se quedo abierta, se abandona
        return fecha

    @staticmethod
    def proxima_de(tipos_presentes):
        """La primera de las cuatro que falta. None si ya estan todas."""
        for t in TIPOS:
            if t not in tipos_presentes:
                return t
        return None

    def estado(self, tid, ahora=None):
        """Que le toca marcar a este trabajador, y como va su dia."""
        ahora = ahora or datetime.now()
        fecha = self._dia_laboral(tid, ahora)
        marcas = self.marcas_de(tid, fecha)
        proxima = self.proxima_de(set(m["tipo"] for m in marcas))
        return {
            "trabajador_id": tid, "fecha": fecha, "marcas": marcas,
            "proxima": proxima, "etiqueta": ETIQUETAS.get(proxima, ""),
            "completa": proxima is None,
            "horas": horas_de_marcas(marcas),
        }

    def marcar(self, tid, ahora=None, origen="app"):
        """
        Registra la marca que corresponda, con la hora del reloj del sistema.

        Cual es no se elige: sale del historial propio del trabajador, asi que
        desde el boton es imposible marcar fuera de orden.

        `origen` queda guardado para cuando las marcas lleguen de un reloj
        biometrico en vez de la pantalla.
        """
        ahora = ahora or datetime.now()
        est = self.estado(tid, ahora)
        if est["completa"]:
            raise ValueError(
                "Ya estan las cuatro marcas del dia %s. Si algo quedo mal, "
                "corrigelo en la pestana Jornadas." % est["fecha"])
        self.cx.execute(
            "INSERT INTO marcas (trabajador_id, fecha, tipo, hora, origen, registrado_en) "
            "VALUES (?,?,?,?,?,?)",
            (tid, est["fecha"], est["proxima"], ahora.strftime("%H:%M"),
             origen, ahora.strftime("%Y-%m-%d %H:%M:%S")))
        self.cx.commit()
        return {"tipo": est["proxima"], "etiqueta": ETIQUETAS[est["proxima"]],
                "hora": ahora.strftime("%H:%M"), "fecha": est["fecha"]}

    # -- correcciones del administrador ---------------------------------
    def editar_marca(self, mid, hora=None, tipo=None):
        m = self.cx.execute("SELECT * FROM marcas WHERE id=?", (mid,)).fetchone()
        if not m:
            raise ValueError("Esa marca ya no existe.")
        m = dict(m)
        if hora is not None:
            if a_minutos(hora) is None:
                raise ValueError("'%s' no es una hora valida. Escribela como 14:30." % hora)
            m["hora"] = hora
        if tipo is not None:
            if tipo not in TIPOS:
                raise ValueError("Tipo de marca desconocido.")
            if tipo != m["tipo"] and any(
                    x["tipo"] == tipo and x["id"] != mid
                    for x in self.marcas_de(m["trabajador_id"], m["fecha"])):
                raise ValueError("Ese dia ya tiene una marca de %s. "
                                 "Corrige o borra la otra primero." % ETIQUETAS[tipo])
            m["tipo"] = tipo
        self.cx.execute("UPDATE marcas SET hora=?, tipo=?, origen='manual' WHERE id=?",
                        (m["hora"], m["tipo"], mid))
        self.cx.commit()

    def agregar_marca(self, tid, fecha, tipo, hora):
        """Para cuando a alguien se le olvido marcar y hay que agregarla."""
        if tipo not in TIPOS:
            raise ValueError("Tipo de marca desconocido.")
        if a_minutos(hora) is None:
            raise ValueError("'%s' no es una hora valida. Escribela como 14:30." % hora)
        datetime.strptime(fecha, "%Y-%m-%d")
        if any(m["tipo"] == tipo for m in self.marcas_de(tid, fecha)):
            raise ValueError("Ese dia ya tiene una marca de %s." % ETIQUETAS[tipo])
        self.cx.execute(
            "INSERT INTO marcas (trabajador_id, fecha, tipo, hora, origen, registrado_en) "
            "VALUES (?,?,?,?,'manual',?)",
            (tid, fecha, tipo, hora, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.cx.commit()

    def borrar_marca(self, mid):
        self.cx.execute("DELETE FROM marcas WHERE id=?", (mid,))
        self.cx.commit()

    def marcas(self, desde=None, hasta=None, tid=None):
        sql = ("SELECT m.*, t.nombre FROM marcas m "
               "JOIN trabajadores t ON t.id = m.trabajador_id WHERE 1=1")
        p = []
        if desde:
            sql += " AND m.fecha >= ?"; p.append(desde)
        if hasta:
            sql += " AND m.fecha <= ?"; p.append(hasta)
        if tid:
            sql += " AND m.trabajador_id = ?"; p.append(tid)
        sql += " ORDER BY m.fecha DESC, t.orden, m.id"
        return [dict(f) for f in self.cx.execute(sql, p)]

    # -- dias armados desde las marcas ----------------------------------
    def jornadas(self, desde=None, hasta=None, tid=None):
        """
        Un dia por trabajador, armado desde sus cuatro marcas.

        Devuelve la misma forma que usaba el formato viejo (entrada, salida,
        minutos de colacion), para que los resumenes y los informes no tengan
        que saber que por debajo ahora hay marcas.
        """
        por_dia = {}
        for m in self.marcas(desde, hasta, tid):
            clave = (m["fecha"], m["trabajador_id"])
            por_dia.setdefault(clave, []).append(m)

        trabajadores = dict((t["id"], t) for t in self.trabajadores(solo_activos=False))
        salida = []
        for (fecha, tid_), marcas in por_dia.items():
            t = trabajadores.get(tid_, {})
            por_tipo = dict((x["tipo"], x["hora"]) for x in marcas)
            salida.append({
                "id": "%s|%s" % (fecha, tid_),
                "trabajador_id": tid_,
                "nombre": t.get("nombre", "?"),
                "valor_hora": t.get("valor_hora", 0),
                "valor_hora_extra": t.get("valor_hora_extra", 0),
                "fecha": fecha,
                "entrada": por_tipo.get("entrada", ""),
                "salida": por_tipo.get("salida", ""),
                "colacion": minutos_colacion(marcas),
                "colacion_inicio": por_tipo.get("colacion_inicio", ""),
                "colacion_fin": por_tipo.get("colacion_fin", ""),
                "horas": horas_de_marcas(marcas),
                "dia": nombre_dia(fecha),
                "extra_dia": 0.0,          # el pago es semanal; se llena para el informe
                "marcas": marcas,
                "completa": self.proxima_de(set(por_tipo)) is None,
                "faltan": [ETIQUETAS[t2] for t2 in TIPOS if t2 not in por_tipo],
                "nota": "",
            })
        salida.sort(key=lambda d: (d["fecha"], d["nombre"]), reverse=True)
        return salida

    def total_jornadas(self):
        return len(set((m["fecha"], m["trabajador_id"])
                       for m in self.cx.execute(
                           "SELECT fecha, trabajador_id FROM marcas")))

    def total_marcas(self):
        return self.cx.execute("SELECT COUNT(*) FROM marcas").fetchone()[0]

    def migrar_jornadas_a_marcas(self):
        """
        Pasa las jornadas del formato viejo (una fila con entrada, salida y
        minutos de colacion) a cuatro marcas. La colacion se ubica al medio del
        turno, porque el formato viejo no guardaba a que hora habia sido.
        """
        hechas = 0
        for j in self.cx.execute("SELECT * FROM jornadas ORDER BY fecha, id").fetchall():
            j = dict(j)
            if self.marcas_de(j["trabajador_id"], j["fecha"]):
                continue                                   # ya migrada
            ent = a_minutos(j["entrada"])
            if ent is None or a_minutos(j["salida"]) is None:
                continue
            bruto = minutos_turno(j["entrada"], j["salida"])
            col = int(j["colacion"] or 0)
            puestas = [("entrada", ent), ("salida", ent + bruto)]
            if 0 < col < bruto:
                medio = ent + (bruto - col) // 2
                puestas += [("colacion_inicio", medio), ("colacion_fin", medio + col)]
            for tipo, minutos in puestas:
                self.cx.execute(
                    "INSERT INTO marcas (trabajador_id, fecha, tipo, hora, origen, "
                    "registrado_en) VALUES (?,?,?,?,'migrado','')",
                    (j["trabajador_id"], j["fecha"], tipo, a_hhmm(minutos)))
            hechas += 1
        self.cx.commit()
        return hechas

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
    regla = str(cfg.get("regla", "semanal"))

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
        "regla": str(cfg.get("regla", "semanal")),
    }


# ------------------------------------------------------- resumen de la semana
def resumen_semanal(datos, lunes):
    """
    La semana de un vistazo, por trabajador.

    Es el calculo que define el pago: las horas extra son las que exceden la
    jornada semanal legal configurada. Que un dia suelto se haya pasado o
    quedado corto no cambia nada; lo que manda es el total de la semana.

    Ademas devuelve el detalle dia por dia, como informacion complementaria.
    """
    cfg = datos.config()
    domingo = (datetime.strptime(lunes, "%Y-%m-%d").date() + timedelta(days=6)).isoformat()
    semanales = float(cfg.get("umbral_semanal", 45) or 45)

    dias_por_trab = {}
    for j in datos.jornadas(lunes, domingo):
        dias_por_trab.setdefault(j["trabajador_id"], []).append(j)

    filas = []
    for t in datos.trabajadores(solo_activos=False):
        dias = sorted(dias_por_trab.get(t["id"], []), key=lambda d: d["fecha"])
        if not dias:
            continue
        horas = round(sum(d["horas"] for d in dias), 2)
        extra = round(max(0.0, horas - semanales), 2)
        ordinarias = round(horas - extra, 2)
        v_extra = valor_hora_extra(cfg, dict(t))
        incompletos = [d for d in dias if not d["completa"]]
        filas.append({
            "id": t["id"], "nombre": t["nombre"],
            "valor_hora": float(t["valor_hora"] or 0), "valor_extra": v_extra,
            "dias": dias, "turnos": len(dias),
            "horas": horas, "ordinarias": ordinarias, "extra": extra,
            "colacion": round(sum(d["colacion"] for d in dias) / 60.0, 2),
            "pago_ordinario": round(ordinarias * float(t["valor_hora"] or 0)),
            "pago_extra": round(extra * v_extra),
            "incompletos": incompletos,
        })
        filas[-1]["total"] = filas[-1]["pago_ordinario"] + filas[-1]["pago_extra"]
        filas[-1]["detalle"] = dias        # mismo nombre que usa el informe mensual

    filas.sort(key=lambda f: f["nombre"].lower())
    totales = {
        "turnos": sum(f["turnos"] for f in filas),
        "horas": round(sum(f["horas"] for f in filas), 2),
        "colacion": round(sum(f["colacion"] for f in filas), 2),
        "ordinarias": round(sum(f["ordinarias"] for f in filas), 2),
        "extra": round(sum(f["extra"] for f in filas), 2),
        "pago_ordinario": sum(f["pago_ordinario"] for f in filas),
        "pago_extra": sum(f["pago_extra"] for f in filas),
        "total": sum(f["total"] for f in filas),
    }
    return {
        "lunes": lunes, "domingo": domingo,
        "titulo": "Semana del %s al %s" % (texto_dia(lunes), texto_dia(domingo)),
        "semanales": semanales, "cfg": cfg, "filas": filas, "totales": totales,
        "regla_extra": texto_regla_extra(cfg),
        "regla": "semanal",
        "umbral_diario": _limpio(cfg.get("umbral_diario", "8")),
        "umbral_semanal": _limpio(cfg.get("umbral_semanal", "45")),
        "negocio": cfg.get("negocio", NEGOCIO_DEF),
        "ciudad": cfg.get("ciudad", CIUDAD_DEF),
    }


def texto_dia(iso):
    d = datetime.strptime(iso, "%Y-%m-%d").date()
    return "%d de %s" % (d.day, nombre_mes(d.month))
